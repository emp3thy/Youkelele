from __future__ import annotations

import numpy as np
import soundfile as sf

from tests.audio_fixtures import write_click_track
from youkelele.music.onsets import (
    Onsets,
    choose_slots_per_bar,
    choose_source,
    detect_onsets,
    direction_for_slot,
    grid_fit,
    mute_mask,
    quantise_bar,
    render_directions,
    rms_ratio,
    section_has_instrument,
)
from youkelele.schemas import Bar, Meter

m44 = Meter(numerator=4, denominator=4)
m34 = Meter(numerator=3, denominator=4)
ISLAND = (0, 2, 3, 5, 6, 7)


def _bars(n: int, seconds: float = 2.0, beats_per_bar: int = 4) -> list[Bar]:
    return [
        Bar(
            index=i, start=i * seconds, end=(i + 1) * seconds,
            beats=list(range(beats_per_bar * i, beats_per_bar * (i + 1))),
        )
        for i in range(n)
    ]


def _onsets(times, centroid=None, zcr=None) -> Onsets:
    times = np.asarray(times, dtype=float)
    centroid = np.full(len(times), 2000.0) if centroid is None else np.asarray(centroid, dtype=float)
    zcr = np.full(len(times), 0.1) if zcr is None else np.asarray(zcr, dtype=float)
    return Onsets(times=times, centroid=centroid, zcr=zcr)


def _island_times(n_bars: int, seconds: float = 2.0, slots: int = 8) -> list[float]:
    width = seconds / slots
    return [b * seconds + k * width for b in range(n_bars) for k in ISLAND]


def test_direction_for_slot_eighths_4_4():
    assert [direction_for_slot(i, 8, m44) for i in range(8)] == list("DUDUDUDU")


def test_direction_for_slot_sixteenths_marks_eighths_down():
    dirs = [direction_for_slot(i, 16, m44) for i in range(16)]
    assert dirs == ["D" if i % 2 == 0 else "U" for i in range(16)]


def test_quantise_bar_island_strum():
    onsets = _onsets(_island_times(1))
    bar = _bars(1)[0]
    classes = quantise_bar(onsets, np.zeros(len(onsets.times), dtype=bool), bar, 8)
    assert "".join(classes) == "S-SS-SSS"
    assert "".join(render_directions(classes, 8, m44)) == "D-DU-UDU"


def test_quantise_bar_marks_muted_onset_x():
    onsets = _onsets(_island_times(1))
    muted = np.zeros(len(onsets.times), dtype=bool)
    muted[1] = True  # the strike at slot 2
    classes = quantise_bar(onsets, muted, _bars(1)[0], 8)
    assert "".join(classes) == "S-xS-SSS"
    assert "".join(render_directions(classes, 8, m44)) == "D-xU-UDU"


def test_quantise_bar_first_onset_in_a_slot_wins():
    onsets = _onsets([0.0, 0.05])
    muted = np.array([False, True])
    assert "".join(quantise_bar(onsets, muted, _bars(1)[0], 8)) == "S-------"


def test_quantise_bar_snaps_early_downbeat_to_the_next_bar():
    # an onset slightly before bar 1's downbeat is bar 1 slot 0, not bar 0 slot 8
    onsets = _onsets([0.0, 1.98, 2.5])
    bars = _bars(2)
    muted = np.zeros(3, dtype=bool)
    assert "".join(quantise_bar(onsets, muted, bars[0], 8)) == "S-------"
    assert "".join(quantise_bar(onsets, muted, bars[1], 8)) == "S-S-----"


def test_mute_mask_disabled_on_mix_returns_all_false():
    onsets = _onsets([0.0, 0.5, 1.0], centroid=[100.0, 2000.0, 2000.0], zcr=[0.01, 0.1, 0.1])
    mask = mute_mask(onsets, enabled=False)
    assert mask.dtype == bool
    assert mask.tolist() == [False, False, False]


def test_mute_mask_relative_thresholds():
    # median centroid 2000, median zcr 0.1: thresholds 1700 and 0.065
    onsets = _onsets(
        [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5],
        centroid=[1600.0, 1600.0, 1800.0, 2000.0, 2000.0, 2000.0, 2000.0],
        zcr=[0.06, 0.07, 0.06, 0.1, 0.1, 0.1, 0.1],
    )
    assert mute_mask(onsets, enabled=True).tolist() == [True, False, False, False, False, False, False]


def test_rms_ratio_is_part_over_mix():
    mix = np.ones(100)
    assert abs(rms_ratio(0.5 * mix, mix) - 0.5) < 1e-6
    assert rms_ratio(np.zeros(100), np.zeros(100)) == 0.0


def test_choose_source_prefers_louder_of_guitar_and_other():
    t = np.arange(4410) / 44100
    mix = np.sin(2 * np.pi * 220 * t)
    source, y, ratio = choose_source(0.1 * mix, 0.5 * mix, mix)
    assert source == "other_stem"
    assert abs(ratio - 0.5) < 1e-3
    assert np.allclose(y, 0.5 * mix)
    source, _, _ = choose_source(0.5 * mix, 0.1 * mix, mix)
    assert source == "guitar_stem"


def test_choose_source_falls_back_to_mix_below_0_05():
    t = np.arange(4410) / 44100
    mix = np.sin(2 * np.pi * 220 * t)
    source, y, ratio = choose_source(0.03 * mix, 0.04 * mix, mix)
    assert source == "mix"
    assert np.allclose(y, mix)
    assert abs(ratio - 0.04) < 1e-3
    source, _, _ = choose_source(0.0 * mix, 0.051 * mix, mix)
    assert source == "other_stem"


def test_section_has_instrument_at_0_10():
    mix = np.ones(1000)
    assert section_has_instrument(0.11 * mix, mix)
    assert not section_has_instrument(0.09 * mix, mix)


def test_choose_slots_per_bar_prefers_8_for_eighth_grid_and_6_for_3_4():
    assert choose_slots_per_bar(_onsets(_island_times(4)), _bars(4), m44) == 8
    times_34 = [b * 1.5 + k * 0.25 for b in range(4) for k in (0, 2, 3, 5)]
    assert choose_slots_per_bar(_onsets(times_34), _bars(4, 1.5, 3), m34) == 6


def test_choose_slots_per_bar_picks_16_when_odd_sixteenths_exceed_25_percent():
    width = 2.0 / 16
    # per bar: 6 eighth positions and 3 odd sixteenths -> 3/9 = 33% odd
    per_bar = (0, 2, 4, 6, 8, 10, 3, 7, 11)
    times = [b * 2.0 + k * width for b in range(4) for k in per_bar]
    assert choose_slots_per_bar(_onsets(times), _bars(4), m44) == 16
    # 2 of 10 odd = 20% stays at eighths
    per_bar = (0, 2, 4, 6, 8, 10, 12, 14, 3, 7)
    times = [b * 2.0 + k * width for b in range(4) for k in per_bar]
    assert choose_slots_per_bar(_onsets(times), _bars(4), m44) == 8


def test_grid_fit_is_share_within_15_percent():
    width = 2.0 / 8
    # deviations in slot widths: 0, 0.1, 0.14 within; 0.2, 0.4 outside
    times = [0.0, 2.1 * width, 3.86 * width, 5.2 * width, 6.4 * width]
    assert abs(grid_fit(_onsets(times), _bars(1), 8) - 3 / 5) < 1e-9
    assert grid_fit(_onsets([]), _bars(1), 8) == 0.0


def test_detect_onsets_finds_clicks_with_features(tmp_path):
    path = tmp_path / "clicks.wav"
    write_click_track(path, 4.0, 120.0)
    y, sr = sf.read(str(path), dtype="float32")
    onsets = detect_onsets(y, sr)
    assert len(onsets.times) == len(onsets.centroid) == len(onsets.zcr)
    expected = np.arange(1, 8) * 0.5  # the click at 0 s has no onset-strength rise before it
    found = [np.min(np.abs(onsets.times - t)) for t in expected]
    assert max(found) < 0.05
    assert np.all(onsets.centroid > 0)


def test_quantise_bar_clamps_an_onset_at_the_lower_window_edge_to_slot_0():
    # floating point puts this onset, exactly half a slot early, at index -1
    bar = Bar(index=0, start=4.4399999999999995, end=6.369999999999999, beats=[0, 1, 2, 3])
    onsets = _onsets([4.319374999999999])
    assert "".join(quantise_bar(onsets, np.zeros(1, dtype=bool), bar, 8)) == "S-------"


def test_quantise_bar_clamps_an_onset_at_the_upper_window_edge_to_the_last_slot():
    # just inside the shifted window, floating point rounds this onset to index 8
    bar = Bar(index=0, start=1.406, end=3.483, beats=[0, 1, 2, 3])
    onsets = _onsets([3.3531874999999998])
    assert "".join(quantise_bar(onsets, np.zeros(1, dtype=bool), bar, 8)) == "-------S"
