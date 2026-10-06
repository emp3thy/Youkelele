"""The per-bar rest rule: does this bar hold a strummed instrument?

A bar rests, and prints an empty stroke row, unless both measurements pass:
the guitar stem's RMS against the mix over the bar is at least 0.05, and the
share of the stem's STFT power below 330 Hz is at least 0.005. The first
catches near-silent bars, the second loud but high-register bars such as a
bell. Both bands come from the spike in
docs/superpowers/research/2026-10-06-v1-7/rests.md. Pure numpy and librosa.
"""

from __future__ import annotations

import librosa
import numpy as np

from youkelele.music.onsets import rms_ratio
from youkelele.schemas import Bar

# Near-silent bars sit at or below 0.069 to 0.09 of the mix; ear-verified bars sit above.
REST_RATIO_MIN = 0.05
# Bells and empty bars read 0.0002 to 0.0006, the quietest ear-verified bar 0.040; log-midpoint of the band.
REST_LOW_SHARE_MIN = 0.005
REST_LOW_HZ = 330  # the register a strummed ukulele or guitar chord holds
REST_SR = 22050  # the spike's STFT rate
_N_FFT = 2048
_HOP = 512


def bar_energy_ratio(stem: np.ndarray, mix: np.ndarray, sr: int, bar: Bar) -> float:
    """RMS of the stem over the bar divided by RMS of the mix, at the native rate."""
    first, last = int(round(bar.start * sr)), int(round(bar.end * sr))
    return rms_ratio(stem[first:last], mix[first:last])


def bar_low_share(stem_22k: np.ndarray, bar: Bar) -> float:
    """Share of the bar's STFT power below 330 Hz; 0.0 for a silent slice.

    A slice shorter than one frame is zero-padded to one so the share stays defined.
    """
    first, last = int(round(bar.start * REST_SR)), int(round(bar.end * REST_SR))
    seg = np.asarray(stem_22k[first:last], dtype=np.float32)
    if len(seg) < _N_FFT:
        seg = np.pad(seg, (0, _N_FFT - len(seg)))
    power = np.abs(librosa.stft(seg, n_fft=_N_FFT, hop_length=_HOP)) ** 2
    freqs = librosa.fft_frequencies(sr=REST_SR, n_fft=_N_FFT)
    return float(power[freqs < REST_LOW_HZ].sum() / (power.sum() + 1e-12))


def bar_holds(energy_ratio: float, low_share: float) -> bool:
    """True when the bar is loud enough against the mix and holds low-register power."""
    return energy_ratio >= REST_RATIO_MIN and low_share >= REST_LOW_SHARE_MIN


def resample_for_rests(stem: np.ndarray, sr: int) -> np.ndarray:
    """The stem at 22 050 Hz (the same array when it already is), so the stage resamples once."""
    if sr == REST_SR:
        return stem
    return librosa.resample(stem, orig_sr=sr, target_sr=REST_SR)
