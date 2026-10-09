from youkelele.music.as_played import _topped_vote, jaccard
from youkelele.music.vote import (
    HYBRID_DELTA,
    PERIOD2_MARGIN,
    choose_pattern,
    unit_and_phase,
    medoid,
    period_margin,
)


def test_medoid_is_a_real_bar_with_best_mean_agreement():
    bars = [list("S-S-S-SS"), list("S-S-S-SS"), list("S-SS-S-S")]
    vector, score = medoid(bars)
    assert vector == list("S-S-S-SS") and abs(score - (1.0 + jaccard(bars[0], bars[2])) / 2) < 1e-9


def test_majority_erases_pushes_that_move_and_medoid_keeps_them():
    # three bars each with one push on a different off-beat: the vote keeps only the beats
    bars = [list("S-S-SSS-"), list("S-SSS-S-"), list("SSS-S-S-")]
    assert _topped_vote(bars) == list("S-S-S-S-")
    assert "S" in medoid(bars)[0][1::2]  # the medoid is one of the bars, pushes included


def test_choose_pattern_picks_majority_below_delta_and_medoid_at_or_above():
    bars_tie = [list("S-S-S-S-")] * 4
    r = choose_pattern(bars_tie)
    assert r.candidate == "majority" and r.vector == list("S-S-S-S-") and r.unit == 1
    # a shared core with one extra push per bar in scattered places: the leave-one-out vote
    # keeps changing (0.635 mean agreement) while the medoid is a real bar (0.733)
    core = list("S-S-S-S-")
    bars = []
    for extra in (1, 3, 5, 7, 1, 3):
        bar = list(core)
        bar[extra] = "S"
        bars.append(bar)
    r = choose_pattern(bars)
    assert r.score_medoid - r.score_majority >= HYBRID_DELTA and r.candidate == "medoid"
    assert r.vector == list("SSS-S-S-")  # the earliest of the tied best bars


def test_choose_pattern_never_switches_to_a_medoid_under_the_stroke_floor():
    bars = [list("--------")] * 3 + [list("x-------")] * 3 + [list("S-------")]
    r = choose_pattern(bars)
    assert r.candidate == "majority"  # the all-rest and all-mute medoids have fewer than 2 S cells


def test_period_margin_and_unit_two_on_alternating_bars():
    a, b = list("S--S--S-"), list("SSS-SSS-")
    assert period_margin([a, b] * 4) >= PERIOD2_MARGIN and unit_and_phase([a, b] * 4)[0] == 2
    assert unit_and_phase([a, list("-------S")] * 4)[0] == 1  # the sparse bar fails the strike floor
    r = choose_pattern([a, b] * 4)
    assert r.unit == 2 and r.vector == a + b


def test_unit_stays_one_when_lag_agreement_fires_but_the_two_bar_medoid_gains_little():
    # sixteen-slot bars, the second of each pair adding one push: lag-2 beats lag-1 by 0.11,
    # but one real bar already represents the section nearly as well as the best pair
    a = list("S-S-S-S-S-S-S-S-")
    b = list("S-S-S-S-S-S-SSS-")
    bars = [a, b] * 4
    lag1 = sum(jaccard(x, y) for x, y in zip(bars, bars[1:])) / (len(bars) - 1)
    lag2 = sum(jaccard(x, y) for x, y in zip(bars, bars[2:])) / (len(bars) - 2)
    assert lag2 - lag1 >= PERIOD2_MARGIN  # the statistic spec 4.2 first named would fire
    assert period_margin(bars) < PERIOD2_MARGIN and unit_and_phase(bars)[0] == 1


def test_period_margin_is_the_two_bar_medoid_over_the_one_bar_medoid():
    a, b = list("S--S--S-"), list("SSS-SSS-")
    bars = [a, b] * 4
    one_bar = (3 + 4 * jaccard(a, b)) / 7  # each bar agrees with 3 copies of itself and 4 of the other
    assert abs(period_margin(bars) - (1.0 - one_bar)) < 1e-9
    assert period_margin(bars[:3]) == 0.0  # fewer than four bars


def test_unit_two_pairs_from_the_best_pairs_phase_and_prints_aligned_to_the_first_bar():
    # a stray opening bar, then a figure alternating from bar 1: the vote pairs (1, 2), (3, 4), ...
    a, b = list("S--S--S-"), list("SSS-SSS-")
    stray = list("S-------")
    bars = [stray] + [a, b] * 4
    assert unit_and_phase(bars) == (2, 1)
    r = choose_pattern(bars)
    assert r.unit == 2
    # bar 0 (and every even bar) plays the second bar of the figure, odd bars the first
    assert r.vector == b + a


def test_single_bar_and_all_rest_sections_do_not_raise():
    # one bar: the support floor leaves the majority empty, so the medoid (the bar itself) wins
    assert choose_pattern([list("S-S-----")]).vector == list("S-S-----")
    r = choose_pattern([list("--------")] * 3)
    assert r.candidate == "majority" and r.vector == list("--------")


def test_two_pairs_are_not_a_two_bar_vote():  # four alternating bars, margin clears, pairs 2
    bars = [list("S-S-S-S-"), list("SSSSSSSS")] * 2
    assert unit_and_phase(bars) == (1, 0)


def test_three_pairs_are_a_two_bar_vote():
    bars = [list("S-S-S-S-"), list("SSSSSSSS")] * 3
    assert unit_and_phase(bars) == (2, 0)


def test_vote_result_records_voted_and_dropped_positions():
    bars = [list("S-S-S-S-"), list("SSSSSSSS")] * 3 + [list("S-S-S-S-")]
    r = choose_pattern(bars)
    assert r.unit == 2 and r.voted == [0, 1, 2, 3, 4, 5] and r.dropped == [6]
    r1 = choose_pattern(bars[:5])
    assert r1.unit == 1 and r1.voted == [0, 1, 2, 3, 4] and r1.dropped == []
