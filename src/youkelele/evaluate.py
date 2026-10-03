"""Accuracy report: compare a run's grid and chords with hand-made ground truth."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import mir_eval
import numpy as np

from youkelele.jsonio import load_model
from youkelele.schemas import Chords, Grid


class TruthFormatError(Exception):
    def __init__(self, path: Path, line_number: int, detail: str) -> None:
        super().__init__(f"{path}:{line_number}: {detail}")
        self.path = path
        self.line_number = line_number
        self.detail = detail


@dataclass
class Report:
    beat_f: float | None
    downbeat_f: float | None
    chord_root: float | None
    chord_majmin: float | None
    chord_triads: float | None


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


def evaluate_run(run_dir: Path, truth_dir: Path) -> Report:
    run_dir, truth_dir = Path(run_dir), Path(truth_dir)
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
    return Report(beat_f, downbeat_f, root, majmin, triads)


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.1f}%"


def format_report(r: Report) -> str:
    return "\n".join(
        [
            f"Beat F-measure: {_pct(r.beat_f)}",
            f"Downbeat F-measure: {_pct(r.downbeat_f)}",
            f"Chord root: {_pct(r.chord_root)}",
            f"Chord major/minor: {_pct(r.chord_majmin)}",
            f"Chord triads: {_pct(r.chord_triads)}",
        ]
    )
