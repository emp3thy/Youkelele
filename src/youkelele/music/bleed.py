"""The bass-on-stem gate: did the separator put the real bass on the source stem?

Spec 1.8 section 6. On one blind song the separator put the bass on the guitar
stem and left the bass stem empty. Four per-span figures measure it: the bass
stem's and the source stem's share of the mix's STFT power below 250 Hz, the
source stem's own share of power below 250 Hz, and the bass stem's RMS against
the mix. The gate fires when the bass stem is near empty and the source stem's
own energy lives low. The bands come from one positive song, so they are
evidence from a single case, not a calibrated range.
"""

from __future__ import annotations

from dataclasses import dataclass

import librosa
import numpy as np

from youkelele.music.onsets import rms_ratio

BLEED_LOW_HZ = 250  # the register of a bass line; bins whose centre lies below it
# Bass-stem RMS against the mix ran 0.002 to 0.317 across songs; the empty stem sat at the bottom.
BASS_STEM_MAX = 0.05
# The source stem's own low share ran 0.376 to 0.462 on the one positive song; a bright stem sits near 0.
OWN_LOW_SHARE_MIN = 0.40
_N_FFT = 4096
_HOP = 2048


@dataclass(frozen=True)
class BleedFigures:
    low_mix_share_bass: float
    low_mix_share_source: float
    low_own_share: float
    bass_stem_ratio: float


def _power(seg: np.ndarray, sr: int) -> tuple[np.ndarray, np.ndarray]:
    """STFT power of the slice (zero-padded to one frame if shorter) and the low-band bin mask."""
    seg = np.asarray(seg, dtype=np.float32)
    if len(seg) < _N_FFT:
        seg = np.pad(seg, (0, _N_FFT - len(seg)))
    power = np.abs(librosa.stft(seg, n_fft=_N_FFT, hop_length=_HOP)) ** 2
    low = librosa.fft_frequencies(sr=sr, n_fft=_N_FFT) < BLEED_LOW_HZ
    return power, low


def bleed_figures(
    source: np.ndarray, bass: np.ndarray, mix: np.ndarray, sr: int, start: float, end: float
) -> BleedFigures:
    """The four bleed figures over the samples in [start, end) seconds."""
    first, last = int(round(start * sr)), int(round(end * sr))
    src, bas, mx = source[first:last], bass[first:last], mix[first:last]
    src_power, low = _power(src, sr)
    bass_power, _ = _power(bas, sr)
    mix_power, _ = _power(mx, sr)
    mix_low = mix_power[low].sum() + 1e-12
    return BleedFigures(
        low_mix_share_bass=float(bass_power[low].sum() / mix_low),
        low_mix_share_source=float(src_power[low].sum() / mix_low),
        low_own_share=float(src_power[low].sum() / (src_power.sum() + 1e-12)),
        bass_stem_ratio=float(rms_ratio(bas, mx)),
    )


def bass_on_stem(f: BleedFigures) -> bool:
    """True when the bass stem is near empty and the source stem's own energy lives low."""
    return f.bass_stem_ratio <= BASS_STEM_MAX and f.low_own_share >= OWN_LOW_SHARE_MIN
