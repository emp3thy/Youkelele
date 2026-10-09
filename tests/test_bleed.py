import numpy as np

from youkelele.music.bleed import BleedFigures, bass_on_stem, bleed_figures

SR = 22050
_t = np.arange(3 * SR) / SR
low = (0.3 * np.sin(2 * np.pi * 100 * _t)).astype(np.float32)
high = (0.3 * np.sin(2 * np.pi * 2000 * _t)).astype(np.float32)
zeros = np.zeros_like(low)


def test_bass_on_the_source_stem_with_an_empty_bass_stem_fires():
    f = bleed_figures(low, zeros, low, SR, 0.0, 3.0)
    assert f.bass_stem_ratio == 0.0 and f.low_own_share > 0.9 and f.low_mix_share_source > 0.9 and bass_on_stem(f)


def test_bass_on_the_bass_stem_does_not_fire():
    f = bleed_figures(high, low, low + high, SR, 0.0, 3.0)
    assert f.bass_stem_ratio > 0.3 and f.low_own_share < 0.05 and f.low_mix_share_bass > 0.9 and not bass_on_stem(f)


def test_a_bright_source_over_an_empty_bass_stem_does_not_fire():  # the bridge-arpeggio limit
    f = bleed_figures(high, zeros, high, SR, 0.0, 3.0)
    assert f.bass_stem_ratio == 0.0 and f.low_own_share < 0.05 and not bass_on_stem(f)


def test_gate_thresholds_are_inclusive():
    assert (
        bass_on_stem(BleedFigures(0, 0, 0.40, 0.05))
        and not bass_on_stem(BleedFigures(0, 0, 0.39, 0.05))
        and not bass_on_stem(BleedFigures(0, 0, 0.40, 0.0501))
    )


def test_a_span_shorter_than_a_frame_still_measures():
    f = bleed_figures(low, zeros, low, SR, 0.0, 0.05)
    assert 0.0 <= f.low_own_share <= 1.0
