import pytest

from youkelele.music.candidates import candidate_set, top2


def test_candidate_set_has_six_names_with_two_bar_and_four_without():
    bars = [list("S-S-S-S-"), list("SSSSSSSS")] * 3
    assert [c.name for c in candidate_set(bars, True, 0)] == ["majority_1", "medoid_1", "majority_2", "medoid_2", "bar_best", "bar_second"]
    assert [c.name for c in candidate_set(bars, False, 0)] == ["majority_1", "medoid_1", "bar_best", "bar_second"]


def test_top2_margin_is_printed_minus_best_different():
    bars = [list("S-S-S-S-")] * 5 + [list("S-S-S-SS")]
    cands = candidate_set(bars, False, 0)
    margin, runner = top2(list("S-S-S-S-"), cands)
    assert runner == list("S-S-S-SS") and margin == pytest.approx(cands[0].score - [c for c in cands if c.vector == runner][0].score)


def test_top2_is_none_when_every_candidate_agrees_or_there_are_no_bars():
    assert top2(list("S-S-S-S-"), candidate_set([list("S-S-S-S-")] * 4, False, 0)) == (None, None)
    assert candidate_set([], False, 0) == [] and top2(list("S-S-S-S-"), []) == (None, None)
