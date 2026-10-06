import numpy as np

from youkelele.music.ring import section_rings, stroke_decay_db


def _pluck(sr, seconds, tau):  # an exponentially decaying 220 Hz tone
    t = np.arange(int(sr * seconds)) / sr
    return np.sin(2 * np.pi * 220 * t) * np.exp(-t / tau)


def test_slow_decay_measures_small_and_fast_decay_large():
    sr, slot = 22050, 0.25
    slow = stroke_decay_db(_pluck(sr, 2.0, tau=1.0), sr, 0.0, None, slot)
    fast = stroke_decay_db(_pluck(sr, 2.0, tau=0.05), sr, 0.0, None, slot)
    assert slow is not None and fast is not None and slow < 5 < fast


def test_decay_is_none_when_the_next_stroke_is_too_close():
    assert stroke_decay_db(_pluck(22050, 2.0, 0.5), 22050, 0.0, 0.3, 0.25) is None  # 1.2 slots
    assert stroke_decay_db(_pluck(22050, 2.0, 0.5), 22050, 0.0, 0.4, 0.25) is not None  # 1.6 slots


def test_decay_is_none_when_the_signal_ends_first():
    assert stroke_decay_db(_pluck(22050, 0.2, 0.5), 22050, 0.0, None, 0.25) is None


def test_section_rings_by_median_and_defaults_true_without_strokes():
    assert section_rings([2.0, 3.0, 12.0]) == (True, 3.0)
    assert section_rings([9.0, 12.0, None]) == (False, 10.5)
    assert section_rings([None, None]) == (True, None)
