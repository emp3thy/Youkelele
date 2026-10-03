from __future__ import annotations

from youkelele.music import phrase
from youkelele.music.phrase import (
    MIN_SECTION_BARS,
    PHRASE_MIN_CHANGES,
    PHRASE_MIN_SHARE,
    aligned_starts,
    bar_change_bars,
    change_bars,
)


def test_constants():
    assert (MIN_SECTION_BARS, PHRASE_MIN_CHANGES, PHRASE_MIN_SHARE) == (4, 4, 0.75)


def test_change_bars():
    assert change_bars(["D", "D", "A", "A", "D"]) == [2, 4]


def test_change_bars_counts_changes_into_and_out_of_silence():
    assert change_bars(["N", "D", "D", "N"]) == [1, 3]


def test_bar_change_bars_compares_first_chord_with_previous_last_chord():
    # bar 1 starts on A after bar 0 ended on A: no change; bar 2 starts on D after A: change
    assert bar_change_bars([("D", "A"), ("A", "A"), ("D", "D")]) == [2]


def test_section_starting_mid_phrase_shifts_by_one():
    changes = list(range(9, 24, 2))  # 9, 11, ..., 23: odd offsets from bar 8
    assert aligned_starts([(0, 8), (8, 24)], changes) == [(0, 9, 0), (9, 24, 1)]


def test_in_phase_section_not_shifted():
    changes = list(range(8, 24, 2))  # 8, 10, ..., 22: even offsets from bar 8
    assert aligned_starts([(0, 8), (8, 24)], changes) == [(0, 8, 0), (8, 24, 0)]


def test_too_few_odd_changes_not_shifted():
    assert aligned_starts([(0, 8), (8, 24)], [9, 11, 13]) == [(0, 8, 0), (8, 24, 0)]


def test_mixed_phase_below_share_not_shifted():
    changes = [9, 11, 13, 15, 16, 18]  # 4 odd of 6 = 0.67 < 0.75
    assert aligned_starts([(0, 8), (8, 24)], changes) == [(0, 8, 0), (8, 24, 0)]


def test_first_section_never_shifted():
    changes = [1, 3, 5, 7, 9, 11]  # odd offsets from bar 0
    assert aligned_starts([(0, 12), (12, 20)], changes) == [(0, 12, 0), (12, 20, 0)]


def test_four_bar_section_not_shifted_to_three():
    # every change sits at an odd offset from bar 8; the four-bar section keeps its four bars
    # (it can hold only two odd offsets, so the change count guard and the length guard agree)
    changes = list(range(9, 24, 2))
    result = aligned_starts([(0, 8), (8, 12), (12, 24)], changes)
    assert result == [(0, 8, 0), (8, 13, 0), (13, 24, 1)]
    assert all(end - start >= MIN_SECTION_BARS for start, end, _ in result)


def test_length_guard_stops_a_four_bar_section_shrinking(monkeypatch):
    # with a lower change threshold the two odd changes would shift (8, 12) to (9, 12)
    monkeypatch.setattr(phrase, "PHRASE_MIN_CHANGES", 2)
    assert aligned_starts([(0, 8), (8, 12)], [9, 11]) == [(0, 8, 0), (8, 12, 0)]
    assert aligned_starts([(0, 8), (8, 13)], [9, 11]) == [(0, 9, 0), (9, 13, 1)]


def test_shift_never_leaves_previous_section_under_four():
    # a legacy grid.json with a two-bar opening section: growing it to three is still under four
    changes = list(range(3, 18, 2))
    assert aligned_starts([(0, 2), (2, 18)], changes) == [(0, 2, 0), (2, 18, 0)]


def test_consecutive_shifts_keep_every_section_whole():
    changes = list(range(9, 40, 2))  # odd offsets from 8 and from 20
    result = aligned_starts([(0, 8), (8, 20), (20, 40)], changes)
    assert result == [(0, 9, 0), (9, 21, 1), (21, 40, 1)]
    assert all(end - start >= MIN_SECTION_BARS for start, end, _ in result)
    assert [r[0] for r in result[1:]] == [r[1] for r in result[:-1]]
