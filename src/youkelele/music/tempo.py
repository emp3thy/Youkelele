"""Beat grid rules: gap filling, tempo octave, downbeat phase and bars.

Every threshold here was measured on five real songs in the grid round-three
spike (docs/superpowers/specs/2026-10-03-spike-grid-round3.md).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

import numpy as np

from youkelele.schemas import Bar, Meter

OctaveMode = Literal["auto", "none", "half", "double"]
OctaveDecision = Literal["none", "half", "double"]

GAP_WINDOW = 17  # intervals around a gap used for the local median
NEAR_TIE = 0.75  # second phase count at least this share of the modal count


def fill_gaps(beats: Sequence[float], factor: float = 1.6) -> list[float]:
    """Insert evenly spaced beats where an interval exceeds `factor` x the local median.

    A dropped beat otherwise flips the bar phase for the rest of the song.
    """
    beats = [float(b) for b in beats]
    if len(beats) < 3:
        return beats
    iv = np.diff(beats)
    half = GAP_WINDOW // 2
    out = [beats[0]]
    for i in range(1, len(beats)):
        lo, hi = max(0, i - 1 - half), min(len(iv), i + half)
        median = float(np.median(iv[lo:hi]))
        gap = beats[i] - beats[i - 1]
        if gap > factor * median:
            n = max(1, int(round(gap / median)) - 1)
            step = gap / (n + 1)
            out.extend(beats[i - 1] + j * step for j in range(1, n + 1))
        out.append(beats[i])
    return out


def bpm_from_beats(beats: Sequence[float]) -> float:
    """60 / median interval; call it on gap-filled beats."""
    if len(beats) < 2:
        raise ValueError("need at least two beats to measure a tempo")
    return 60.0 / float(np.median(np.diff(np.asarray(beats, dtype=float))))


def decide_octave(bpm: float, mode: OctaveMode) -> OctaveDecision:
    """`auto` halves if and only if bpm > 140 and the halved tempo is 60 to 95."""
    if mode != "auto":
        return mode
    return "half" if bpm > 140 and 60 <= bpm / 2 <= 95 else "none"


def downbeat_indices(
    beats: Sequence[float], downbeats: Sequence[float], tol: float = 0.07
) -> list[int]:
    """Index of the nearest beat for each downbeat within `tol` seconds."""
    if not len(beats):
        return []
    arr = np.asarray(beats, dtype=float)
    found: set[int] = set()
    for d in downbeats:
        i = int(np.argmin(np.abs(arr - d)))
        if abs(arr[i] - d) <= tol:
            found.add(i)
    return sorted(found)


def _phase_counts(downbeat_idx: Sequence[int], numerator: int) -> np.ndarray:
    return np.bincount(np.asarray(downbeat_idx, dtype=int) % numerator, minlength=numerator)


def modal_phase(downbeat_idx: Sequence[int], numerator: int) -> tuple[int, float]:
    """Most common downbeat beat-index modulo `numerator`, and its share."""
    if not len(downbeat_idx):
        return 0, 0.0
    counts = _phase_counts(downbeat_idx, numerator)
    phase = int(counts.argmax())
    return phase, float(counts[phase] / counts.sum())


def normalise_octave(
    beats: Sequence[float],
    downbeat_idx: Sequence[int],
    target_period: float,
    tol: float = 0.75,
) -> tuple[list[float], list[int]]:
    """Halve locally: drop every beat closer than `tol * target_period` to the last kept beat.

    A leading run of fast beats starts on the beat whose index parity matches the
    modal downbeat parity within that run. Being local, this also repairs a
    detector that switches octave mid-song. Downbeats on dropped beats are dropped.
    """
    arr = [float(b) for b in beats]
    if not arr:
        return [], []
    db = np.asarray(downbeat_idx, dtype=int)
    min_gap = tol * target_period
    iv = np.diff(arr)
    fast_end = 0
    while fast_end < len(iv) and iv[fast_end] < min_gap:
        fast_end += 1
    start = 0
    if fast_end > 1:
        parity = np.bincount(db[db <= fast_end] % 2, minlength=2)
        start = int(parity.argmax()) if parity.sum() else 0
    kept = [start]
    for i in range(start + 1, len(arr)):
        if arr[i] - arr[kept[-1]] >= min_gap:
            kept.append(i)
    new_index = {old: new for new, old in enumerate(kept)}
    return [arr[i] for i in kept], sorted(new_index[i] for i in db if i in new_index)


def double_beats(
    beats: Sequence[float], downbeat_idx: Sequence[int]
) -> tuple[list[float], list[int]]:
    """Insert a midpoint between every pair of beats."""
    arr = [float(b) for b in beats]
    out: list[float] = []
    for a, b in zip(arr, arr[1:]):
        out += [a, (a + b) / 2]
    out += arr[-1:]
    return out, [2 * int(i) for i in downbeat_idx]


def _chroma_change(chroma_per_beat: np.ndarray, starts: list[int], n_beats: int) -> float:
    """Mean (1 - cosine) between adjacent bars' mean chroma for bars starting at `starts`."""
    vecs = []
    for s, e in zip(starts, starts[1:] + [n_beats]):
        v = chroma_per_beat[:, s:e].mean(axis=1)
        vecs.append(v / (np.linalg.norm(v) + 1e-9))
    if len(vecs) < 2:
        return 0.0
    V = np.array(vecs)
    return float(np.mean(1 - np.sum(V[:-1] * V[1:], axis=1)))


def _choose_phase(
    downbeat_idx: Sequence[int],
    numerator: int,
    n_beats: int,
    chroma_per_beat: np.ndarray | None,
) -> int:
    phase, _ = modal_phase(downbeat_idx, numerator)
    if chroma_per_beat is None or not len(downbeat_idx) or numerator < 2:
        return phase
    counts = _phase_counts(downbeat_idx, numerator)
    order = np.argsort(-counts, kind="stable")
    first, second = int(order[0]), int(order[1])
    if counts[second] < NEAR_TIE * counts[first]:
        return phase
    scores = {
        p: _chroma_change(chroma_per_beat, list(range(p, n_beats, numerator)), n_beats)
        for p in sorted((first, second))
    }
    return max(scores, key=lambda p: scores[p])


def build_bars(
    beats: Sequence[float],
    downbeat_idx: Sequence[int],
    meter: Meter,
    duration: float,
    chroma_per_beat: np.ndarray | None = None,
) -> list[Bar]:
    """Bars of `meter.numerator` beats starting on the modal downbeat phase.

    When two phases tie or nearly tie (after halving) and per-beat chroma
    (12 x beats) is given, the phase with the larger adjacent-bar chroma change
    wins. Beats before the first full bar form a pickup bar 0 (flagged `pickup`); the
    final bar ends one median beat after the last beat, capped at `duration`; beats at or after `duration` (a downbeat at the exact end of
    the audio) are ignored.
    """
    times = [float(b) for b in beats]
    n_beats = sum(1 for t in times if t < duration)
    n = meter.numerator
    idx = [i for i in downbeat_idx if i < n_beats]
    if n_beats == 0:
        return []
    phase = _choose_phase(idx, n, n_beats, chroma_per_beat)
    phase = min(phase, n_beats - 1)
    starts = ([0] if phase > 0 else []) + list(range(phase, n_beats, n))
    if n_beats >= 2:
        final_end = min(float(duration), times[n_beats - 1] + float(np.median(np.diff(times[:n_beats]))))
    else:
        final_end = float(duration)
    bars = []
    for number, (s, e) in enumerate(zip(starts, starts[1:] + [n_beats])):
        end = times[e] if e < n_beats else final_end
        bars.append(
            Bar(
                index=number,
                start=times[s],
                end=end,
                beats=list(range(s, e)),
                pickup=number == 0 and phase > 0,
            )
        )
    return bars
