"""Strums stage (ukulele profile): the as-played strike pattern of each section."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import numpy as np
import soundfile as sf

from youkelele.jsonio import load_model, save_model
from youkelele.music.as_played import (
    EXPLAINED_BELOW,
    MIN_SECTION_BARS,
    STAGE_UNCERTAIN_GRID_FIT,
    UNCERTAIN_BELOW,
    UNCERTAIN_BELOW_SIXTEENTH,
    _topped_vote,
    eighth_grid,
    section_summary,
    structure_test,
)
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
from youkelele.music.recall import HIGH_BAND_FMIN, gate_section
from youkelele.music.relabel import ONE_LOOP_SHARE, longest_member, one_loop_share, section_plan
from youkelele.music.riff import is_riff, onset_chroma, riff_features
from youkelele.music.trailing import NO_CHORD, trailing_silent_bars
from youkelele.schemas import Bar, Chords, Grid, SectionPattern, Strums
from youkelele.stage import Stage, StageContext


_NO_ONSETS = Onsets(times=np.zeros(0), centroid=np.zeros(0), zcr=np.zeros(0))
_EPS = 1e-6
# the riff thresholds were measured on the source signal at this rate (riff-thresholds.md)
_RIFF_SR = 22050


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
        patterns: list[SectionPattern | None] = [None] * len(plan)
        short: list[int] = []
        # a trimmed last section with no chord and no strike has nothing to strum (spec 3.5): it is
        # marked, not inherited from its neighbour
        last_bars = range(last_sec.start_bar, last_sec.end_bar - drop)
        empty_outro = (
            not any(_bar_has_chord(chords, bars[b]) for b in last_bars)
            and not any(d != "-" for b in last_bars for d in render_directions(classes[b], slots, meter))
        )
        # the riff marker (spec 4.3): one constant-Q pass over the whole source, read per section.
        # It reads the detector's own onsets, before the recall gate: the thresholds were measured
        # on those, and the gate's percussive additions would move the features.
        riff_times = today.times
        chroma = (
            _onset_chroma_at_riff_rate(y, sr, riff_times) if any(has_instrument) else np.zeros((0, 12))
        )
        for i in range(len(plan)):
            if not has_instrument[i] or (ends_song(i) and empty_outro):
                patterns[i] = SectionPattern(
                    section=i, slots=["-"] * slots, confidence=0.0, bar_repeat=0.0,
                    uncertain=True, no_instrument=True, inherited_from=None,
                )
                continue
            start, end = first_bar(i), analysed_end(i)
            section_classes = classes[start:end]
            rendered, confidence, repeat, explained = section_summary(section_classes, slots, meter)
            # the vote the section prints, as strike classes; the seed makes a re-run identical
            structured, p, density = structure_test(section_classes, _topped_vote(section_classes), seed=start)
            inside = (riff_times >= bars[start].start) & (riff_times < bars[end - 1].end)
            entropy, single_share = riff_features(chroma[inside])
            long_enough = end - start >= MIN_SECTION_BARS
            patterns[i] = SectionPattern(
                section=i, slots=rendered, confidence=confidence, bar_repeat=repeat,
                uncertain=(
                    confidence < confidence_floor or explained < EXPLAINED_BELOW
                    or not long_enough or not structured
                ),
                no_instrument=False, inherited_from=None, explained=explained, recall_boost=boosted[i],
                chance_p=p, strike_density=density,
                riff=is_riff(entropy, single_share), riff_entropy=entropy, riff_single_share=single_share,
                riff_onsets=int(np.count_nonzero(inside)),
            )
            if not long_enough:
                short.append(i)

        def donor(j: int) -> bool:
            if not 0 <= j < len(plan) or j in short:
                return False
            return not patterns[j].no_instrument

        for i in short:
            neighbours = [j for j in (i - 1, i + 1) if donor(j)]
            if not neighbours:
                continue  # keeps its own majority vector, already uncertain
            j = max(neighbours, key=lambda k: plan[k].end_bar - plan[k].start_bar)
            src = patterns[j]
            # only the donor's slots and figures are copied: the donor's chance test and riff
            # features describe the donor's bars, and this section's own measured ones are
            # discarded with them, since a section this short gives too few bars to judge
            patterns[i] = SectionPattern(
                section=i, slots=list(src.slots), confidence=src.confidence, bar_repeat=src.bar_repeat,
                uncertain=True, no_instrument=False, inherited_from=j, explained=src.explained,
                recall_boost=boosted[i],  # this section's own onsets, though the slots are the donor's
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
                slots_per_bar=slots, source=source, source_ratio=source_ratio, grid_fit=fit,
                uncertain=uncertain, patterns=patterns,
                bar_onsets=[render_directions(c, slots, meter) for c in classes],
                plan=plan,
            ),
        )
        ctx.note("source", source)
        ctx.note("grid_fit", f"{fit:.2f}")
        ctx.note("merged", merged)
        ctx.note("one_loop", f"{share:.2f}")
