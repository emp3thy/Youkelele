import numpy as np
import pytest

from youkelele.music.rests import (
    REST_LOW_SHARE_MIN,
    bar_energy_ratio,
    bar_holds,
    bar_low_share,
    bar_window,
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
    assert bar_energy_ratio(zeros, mix, SR, BAR, 8) == 0.0
    assert not bar_holds(0.0, 0.5)


def test_a_low_tone_bar_holds():
    tone = _tone(110, 0.3)
    assert bar_energy_ratio(tone, tone, SR, BAR, 8) == pytest.approx(1.0)
    share = bar_low_share(tone, BAR, 8)
    assert share > 0.9
    assert bar_holds(1.0, share)


def test_a_loud_bell_bar_rests_by_register():
    bell = _tone(2000, 0.9)
    assert bar_energy_ratio(bell, bell, SR, BAR, 8) == pytest.approx(1.0)
    share = bar_low_share(bell, BAR, 8)
    assert share < REST_LOW_SHARE_MIN
    assert not bar_holds(1.0, share)


def test_thresholds_are_inclusive():
    assert bar_holds(0.05, 0.005)
    assert not bar_holds(0.0499, 0.005)
    assert not bar_holds(0.05, 0.0049)


def test_a_bar_shorter_than_a_frame_still_measures():
    short_tone = _tone(110, 0.3)
    assert int(round((SHORT_BAR.end - SHORT_BAR.start) * SR)) < 2048
    assert bar_low_share(short_tone, SHORT_BAR, 8) > 0.5
    assert bar_low_share(np.zeros(2048, dtype=np.float32), SHORT_BAR, 8) == 0.0


def test_resample_is_identity_at_22050_and_changes_length_otherwise():
    tone = _tone(110, 0.3)
    assert resample_for_rests(tone, 22050) is tone
    assert len(resample_for_rests(np.zeros(44100, dtype=np.float32), 44100)) == 22050


def test_bar_window_trims_half_a_slot_at_the_end_only():
    assert bar_window(BAR, 8) == (0.5, 2.375)


def test_energy_in_the_last_half_slot_belongs_to_the_next_bar():  # the Chelsea Dagger 7 and 12 case
    tone = _tone(110, 0.3)
    mix = tone
    stem = np.zeros_like(mix)
    stem[int(2.4 * SR):int(2.5 * SR)] = tone[int(2.4 * SR):int(2.5 * SR)]
    assert bar_energy_ratio(stem, mix, SR, BAR, 8) == 0.0
    assert bar_low_share(stem, BAR, 8) == 0.0


def test_energy_just_before_the_bar_line_is_not_counted():  # the ringing previous stroke
    tone = _tone(110, 0.3)
    stem = np.zeros_like(tone)
    stem[int(0.4 * SR):int(0.5 * SR)] = tone[int(0.4 * SR):int(0.5 * SR)]
    assert bar_energy_ratio(stem, tone, SR, BAR, 8) == 0.0


def test_a_low_tone_bar_still_holds_on_the_trimmed_window():
    tone = _tone(110, 0.3)
    assert bar_energy_ratio(tone, tone, SR, BAR, 8) == pytest.approx(1.0)
    assert bar_low_share(tone, BAR, 8) > 0.9
