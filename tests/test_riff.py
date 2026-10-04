import numpy as np

from youkelele.music.riff import (
    RIFF_ENTROPY_MAX,
    RIFF_SINGLE_PC_MIN,
    is_riff,
    onset_chroma,
    riff_features,
)

SR = 22050
ONSETS = [0.5 * k for k in range(8)]


def tone(freqs_per_onset, onsets, sr, harmonics=6, length=0.4):
    """Decaying sines (six harmonics at 1/k) starting at each onset time."""
    n = int(sr * (max(onsets) + length + 0.2))
    y = np.zeros(n, dtype=np.float32)
    t = np.arange(int(sr * length)) / sr
    env = np.exp(-6.0 * t)
    for freqs, onset in zip(freqs_per_onset, onsets, strict=True):
        start = int(round(onset * sr))
        for f in freqs:
            for k in range(1, harmonics + 1):
                y[start : start + t.size] += (env * np.sin(2 * np.pi * f * k * t) / k).astype(np.float32)
    return y / max(1.0, float(np.abs(y).max()))


def _features(freqs):
    y = tone([freqs] * 8, onsets=ONSETS, sr=SR)
    return riff_features(onset_chroma(y, SR, np.array(ONSETS)))


def test_single_note_onsets_read_as_riff():
    entropy, share = _features([196.0])
    assert entropy < 0.6 and share > 0.9 and is_riff(entropy, share)


def test_four_note_chords_do_not_read_as_riff():
    # G7 (G3 B3 D4 F4): four distinct pitch classes, no doubled root. A voicing that
    # doubles the root (G3 B3 D4 G4) lets G dominate the clean synthetic spectrum
    # (entropy 0.78, single share 1.0), which a recorded strum does not do.
    entropy, share = _features([196.0, 246.9, 293.7, 349.2])
    assert entropy > RIFF_ENTROPY_MAX and share < 0.2 and not is_riff(entropy, share)
    assert entropy - _features([196.0])[0] >= 0.2


def test_no_onsets_gives_no_features_and_no_riff():
    assert riff_features(np.zeros((0, 12))) == (None, None)
    assert not is_riff(None, None)


def test_onset_near_the_end_with_no_window_frames_is_a_zero_row():
    chroma = onset_chroma(np.zeros(22050), 22050, np.array([0.99]))
    assert chroma.shape == (1, 12) and not chroma.any()


def test_zero_row_counts_as_full_entropy_and_not_single():
    entropy, share = riff_features(np.zeros((1, 12)))
    assert entropy == 1.0 and share == 0.0


def test_features_are_the_median_entropy_and_the_single_pitch_class_share():
    single = np.zeros(12)
    single[3] = 1.0
    flat = np.ones(12)
    entropy, share = riff_features(np.array([single, single, flat]))
    assert abs(entropy) < 1e-9 and abs(share - 2 / 3) < 1e-9


def test_chroma_is_driven_at_the_signals_own_sample_rate():
    y = tone([[196.0]] * 8, onsets=ONSETS, sr=16000)
    chroma = onset_chroma(y, 16000, np.array(ONSETS))
    assert chroma.shape == (8, 12)
    assert (chroma.argmax(axis=1) == 7).all()  # G


def test_thresholds_are_the_spec_values():
    assert (RIFF_ENTROPY_MAX, RIFF_SINGLE_PC_MIN) == (0.82, 0.45)
    assert is_riff(0.82, 0.45) and not is_riff(0.83, 0.45) and not is_riff(0.82, 0.44)
