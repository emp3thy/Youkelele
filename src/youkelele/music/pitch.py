"""Monophonic pitch naming at onsets already trusted by the strums stage.

`track_pitch` calls librosa (pyin); everything else is pure numpy. The rhythm
never comes from the tracker: it only names a pitch at each given onset.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

PITCH_SR = 22050
PYIN_FMIN = 82.4
PYIN_FMAX = 1318.5
PYIN_FRAME = 2048
PYIN_HOP = 256
NOTE_SKIP_IN_S = 0.020
NOTE_SKIP_OUT_S = 0.010
NOTE_VOICED_MIN = 0.5
PITCH_CHANGE_MIN = 0.4


@dataclass
class PitchTrack:
    times: np.ndarray  # frame centre times in seconds
    midi: np.ndarray  # fractional MIDI note, nan where unvoiced


def track_pitch(y: np.ndarray, sr: int) -> PitchTrack:
    import librosa

    y = np.asarray(y, dtype=np.float32)
    if sr != PITCH_SR:
        y = librosa.resample(y, orig_sr=sr, target_sr=PITCH_SR)
    f0, voiced_flag, _ = librosa.pyin(
        y,
        fmin=PYIN_FMIN,
        fmax=PYIN_FMAX,
        sr=PITCH_SR,
        frame_length=PYIN_FRAME,
        hop_length=PYIN_HOP,
    )
    midi = np.full(len(f0), np.nan)
    voiced = np.asarray(voiced_flag, dtype=bool) & np.isfinite(f0)
    midi[voiced] = librosa.hz_to_midi(f0[voiced])
    times = librosa.frames_to_time(np.arange(len(f0)), sr=PITCH_SR, hop_length=PYIN_HOP)
    return PitchTrack(times=times, midi=midi)


def name_notes(
    track: PitchTrack, onsets: Sequence[float], ends: Sequence[float]
) -> list[int | None]:
    notes: list[int | None] = []
    for onset, end in zip(onsets, ends):
        lo = onset + NOTE_SKIP_IN_S
        hi = end - NOTE_SKIP_OUT_S
        mask = (track.times >= lo) & (track.times < hi)
        window = track.midi[mask]
        if window.size == 0:
            notes.append(None)
            continue
        voiced = window[~np.isnan(window)]
        if voiced.size / window.size < NOTE_VOICED_MIN:
            notes.append(None)
            continue
        notes.append(int(round(float(np.median(voiced)))))
    return notes


def pitch_change_share(notes: Sequence[int | None]) -> float | None:
    pairs = [(a, b) for a, b in zip(notes, notes[1:]) if a is not None and b is not None]
    if not pairs:
        return None
    return sum(1 for a, b in pairs if a != b) / len(pairs)
