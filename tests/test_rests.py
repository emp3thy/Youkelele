import numpy as np
import pytest

from youkelele.music.rests import (
    REST_LOW_SHARE_MIN,
    bar_energy_ratio,
    bar_holds,
    bar_low_share,
    resample_for_rests,
)
from youkelele.schemas import Bar

SR = 22050
BAR = Bar(index=0, start=0.5, end=2.5, beats=[0, 1, 2, 3])
SHORT_BAR = Bar(index=0, start=0.5, end=0.56, beats=[0])


def _tone(freq: float, amp: float, seconds: float = 3.0) -> np.ndarray:
    t = np.arange(int(seconds * SR)) / SR
    return (amp * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def test_a_silent_bar_rests_by_ratio():
    mix = _tone(220, 0.3)
    zeros = np.zeros_like(mix)
    assert bar_energy_ratio(zeros, mix, SR, BAR) == 0.0
    assert not bar_holds(0.0, 0.5)


def test_a_low_tone_bar_holds():
    tone = _tone(110, 0.3)
    assert bar_energy_ratio(tone, tone, SR, BAR) == pytest.approx(1.0)
    share = bar_low_share(tone, BAR)
    assert share > 0.9
    assert bar_holds(1.0, share)


def test_a_loud_bell_bar_rests_by_register():
    bell = _tone(2000, 0.9)
    assert bar_energy_ratio(bell, bell, SR, BAR) == pytest.approx(1.0)
    share = bar_low_share(bell, BAR)
    assert share < REST_LOW_SHARE_MIN
    assert not bar_holds(1.0, share)


def test_thresholds_are_inclusive():
    assert bar_holds(0.05, 0.005)
    assert not bar_holds(0.0499, 0.005)
    assert not bar_holds(0.05, 0.0049)


def test_a_bar_shorter_than_a_frame_still_measures():
    short_tone = _tone(110, 0.3)
    assert int(round((SHORT_BAR.end - SHORT_BAR.start) * SR)) < 2048
    assert bar_low_share(short_tone, SHORT_BAR) > 0.5
    assert bar_low_share(np.zeros(2048, dtype=np.float32), SHORT_BAR) == 0.0


def test_resample_is_identity_at_22050_and_changes_length_otherwise():
    tone = _tone(110, 0.3)
    assert resample_for_rests(tone, 22050) is tone
    assert len(resample_for_rests(np.zeros(44100, dtype=np.float32), 44100)) == 22050
