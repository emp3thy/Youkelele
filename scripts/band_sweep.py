"""Sweep one named constant against the truth files, with leave-one-song-out (spec 1.8, 9.3).

    uv run python scripts/band_sweep.py --runs runs --truth truth --constant REST_RATIO_MIN \
        --from 0.02 --to 0.10 --step 0.005

Tooling, not a stage: it reads every run folder that has a truth folder of the same name,
recomputes the constant's decision from figures the run already stored, and never writes.
The constant is set on its module (as `monkeypatch.setattr` would) for each swept value and
restored afterwards. It prints the metric pooled over the songs at each value; then, for
each song held out, the best value over the other songs and the band of values tying it;
then whether the current value sits inside every held-out band.

- `REST_RATIO_MIN`, `REST_LOW_SHARE_MIN`: per-bar rest F (`score_rests`), each bar's `rests`
  flag recomputed from its stored `energy_ratio` and `low_share`.
- `BASS_STEM_MAX`, `OWN_LOW_SHARE_MIN`: the bass-on-stem gate's precision and recall over
  `riffs.txt`'s labelled ranges, `bleed` the positive label, from each section's four stored
  figures.
- `PERIOD2_MIN_PAIRS`, `MIN_SLOT_SUPPORT`, `MIN_VOTE_BARS`: false certain plus false grey
  (`score_patterns`), every voiced member re-voted from `bar_onsets` and the stored `rests`
  flags with the stage's own functions (`revote`).
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType

from youkelele.jsonio import load_model
from youkelele.music import as_played, bleed, rests, vote
from youkelele.music.as_played import (
    EXPLAINED_BELOW,
    UNCERTAIN_BELOW,
    UNCERTAIN_BELOW_SIXTEENTH,
    eighth_grid,
    structure_test,
)
from youkelele.music.bleed import BleedFigures, bass_on_stem
from youkelele.music.compat import with_bars
from youkelele.music.members import aligned_agreement, member_figures, member_spans, section_offset, vector_bar
from youkelele.music.onsets import render_directions
from youkelele.music.relabel import longest_member
from youkelele.music.trailing import trailing_silent_bars
from youkelele.music.vote import VoteResult, align_to_first_bar, choose_pattern
from youkelele.schemas import BarStrums, Chords, Grid, SectionPattern, Strums
from youkelele.stages.strums import MEMBER_AGREE
from youkelele.truth import (
    REST_LABELS,
    RESTING,
    SKIPPED,
    false_certain,
    false_grey,
    read_labels,
    read_patterns,
    score_patterns,
    score_rests,
)

_TIE = 1e-9  # metric values this close count as equal
_FOLD = {"D": "S", "U": "S"}  # the printed alphabet back to strike classes


@dataclass
class Song:
    """One run and its truth, loaded once before the sweep."""

    name: str
    strums: Strums
    grid: Grid
    chords: Chords
    truth: list  # the records of the truth file the constant's metric reads
    gated: set[int] = field(default_factory=set)  # bars of a gated longest member: the energy floor alone
    fixed: set[int] = field(default_factory=set)  # bars whose stored rest flag the rule does not reproduce


@dataclass
class Point:
    value: float
    objective: float | None  # the metric the best value is chosen on; None when nothing was scored
    counts: dict[str, int]


@dataclass
class HeldOut:
    song: str
    best: float | None  # the middle of the band (the lower of two middles)
    band: tuple[float, float] | None  # the widest run of swept values tying the best metric
    objective: float | None


@dataclass
class SweepResult:
    constant: str
    module: str
    current: float
    metric: str
    short: str  # the metric's name on a held-out line
    higher_is_better: bool
    songs: list[str]  # the songs with something scored, pooled
    unscored: list[str]  # songs with a truth folder but nothing the metric scores
    pooled: list[Point]
    held_out: list[HeldOut]
    inside: bool | None  # the current value inside every held-out band; None when no band exists
    columns: list[str]
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Metric:
    label: str
    short: str
    truth_file: str
    reader: Callable[[Path], list]
    counts: Callable[[Song], dict[str, int] | None]  # None when the song has nothing scored
    objective: Callable[[dict[str, int]], float | None]
    columns: list[str]
    higher_is_better: bool


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _f(hits: int, false_pos: int, false_neg: int) -> float | None:
    return _ratio(2 * hits, 2 * hits + false_pos + false_neg)


# ---- rests: REST_RATIO_MIN, REST_LOW_SHARE_MIN


def _bar_rests(bar: BarStrums, gated: bool) -> bool:
    """The rest rule at the module's current constants; a gated member's bar keeps the energy
    floor alone (1.8 spec 6), as the stage's `_member_bar_holds` does."""
    if gated:
        return bar.energy_ratio < rests.REST_RATIO_MIN
    return not rests.bar_holds(bar.energy_ratio, bar.low_share)


def _gated_bars(strums: Strums, grid: Grid) -> set[int]:
    """Bars of the longest member of each planned section whose pattern is gated. A shorter
    member's own gate is not stored, so its bars take the full rule."""
    gated: set[int] = set()
    for sec, pattern in zip(strums.plan, strums.patterns):
        if pattern.bass_on_stem:
            start, end = longest_member(sec, grid)
            gated.update(range(start, end))
    return gated


def _fixed_bars(strums: Strums, gated: set[int]) -> set[int]:
    """Bars the rule at the stage's constants does not reproduce, which keep their stored flag:
    those without figures (before 1.7), and those of a member whose section-level cut failed
    (they carry `rests` False whatever their figures)."""
    return {
        b.index for b in strums.bars
        if b.energy_ratio is None or b.low_share is None or _bar_rests(b, b.index in gated) != b.rests
    }


def rest_flags(song: Song) -> Strums:
    """A copy of the song's strums with every bar's `rests` flag recomputed at the current constants."""
    bars = [
        b if b.index in song.fixed else b.model_copy(update={"rests": _bar_rests(b, b.index in song.gated)})
        for b in song.strums.bars
    ]
    return song.strums.model_copy(update={"bars": bars})


def _rest_counts(song: Song) -> dict[str, int] | None:
    strums = rest_flags(song)
    _, _, false_rests, false_holds, _ = score_rests(song.truth, strums)
    # the bars score_rests scores, to recover its hits: the last label of a bar wins, contested is skipped
    recorded = {b.index for b in strums.bars}
    labels = {i: t.label for t in song.truth if t.label in REST_LABELS for i in range(t.start, t.end)}
    scored = [label in RESTING for i, label in labels.items() if label not in SKIPPED and i in recorded]
    if not scored:
        return None
    return {"hits": sum(scored) - false_holds, "false rests": false_rests, "false holds": false_holds}


def _rest_objective(c: dict[str, int]) -> float | None:
    return _f(c["hits"], c["false rests"], c["false holds"])


# ---- the bass-on-stem gate: BASS_STEM_MAX, OWN_LOW_SHARE_MIN


def _figures(pattern: SectionPattern) -> BleedFigures | None:
    values = (pattern.low_mix_share_bass, pattern.low_mix_share_source, pattern.low_own_share, pattern.bass_stem_ratio)
    return None if any(v is None for v in values) else BleedFigures(*values)


def _range_figures(song: Song, start: int, end: int) -> list[BleedFigures]:
    """The stored figures of every planned section the bar range overlaps (none before 1.8)."""
    spans = [(p.start_bar, p.end_bar) for p in song.strums.plan] or [
        (s.start_bar, s.end_bar) for s in song.grid.sections
    ]
    found = [
        _figures(song.strums.patterns[k])
        for k, (a, b) in enumerate(spans)
        if a < end and start < b and k < len(song.strums.patterns)
    ]
    return [f for f in found if f is not None]


def _unmeasured(song: Song) -> int:
    """Labelled ranges the gate cannot be scored on: no overlapping section stored its figures."""
    return sum(1 for t in song.truth if not _range_figures(song, t.start, t.end))


def _gate_counts(song: Song) -> dict[str, int] | None:
    """The gate over each labelled range: it fires when it fires on any planned section the
    range overlaps. A range over sections with no stored figures (runs before 1.8) is not scored."""
    counts = {"true": 0, "false": 0, "missed": 0}
    scored = False
    for t in song.truth:
        figures = _range_figures(song, t.start, t.end)
        if not figures:
            continue
        scored = True
        fired = any(bass_on_stem(f) for f in figures)
        positive = t.label == "bleed"
        if fired and positive:
            counts["true"] += 1
        elif fired:
            counts["false"] += 1
        elif positive:
            counts["missed"] += 1
    return counts if scored else None


def _gate_objective(c: dict[str, int]) -> float | None:
    return _f(c["true"], c["false"], c["missed"])


# ---- the vote: PERIOD2_MIN_PAIRS, MIN_SLOT_SUPPORT, MIN_VOTE_BARS


@dataclass
class _Voice:
    """A voiced member's vote, as the stage's `_Member` carries it."""

    position: int
    start: int
    end: int
    holding: list[int]
    riff: bool
    vote: VoteResult
    confidence: float
    chance_p: float | None
    uncertain: bool
    voted_bars: list[int]
    dropped_bars: list[int]
    confidence_all_bars: float
    chance_p_all_bars: float | None


def revote(strums: Strums, grid: Grid, chords: Chords) -> Strums:
    """Every voiced member re-voted as `stages/strums.py` votes it, at the current constants.

    The one place the stage's order of operations is reproduced, so a mismatch shows here:
    the member spans from the plan (`member_spans`), the trailing silent bars dropped, the
    holding bars from the stored `rests` flags, `bar_onsets` with D and U folded to S;
    `_vote_member` (choose_pattern, structure_test seeded by the member's first bar,
    member_figures, the reading over the whole analysed span, the certainty rules); then
    `_align_member` and `_prints_section` and `_bar_records` for the printed rows. A silent
    member and a resting bar keep their stored record. Only the longest member's gate is
    stored, so a shorter member is taken as ungated. The nearest rival (top2) is not recomputed.
    """
    slots, meter = strums.slots_per_bar, grid.meter
    floor = UNCERTAIN_BELOW if eighth_grid(slots, meter) else UNCERTAIN_BELOW_SIXTEENTH
    classes = [[_FOLD.get(c, c) for c in row] for row in strums.bar_onsets]
    records = {r.index: r for r in with_bars(strums, grid).bars}
    last = grid.sections[-1]
    drop = trailing_silent_bars(chords, grid.bars, cap=last.end_bar - last.start_bar)
    patterns = list(strums.patterns)

    def voice(position: int, start: int, end: int, gated: bool) -> _Voice | None:
        trimmed = end - (drop if end == last.end_bar else 0)
        holding = [b for b in range(start, trimmed) if not records[b].rests]
        rows = [records[b] for b in range(start, end)]
        silent = not holding or all(
            r.uncertain and not r.strokes and all(c == "-" for c in r.pattern) and r.confidence == 0.0 for r in rows
        )
        if silent:
            return None
        bars = [classes[b] for b in holding]
        v = choose_pattern(bars)
        structured, p, _ = structure_test(bars, v.vector, seed=start)
        confidence, _, explained = member_figures(bars, v.vector, v.unit, slots)
        all_bars = [classes[b] for b in range(start, trimmed)]
        all_vector = align_to_first_bar(v.vector, v.unit, (holding[0] - start) % 2)
        confidence_all, _, _ = member_figures(all_bars, all_vector, v.unit, slots)
        structured_all, p_all, _ = structure_test(all_bars, v.vector, seed=start)
        voted = [holding[i] for i in v.voted]
        uncertain = (
            confidence < floor
            or explained < EXPLAINED_BELOW
            or not structured
            or confidence_all < floor
            or not structured_all
            or len(voted) < as_played.MIN_VOTE_BARS
            or gated
        )
        return _Voice(
            position, start, end, holding, any(r.riff for r in rows), v, confidence, p, uncertain,
            voted, [holding[i] for i in v.dropped], confidence_all, p_all,
        )

    for k, sec in enumerate(strums.plan):
        spans = member_spans(sec, grid)
        longest_at = spans.index(longest_member(sec, grid))
        gated = k < len(patterns) and patterns[k].bass_on_stem
        voices = [voice(p, s, e, gated and p == longest_at) for p, (s, e) in enumerate(spans)]
        longest = voices[longest_at]
        for member in voices:
            if member is None:
                continue
            shown, offset = member, 0
            if member is not longest and not member.riff and longest is not None:
                own_bars = [classes[b] for b in member.holding]
                aligned = section_offset(own_bars, longest.vote.vector, longest.vote.unit, slots)
                agreement = aligned_agreement(member.vote.vector, longest.vote.vector, longest.vote.unit, slots, aligned)
                if agreement >= MEMBER_AGREE:
                    shown, offset = longest, aligned
            for b in range(member.start, member.end):
                if records[b].rests:
                    continue
                cell = vector_bar(shown.vote.vector, shown.vote.unit, slots, b - member.holding[0] + offset)
                records[b] = records[b].model_copy(update={
                    "pattern": render_directions(cell, slots, meter), "unit": shown.vote.unit,
                    "confidence": shown.confidence, "chance_p": shown.chance_p, "uncertain": shown.uncertain,
                })
        if longest is not None and k < len(patterns):
            patterns[k] = patterns[k].model_copy(update={
                "slots": render_directions(longest.vote.vector[:slots], slots, meter),
                "confidence": longest.confidence, "uncertain": longest.uncertain, "unit": longest.vote.unit,
                "chance_p": longest.chance_p, "candidate": longest.vote.candidate,
                "score_majority": longest.vote.score_majority, "score_medoid": longest.vote.score_medoid,
                "voted_bars": longest.voted_bars, "dropped_bars": longest.dropped_bars,
                "confidence_all_bars": longest.confidence_all_bars, "chance_p_all_bars": longest.chance_p_all_bars,
            })
    bars = [records[i] for i in sorted(records)]
    return strums.model_copy(update={"patterns": patterns, "bars": bars})


def _vote_counts(song: Song) -> dict[str, int] | None:
    if not song.truth:
        return None
    scores = score_patterns(song.truth, revote(song.strums, song.grid, song.chords), song.grid)
    return {"false certain": false_certain(scores), "false grey": false_grey(scores)}


def _vote_objective(c: dict[str, int]) -> int:
    return c["false certain"] + c["false grey"]


# ---- the constants


_RESTS = Metric(
    "per-bar rest F", "F", "rests.txt", read_labels, _rest_counts, _rest_objective,
    ["hits", "false rests", "false holds"], higher_is_better=True,
)
_GATE = Metric(
    "bass-on-stem gate F over riffs.txt's bleed labels", "F", "riffs.txt", read_labels, _gate_counts, _gate_objective,
    ["true", "false", "missed"], higher_is_better=True,
)
_VOTE = Metric(
    "false certain plus false grey", "errors", "patterns.txt", read_patterns, _vote_counts, _vote_objective,
    ["false certain", "false grey"], higher_is_better=False,
)
CONSTANTS: dict[str, tuple[ModuleType, Metric]] = {
    "REST_RATIO_MIN": (rests, _RESTS),
    "REST_LOW_SHARE_MIN": (rests, _RESTS),
    "BASS_STEM_MAX": (bleed, _GATE),
    "OWN_LOW_SHARE_MIN": (bleed, _GATE),
    "PERIOD2_MIN_PAIRS": (vote, _VOTE),
    "MIN_SLOT_SUPPORT": (as_played, _VOTE),
    "MIN_VOTE_BARS": (as_played, _VOTE),
}


def _load(name: str, run: Path, truth_dir: Path, metric: Metric) -> Song:
    strums = load_model(run / "04_strums" / "strums.json", Strums)
    grid = load_model(run / "02_grid" / "grid.json", Grid)
    chords = load_model(run / "03_harmony" / "chords.json", Chords)
    path = truth_dir / metric.truth_file
    song = Song(name, strums, grid, chords, metric.reader(path) if path.exists() else [])
    song.gated = _gated_bars(strums, grid)
    song.fixed = _fixed_bars(strums, song.gated)  # at the stage's constants, before any is moved
    return song


def _typed(constant: str, current: object, value: float) -> float:
    """The swept value in the constant's own type: an integer constant takes whole numbers only."""
    if isinstance(current, int):
        if value != int(value):
            raise ValueError(f"{constant} is a whole number; cannot sweep it at {value}")
        return int(value)
    return float(value)


def _better(a: float, b: float, higher: bool) -> bool:
    return a > b + _TIE if higher else a < b - _TIE


def _band(values: list[float], objectives: list[float | None], higher: bool) -> HeldOut:
    """The best metric, the widest run of consecutive values tying it (the earliest on a tie of
    widths) and the run's middle value."""
    scored = [o for o in objectives if o is not None]
    if not scored:
        return HeldOut("", None, None, None)
    best = scored[0]
    for o in scored[1:]:
        if _better(o, best, higher):
            best = o
    runs: list[list[int]] = []
    for i, o in enumerate(objectives):
        if o is not None and abs(o - best) <= _TIE:
            if runs and runs[-1][-1] == i - 1:
                runs[-1].append(i)
            else:
                runs.append([i])
    widest = max(runs, key=len)  # max keeps the first of equal lengths
    return HeldOut("", values[widest[(len(widest) - 1) // 2]], (values[widest[0]], values[widest[-1]]), best)


def _pool(per_song: dict[str, list[dict[str, int] | None]], songs: list[str], i: int) -> dict[str, int] | None:
    """The songs' counts at the i-th value, summed; None when none of them scored."""
    counts = [per_song[s][i] for s in songs if per_song[s][i] is not None]
    if not counts:
        return None
    return {c: sum(x[c] for x in counts) for c in counts[0]}


def sweep(constant: str, values: list[float], runs: dict[str, Path], truths: dict[str, Path]) -> SweepResult:
    """The pooled metric at each value, each held-out song's best and band, and the verdict.

    `runs` and `truths` map a song's name to its run folder and its truth folder; only songs in
    both are read. The constant is restored when the sweep ends, however it ends.
    """
    if constant not in CONSTANTS:
        raise ValueError(f"unknown constant {constant!r}; expected one of {', '.join(CONSTANTS)}")
    module, metric = CONSTANTS[constant]
    current = getattr(module, constant)
    typed = [_typed(constant, current, v) for v in values]
    names = sorted(set(runs) & set(truths))
    songs = [_load(n, Path(runs[n]), Path(truths[n]), metric) for n in names]

    per_song: dict[str, list[dict[str, int] | None]] = {s.name: [] for s in songs}
    try:
        for value in typed:
            setattr(module, constant, value)
            for song in songs:
                per_song[song.name].append(metric.counts(song))
    finally:
        setattr(module, constant, current)

    scored = [s for s in names if any(c is not None for c in per_song[s])]
    unscored = [s for s in names if s not in scored]

    def curve(pool: list[str]) -> list[Point]:
        points = []
        for i, value in enumerate(typed):
            counts = _pool(per_song, pool, i)
            points.append(Point(value, metric.objective(counts) if counts else None, counts or {}))
        return points

    pooled = curve(scored)
    held_out = []
    for song in scored:
        others = curve([s for s in scored if s != song])
        h = _band(typed, [p.objective for p in others], metric.higher_is_better)
        h.song = song
        held_out.append(h)
    bands = [h.band for h in held_out if h.band is not None]
    inside = all(lo - _TIE <= current <= hi + _TIE for lo, hi in bands) if bands else None
    notes = []
    if metric is _GATE:
        unmeasured = sum(_unmeasured(s) for s in songs)
        if unmeasured:
            notes.append(f"{unmeasured} labelled ranges lie on sections without the bleed figures (runs before 1.8): not scored")
    missing = sorted(set(truths) - set(runs))
    if missing:
        notes.append(f"no run for: {', '.join(missing)}")
    return SweepResult(
        constant, module.__name__, current, metric.label, metric.short, metric.higher_is_better, scored, unscored,
        pooled, held_out, inside, metric.columns, notes,
    )


def _number(x: float | None) -> str:
    if x is None:
        return "n/a"
    return str(x) if isinstance(x, int) else f"{x:.3f}"


def format_sweep(r: SweepResult) -> str:
    direction = "higher" if r.higher_is_better else "lower"
    lines = [
        f"{r.constant} ({r.module}), current {r.current:g}",
        f"metric: {r.metric}, pooled over {len(r.songs)} songs ({direction} is better)",
    ]
    if r.unscored:
        lines.append(f"nothing scored on: {', '.join(r.unscored)}")
    lines.extend(r.notes)
    lines.append("")
    header = ["value", r.short, *r.columns]
    rows = [header] + [
        [f"{p.value:g}", _number(p.objective), *(str(p.counts[c]) if p.counts else "-" for c in r.columns)]
        for p in r.pooled
    ]
    widths = [max(len(row[j]) for row in rows) for j in range(len(header))]
    lines.extend("  ".join(cell.ljust(w) for cell, w in zip(row, widths)).rstrip() for row in rows)
    lines.append("")
    lines.append("Held out (best over the other songs):")
    if not r.held_out:
        lines.append("  no song scores")
    for h in r.held_out:
        if h.band is None:
            lines.append(f"  {h.song} held out: no other song scores")
        else:
            lo, hi = h.band
            lines.append(f"  {h.song} held out: best {h.best:g}, band {lo:g} to {hi:g}, {r.short} {_number(h.objective)}")
    if r.inside is None:
        verdict = "n/a (no band)"
    elif r.inside:
        verdict = "yes"
    else:
        outside = [h.song for h in r.held_out if h.band and not h.band[0] - _TIE <= r.current <= h.band[1] + _TIE]
        verdict = f"no (outside: {', '.join(outside)})"
    lines.append(f"Current {r.current:g} inside every held-out band: {verdict}")
    return "\n".join(lines)


def _values(start: float, stop: float, step: float) -> list[float]:
    n = int(round((stop - start) / step))
    return [round(start + i * step, 10) for i in range(n + 1)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Sweep one constant against the truth files and report the pooled curve with leave-one-song-out.",
    )
    parser.add_argument("--runs", type=Path, default=Path("runs"), help="the folder holding the run folders (read only)")
    parser.add_argument("--truth", type=Path, default=Path("truth"), help="the folder holding the truth folders")
    parser.add_argument("--constant", required=True, choices=list(CONSTANTS), help="the constant to sweep")
    parser.add_argument("--from", dest="start", type=float, required=True, help="the first value")
    parser.add_argument("--to", dest="stop", type=float, required=True, help="the last value, included")
    parser.add_argument("--step", type=float, required=True, help="the step between values")
    args = parser.parse_args(argv)
    if args.step <= 0 or args.stop < args.start:
        parser.error("expected --step above 0 and --to at or above --from")
    truths = {p.name: p for p in sorted(args.truth.iterdir()) if p.is_dir()}
    runs = {
        name: args.runs / name for name in truths if (args.runs / name / "04_strums" / "strums.json").exists()
    }
    try:
        result = sweep(args.constant, _values(args.start, args.stop, args.step), runs, truths)
    except ValueError as exc:
        print(f"band_sweep: {exc}", file=sys.stderr)
        return 2
    print(format_sweep(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
