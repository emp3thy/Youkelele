from __future__ import annotations

import random

from youkelele.music.as_played import (
    DENSITY_FLOOR,
    EXPLAINED_BELOW,
    MIN_SECTION_BARS,
    STAGE_UNCERTAIN_GRID_FIT,
    STRIKE_SHARE,
    UNCERTAIN_BELOW,
    UNCERTAIN_BELOW_SIXTEENTH,
    bar_repeat,
    eighth_grid,
    explained_onsets,
    fill_to_floor,
    jaccard,
    majority_vector,
    section_summary,
)
from youkelele.schemas import Meter

m44 = Meter(numerator=4, denominator=4)
m34 = Meter(numerator=3, denominator=4)


def _random_bars(n: int, slots: int, seed: int = 7) -> list[list[str]]:
    rng = random.Random(seed)
    return [[rng.choice("S-") for _ in range(slots)] for _ in range(n)]


def test_constants():
    assert UNCERTAIN_BELOW == 0.45
    assert UNCERTAIN_BELOW_SIXTEENTH == 0.55
    assert MIN_SECTION_BARS == 4
    assert STAGE_UNCERTAIN_GRID_FIT == 0.6
    assert STRIKE_SHARE == 1 / 3
    assert DENSITY_FLOOR == 0.6
    assert EXPLAINED_BELOW == 0.6


def test_eighth_grid_is_two_slots_per_beat():
    assert eighth_grid(8, m44)
    assert not eighth_grid(16, m44)
    assert eighth_grid(6, m34)
    assert not eighth_grid(12, m34)


def test_jaccard_over_strike_positions_with_half_credit_for_mute():
    assert jaccard(list("S-SS"), list("S-SS")) == 1.0
    assert jaccard(list("S---"), list("-S--")) == 0.0
    assert jaccard(list("S-S-"), list("x-S-")) == 0.75
    assert jaccard(list("x---"), list("x---")) == 1.0
    assert jaccard(list("----"), list("----")) == 1.0
    assert abs(jaccard(list("SS--"), list("S-S-")) - 1 / 3) < 1e-9


def test_majority_vector_ignores_one_noisy_bar():
    bars = [list("S-SS-SSS")] * 7 + [list("-S--S---")]
    assert "".join(majority_vector(bars)) == "S-SS-SSS"
    slots, confidence, _, explained = section_summary(bars, 8, m44)
    assert "".join(slots) == "D-DU-UDU"
    assert abs(explained - 42 / 44) < 1e-9
    assert confidence > 0.8


def test_majority_vector_marks_slot_muted_when_most_strikes_muted():
    bars = [list("x-S-")] * 3 + [list("S-S-")] * 2
    assert "".join(majority_vector(bars)) == "x-S-"
    bars = [list("x-S-")] * 2 + [list("S-S-")] * 3
    assert "".join(majority_vector(bars)) == "S-S-"


def test_majority_vector_needs_more_than_a_third_of_the_bars():
    bars = [list("SS")] + [list("S-")] * 3
    assert "".join(majority_vector(bars)) == "S-"
    bars = [list("SS")] * 2 + [list("--")] * 4
    assert "".join(majority_vector(bars)) == "--"  # exactly a third is not enough
    bars = [list("SS")] * 3 + [list("--")] * 6
    assert "".join(majority_vector(bars)) == "--"
    bars = [list("SS")] * 4 + [list("--")] * 6
    assert "".join(majority_vector(bars)) == "SS"


def test_majority_vector_third_share_keeps_slots_struck_in_41_percent_of_bars():
    bars = [list("S-")] * 5 + [list("--")] * 7  # 5 of 12 bars is 41.7 percent
    assert "".join(majority_vector(bars)) == "S-"
    bars = [list("S-")] * 4 + [list("--")] * 8  # 4 of 12 is a third exactly
    assert "".join(majority_vector(bars)) == "--"


def test_majority_vector_threshold_is_a_parameter():
    bars = [list("S-")] * 2 + [list("--")] * 2
    assert "".join(majority_vector(bars, 0.5)) == "--"
    assert "".join(majority_vector(bars, 0.4)) == "S-"


def test_fill_to_floor_adds_highest_rate_slots():
    assert "".join(fill_to_floor(list("S---"), [1, 0.3, 0.2, 0.1], 2)) == "SS--"
    assert "".join(fill_to_floor(list("S---"), [1, 0.1, 0.3, 0.2], 3)) == "S-SS"


def test_fill_to_floor_leaves_a_vector_that_meets_the_floor():
    assert "".join(fill_to_floor(list("S-S-"), [1, 0.3, 0.9, 0.1], 2)) == "S-S-"
    assert "".join(fill_to_floor(list("SSS-"), [1, 1, 1, 0.1], 2)) == "SSS-"
    assert "".join(fill_to_floor(list("x---"), [1, 0.3, 0.2, 0.1], 0)) == "x---"


def test_fill_to_floor_stops_when_every_slot_is_struck():
    assert "".join(fill_to_floor(list("S-"), [1, 0.1], 5)) == "SS"


def test_section_summary_returns_explained():
    bars = [list("S-S-")] * 3 + [list("S--S")]
    slots, confidence, repeat, explained = section_summary(bars, 4, m44)
    assert "".join(slots) == "D-D-"
    assert abs(explained - 7 / 8) < 1e-9
    assert 0.0 <= confidence <= 1.0
    assert 0.0 <= repeat <= 1.0


def test_section_summary_density_floor_restores_slots_below_the_third_share():
    # 12 bars of 16 slots, each striking 4 slots in a rotation: every slot is struck in a quarter
    # of the bars, so the vote keeps nothing, but the median bar strikes 4 and the floor is 2
    bars = [["S" if (j - 4 * i) % 16 < 4 else "-" for j in range(16)] for i in range(12)]
    assert "".join(majority_vector(bars)) == "-" * 16
    slots, _, _, explained = section_summary(bars, 16, m44)
    assert [j for j, c in enumerate(slots) if c != "-"] == [0, 1]
    assert round(DENSITY_FLOOR * 4) == 2
    assert abs(explained - 6 / 48) < 1e-9


def test_dense_section_never_gets_sparser():
    slots, confidence, _, explained = section_summary([list("SSSSSSSS")] * 6, 8, m44)
    assert "".join(slots) == "DUDUDUDU"
    assert all(c != "-" for c in slots)
    assert explained == 1.0
    assert confidence == 1.0


def test_section_summary_without_bars_is_all_rests_and_zero():
    assert section_summary([], 8, m44) == (["-"] * 8, 0.0, 0.0, 0.0)


def test_bar_repeat_one_for_identical_bars_low_for_random():
    assert bar_repeat([list("S-SS-SSS")] * 6) == 1.0
    assert bar_repeat(_random_bars(16, 16)) < 0.5


def test_random_sixteenth_bars_pass_explained_and_the_eighth_floor_but_not_the_sixteenth_floor():
    # noise striking half the slots: the third-share vote keeps most slots, so explained is high
    # and the mean Jaccard clears 0.45; only the sixteenth-grid floor and bar_repeat show it
    _, confidence, repeat, explained = section_summary(_random_bars(16, 16, seed=3), 16, m44)
    assert explained >= EXPLAINED_BELOW
    assert UNCERTAIN_BELOW <= confidence < UNCERTAIN_BELOW_SIXTEENTH
    assert repeat < 0.4


def test_repeated_vector_absent_from_any_textbook_pattern_is_returned_as_is():
    vector = "-SSSS-S--SSSS-S-"
    slots, confidence, repeat, explained = section_summary([list(vector)] * 10, 16, m44)
    assert "".join("-" if s == "-" else "S" for s in slots) == vector
    assert "".join(slots) == "-UDUD-D--UDUD-D-"
    assert confidence == 1.0
    assert repeat == 1.0
    assert explained == 1.0


def test_explained_onsets_share_of_strikes_on_pattern_slots():
    bars = [["S", "-", "S", "-"], ["S", "-", "-", "S"]]
    assert explained_onsets(bars, ["S", "-", "S", "-"]) == 0.75  # 3 of 4 strikes on struck slots


def test_explained_onsets_zero_without_strikes():
    assert explained_onsets([["-", "-"], ["-", "-"]], ["S", "S"]) == 0.0
    assert explained_onsets([], ["S", "S"]) == 0.0


def test_explained_onsets_counts_mutes_as_strikes():
    assert explained_onsets([["x", "-", "S", "-"]], ["S", "-", "-", "-"]) == 0.5
