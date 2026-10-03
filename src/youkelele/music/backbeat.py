"""Drum backbeat test: is there more high-band energy on beats 2 and 4 than on 1 and 3?

Used by the automatic tempo-octave rule. A genuine fast rock song has a snare on
2 and 4 at the detected tempo (ratio well above 1); a doubled ballad has not
(ratio below 1). Measured on real drum stems in the lessons analysis.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

DRUMS_SILENT_RMS = 0.003
BACKBEAT_BAND_HZ = (1500.0, 6000.0)
MIN_BEATS = 8
_N_FFT = 1024
_PEAK_FRAMES = 2  # frames either side of a beat searched for the flux peak


def drums_silent(y: np.ndarray) -> bool:
    """True when the drum stem's RMS is below `DRUMS_SILENT_RMS`."""
    if len(y) == 0:
        return True
    return float(np.sqrt(np.mean(np.square(y, dtype=np.float64)))) < DRUMS_SILENT_RMS


def backbeat_ratio(
    y: np.ndarray, sr: int, beats: Sequence[float], numerator: int
) -> float | None:
    """High-band flux on the backbeat beats over the flux on the strong beats.

    Beat index 0 is taken as the downbeat. In 4/4 the backbeat is indices 1 and 3
    against 0 and 2; in 3/4 it is 1 and 2 against 0. Returns None for fewer than
    eight beats or when the denominator is zero.
    """
    import librosa

    if len(beats) < MIN_BEATS or len(y) < _N_FFT:
        return None
    hop = max(1, int(round(sr * 256 / 22050)))
    spec = np.abs(librosa.stft(np.asarray(y, dtype=np.float32), n_fft=_N_FFT, hop_length=hop))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=_N_FFT)
    band = spec[(freqs > BACKBEAT_BAND_HZ[0]) & (freqs < BACKBEAT_BAND_HZ[1])]
    flux = np.maximum(np.diff(np.log1p(band), axis=1), 0).sum(axis=0)
    times = librosa.frames_to_time(np.arange(len(flux)) + 1, sr=sr, hop_length=hop)

    def at(t: float) -> float:
        i = int(np.searchsorted(times, t))
        if i >= len(flux):
            return 0.0
        return float(flux[max(0, i - _PEAK_FRAMES) : i + _PEAK_FRAMES + 1].max())

    back_idx = (1, 2) if numerator == 3 else (1, 3)
    strong_idx = (0,) if numerator == 3 else (0, 2)
    back = strong = 0.0
    for i, t in enumerate(beats):
        pos = i % numerator
        if pos in back_idx:
            back += at(t)
        elif pos in strong_idx:
            strong += at(t)
    if strong <= 0:
        return None
    return back / strong
