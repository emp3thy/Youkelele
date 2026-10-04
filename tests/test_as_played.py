from __future__ import annotations

import random

from youkelele.music.as_played import (
    MIN_SECTION_BARS,
    STAGE_UNCERTAIN_GRID_FIT,
    UNCERTAIN_BELOW,
    bar_repeat,
    explained_onsets,
    jaccard,
    majority_vector,
    section_summary,
)
from youkelele.schemas import Meter

m44 = Meter(numerator=4, denominator=4)


def _random_bars(n: int, slots: int, seed: int = 7) -> list[list[str]]:
    rng = random.Random(seed)
    return [[rng.choice("S-") for _ in range(slots)] for _ in range(n)]


def test_constants():
    assert UNCERTAIN_BELOW == 0.45
    assert MIN_SECTION_BARS == 4
    assert STAGE_UNCERTAIN_GRID_FIT == 0.6


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
    slots, confidence, _ = section_summary(bars, 8, m44)
    assert "".join(slots) == "D-DU-UDU"
    assert confidence > 0.8


def test_majority_vector_marks_slot_muted_when_most_strikes_muted():
    bars = [list("x-S-")] * 3 + [list("S-S-")] * 2
    assert "".join(majority_vector(bars)) == "x-S-"
    bars = [list("x-S-")] * 2 + [list("S-S-")] * 3
    assert "".join(majority_vector(bars)) == "S-S-"


def test_majority_vector_needs_more_than_half_the_bars():
    bars = [list("SS")] * 2 + [list("S-")] * 2
    assert "".join(majority_vector(bars)) == "S-"


def test_bar_repeat_one_for_identical_bars_low_for_random():
    assert bar_repeat([list("S-SS-SSS")] * 6) == 1.0
    assert bar_repeat(_random_bars(16, 16)) < 0.5


def test_section_summary_confidence_below_floor_on_random_bars():
    _, confidence, repeat = section_summary(_random_bars(16, 16, seed=3), 16, m44)
    assert confidence < UNCERTAIN_BELOW
    assert repeat < UNCERTAIN_BELOW


def test_repeated_vector_absent_from_any_textbook_pattern_is_returned_as_is():
    vector = "-SSSS-S--SSSS-S-"
    slots, confidence, repeat = section_summary([list(vector)] * 10, 16, m44)
    assert "".join("-" if s == "-" else "S" for s in slots) == vector
    assert "".join(slots) == "-UDUD-D--UDUD-D-"
    assert confidence == 1.0
    assert repeat == 1.0


def test_explained_onsets_share_of_strikes_on_pattern_slots():
    bars = [["S", "-", "S", "-"], ["S", "-", "-", "S"]]
    assert explained_onsets(bars, ["S", "-", "S", "-"]) == 0.75  # 3 of 4 strikes on struck slots


def test_explained_onsets_zero_without_strikes():
    assert explained_onsets([["-", "-"], ["-", "-"]], ["S", "S"]) == 0.0
    assert explained_onsets([], ["S", "S"]) == 0.0


def test_explained_onsets_counts_mutes_as_strikes():
    assert explained_onsets([["x", "-", "S", "-"]], ["S", "-", "-", "-"]) == 0.5
