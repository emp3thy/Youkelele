"""Run report: accuracy against hand-made truth, truth-free diagnostics, and run-to-run compare."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import zip_longest
from pathlib import Path

import mir_eval
import numpy as np

from youkelele.jsonio import load_model
from youkelele.music.as_played import explained_onsets
from youkelele.music.relabel import default_plan, longest_member
from youkelele.music.sections import runs_text, vocal_flags, vocal_runs
from youkelele.music.trailing import trailing_silent_bars
from youkelele.render.html import display_names
from youkelele.schemas import ChordEvent, Chords, Grid, Key, Strums

BAR_START_TOLERANCE = 0.06  # a chord change this close to a bar start counts as on the bar
MOSTLY_RESTS = 0.75  # a printed-as-certain pattern with at least this share of rests


class TruthFormatError(Exception):
    def __init__(self, path: Path, line_number: int, detail: str) -> None:
        super().__init__(f"{path}:{line_number}: {detail}")
        self.path = path
        self.line_number = line_number
        self.detail = detail


@dataclass
class SectionDiag:
    index: int
    label: str
    strikes_per_bar: float
    explained: float
    rest_share: float
    uncertain: bool
    recall_boost: bool
    start_bar: int = 0
    end_bar: int = 0  # exclusive
    members: list[int] = field(default_factory=list)  # the grid sections the planned section covers
    member_labels: list[str] = field(default_factory=list)  # their grid labels, in order
    chance_p: float | None = None  # the structure test's p-value; None before 1.5 or for a full vote
    strike_density: float | None = None
    riff: bool = False
    riff_entropy: float | None = None
    riff_single_share: float | None = None
    riff_onsets: int | None = None  # the detector's own onsets the riff pair rests on
    analysed_start: int = 0  # the first bar of the longest member, the bars the figures are read over
    name: str = ""  # the sheet's name for the section (`Verse 2`); the label when empty
    pattern: list[str] = field(default_factory=list)  # the printed pattern's slots
    confidence: float = 0.0  # the pattern's confidence


def _label_text(d: SectionDiag) -> str:
    """The sheet's name, with `(grid a, b: l1, l2)` after it when it merges several grid sections."""
    name = d.name or d.label
    if len(d.members) < 2:
        return name
    return f"{name} (grid {', '.join(str(m) for m in d.members)}: {', '.join(d.member_labels)})"


def _scored_label(event: ChordEvent) -> str:
    """The label mir_eval scores: a power event's triad (`C#:min`), since `C#:5` has no third."""
    return event.triad if event.power else event.label


@dataclass
class Report:
    beat_f: float | None
    downbeat_f: float | None
    chord_root: float | None
    chord_majmin: float | None
    chord_triads: float | None
    # truth-free diagnostics: always filled, whether or not a truth directory is given
    n_share: float | None = None
    all_n_bars: int | None = None
    filled_bars: int | None = None
    changes_on_bar_share: float | None = None
    sub_beat_events: int | None = None
    key_confidence: float | None = None
    key: Key | None = None
    boxes_mostly_rests: int | None = None
    vocal_runs: list[tuple[int, int]] | None = None  # None when the grid has no vocal levels
    vocal_bars: int | None = None  # the bar count, so a trailing run prints marked
    sections: list[SectionDiag] = field(default_factory=list)
    truth_given: bool = False  # a truth directory was supplied: print the truth lines (n/a if absent)


@dataclass
class SectionDelta:
    """B minus A for one section pair."""

    strikes_per_bar: float
    explained: float
    rest_share: float
    riff_changed: bool = False  # the riff flag differs between the runs
    certainty_changed: bool = False  # the uncertain flag differs between the runs

    @property
    def changed(self) -> bool:
        """Any figure moved, or the riff flag or the certainty flipped."""
        return bool(
            self.riff_changed
            or self.certainty_changed
            or self.strikes_per_bar
            or self.explained
            or self.rest_share
        )


@dataclass
class Comparison:
    overseg: float | None
    underseg: float | None
    seg: float | None
    majmin: float | None
    sections: list[tuple[SectionDiag | None, SectionDiag | None]]
    notes: list[str]
    deltas: list[SectionDelta | None] = field(default_factory=list)  # one per pair; None if a side is missing


def _read_beats(path: Path) -> tuple[np.ndarray, np.ndarray]:
    beats: list[float] = []
    downbeats: list[float] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        parts = line.split()
        if not parts:
            continue
        try:
            time = float(parts[0])
        except ValueError:
            raise TruthFormatError(
                path, number, f"expected a beat time in seconds, got {parts[0]!r}"
            ) from None
        beats.append(time)
        if len(parts) > 1 and parts[1] == "1":
            downbeats.append(time)
    return np.array(beats, dtype=float), np.array(downbeats, dtype=float)


def _read_chords(path: Path) -> tuple[np.ndarray, list[str]]:
    intervals: list[list[float]] = []
    labels: list[str] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        fields = line.split("\t") if "\t" in line else line.split()
        if len(fields) < 3:
            raise TruthFormatError(path, number, "expected 'start end label' (tab-separated)")
        try:
            interval = [float(fields[0]), float(fields[1])]
        except ValueError:
            raise TruthFormatError(
                path, number, f"expected start and end times in seconds, got {fields[:2]!r}"
            ) from None
        intervals.append(interval)
        labels.append(fields[2].strip())
    return np.array(intervals, dtype=float).reshape(-1, 2), labels


def _f_measure(reference: np.ndarray, estimated: np.ndarray) -> float | None:
    if len(reference) == 0:
        return None
    if len(estimated) == 0:
        return 0.0
    return float(mir_eval.beat.f_measure(np.sort(reference), np.sort(estimated)))


def _chord_scores(
    ref_intervals: np.ndarray,
    ref_labels: list[str],
    est_intervals: np.ndarray,
    est_labels: list[str],
) -> tuple[float | None, float | None, float | None]:
    if len(ref_labels) == 0:
        return None, None, None
    if len(est_labels) == 0:
        return 0.0, 0.0, 0.0
    est_intervals, est_labels = mir_eval.util.adjust_intervals(
        est_intervals,
        est_labels,
        float(ref_intervals.min()),
        float(ref_intervals.max()),
        mir_eval.chord.NO_CHORD,
        mir_eval.chord.NO_CHORD,
    )
    scores = mir_eval.chord.evaluate(ref_intervals, ref_labels, est_intervals, est_labels)
    return float(scores["root"]), float(scores["majmin"]), float(scores["triads"])


def _chord_diagnostics(grid: Grid, chords: Chords) -> dict[str, float | int | None]:
    events = chords.events
    total = sum(e.end - e.start for e in events)
    n_time = sum(e.end - e.start for e in events if e.label == "N")
    n_share = n_time / total if total > 0 else None

    all_n = 0
    for bar in grid.bars:
        overlapping = [e for e in events if min(e.end, bar.end) - max(e.start, bar.start) > 1e-9]
        if all(e.label == "N" for e in overlapping):
            all_n += 1

    bar_starts = [bar.start for bar in grid.bars]
    changes = [cur for prev, cur in zip(events, events[1:]) if prev.label != cur.label]
    on_bar = sum(
        1 for cur in changes if any(abs(cur.start - b) <= BAR_START_TOLERANCE for b in bar_starts)
    )
    changes_on_bar = on_bar / len(changes) if changes else None

    sub_beat = None
    if len(grid.beats) >= 2:
        median = float(np.median(np.diff(grid.beats)))
        sub_beat = sum(1 for e in events if e.end - e.start < median)

    return {
        "n_share": n_share,
        "all_n_bars": all_n,
        "filled_bars": len({e.bar for e in events if e.filled}),
        "changes_on_bar_share": changes_on_bar,
        "sub_beat_events": sub_beat,
        "key_confidence": chords.key.confidence,
        "key": chords.key,
    }


def _section_diags(grid: Grid, strums: Strums, chords: Chords) -> list[SectionDiag]:
    """Per planned section strum figures over the bars the strums stage analysed.

    Pattern `k` belongs to planned section `k` (the strums' own plan, or one section per grid
    section for a file before 1.5). The figures are read over the planned section's longest
    member; that member loses the last section's trailing no-chord bars exactly as in the
    strums stage, so the figures match the pattern's own `explained`.
    """
    diags: list[SectionDiag] = []
    plan = strums.plan or default_plan(grid, chords)
    drop = 0
    tail_end = None
    if grid.sections:
        tail = grid.sections[-1]
        tail_end = tail.end_bar
        drop = trailing_silent_bars(chords, grid.bars, cap=tail.end_bar - tail.start_bar)
    names = display_names([section.label for section in plan])
    for k, pattern in enumerate(strums.patterns):
        if not 0 <= k < len(plan):
            continue
        section = plan[k]
        start, end = longest_member(section, grid)
        end -= drop if end == tail_end else 0
        bars = strums.bar_onsets[start:end]
        strikes = sum(1 for bar in bars for cell in bar if cell != "-")
        rests = sum(1 for slot in pattern.slots if slot == "-")
        diags.append(
            SectionDiag(
                index=k,
                label=section.label,
                strikes_per_bar=strikes / len(bars) if bars else 0.0,
                explained=explained_onsets(bars, pattern.slots),
                rest_share=rests / len(pattern.slots) if pattern.slots else 0.0,
                uncertain=pattern.uncertain,
                recall_boost=bool(getattr(pattern, "recall_boost", False)),
                start_bar=section.start_bar,
                end_bar=section.end_bar,
                members=list(section.members),
                member_labels=[grid.sections[m].label for m in section.members],
                chance_p=pattern.chance_p,
                strike_density=pattern.strike_density,
                riff=pattern.riff,
                riff_entropy=pattern.riff_entropy,
                riff_single_share=pattern.riff_single_share,
                riff_onsets=pattern.riff_onsets,
                analysed_start=start,
                name=names[k],
                pattern=list(pattern.slots),
                confidence=pattern.confidence,
            )
        )
    return diags


def _boxes_mostly_rests(strums: Strums, diags: list[SectionDiag]) -> int:
    no_instrument = {p.section for p in strums.patterns if p.no_instrument}
    return sum(
        1
        for d in diags
        if not d.uncertain and d.index not in no_instrument and d.rest_share >= MOSTLY_RESTS
    )


def _load_strums(run_dir: Path) -> Strums | None:
    path = run_dir / "04_strums" / "strums.json"
    return load_model(path, Strums) if path.is_file() else None


def _diagnose(run_dir: Path) -> tuple[Report, Strums | None]:
    grid = load_model(run_dir / "02_grid" / "grid.json", Grid)
    chords = load_model(run_dir / "03_harmony" / "chords.json", Chords)
    strums = _load_strums(run_dir)
    report = Report(None, None, None, None, None, **_chord_diagnostics(grid, chords))
    if grid.bar_vocal_db:
        report.vocal_runs = vocal_runs(vocal_flags(grid.bar_vocal_db), keep_trailing=True)
        report.vocal_bars = len(grid.bar_vocal_db)
    if strums is not None:
        report.sections = _section_diags(grid, strums, chords)
        report.boxes_mostly_rests = _boxes_mostly_rests(strums, report.sections)
    return report, strums


def evaluate_run(run_dir: Path, truth_dir: Path | None = None) -> Report:
    """Report a run's truth-free diagnostics; the truth fields are filled when truth is given."""
    run_dir = Path(run_dir)
    report, _ = _diagnose(run_dir)
    if truth_dir is None:
        return report
    truth_dir = Path(truth_dir)
    report.truth_given = True
    grid = load_model(run_dir / "02_grid" / "grid.json", Grid)
    chords = load_model(run_dir / "03_harmony" / "chords.json", Chords)

    beat_f = downbeat_f = None
    beats_file = truth_dir / "beats.txt"
    if beats_file.is_file():
        ref_beats, ref_downbeats = _read_beats(beats_file)
        est_beats = np.array(grid.beats, dtype=float)
        est_downbeats = np.array([grid.beats[i] for i in grid.downbeats], dtype=float)
        beat_f = _f_measure(ref_beats, est_beats)
        downbeat_f = _f_measure(ref_downbeats, est_downbeats)

    root = majmin = triads = None
    chords_file = truth_dir / "chords.lab"
    if chords_file.is_file():
        ref_intervals, ref_labels = _read_chords(chords_file)
        est_intervals = np.array([[e.start, e.end] for e in chords.events], dtype=float)
        est_intervals = est_intervals.reshape(-1, 2)
        root, majmin, triads = _chord_scores(
            ref_intervals, ref_labels, est_intervals, [_scored_label(e) for e in chords.events]
        )
    report.beat_f, report.downbeat_f = beat_f, downbeat_f
    report.chord_root, report.chord_majmin, report.chord_triads = root, majmin, triads
    return report


def _segmentation_scores(
    a: Chords, b: Chords
) -> tuple[float | None, float | None, float | None, float | None]:
    if not a.events or not b.events:
        return None, None, None, None
    ref_intervals = np.array([[e.start, e.end] for e in a.events], dtype=float).reshape(-1, 2)
    est_intervals = np.array([[e.start, e.end] for e in b.events], dtype=float).reshape(-1, 2)
    est_intervals, est_labels = mir_eval.util.adjust_intervals(
        est_intervals,
        [_scored_label(e) for e in b.events],
        float(ref_intervals.min()),
        float(ref_intervals.max()),
        mir_eval.chord.NO_CHORD,
        mir_eval.chord.NO_CHORD,
    )
    ref_labels = [_scored_label(e) for e in a.events]
    majmin = mir_eval.chord.evaluate(ref_intervals, ref_labels, est_intervals, est_labels)["majmin"]
    return (
        float(mir_eval.chord.overseg(ref_intervals, est_intervals)),
        float(mir_eval.chord.underseg(ref_intervals, est_intervals)),
        float(mir_eval.chord.seg(ref_intervals, est_intervals)),
        float(majmin),
    )


def _grid_shape(grid: Grid) -> tuple[int, list[tuple[int, int]]]:
    """The bar count and the grid sections' boundaries: what makes bar numbers comparable."""
    return len(grid.bars), [(s.start_bar, s.end_bar) for s in grid.sections]


def _pair_sections(
    left: list[SectionDiag], right: list[SectionDiag], grid_a: Grid, grid_b: Grid, notes: list[str]
) -> list[tuple[SectionDiag | None, SectionDiag | None]]:
    """Each planned section of A with B's planned section read over the same longest member.

    On one grid a planned section is identified by its longest member's first bar, so a
    section merged in one run meets the counterpart of the member its figures come from,
    and a section with no counterpart is paired with None. When the grids differ (bar
    count or section boundaries) bar numbers mean different things, so the sections are
    paired by position and a note says so.
    """
    if _grid_shape(grid_a) != _grid_shape(grid_b):
        counts = (len(left), len(right))
        if all(counts):
            notes.append(
                f"section counts differ ({counts[0]} vs {counts[1]}); pairs matched by position"
                if counts[0] != counts[1]
                else "grid.json differs between the runs; pairs matched by position"
            )
        return list(zip_longest(left, right))
    by_start_a = {d.analysed_start: d for d in left}
    by_start_b = {d.analysed_start: d for d in right}
    return [(by_start_a.get(s), by_start_b.get(s)) for s in sorted(by_start_a.keys() | by_start_b.keys())]


def compare_runs(a: Path, b: Path) -> Comparison:
    """Score run `b` against run `a` (the reference); neither needs truth."""
    a, b = Path(a), Path(b)
    report_a, strums_a = _diagnose(a)
    report_b, strums_b = _diagnose(b)
    chords_a = load_model(a / "03_harmony" / "chords.json", Chords)
    chords_b = load_model(b / "03_harmony" / "chords.json", Chords)
    overseg, underseg, seg, majmin = _segmentation_scores(chords_a, chords_b)

    notes: list[str] = []
    if overseg is None:
        notes.append("a run has no chord events; chord comparison skipped")
    if strums_a is None or strums_b is None:
        missing = " and ".join(
            name for name, st in (("A", strums_a), ("B", strums_b)) if st is None
        )
        notes.append(f"no strums.json in run {missing}; strum comparison is one-sided")
    elif strums_a.slots_per_bar != strums_b.slots_per_bar:
        notes.append(
            f"slots per bar differ ({strums_a.slots_per_bar} vs {strums_b.slots_per_bar}); "
            "strum figures are not directly comparable"
        )
    pairs = _pair_sections(
        report_a.sections, report_b.sections,
        load_model(a / "02_grid" / "grid.json", Grid), load_model(b / "02_grid" / "grid.json", Grid),
        notes,
    )
    deltas = [
        SectionDelta(
            right.strikes_per_bar - left.strikes_per_bar,
            right.explained - left.explained,
            right.rest_share - left.rest_share,
            riff_changed=left.riff != right.riff,
            certainty_changed=left.uncertain != right.uncertain,
        )
        if left is not None and right is not None
        else None
        for left, right in pairs
    ]
    return Comparison(overseg, underseg, seg, majmin, pairs, notes, deltas)


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.1f}%"


def _num(value: float | int | None, spec: str = "") -> str:
    return "n/a" if value is None else format(value, spec)


def _section_line(d: SectionDiag) -> str:
    flags = (" uncertain" if d.uncertain else "") + (" recall-boost" if d.recall_boost else "")
    features = (
        f"{d.riff_entropy:.2f}/{d.riff_single_share:.2f}"
        if d.riff_entropy is not None and d.riff_single_share is not None
        else "n/a"
    )
    if d.riff_onsets is not None:  # 0 onsets gives "n/a (0 onsets)"
        features += f" ({d.riff_onsets} onset{'' if d.riff_onsets == 1 else 's'})"
    return (
        f"  {d.index} {_label_text(d)} bars {d.start_bar}-{d.end_bar}: "
        f"{''.join(d.pattern) or 'n/a'}, conf {d.confidence:.2f}, strikes/bar {d.strikes_per_bar:.1f}, "
        f"explained {_pct(d.explained)}, rests {_pct(d.rest_share)}, "
        f"p {_num(d.chance_p, '.3f')}, density {_num(d.strike_density, '.2f')}, "
        f"riff {features}{' riff' if d.riff else ''}{flags}"
    )


def _key_line(key: Key | None) -> str:
    """`Key: tonic mode (method, margin, mode margin, runner-up[, mix tonic mode])`."""
    if key is None:
        return "Key: n/a"
    figures = (
        f"{key.method}, margin {_num(key.margin, '.3f')}, "
        f"mode margin {_num(key.mode_margin, '.3f')}, runner-up {key.runner_up or 'n/a'}"
    )
    if key.mix is not None:
        figures += f", mix {key.mix.tonic} {key.mix.mode}"
    if key.tonic_votes is not None:
        votes = key.tonic_votes
        figures += (
            f", votes score {votes.score or 'none'} pair {votes.pair or 'none'} "
            f"mix {votes.mix or 'none'} ({votes.decided_by or 'none'})"
        )
    return f"Key: {key.tonic} {key.mode} ({figures})"


def format_report(r: Report) -> str:
    lines = [
        f"N share: {_pct(r.n_share)}",
        f"All-N bars: {_num(r.all_n_bars)}",
        f"Filled bars: {_num(r.filled_bars)}",
        f"Changes on bar: {_pct(r.changes_on_bar_share)}",
        f"Sub-beat events: {_num(r.sub_beat_events)}",
        _key_line(r.key),
        f"Key confidence: {_num(r.key_confidence, '.2f')}",
        f"Boxes mostly rests: {_num(r.boxes_mostly_rests)}",
        f"Vocal runs: {'n/a' if r.vocal_runs is None else runs_text(r.vocal_runs, r.vocal_bars)}",
    ]
    lines.extend(_section_line(d) for d in r.sections)
    truth = [r.beat_f, r.downbeat_f, r.chord_root, r.chord_majmin, r.chord_triads]
    if r.truth_given or any(value is not None for value in truth):
        lines.extend(
            [
                f"Beat F-measure: {_pct(r.beat_f)}",
                f"Downbeat F-measure: {_pct(r.downbeat_f)}",
                f"Chord root: {_pct(r.chord_root)}",
                f"Chord major/minor: {_pct(r.chord_majmin)}",
                f"Chord triads: {_pct(r.chord_triads)}",
            ]
        )
    return "\n".join(lines)


def _cell(d: SectionDiag | None) -> str:
    if d is None:
        return "n/a"
    flags = (" unc" if d.uncertain else "") + (" boost" if d.recall_boost else "")
    riff = " riff" if d.riff else ""
    return f"{d.strikes_per_bar:.1f}/{_pct(d.explained)}/{_pct(d.rest_share)}{flags} p {_num(d.chance_p, '.3f')}{riff}"


def _delta(d: SectionDelta | None) -> str:
    if d is None:
        return "n/a"
    marks = (" riff flag changed" if d.riff_changed else "") + (
        " certainty changed" if d.certainty_changed else ""
    )
    return f"{d.strikes_per_bar:+.1f}/{d.explained * 100:+.1f}pp/{d.rest_share * 100:+.1f}pp{marks}"


def format_comparison(c: Comparison) -> str:
    lines = [
        f"overseg {_num(c.overseg, '.3f')}  underseg {_num(c.underseg, '.3f')}  "
        f"seg {_num(c.seg, '.3f')}  majmin {_num(c.majmin, '.3f')}"
    ]
    if c.sections:
        lines.append(
            "  sections: strikes per bar/explained/rests; unc = uncertain, boost = recall boost, "
            "p = the structure test's chance p, riff = a riff section"
        )
    for i, (left, right) in enumerate(c.sections):
        side = left if left is not None else right
        delta = c.deltas[i] if i < len(c.deltas) else None
        lines.append(f"  {side.index} {_label_text(side)}: A {_cell(left)}  B {_cell(right)}  B-A {_delta(delta)}")
    lines.extend(f"note: {note}" for note in c.notes)
    return "\n".join(lines)
