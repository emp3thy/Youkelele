from __future__ import annotations

import numpy as np
import pytest

from youkelele.music.tempo import (
    bpm_from_beats,
    build_bars,
    decide_octave,
    double_beats,
    downbeat_indices,
    fill_gaps,
    modal_phase,
    normalise_octave,
)
from youkelele.schemas import Meter

FOUR = Meter(numerator=4, denominator=4)


def test_bpm_from_regular_beats():
    assert bpm_from_beats([0, 0.5, 1.0, 1.5]) == pytest.approx(120)


def test_fill_gaps_inserts_one_dropped_beat():
    beats = [i * 0.5 for i in range(21) if i != 10]  # 5.0 s dropped
    filled = fill_gaps(beats)
    assert len(filled) == 21
    assert filled == pytest.approx([i * 0.5 for i in range(21)])


def test_fill_gaps_leaves_regular_beats_alone():
    beats = [i * 0.5 for i in range(30)]
    assert fill_gaps(beats) == pytest.approx(beats)


def test_decide_octave_auto_halves_150_keeps_139_and_85():
    assert decide_octave(150, "auto") == "half"
    assert decide_octave(139, "auto") == "none"
    assert decide_octave(85, "auto") == "none"


def test_decide_octave_overrides_pass_through():
    assert decide_octave(150, "none") == "none"
    assert decide_octave(85, "double") == "double"
    assert decide_octave(100, "half") == "half"


def test_downbeat_indices_and_modal_phase():
    beats = [i * 0.5 for i in range(16)]
    idx = downbeat_indices(beats, [0.52, 2.49, 4.5, 6.3, 9.0])  # 6.3 is 0.2 s off: dropped
    assert idx == [1, 5, 9]
    assert modal_phase([1, 5, 9, 2], 4) == (1, pytest.approx(0.75))


def test_normalise_octave_repairs_half_doubled_list():
    period = 0.7
    true_beats = [i * period for i in range(86)]  # 0 .. 59.5 s
    beats = []
    for b in true_beats:
        beats.append(b)
        if b < 20.0:
            beats.append(b + period / 2)  # Beat This! at double tempo for the first 20 s
    downbeats = true_beats[::4]
    idx = downbeat_indices(beats, downbeats)
    out, out_idx = normalise_octave(beats, idx, target_period=period)
    assert out == pytest.approx(true_beats)
    duration = true_beats[-1] + period
    bars = build_bars(out, out_idx, FOUR, duration)
    lengths = np.array([bar.end - bar.start for bar in bars])
    assert lengths.max() / np.median(lengths) < 1.1


def test_normalise_octave_starts_on_modal_downbeat_parity():
    beats = [i * 0.25 for i in range(64)]  # doubled 0.5 s grid; true beats at odd indices
    downbeats = [0.25 + 2.0 * j for j in range(8)]
    idx = downbeat_indices(beats, downbeats)
    assert all(i % 2 == 1 for i in idx)
    out, out_idx = normalise_octave(beats, idx, target_period=0.5)
    assert out[0] == pytest.approx(0.25)
    assert np.diff(out) == pytest.approx([0.5] * (len(out) - 1))
    assert [out[i] for i in out_idx] == pytest.approx(downbeats)


def test_double_octave_inserts_midpoints():
    out, idx = double_beats([0.0, 1.0, 2.0], [0, 2])
    assert out == pytest.approx([0.0, 0.5, 1.0, 1.5, 2.0])
    assert idx == [0, 4]


def test_build_bars_handles_pickup_tail_and_end_downbeat():
    beats = [i * 0.5 for i in range(21)]  # last beat at 10.0 == duration
    downbeats = [0.5, 2.5, 4.5, 6.5, 8.5, 10.0]  # Beat This! may emit one at the very end
    idx = downbeat_indices(beats, downbeats)
    bars = build_bars(beats, idx, FOUR, duration=10.0)
    assert [bar.index for bar in bars] == list(range(6))
    assert bars[0].beats == [0]  # pickup
    assert (bars[0].start, bars[0].end) == (0.0, 0.5)
    assert bars[1].beats == [1, 2, 3, 4]
    assert bars[-1].beats == [17, 18, 19]
    assert bars[-1].end == 10.0
    assert all(bar.end > bar.start for bar in bars)
    assert all(a.end == b.start for a, b in zip(bars, bars[1:]))


def test_build_bars_phase_tie_break_by_chroma_change():
    beats = [i * 0.5 for i in range(64)]
    # downbeats tie between phase 0 and phase 2 (half a bar apart, as after halving)
    idx = sorted(list(range(0, 32, 4)) + list(range(34, 64, 4)))
    assert modal_phase(idx, 4)[0] == 0
    # the chord changes every four beats starting on beat 2
    c_major = np.zeros(12)
    c_major[[0, 4, 7]] = 1.0
    f_sharp = np.zeros(12)
    f_sharp[[6, 10, 1]] = 1.0
    chroma = np.stack(
        [c_major if ((i - 2) // 4) % 2 == 0 else f_sharp for i in range(64)], axis=1
    )
    without = build_bars(beats, idx, FOUR, duration=32.0)
    assert without[0].beats == [0, 1, 2, 3]
    with_chroma = build_bars(beats, idx, FOUR, duration=32.0, chroma_per_beat=chroma)
    assert with_chroma[0].beats == [0, 1]  # pickup
    assert with_chroma[1].beats == [2, 3, 4, 5]
