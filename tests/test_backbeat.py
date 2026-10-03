from __future__ import annotations

import numpy as np

from tests.audio_fixtures import drum_track
from youkelele.music.backbeat import backbeat_ratio, drums_silent

SR = 22050
BPM = 120


def _beats(seconds: float) -> list[float]:
    return [i * 60.0 / BPM for i in range(int(seconds * BPM / 60))]


def test_backbeat_ratio_above_one_for_snare_on_two_and_four():
    y = drum_track(SR, BPM, 20.0, (1, 3))
    assert backbeat_ratio(y, SR, _beats(20.0), 4) > 1.5


def test_backbeat_ratio_below_one_for_hits_on_one_and_three():
    y = drum_track(SR, BPM, 20.0, (0, 2))
    assert backbeat_ratio(y, SR, _beats(20.0), 4) < 0.7


def test_backbeat_ratio_three_four_uses_indices_one_and_two_against_zero():
    y = drum_track(SR, BPM, 20.0, (1, 2), beats_per_bar=3)
    assert backbeat_ratio(y, SR, _beats(20.0), 3) > 1.5


def test_backbeat_ratio_none_for_fewer_than_eight_beats():
    y = drum_track(SR, BPM, 20.0, (1, 3))
    assert backbeat_ratio(y, SR, _beats(20.0)[:7], 4) is None


def test_backbeat_ratio_none_when_denominator_is_zero():
    assert backbeat_ratio(np.zeros(SR * 10), SR, _beats(10.0), 4) is None


def test_drums_silent_true_for_near_silence_false_for_hits():
    rng = np.random.default_rng(1)
    quiet = 1e-4 * rng.standard_normal(SR * 5)
    assert drums_silent(quiet)
    assert not drums_silent(drum_track(SR, BPM, 5.0, (1, 3)))
