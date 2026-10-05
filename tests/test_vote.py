from youkelele.music.as_played import _topped_vote, jaccard
from youkelele.music.vote import (
    HYBRID_DELTA,
    PERIOD2_MARGIN,
    choose_pattern,
    choose_unit,
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
    assert period_margin([a, b] * 4) >= PERIOD2_MARGIN and choose_unit([a, b] * 4) == 2
    assert choose_unit([a, list("-------S")] * 4) == 1  # the sparse bar fails the strike floor
    r = choose_pattern([a, b] * 4)
    assert r.unit == 2 and r.vector == a + b


def test_single_bar_and_all_rest_sections_do_not_raise():
    assert choose_pattern([list("S-S-----")]).vector == _topped_vote([list("S-S-----")])
    r = choose_pattern([list("--------")] * 3)
    assert r.candidate == "majority" and r.vector == list("--------")
