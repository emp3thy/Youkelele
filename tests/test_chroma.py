import numpy as np
import pytest

from youkelele.music.chroma import HarmonicChroma, harmonic_chroma
from youkelele.schemas import Bar


def _bars(n: int, seconds: float = 2.0) -> list[Bar]:
    return [
        Bar(index=i, start=i * seconds, end=(i + 1) * seconds, beats=list(range(4 * i, 4 * i + 4)))
        for i in range(n)
    ]


def _triad(freqs, sr: int, seconds: float = 2.0) -> np.ndarray:
    t = np.arange(int(seconds * sr)) / sr
    return sum(np.sin(2 * np.pi * f * t) for f in freqs) * 0.2


def test_harmonic_chroma_bar_means_shape_and_mask_mean():
    sr = 22050
    silence = np.zeros(2 * sr)
    c_major = _triad((261.63, 329.63, 392.0), sr)
    g_major = _triad((392.0, 493.88, 587.33), sr)
    guitar = np.concatenate([c_major, silence])
    piano = np.concatenate([silence, g_major])[:, None]  # a channels-last stem is folded to mono
    bass = np.zeros(sr)  # a shorter stem is padded with silence
    chroma, y = harmonic_chroma([guitar, piano, bass], sr)
    assert isinstance(chroma, HarmonicChroma)
    assert y.shape == (4 * sr,)
    assert y == pytest.approx(guitar + piano[:, 0], abs=1e-6)
    assert chroma.frames.shape[0] == 12 and chroma.frames.shape[1] == len(chroma.times)

    means = chroma.bar_means(_bars(2))
    assert means.shape == (2, 12)
    assert set(np.argsort(means[0])[-3:]) == {0, 4, 7}
    assert set(np.argsort(means[1])[-3:]) == {7, 11, 2}

    first = chroma.mean(np.array([True, False]), _bars(2))
    assert set(np.argsort(first)[-3:]) == {0, 4, 7}
    assert first == pytest.approx(means[0], abs=0.05)
    everything = chroma.frames.mean(axis=1)
    assert chroma.mean(np.array([False, False]), _bars(2)) == pytest.approx(everything)
    assert chroma.mean(np.array([], dtype=bool), []) == pytest.approx(everything)


def test_harmonic_chroma_of_silence_is_zero():
    chroma, y = harmonic_chroma([np.zeros(44100), np.zeros(44100)], 22050)
    assert not y.any()
    assert not chroma.bar_means(_bars(1)).any()
    assert not chroma.mean(np.array([True]), _bars(1)).any()
