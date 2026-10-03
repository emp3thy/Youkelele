import numpy as np

from youkelele.music.key import estimate_key


def _chroma(pitch_classes):
    chroma = np.full(12, 0.05)
    for pc in pitch_classes:
        chroma[pc] = 1.0
    return chroma


def test_estimate_key_c_major_from_scale_chroma():
    chroma = _chroma([0, 2, 4, 5, 7, 9, 11])
    chroma[0] += 0.5
    chroma[7] += 0.3
    key = estimate_key(chroma)
    assert (key.tonic, key.mode) == ("C", "major")
    assert 0 <= key.confidence <= 1


def test_estimate_key_a_minor_prefers_minor_profile():
    chroma = _chroma([9, 11, 0, 2, 4, 5, 8])
    chroma[9] += 0.6
    chroma[4] += 0.4
    chroma[0] += 0.3
    key = estimate_key(chroma)
    assert (key.tonic, key.mode) == ("A", "minor")
