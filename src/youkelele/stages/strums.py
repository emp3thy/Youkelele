"""Strums stage (ukulele profile): the as-played strike pattern of each section."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf

from youkelele.jsonio import load_model, save_model
from youkelele.music.as_played import (
    EXPLAINED_BELOW,
    STAGE_UNCERTAIN_GRID_FIT,
    UNCERTAIN_BELOW,
    UNCERTAIN_BELOW_SIXTEENTH,
    eighth_grid,
    structure_test,
)
from youkelele.music.members import first_bar_agreement, member_figures, member_spans, vector_bar
from youkelele.music.onsets import (
    Onsets,
    StrikeClass,
    choose_slots_per_bar,
    choose_source,
    detect_onsets,
    grid_fit,
    mute_mask,
    quantise_bar,
    render_directions,
    section_has_instrument,
)
from youkelele.music.pitch import PITCH_CHANGE_MIN, PitchTrack, name_notes, pitch_change_share, track_pitch
from youkelele.music.recall import HIGH_BAND_FMIN, gate_section
from youkelele.music.relabel import ONE_LOOP_SHARE, longest_member, one_loop_share, section_plan
from youkelele.music.riff import is_riff, onset_chroma, riff_features
from youkelele.music.ring import section_rings, stroke_decay_db
from youkelele.music.trailing import NO_CHORD, trailing_silent_bars
from youkelele.music.vote import VoteResult, choose_pattern
from youkelele.schemas import Bar, BarStrums, Chords, Grid, Meter, SectionPattern, Stroke, Strums
from youkelele.stage import Stage, StageContext


_NO_ONSETS = Onsets(times=np.zeros(0), centroid=np.zeros(0), zcr=np.zeros(0))
_EPS = 1e-6
# the riff thresholds were measured on the source signal at this rate (riff-thresholds.md)
_RIFF_SR = 22050
# A member of a merged section prints the section's pattern when the first bars of the two
# votes agree at least this much, else its own (spec 4.3). Measured on the one merged section
# with disagreeing members: 0.31 must print its own, 0.375 the section's (A4).
MEMBER_AGREE = 0.35
STRUMS_SCHEMA = 2  # 1.6: every bar carries its strokes (`bars`)


@dataclass
class _Member:
    """One member grid section of a planned section and what the stage measures on it."""

    position: int  # index into the planned section's members list
    start: int  # first bar
    end: int  # one past the last bar, trailing bars included
    analysed_end: int  # one past the last bar the vote, ring and riff test read
    silent: bool  # no instrument, the empty outro or nothing analysed: printed all rest (rule 7)
    vote: VoteResult | None = None
    confidence: float = 0.0
    repeat: float = 0.0
    explained: float = 0.0
    chance_p: float | None = None
    density: float | None = None
    uncertain: bool = True
    entropy: float | None = None
    single_share: float | None = None
    riff_onsets: int | None = None
    pitch_change: float | None = None
    riff: bool = False
    rings: bool = True
    ring_decay_db: float | None = None


def _onset_chroma_at_riff_rate(y: np.ndarray, sr: int, times: np.ndarray) -> np.ndarray:
    """`onset_chroma` of every onset on `y` resampled once to the rate the riff thresholds assume."""
    if len(times) == 0:
        return np.zeros((0, 12))
    if sr != _RIFF_SR:
        import librosa

        y = librosa.resample(np.asarray(y, dtype=np.float32), orig_sr=sr, target_sr=_RIFF_SR)
    return onset_chroma(y, _RIFF_SR, times)


def _bar_has_chord(chords: Chords, bar: Bar) -> bool:
    """True when a chord (any event not labelled "N") sounds during the bar."""
    return any(
        e.label != NO_CHORD and e.start < bar.end - _EPS and e.end > bar.start + _EPS
        for e in chords.events
    )


def _onset_label(muted: bool, added: bool = False) -> str:
    """The Audacity label for one detected onset: S for a strike, x for a mute, + if the recall gate added it."""
    return ("x" if muted else "S") + ("+" if added else "")


def _onsets_label_track(onsets: Onsets, muted: np.ndarray, added: np.ndarray) -> str:
    """Audacity label track: start, end (equal, a point label) and label, tab separated."""
    return "".join(
        f"{t:.3f}\t{t:.3f}\t{_onset_label(bool(m), bool(a))}\n" for t, m, a in zip(onsets.times, muted, added)
    )


def _splice(base: Onsets, pieces: list[Onsets]) -> tuple[Onsets, np.ndarray]:
    """Today's onsets plus the onsets each accepted section added, sorted by time, and the added mask.

    Each piece lies inside one planned section's longest member, a whole grid section, and
    no grid section belongs to two planned sections, so the pieces never overlap one another.
    """
    parts = [base, *pieces]
    times = np.concatenate([p.times for p in parts])
    order = np.argsort(times, kind="stable")
    added = np.concatenate([np.zeros(len(base.times), dtype=bool)] + [np.ones(len(p.times), dtype=bool) for p in pieces])
    onsets = Onsets(
        times=times[order],
        centroid=np.concatenate([p.centroid for p in parts])[order],
        zcr=np.concatenate([p.zcr for p in parts])[order],
    )
    return onsets, added[order]


def _read_mono(path: Path) -> tuple[np.ndarray, int]:
    data, sr = sf.read(str(path), dtype="float32", always_2d=True)
    return data.mean(axis=1), int(sr)


def _quantise_window(bar: Bar, slots: int) -> tuple[float, float]:
    """The time window `quantise_bar` reads for a bar: shifted back by half a slot."""
    width = (bar.end - bar.start) / slots
    return bar.start - width / 2, bar.end - width / 2


def _onset_bars(times: np.ndarray, bars: Sequence[Bar], slots: int) -> np.ndarray:
    """The bar whose quantise window holds each onset (the later bar where two windows meet), else -1."""
    out = np.full(len(times), -1)
    for b, bar in enumerate(bars):
        lo, hi = _quantise_window(bar, slots)
        out[(times >= lo) & (times < hi)] = b
    return out


def _stroke_decays(
    y: np.ndarray, sr: int, times: np.ndarray, onset_bar: np.ndarray, bars: Sequence[Bar], slots: int
) -> list[float | None]:
    """Each onset's decay in its first slot (spec 4.4), the next onset of the song bounding it."""
    decays: list[float | None] = []
    for i, t in enumerate(times):
        b = int(onset_bar[i])
        if b < 0:
            decays.append(None)
            continue
        following = float(times[i + 1]) if i + 1 < len(times) else None
        slot_seconds = (bars[b].end - bars[b].start) / slots
        decays.append(stroke_decay_db(y, sr, float(t), following, slot_seconds))
    return decays


def _slot_onsets(times: np.ndarray, muted: np.ndarray, bar: Bar, slots: int) -> list[int | None]:
    """The onset each cell of `quantise_bar(...)` took its class from; None for a rest.

    The same window, rounding and precedence as `quantise_bar` (a strike beats a mute,
    else the first onset wins), so the cells and their onsets always match.
    """
    lo, hi = _quantise_window(bar, slots)
    width = (bar.end - bar.start) / slots
    classes = ["-"] * slots
    owners: list[int | None] = [None] * slots
    for i in range(int(np.searchsorted(times, lo, side="left")), len(times)):
        t, m = float(times[i]), bool(muted[i])
        if t >= hi:
            break
        j = min(max(int(np.floor((t - bar.start) / width + 0.5)), 0), slots - 1)
        if classes[j] == "-" or (classes[j] == "x" and not m):
            classes[j] = "x" if m else "S"
            owners[j] = i
    return owners


def _note_ends(times: np.ndarray, idx: np.ndarray, bars: Sequence[Bar]) -> list[float]:
    """For each chosen onset: the next onset of the song or its bar's end, whichever is first."""
    starts = np.array([b.start for b in bars])
    ends = []
    for i in idx:
        t = float(times[i])
        bar_end = bars[max(int(np.searchsorted(starts, t, side="right")) - 1, 0)].end
        ends.append(min(float(times[i + 1]), bar_end) if i + 1 < len(times) else bar_end)
    return ends


def _vote_member(member: _Member, classes: Sequence[Sequence[StrikeClass]], slots: int, floor: float) -> None:
    """Rule 1: the member's own vote, figures, chance test and certainty."""
    bars = classes[member.start : member.analysed_end]
    vote = choose_pattern(bars)
    # a unit-2 vote is tested by its first bar, the vote's representative
    structured, p, density = structure_test(bars, vote.vector[:slots], seed=member.start)
    confidence, repeat, explained = member_figures(bars, vote.vector, vote.unit, slots)
    member.vote, member.chance_p, member.density = vote, p, density
    member.confidence, member.repeat, member.explained = confidence, repeat, explained
    # no length term: a short member prints its own vote, greyed when the test fails (spec 4.5)
    member.uncertain = confidence < floor or explained < EXPLAINED_BELOW or not structured


def _ring_member(member: _Member, onset_bar: np.ndarray, decays: Sequence[float | None], mix_source: bool) -> None:
    """Rule 4: the member rings when its strokes' median decay is low; on the full mix always."""
    inside = np.flatnonzero((onset_bar >= member.start) & (onset_bar < member.analysed_end))
    rings, member.ring_decay_db = section_rings([decays[i] for i in inside])
    # drums make the mix's decay meaningless, so the sheet draws no short strokes from it
    member.rings = True if mix_source else rings


def _riff_inside(member: _Member, riff_times: np.ndarray, bars: Sequence[Bar]) -> np.ndarray:
    """Mask of the detector's own onsets inside the member's analysed bars."""
    return (riff_times >= bars[member.start].start) & (riff_times < bars[member.analysed_end - 1].end)


def _riff_features_member(member: _Member, riff_times: np.ndarray, chroma: np.ndarray, bars: Sequence[Bar]) -> None:
    """Rule 3, first half: 1.5's two chroma features on the member's own onsets."""
    inside = _riff_inside(member, riff_times, bars)
    member.entropy, member.single_share = riff_features(chroma[inside])
    member.riff_onsets = int(np.count_nonzero(inside))


def _riff_test(member: _Member, track: PitchTrack, riff_times: np.ndarray, bars: Sequence[Bar]) -> None:
    """Rule 3, second half, for a member whose chroma features pass: the pitch must also change.

    Only such members are named, so a section's share never depends on whether another
    section happened to start the pitch tracker.
    """
    idx = np.flatnonzero(_riff_inside(member, riff_times, bars))
    notes = name_notes(track, riff_times[idx], _note_ends(riff_times, idx, bars))
    member.pitch_change = pitch_change_share(notes)
    member.riff = member.pitch_change is not None and member.pitch_change >= PITCH_CHANGE_MIN


def _prints_section(member: _Member, longest: _Member, slots: int) -> bool:
    """Rule 5: the member prints its section's (the longest member's) pattern rather than its own."""
    if member is longest:
        return True
    if longest.silent:
        return False
    return first_bar_agreement(member.vote.vector, longest.vote.vector, slots) >= MEMBER_AGREE


def _section_pattern(k: int, longest: _Member, slots: int, meter: Meter, boosted: bool) -> SectionPattern:
    """Rule 2: the planned section's pattern is its longest member's, or 1.5's all-rest record."""
    if longest.silent:
        return SectionPattern(
            section=k, slots=["-"] * slots, confidence=0.0, bar_repeat=0.0,
            uncertain=True, no_instrument=True, inherited_from=None,
        )
    vote = longest.vote
    return SectionPattern(
        section=k, slots=render_directions(vote.vector[:slots], slots, meter),
        confidence=longest.confidence, bar_repeat=longest.repeat, uncertain=longest.uncertain,
        no_instrument=False, inherited_from=None, explained=longest.explained, recall_boost=boosted,
        chance_p=longest.chance_p, strike_density=longest.density,
        riff=longest.riff, riff_entropy=longest.entropy, riff_single_share=longest.single_share,
        riff_onsets=longest.riff_onsets,
        candidate=vote.candidate, score_majority=vote.score_majority, score_medoid=vote.score_medoid,
        unit=vote.unit, pitch_change_share=longest.pitch_change,
        rings=longest.rings, ring_decay_db=longest.ring_decay_db,
    )


def _bar_records(
    member: _Member, longest: _Member, slots: int, meter: Meter, rendered: Sequence[Sequence[str]],
    owners: Callable[[int], list[int | None]], decays: Sequence[float | None],
) -> list[BarStrums]:
    """Rules 5 to 7: one record per bar of the member, trailing bars included."""
    if member.silent:
        return [
            BarStrums(index=b, member=member.position, strokes=[], pattern=["-"] * slots, uncertain=True)
            for b in range(member.start, member.end)
        ]
    shown = longest if _prints_section(member, longest, slots) else member
    records = []
    for b in range(member.start, member.end):
        cell = vector_bar(shown.vote.vector, shown.vote.unit, slots, b - member.start)
        strokes = [
            Stroke(slot=j, kind=rendered[b][j], rings=member.rings, decay_db=decays[i])
            for j, i in enumerate(owners(b))
            if i is not None
        ]
        records.append(
            BarStrums(
                index=b, member=member.position, strokes=strokes,
                pattern=render_directions(cell, slots, meter), unit=shown.vote.unit,
                confidence=shown.confidence, chance_p=shown.chance_p, uncertain=shown.uncertain,
                riff=member.riff,
            )
        )
    return records


class StrumsStage(Stage):
    name = "strums"
    requires = (
        "separate/stems/guitar.wav",
        "separate/stems/other.wav",
        "ingest/audio.wav",
        "grid/grid.json",
        "harmony/chords.json",
    )
    produces = ("strums/strums.json",)

    def __init__(self, onset_detector: Callable[..., Onsets] = detect_onsets) -> None:
        """`onset_detector(y, sr)` gives today's onsets and `onset_detector(y, sr, fmin=...)` the high band's."""
        self._detect = onset_detector

    def run(self, ctx: StageContext) -> None:
        guitar, sr_g = _read_mono(ctx.input("separate/stems/guitar.wav"))
        other, sr_o = _read_mono(ctx.input("separate/stems/other.wav"))
        mix, sr = _read_mono(ctx.input("ingest/audio.wav"))
        if sr_g != sr or sr_o != sr:
            raise ValueError(f"sample rates differ: guitar {sr_g}, other {sr_o}, mix {sr}")
        grid = load_model(ctx.input("grid/grid.json"), Grid)
        chords = load_model(ctx.input("harmony/chords.json"), Chords)
        n = min(len(guitar), len(other), len(mix))
        guitar, other, mix = guitar[:n], other[:n], mix[:n]

        source, y, source_ratio = choose_source(guitar, other, mix)
        today = self._detect(y, sr)
        bars, meter = grid.bars, grid.meter
        slots = choose_slots_per_bar(today, bars, meter, grid.bpm)
        fit = grid_fit(today, bars, slots)

        # bars after the last chord are silence or noise: the last section's vote and gate ignore them.
        # The score builder calls trailing_silent_bars the same way; the two calls must stay in step,
        # or the sheet would print bars whose strokes the pattern never saw.
        last_sec = grid.sections[-1]
        drop = trailing_silent_bars(chords, bars, cap=last_sec.end_bar - last_sec.start_bar)
        if drop:
            ctx.log(f"  ignoring {drop} trailing bars after the last chord")

        # the section plan (spec 3.3): every per-section figure is read over the bars of the planned
        # section's longest member; a merged fragment is absorbed for naming, not for strumming
        plan = section_plan(grid, chords)
        members = [longest_member(sec, grid) for sec in plan]

        def ends_song(i: int) -> bool:
            """The member is the grid's last section (members are whole grid sections)."""
            return members[i][1] == last_sec.end_bar

        def first_bar(i: int) -> int:
            return members[i][0]

        def analysed_end(i: int) -> int:
            return members[i][1] - (drop if ends_song(i) else 0)

        has_instrument: list[bool] = []
        for i in range(len(plan)):
            a = int(round(bars[first_bar(i)].start * sr))
            b = int(round(bars[analysed_end(i) - 1].end * sr))
            has_instrument.append(section_has_instrument(y[a:b], mix[a:b]))

        # recall gate (spec 4.3): per section, today's onsets or their union with the high band's.
        # The gate is off on the sixteenth grid, so the high band is not detected there at all.
        eighths = eighth_grid(slots, meter)
        high = self._detect(y, sr, fmin=HIGH_BAND_FMIN) if eighths else _NO_ONSETS
        boosted = [False] * len(plan)
        pieces: list[Onsets] = []
        for i in range(len(plan)):
            if not has_instrument[i]:
                continue  # nothing is printed for it, so nothing is recovered
            section_onsets, added, decision = gate_section(
                today, high, y, sr, bars[first_bar(i):analysed_end(i)], slots, fit, meter
            )
            if decision.accepted:
                boosted[i] = True
                pieces.append(
                    Onsets(
                        times=section_onsets.times[added],
                        centroid=section_onsets.centroid[added],
                        zcr=section_onsets.zcr[added],
                    )
                )
                ctx.log(f"  recall boost: section {i}, {decision.before:.1f} -> {decision.after:.1f} strikes per bar")
        onsets, added = _splice(today, pieces)

        muted = mute_mask(onsets, enabled=source != "mix")
        if ctx.options.debug:
            # optional diagnostic, so not in produces
            (ctx.out_dir / "onsets.txt").write_text(_onsets_label_track(onsets, muted, added), encoding="utf-8")
        classes: list[list[StrikeClass]] = [quantise_bar(onsets, muted, bar, slots) for bar in bars]

        # the confidence floor depends on the grid (spec 4.2; the evidence is beside the constants)
        confidence_floor = UNCERTAIN_BELOW if eighths else UNCERTAIN_BELOW_SIXTEENTH
        rendered = [render_directions(c, slots, meter) for c in classes]
        # a trimmed last section with no chord and no strike has nothing to strum (spec 3.5): it is
        # marked all rest, not given a pattern
        last_bars = range(last_sec.start_bar, last_sec.end_bar - drop)
        empty_outro = (
            not any(_bar_has_chord(chords, bars[b]) for b in last_bars)
            and not any(d != "-" for b in last_bars for d in rendered[b])
        )

        def new_member(position: int, start: int, end: int) -> _Member:
            trimmed = end - (drop if end == last_sec.end_bar else 0)
            if trimmed <= start or (end == last_sec.end_bar and empty_outro):
                return _Member(position, start, end, trimmed, silent=True)
            a, b = int(round(bars[start].start * sr)), int(round(bars[trimmed - 1].end * sr))
            return _Member(position, start, end, trimmed, silent=not section_has_instrument(y[a:b], mix[a:b]))

        # every planned section votes per member (spec 4.3); its own figures are its longest member's
        sections: list[list[_Member]] = []
        longest: list[_Member] = []
        for k, sec in enumerate(plan):
            spans = member_spans(sec, grid)
            sections.append([new_member(p, s, e) for p, (s, e) in enumerate(spans)])
            longest.append(sections[k][spans.index(members[k])])
        voiced = [m for sec in sections for m in sec if not m.silent]

        # the riff marker (spec 4.3): one constant-Q pass over the whole source, read per member.
        # It reads the detector's own onsets, before the recall gate: the thresholds were measured
        # on those, and the gate's percussive additions would move the features.
        riff_times = today.times
        chroma = _onset_chroma_at_riff_rate(y, sr, riff_times) if voiced else np.zeros((0, 12))
        # the ring flag (spec 4.4) reads every stroke the sheet prints: the onsets after the gate
        onset_bar = _onset_bars(onsets.times, bars, slots)
        decays = _stroke_decays(y, sr, onsets.times, onset_bar, bars, slots)
        for m in voiced:
            _vote_member(m, classes, slots, confidence_floor)
            _ring_member(m, onset_bar, decays, mix_source=source == "mix")
            _riff_features_member(m, riff_times, chroma, bars)
        # the pitch tracker runs over the whole stem, so at most once, and only when needed (spec 5.1)
        candidates = [m for m in voiced if is_riff(m.entropy, m.single_share)]
        if candidates:
            track = track_pitch(y, sr)
            for m in candidates:
                _riff_test(m, track, riff_times, bars)

        patterns = [_section_pattern(k, longest[k], slots, meter, boosted[k]) for k in range(len(plan))]

        def owners(b: int) -> list[int | None]:
            return _slot_onsets(onsets.times, muted, bars[b], slots)

        bar_records = sorted(
            (
                record
                for k, sec in enumerate(sections)
                for m in sec
                for record in _bar_records(m, longest[k], slots, meter, rendered, owners, decays)
            ),
            key=lambda r: r.index,
        )

        uncertain = fit < STAGE_UNCERTAIN_GRID_FIT
        ctx.log(f"  source {source} (ratio {source_ratio:.2f}), {slots} slots per bar, grid fit {fit:.2f}")
        merged = (
            f"{len(grid.sections)} grid sections into {len(plan)}" if len(plan) < len(grid.sections) else "none"
        )
        if len(plan) < len(grid.sections):
            ctx.log(f"  merged {merged}")
        share = one_loop_share(grid, chords)
        if share >= ONE_LOOP_SHARE:
            ctx.log(f"  verse and chorus share their chords (share {share:.2f})")
        save_model(
            ctx.output("strums/strums.json"),
            Strums(
                schema_version=STRUMS_SCHEMA,
                slots_per_bar=slots, source=source, source_ratio=source_ratio, grid_fit=fit,
                uncertain=uncertain, patterns=patterns,
                bar_onsets=rendered,
                plan=plan,
                bars=bar_records,
            ),
        )
        ctx.note("source", source)
        ctx.note("grid_fit", f"{fit:.2f}")
        ctx.note("merged", merged)
        ctx.note("one_loop", f"{share:.2f}")
