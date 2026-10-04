from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from youkelele.music.onsets import Onsets
from youkelele.music.recall import (
    FIT_TOLERANCE,
    HIGH_BAND_FMIN,
    MERGE_MS,
    MIN_GAIN,
    SILENT_BAR_SHARE,
    SPARSE_SHARE,
    SectionDecision,
    gate_section,
    merge_onsets,
    silent_bar_mask,
)
from youkelele.schemas import Bar, Meter

SR = 8000
BAR_SECONDS = 2.0
SLOTS = 8
m44 = Meter(numerator=4, denominator=4)
m34 = Meter(numerator=3, denominator=4)


def _bars(n: int) -> list[Bar]:
    return [
        Bar(index=i, start=i * BAR_SECONDS, end=(i + 1) * BAR_SECONDS, beats=list(range(4 * i, 4 * i + 4)))
        for i in range(n)
    ]


def _onsets(times, centroid: float = 2000.0) -> Onsets:
    times = np.asarray(sorted(times), dtype=float)
    return Onsets(times=times, centroid=np.full(len(times), centroid), zcr=np.full(len(times), 0.1))


def _times(per_bar: dict[int, Sequence[int]], slots: int = SLOTS) -> list[float]:
    width = BAR_SECONDS / slots
    return [b * BAR_SECONDS + k * width for b, ks in per_bar.items() for k in ks]


def _every_bar(slots: Sequence[int], n: int = 8) -> dict[int, Sequence[int]]:
    return {b: slots for b in range(n)}


def _signal(bar_amps: Sequence[float]) -> np.ndarray:
    n = int(BAR_SECONDS * SR)
    t = np.arange(n) / SR
    return np.concatenate([a * np.sin(2 * np.pi * 220.0 * t) for a in bar_amps])


def _gate(base, extra, y=None, n_bars: int = 8, slots: int = SLOTS, song_fit: float = 1.0, meter=m44):
    y = _signal([0.3] * n_bars) if y is None else y
    return gate_section(base, extra, y, SR, _bars(n_bars), slots, song_fit, meter)


def test_constants_are_the_measured_values():
    assert HIGH_BAND_FMIN == 3000.0
    assert SPARSE_SHARE == 0.4
    assert MERGE_MS == 60.0
    assert MIN_GAIN == 1.0
    assert FIT_TOLERANCE == 0.05
    assert SILENT_BAR_SHARE == 0.25



def test_merge_onsets_drops_extra_within_60ms_and_marks_added():
    base = _onsets([0.0, 1.0])
    extra = Onsets(
        times=np.array([0.05, 0.5, 1.07, 1.5]),
        centroid=np.array([10.0, 20.0, 30.0, 40.0]),
        zcr=np.array([0.01, 0.02, 0.03, 0.04]),
    )
    keep = np.array([True, True, True, False])
    union, added = merge_onsets(base, extra, 60.0, keep)
    assert union.times.tolist() == [0.0, 0.5, 1.0, 1.07]
    assert added.dtype == bool
    assert added.tolist() == [False, True, False, True]
    assert union.centroid.tolist() == [2000.0, 20.0, 2000.0, 30.0]
    assert union.zcr.tolist() == [0.1, 0.02, 0.1, 0.03]


def test_merge_onsets_with_no_base_adds_every_kept_extra():
    union, added = merge_onsets(_onsets([]), _onsets([0.3, 0.1]), 60.0, np.array([True, True]))
    assert union.times.tolist() == [0.1, 0.3]
    assert added.tolist() == [True, True]


def test_silent_bar_mask_marks_bars_far_below_median():
    # shares of the median bar (0.3): 1.0, 1.0, 0.033, 1.0, 0.33, 1.0
    y = _signal([0.3, 0.3, 0.01, 0.3, 0.1, 0.3])
    mask = silent_bar_mask(y, SR, _bars(6), 0.25)
    assert mask.dtype == bool
    assert mask.tolist() == [False, False, True, False, False, False]


def test_silent_bar_mask_on_silence_marks_nothing():
    assert silent_bar_mask(np.zeros(4 * int(BAR_SECONDS * SR)), SR, _bars(4), 0.25).tolist() == [False] * 4


def test_gate_accepts_sparse_section_with_regular_union():
    base = _onsets(_times(_every_bar((0, 4))))
    extra = _onsets(_times(_every_bar((0, 2, 4, 5, 6))), centroid=1500.0)
    onsets, added, decision = _gate(base, extra)
    assert isinstance(decision, SectionDecision)
    assert decision.accepted
    assert decision.reason == "accepted"
    assert decision.before == 2.0
    assert decision.after == 5.0
    assert len(onsets.times) == 40
    assert int(added.sum()) == 24  # slots 0 and 4 lie on base onsets and are not added twice
    assert np.all(np.diff(onsets.times) > 0)
    assert np.all(onsets.centroid[added] == 1500.0)
    assert np.all(onsets.centroid[~added] == 2000.0)


def test_gate_skips_sixteenth_grid():
    base = _onsets(_times(_every_bar((0, 8)), slots=16))
    extra = _onsets(_times(_every_bar((0, 2, 4, 8, 10, 12)), slots=16))
    onsets, added, decision = _gate(base, extra, slots=16)
    assert not decision.accepted
    assert decision.reason == "sixteenth grid"
    assert onsets.times.tolist() == base.times.tolist()
    assert not added.any()


def test_gate_rejects_when_jaccard_falls():
    base = _onsets(_times(_every_bar((0, 4))))
    # two off-beat extras per bar on a different pair of slots each bar: more strikes, no pattern
    pairs = [(1, 5), (2, 6), (3, 7), (1, 6), (2, 7), (3, 5), (1, 7), (2, 5)]
    extra = _onsets(_times(dict(enumerate(pairs))))
    onsets, added, decision = _gate(base, extra)
    assert not decision.accepted
    assert decision.reason == "jaccard"
    assert decision.before == 2.0
    assert decision.after == 4.0
    assert onsets.times.tolist() == base.times.tolist()
    assert not added.any()


def test_gate_skips_dense_section():
    # 4 strikes per bar is at SPARSE_SHARE x 8 = 3.2 or above
    base = _onsets(_times(_every_bar((0, 2, 4, 6))))
    extra = _onsets(_times(_every_bar((1, 3, 5, 7))))
    onsets, added, decision = _gate(base, extra)
    assert not decision.accepted
    assert decision.reason == "dense"
    assert decision.before == decision.after == 4.0
    assert onsets.times.tolist() == base.times.tolist()
    assert not added.any()


def test_gate_sparse_boundary_in_3_4_is_exact():
    # 3/4 has 6 slots and 0.4 x 6 is 2.4000000000000004 in floating point; 12 strikes over 5 bars
    # is 2.4 per bar, on the boundary, so the section is dense
    bars = [
        Bar(index=i, start=i * BAR_SECONDS, end=(i + 1) * BAR_SECONDS, beats=list(range(3 * i, 3 * i + 3)))
        for i in range(5)
    ]
    y = _signal([0.3] * 5)
    on_boundary = {0: (0, 2, 4), 1: (0, 2, 4), 2: (0, 2), 3: (0, 2), 4: (0, 2)}
    extra = _onsets(_times(_every_bar((1, 3, 5), 5), slots=6))
    base = _onsets(_times(on_boundary, slots=6))
    _, _, decision = gate_section(base, extra, y, SR, bars, 6, 1.0, m34)
    assert decision.before == 2.4
    assert decision.reason == "dense"
    # one strike fewer is sparse, so the gate goes on to try the union
    under = {**on_boundary, 1: (0, 2)}
    _, _, decision = gate_section(_onsets(_times(under, slots=6)), extra, y, SR, bars, 6, 1.0, m34)
    assert decision.reason != "dense"


def test_gate_skips_section_without_onsets():
    # an intro before the guitar enters: no onsets today, a silent stem, and stray high-band peaks
    extra = _onsets(_times(_every_bar((0, 2, 4))))
    onsets, added, decision = _gate(_onsets([]), extra, y=np.zeros(8 * int(BAR_SECONDS * SR)))
    assert not decision.accepted
    assert decision.reason == "no onsets"
    assert decision.before == decision.after == 0.0
    assert len(onsets.times) == 0
    assert len(added) == 0


def test_gate_adds_nothing_in_silent_bars():
    # the guitar enters at bar 2; bars 0 and 1 are at 0.003 of the median bar RMS
    y = _signal([0.001, 0.001] + [0.3] * 6)
    base = _onsets(_times({b: (0, 4) for b in range(2, 8)}))
    extra = _onsets(_times(_every_bar((0, 2, 4, 5, 6))))
    onsets, added, decision = _gate(base, extra, y=y)
    assert decision.accepted
    assert decision.reason == "accepted"
    assert int(added.sum()) == 18
    assert np.all(onsets.times[added] >= 2 * BAR_SECONDS)
    assert not np.any(onsets.times < 2 * BAR_SECONDS)


def test_gate_selects_only_onsets_inside_the_section_bars():
    # the section is bars 0-3 of the song; onsets of later bars are not the section's
    base = _onsets(_times(_every_bar((0, 4))))
    extra = _onsets(_times(_every_bar((0, 2, 4, 5, 6))))
    onsets, added, decision = _gate(base, extra, n_bars=4)
    assert decision.accepted
    assert len(onsets.times) == 20
    assert onsets.times.max() < 4 * BAR_SECONDS


def test_gate_rejects_when_raw_onsets_exceed_slots():
    # extras 70 ms after a base onset survive the merge but quantise into the base onset's slot
    base = _onsets(_times(_every_bar((0, 2, 4))))
    near = [t + 0.07 for t in _times(_every_bar((0, 2, 4)))]
    far = _times(_every_bar((1, 3, 5, 6, 7)))
    extra = _onsets(near + far)
    _, added, decision = _gate(base, extra)
    assert decision.reason == "raw"
    assert not decision.accepted
    assert not added.any()


def test_gate_rejects_when_section_fit_falls_below_the_song_fit():
    base = _onsets(_times(_every_bar((0, 4))))
    # extras a quarter slot late: they quantise to their slots but miss the 15 percent fit window
    late = _onsets([t + 0.25 * BAR_SECONDS / SLOTS for t in _times(_every_bar((2, 5, 6)))])
    _, added, decision = _gate(base, late, song_fit=1.0)
    assert decision.reason == "fit"
    assert not decision.accepted
    assert not added.any()


def test_gate_rejects_small_gain():
    base = _onsets(_times(_every_bar((0, 4))))
    extra = _onsets(_times({b: (2,) for b in range(0, 8, 2)}))  # half a strike per bar
    _, added, decision = _gate(base, extra)
    assert decision.reason == "gain"
    assert decision.after == 2.5
    assert not added.any()
