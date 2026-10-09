from youkelele.music.rhythm_distance import swap_distance


def test_swap_distance_counts_a_one_slot_push_as_one():
    assert swap_distance(list("S-S-S-S-"), list("S-S-S--S")) == 1


def test_swap_distance_with_unequal_counts_is_the_slot_count():
    assert swap_distance(list("S-S-S-S-"), list("S-S-S---")) == 8


def test_swap_distance_treats_mutes_as_strikes_and_is_symmetric():
    assert swap_distance(list("x-S-"), list("S-x-")) == 0 and swap_distance(list("S---"), list("---S")) == swap_distance(list("---S"), list("S---"))
