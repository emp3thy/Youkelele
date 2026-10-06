"""Run report: accuracy against hand-made truth, truth-free diagnostics, and run-to-run compare."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import zip_longest
from collections.abc import Sequence
from pathlib import Path

import mir_eval
import numpy as np

from youkelele.jsonio import load_model
from youkelele.music.as_played import explained_onsets
from youkelele.music.compat import with_bars
from youkelele.music.members import member_spans
from youkelele.music.relabel import default_plan, longest_member
from youkelele.music.sections import runs_text, vocal_flags, vocal_runs
from youkelele.music.trailing import trailing_silent_bars
from youkelele.render.html import display_names
from youkelele.schemas import ChordEvent, Chords, Grid, Key, Riffs, SectionPattern, Strums

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
    candidate: str = "majority"  # which candidate the vote kept
    score_majority: float | None = None
    score_medoid: float | None = None
    unit: int = 1
    pitch_change_share: float | None = None
    rings: bool = True
    ring_decay_db: float | None = None
    # per member that prints its own pattern: (start, end, pattern text, prints own, uncertain)
    member_patterns: list[tuple[int, int, str, bool, bool]] = field(default_factory=list)
    # the riff gate: (agreement, support, named share, printable, reason), when the run has one
    riff_gate: tuple[float, float, float, bool, str | None] | None = None
    riff_rule: str | None = None  # the rule that marked the section a riff ("A"), when one did
    root_share: float | None = None  # share of named onset pitches on the chord root
    named_share: float | None = None  # share of the section's onsets the pitch tracker named
    resting_bars: list[int] = field(default_factory=list)  # bars in the planned span whose record rests


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
    resting_bars: list[int] = field(default_factory=list)  # every bar whose record rests, in index order
    truth_given: bool = False  # a truth directory was supplied: print the truth lines (n/a if absent)


@dataclass
class SectionDelta:
    """B minus A for one section pair."""

    strikes_per_bar: float
    explained: float
    rest_share: float
    riff_changed: bool = False  # the riff flag differs between the runs
    certainty_changed: bool = False  # the uncertain flag differs between the runs
    pattern_changes: int = 0  # bars whose printed pattern differs (grids that match only)
    candidate_changed: bool = False  # the vote kept a different candidate
    rest_changes: int = 0  # bars in the paired span whose `rests` differs (grids that match only)
    riff_rule_b: str | None = None  # the right side's riff rule

    @property
    def changed(self) -> bool:
        """Any figure moved, or the riff flag or the certainty flipped."""
        return bool(
            self.riff_changed
            or self.certainty_changed
            or self.pattern_changes
            or self.candidate_changed
            or self.rest_changes
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


def _member_patterns(
    section, pattern: SectionPattern, strums: Strums, grid: Grid
) -> list[tuple[int, int, str, bool, bool]]:
    """The members whose bars print a pattern other than the section's own (start, end, text, True, uncertain)."""
    by_index = {b.index: b for b in strums.bars}
    found = []
    for start, end in member_spans(section, grid):
        records = [by_index[i] for i in range(start, end) if i in by_index]
        if not records or all(r.pattern == list(pattern.slots) for r in records):
            continue
        first = next(r for r in records if r.pattern != list(pattern.slots))
        found.append((start, end, "".join(first.pattern), True, any(r.uncertain for r in records)))
    return found


def _section_diags(
    grid: Grid, strums: Strums, chords: Chords, riffs: Riffs | None = None
) -> list[SectionDiag]:
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
    try:
        strums = with_bars(strums, grid)
    except ValueError:  # patterns that do not match the plan cannot be backfilled: no member lines
        pass
    gates = {r.section: r for r in riffs.sections} if riffs is not None else {}
    for k, pattern in enumerate(strums.patterns):
        if not 0 <= k < len(plan):
            continue
        section = plan[k]
        start, end = longest_member(section, grid)
        end -= drop if end == tail_end else 0
        bars = strums.bar_onsets[start:end]
        strikes = sum(1 for bar in bars for cell in bar if cell != "-")
        rests = sum(1 for slot in pattern.slots if slot == "-")
        resting = sorted(
            b.index for b in strums.bars if b.rests and section.start_bar <= b.index < section.end_bar
        )
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
                candidate=pattern.candidate,
                score_majority=pattern.score_majority,
                score_medoid=pattern.score_medoid,
                unit=pattern.unit,
                pitch_change_share=pattern.pitch_change_share,
                rings=pattern.rings,
                ring_decay_db=pattern.ring_decay_db,
                member_patterns=_member_patterns(section, pattern, strums, grid),
                riff_gate=(
                    (gate.agreement, gate.support, gate.named_share, gate.printable, gate.reason)
                    if (gate := gates.get(k)) is not None
                    else None
                ),
                riff_rule=pattern.riff_rule,
                root_share=pattern.root_share,
                named_share=pattern.named_share,
                resting_bars=resting,
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


def _load_riffs(run_dir: Path) -> Riffs | None:
    path = run_dir / "05_riff" / "riff.json"
    return load_model(path, Riffs) if path.is_file() else None


def _diagnose(run_dir: Path) -> tuple[Report, Strums | None]:
    grid = load_model(run_dir / "02_grid" / "grid.json", Grid)
    chords = load_model(run_dir / "03_harmony" / "chords.json", Chords)
    strums = _load_strums(run_dir)
    report = Report(None, None, None, None, None, **_chord_diagnostics(grid, chords))
    if grid.bar_vocal_db:
        report.vocal_runs = vocal_runs(vocal_flags(grid.bar_vocal_db), keep_trailing=True)
        report.vocal_bars = len(grid.bar_vocal_db)
    if strums is not None:
        report.sections = _section_diags(grid, strums, chords, _load_riffs(run_dir))
        report.resting_bars = sorted(b.index for b in _with_bars_or_self(strums, grid).bars if b.rests)
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


def _printed_patterns(strums: Strums | None, grid: Grid) -> dict[int, list[str]]:
    """Each bar's printed pattern by bar index; a run before 1.6 is read through its backfilled bars."""
    if strums is None:
        return {}
    try:
        strums = with_bars(strums, grid)
    except ValueError:  # patterns that do not match the plan cannot be backfilled
        return {}
    return {b.index: list(b.pattern) for b in strums.bars}


def _with_bars_or_self(strums: Strums, grid: Grid) -> Strums:
    """The strums with its per-bar records, backfilled when it can be; as read otherwise."""
    try:
        return with_bars(strums, grid)
    except ValueError:  # patterns that do not match the plan cannot be backfilled
        return strums


def _rest_flags(strums: Strums | None, grid: Grid) -> dict[int, bool]:
    """Each bar's `rests` flag by bar index; a run before 1.7 rests nowhere."""
    if strums is None:
        return {}
    return {b.index: b.rests for b in _with_bars_or_self(strums, grid).bars}


def _rest_changes(
    left: SectionDiag, right: SectionDiag, rests_a: dict[int, bool], rests_b: dict[int, bool]
) -> int:
    """Bars both sections cover that both runs record, whose `rests` flag differs."""
    bars = set(range(left.start_bar, left.end_bar)) & set(range(right.start_bar, right.end_bar))
    return sum(1 for i in bars if i in rests_a and i in rests_b and rests_a[i] != rests_b[i])


def _pattern_changes(
    left: SectionDiag,
    right: SectionDiag,
    printed_a: dict[int, list[str]],
    printed_b: dict[int, list[str]],
) -> int:
    """Bars both sections cover that both runs print, with a different pattern."""
    bars = set(range(left.start_bar, left.end_bar)) & set(range(right.start_bar, right.end_bar))
    return sum(1 for i in bars if i in printed_a and i in printed_b and printed_a[i] != printed_b[i])


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
    grid_a = load_model(a / "02_grid" / "grid.json", Grid)
    grid_b = load_model(b / "02_grid" / "grid.json", Grid)
    printed_a = _printed_patterns(strums_a, grid_a)
    printed_b = _printed_patterns(strums_b, grid_b)
    rests_a = _rest_flags(strums_a, grid_a)
    rests_b = _rest_flags(strums_b, grid_b)
    same_grid = _grid_shape(grid_a) == _grid_shape(grid_b)
    deltas = [
        SectionDelta(
            right.strikes_per_bar - left.strikes_per_bar,
            right.explained - left.explained,
            right.rest_share - left.rest_share,
            riff_changed=left.riff != right.riff,
            certainty_changed=left.uncertain != right.uncertain,
            pattern_changes=_pattern_changes(left, right, printed_a, printed_b) if same_grid else 0,
            candidate_changed=left.candidate != right.candidate,
            rest_changes=_rest_changes(left, right, rests_a, rests_b) if same_grid else 0,
            riff_rule_b=right.riff_rule,
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


def _ranges(indices: Sequence[int]) -> str:
    """Sorted bar indices as ranges: `0-3, 10, 11` (only a run of three or more prints as `a-b`)."""
    runs: list[list[int]] = []
    for i in sorted(indices):
        if runs and i == runs[-1][1] + 1:
            runs[-1][1] = i
        else:
            runs.append([i, i])
    return ", ".join(f"{a}-{b}" if b - a >= 2 else ", ".join(map(str, range(a, b + 1))) for a, b in runs)


def _section_line(d: SectionDiag) -> str:
    flags = (" uncertain" if d.uncertain else "") + (" recall-boost" if d.recall_boost else "")
    features = (
        f"{d.riff_entropy:.2f}/{d.riff_single_share:.2f}"
        if d.riff_entropy is not None and d.riff_single_share is not None
        else "n/a"
    )
    if d.riff_onsets is not None:  # 0 onsets gives "n/a (0 onsets)"
        features += f" ({d.riff_onsets} onset{'' if d.riff_onsets == 1 else 's'})"
    line = (
        f"  {d.index} {_label_text(d)} bars {d.start_bar}-{d.end_bar}: "
        f"{''.join(d.pattern) or 'n/a'}, conf {d.confidence:.2f}, strikes/bar {d.strikes_per_bar:.1f}, "
        f"explained {_pct(d.explained)}, rests {_pct(d.rest_share)}, "
        f"p {_num(d.chance_p, '.3f')}, density {_num(d.strike_density, '.2f')}, "
        f"riff {features}{' riff' if d.riff else ''}{flags}"
    )
    return "\n".join([line + _vote_figures(d), *_member_lines(d), *_gate_lines(d)])


def _vote_figures(d: SectionDiag) -> str:
    parts = []
    if d.score_medoid is not None and d.score_majority is not None:
        kept, other = (
            (d.score_medoid, d.score_majority)
            if d.candidate == "medoid"
            else (d.score_majority, d.score_medoid)
        )
        parts.append(f"vote {d.candidate} ({kept:.2f} vs {other:.2f})")
    if d.unit == 2:
        parts.append("unit 2")
    parts.append(f"pcs {_num(d.pitch_change_share, '.2f')}")
    if d.riff_rule:
        parts.append(f"rule {d.riff_rule}")
    parts.append(f"root {_num(d.root_share, '.2f')}")
    parts.append(f"named {_num(d.named_share, '.2f')}")
    if d.ring_decay_db is None:
        parts.append("rings n/a")
    else:
        parts.append(f"{'rings' if d.rings else 'short'} {d.ring_decay_db:.1f}dB")
    return ", " + ", ".join(parts)


def _member_lines(d: SectionDiag) -> list[str]:
    return [
        f"    member {start}-{end} prints own {text}{' (uncertain)' if uncertain else ''}"
        for start, end, text, own, uncertain in d.member_patterns
        if own
    ]


def _gate_lines(d: SectionDiag) -> list[str]:
    if d.riff_gate is None:
        return []
    agreement, support, named, printable, reason = d.riff_gate
    verdict = "printable" if printable else "not transcribed" + (f" ({reason})" if reason else "")
    return [
        f"    riff gate: agreement {agreement:.2f} support {support:.2f} named {named:.2f} {verdict}"
    ]


def _key_line(key: Key | None) -> str:
    """`Key: tonic mode (method, score margin, mode margin, runner-up[, mix tonic mode][, votes ...])`.

    The margin is the score's unless the pair rule decided a close score, when it is the pair
    rule's (`pair margin`). The votes tail, `votes score X pair Y mix Z (decided by)`, is
    printed when the key carries the three votes (1.5 files).
    """
    if key is None:
        return "Key: n/a"
    by_pair = key.tonic_votes is not None and key.tonic_votes.decided_by == "pair rule"
    figures = (
        f"{key.method}, {'pair' if by_pair else 'score'} margin {_num(key.margin, '.3f')}, "
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
    if r.resting_bars:
        lines.append(f"{len(r.resting_bars)} bars rest: {_ranges(r.resting_bars)}")
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
    marks = (
        (
            " riff flag changed" + (f" (rule {d.riff_rule_b})" if d.riff_rule_b else "")
            if d.riff_changed
            else ""
        )
        + (" certainty changed" if d.certainty_changed else "")
        + (f" patterns changed in {d.pattern_changes} bars" if d.pattern_changes else "")
        + (f" rests changed in {d.rest_changes} bars" if d.rest_changes else "")
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
        vote = ""
        if delta is not None and delta.candidate_changed:
            vote = f"  vote: {left.candidate} -> {right.candidate}"
        lines.append(
            f"  {side.index} {_label_text(side)}: A {_cell(left)}  B {_cell(right)}  B-A {_delta(delta)}{vote}"
        )
    lines.extend(f"note: {note}" for note in c.notes)
    return "\n".join(lines)
