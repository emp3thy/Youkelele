"""Run report: accuracy against hand-made truth, truth-free diagnostics, and run-to-run compare."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import zip_longest
from pathlib import Path

import mir_eval
import numpy as np

from youkelele.jsonio import load_model
from youkelele.music.as_played import explained_onsets
from youkelele.schemas import Chords, Grid, Strums

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


@dataclass
class Report:
    beat_f: float | None
    downbeat_f: float | None
    chord_root: float | None
    chord_majmin: float | None
    chord_triads: float | None
    # truth-free diagnostics (filled only when no truth directory is given)
    n_share: float | None = None
    all_n_bars: int | None = None
    filled_bars: int | None = None
    changes_on_bar_share: float | None = None
    sub_beat_events: int | None = None
    key_confidence: float | None = None
    boxes_mostly_rests: int | None = None
    sections: list[SectionDiag] = field(default_factory=list)


@dataclass
class Comparison:
    overseg: float | None
    underseg: float | None
    seg: float | None
    majmin: float | None
    sections: list[tuple[SectionDiag | None, SectionDiag | None]]
    notes: list[str]


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
    }


def _section_diags(grid: Grid, strums: Strums) -> list[SectionDiag]:
    diags: list[SectionDiag] = []
    for pattern in strums.patterns:
        if not 0 <= pattern.section < len(grid.sections):
            continue
        section = grid.sections[pattern.section]
        bars = strums.bar_onsets[section.start_bar : section.end_bar]
        strikes = sum(1 for bar in bars for cell in bar if cell != "-")
        rests = sum(1 for slot in pattern.slots if slot == "-")
        diags.append(
            SectionDiag(
                index=pattern.section,
                label=section.label,
                strikes_per_bar=strikes / len(bars) if bars else 0.0,
                explained=explained_onsets(bars, pattern.slots),
                rest_share=rests / len(pattern.slots) if pattern.slots else 0.0,
                uncertain=pattern.uncertain,
                recall_boost=bool(getattr(pattern, "recall_boost", False)),
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
    if strums is not None:
        report.sections = _section_diags(grid, strums)
        report.boxes_mostly_rests = _boxes_mostly_rests(strums, report.sections)
    return report, strums


def evaluate_run(run_dir: Path, truth_dir: Path | None = None) -> Report:
    """Report a run's truth-free diagnostics; the truth fields are filled when truth is given."""
    run_dir = Path(run_dir)
    report, _ = _diagnose(run_dir)
    if truth_dir is None:
        return report
    truth_dir = Path(truth_dir)
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
            ref_intervals, ref_labels, est_intervals, [e.label for e in chords.events]
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
        [e.label for e in b.events],
        float(ref_intervals.min()),
        float(ref_intervals.max()),
        mir_eval.chord.NO_CHORD,
        mir_eval.chord.NO_CHORD,
    )
    ref_labels = [e.label for e in a.events]
    majmin = mir_eval.chord.evaluate(ref_intervals, ref_labels, est_intervals, est_labels)["majmin"]
    return (
        float(mir_eval.chord.overseg(ref_intervals, est_intervals)),
        float(mir_eval.chord.underseg(ref_intervals, est_intervals)),
        float(mir_eval.chord.seg(ref_intervals, est_intervals)),
        float(majmin),
    )


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
    counts = (len(report_a.sections), len(report_b.sections))
    if counts[0] != counts[1] and all(counts):
        notes.append(f"section counts differ ({counts[0]} vs {counts[1]}); pairs matched by position")
    pairs = list(zip_longest(report_a.sections, report_b.sections))
    return Comparison(overseg, underseg, seg, majmin, pairs, notes)


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.1f}%"


def _num(value: float | int | None, spec: str = "") -> str:
    return "n/a" if value is None else format(value, spec)


def _section_line(d: SectionDiag) -> str:
    flags = (" uncertain" if d.uncertain else "") + (" recall-boost" if d.recall_boost else "")
    return (
        f"  {d.index} {d.label}: strikes/bar {d.strikes_per_bar:.1f}, "
        f"explained {_pct(d.explained)}, rests {_pct(d.rest_share)}{flags}"
    )


def format_report(r: Report) -> str:
    lines = [
        f"N share: {_pct(r.n_share)}",
        f"All-N bars: {_num(r.all_n_bars)}",
        f"Filled bars: {_num(r.filled_bars)}",
        f"Changes on bar: {_pct(r.changes_on_bar_share)}",
        f"Sub-beat events: {_num(r.sub_beat_events)}",
        f"Key confidence: {_num(r.key_confidence, '.2f')}",
        f"Boxes mostly rests: {_num(r.boxes_mostly_rests)}",
    ]
    lines.extend(_section_line(d) for d in r.sections)
    truth = [r.beat_f, r.downbeat_f, r.chord_root, r.chord_majmin, r.chord_triads]
    if any(value is not None for value in truth):
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
    return f"{d.strikes_per_bar:.1f}/{_pct(d.explained)}/{_pct(d.rest_share)}"


def format_comparison(c: Comparison) -> str:
    lines = [
        f"overseg {_num(c.overseg, '.3f')}  underseg {_num(c.underseg, '.3f')}  "
        f"seg {_num(c.seg, '.3f')}  majmin {_num(c.majmin, '.3f')}"
    ]
    for left, right in c.sections:
        side = left if left is not None else right
        lines.append(
            f"  {side.index} {side.label}: A {_cell(left)}  B {_cell(right)}"
            "  (strikes per bar/explained/rests)"
        )
    lines.extend(f"note: {note}" for note in c.notes)
    return "\n".join(lines)
