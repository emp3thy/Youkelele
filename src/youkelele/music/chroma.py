"""The harmonic-stem chroma, computed once per run and shared by the fill and the key.

The guitar, bass, piano and other stems are summed to one mono signal and its CQT
chroma is taken once (hop 512). The fill reads per-bar means of it; the key reads its
mean over the bars loud enough to count, so silence and pre-roll do not vote.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from youkelele.schemas import Bar

HOP_LENGTH = 512


@dataclass
class HarmonicChroma:
    frames: np.ndarray  # 12 x n_frames
    times: np.ndarray  # n_frames, seconds
    sr: int

    def _in_bar(self, bar: Bar) -> np.ndarray:
        return (self.times >= bar.start) & (self.times < bar.end)

    def bar_means(self, bars: Sequence[Bar]) -> np.ndarray:
        """Mean chroma per bar (bars x 12); zeros for a bar with no frames."""
        out = np.zeros((len(bars), 12))
        for i, bar in enumerate(bars):
            mask = self._in_bar(bar)
            if mask.any():
                out[i] = self.frames[:, mask].mean(axis=1)
        return out

    def mean(self, mask: np.ndarray, bars: Sequence[Bar]) -> np.ndarray:
        """Mean chroma over the frames of the bars whose `mask` entry is true.

        Falls back to every frame when no frame falls in a passing bar; zeros when
        there are no frames at all.
        """
        if self.frames.shape[1] == 0:
            return np.zeros(12)
        frames = np.zeros(self.frames.shape[1], dtype=bool)
        for bar, keep in zip(bars, mask):
            if keep:
                frames |= self._in_bar(bar)
        if not frames.any():
            frames[:] = True
        return self.frames[:, frames].mean(axis=1)


def sum_stems(stems: Sequence[np.ndarray]) -> np.ndarray:
    """Sum the stems to one mono float32 signal; shorter stems are padded with silence.

    A 2-D stem is channels-last and is folded to mono first.
    """
    signals = [np.asarray(s, dtype=np.float32) for s in stems]
    signals = [s.mean(axis=1) if s.ndim == 2 else s for s in signals]
    mix = np.zeros(max((len(s) for s in signals), default=0), dtype=np.float32)
    for signal in signals:
        mix[: len(signal)] += signal
    return mix


def chroma_of(y: np.ndarray, sr: int) -> HarmonicChroma:
    """The CQT chroma of one mono signal; no frames for silence (no pitch to tune from)."""
    if not np.any(y):
        return HarmonicChroma(np.zeros((12, 0)), np.zeros(0), sr)
    import librosa

    signal = np.asarray(y, dtype=np.float32)
    frames = librosa.feature.chroma_cqt(y=signal, sr=sr, hop_length=HOP_LENGTH)
    times = librosa.frames_to_time(np.arange(frames.shape[1]), sr=sr, hop_length=HOP_LENGTH)
    return HarmonicChroma(frames, times, sr)


def harmonic_chroma(stems: Sequence[np.ndarray], sr: int) -> tuple[HarmonicChroma, np.ndarray]:
    """The chroma of the summed harmonic stems, and the summed mono signal itself."""
    y = sum_stems(stems)
    return chroma_of(y, sr), y
