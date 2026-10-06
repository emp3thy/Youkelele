"""Riff features: two onset-pitch measures that tell a single-note line from strummed chords.

The constants were fixed by the riff-thresholds measurement
(docs/superpowers/research/2026-10-04-v1-5/riff-thresholds.md). Only
`onset_chroma` calls librosa; everything else is pure numpy.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from youkelele.music.key import pitch_class
from youkelele.schemas import ChordEvent

RIFF_ENTROPY_MAX = 0.82  # median per-onset normalised chroma entropy at or below this
RIFF_SINGLE_PC_MIN = 0.45  # share of onsets with one dominant pitch class at or above this
RIFF_WINDOW = (0.040, 0.130)  # seconds after the onset: past the attack, inside a short sixteenth
RIFF_FMIN_NOTE = "C2"
RIFF_OCTAVES = 6
RIFF_HOP_SECONDS = 256 / 22050
_BINS_PER_OCTAVE = 12
_SINGLE_PC_RATIO = 0.5  # a pitch class counts as present at this share of the maximum
_EPS = 1e-12


def onset_chroma(y: np.ndarray, sr: int, times: np.ndarray) -> np.ndarray:
    """Constant-Q power folded to 12 pitch classes, averaged in the window after each onset.

    Shape `(len(times), 12)`; a row of zeros where no frame falls inside the window.
    """
    import librosa

    times = np.asarray(times, dtype=float)
    out = np.zeros((len(times), 12))
    if len(times) == 0:
        return out
    hop = round(sr * RIFF_HOP_SECONDS)
    power = (
        np.abs(
            librosa.cqt(
                np.asarray(y, dtype=np.float32),
                sr=sr,
                hop_length=hop,
                fmin=librosa.note_to_hz(RIFF_FMIN_NOTE),
                n_bins=RIFF_OCTAVES * _BINS_PER_OCTAVE,
                bins_per_octave=_BINS_PER_OCTAVE,
            )
        )
        ** 2
    )
    chroma = power.reshape(RIFF_OCTAVES, _BINS_PER_OCTAVE, -1).sum(axis=0)
    n_frames = chroma.shape[1]
    for i, t in enumerate(times):
        first = int(np.floor((t + RIFF_WINDOW[0]) * sr / hop))
        stop = min(int(np.floor((t + RIFF_WINDOW[1]) * sr / hop)) + 1, n_frames)
        if first < stop:
            out[i] = chroma[:, max(first, 0) : stop].mean(axis=1)
    return out


def riff_features(chroma: np.ndarray) -> tuple[float | None, float | None]:
    """The median per-onset normalised entropy (log base 12) and the single-pitch-class share.

    A zero row counts as entropy 1.0 and not single; no onsets gives `(None, None)`.
    """
    chroma = np.asarray(chroma, dtype=float)
    if chroma.shape[0] == 0:
        return None, None
    entropies: list[float] = []
    singles: list[bool] = []
    for row in chroma:
        peak = row.max()
        if peak <= 0:
            entropies.append(1.0)
            singles.append(False)
            continue
        p = row / (row.sum() + _EPS)
        entropies.append(float(-(p * np.log(p + _EPS)).sum() / np.log(12)))
        singles.append(int(np.sum(row >= _SINGLE_PC_RATIO * peak)) == 1)
    return float(np.median(entropies)), float(np.mean(singles))


def is_riff(entropy: float | None, single_share: float | None) -> bool:
    """A single-note line: both measures present, low entropy and a high single-pitch-class share."""
    if entropy is None or single_share is None:
        return False
    return entropy <= RIFF_ENTROPY_MAX and single_share >= RIFF_SINGLE_PC_MIN


def chord_roots(events: Sequence[ChordEvent], times: Sequence[float]) -> list[int | None]:
    """The pitch class of the chord root under each time; `None` for no chord or no event."""
    out: list[int | None] = []
    for t in times:
        root: int | None = None
        for event in events:
            if event.start <= t < event.end:
                name = event.label.split(":")[0]
                if name not in ("N", "X"):
                    root = pitch_class(name)
                break
        out.append(root)
    return out


def root_share(notes: Sequence[int | None], roots: Sequence[int | None]) -> float | None:
    """The share of onsets, among those with a named note and a chord root, on the root."""
    pairs = [(n, r) for n, r in zip(notes, roots, strict=True) if n is not None and r is not None]
    if not pairs:
        return None
    return sum(1 for n, r in pairs if n % 12 == r) / len(pairs)


def named_share(notes: Sequence[int | None]) -> float | None:
    """The share of onsets that were given a pitch name; `None` for no onsets."""
    if not notes:
        return None
    return sum(1 for n in notes if n is not None) / len(notes)
