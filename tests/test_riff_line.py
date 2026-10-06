import random

from youkelele.music.riff_line import (
    RIFF_AGREE_MIN,
    RIFF_SUPPORT_MIN,
    choose_riff,
    gate,
    note_jaccard,
)

NYT = [60, 60, 62, None, None, None, 62, None, 60, None, 62, 63, None, 62, None, 60]  # the verified riff, 16 slots


def test_choose_riff_on_steady_bars_passes_the_gate():
    bars = [NYT] * 6 + [NYT[:10] + [None] * 6]
    c = choose_riff(bars)
    assert c.unit == 1 and c.notes == NYT and c.agreement >= RIFF_AGREE_MIN and c.support >= RIFF_SUPPORT_MIN
    assert gate(c, named_share=0.91, riff_flag=True) == (True, None)


def test_two_bar_riff_from_an_odd_bar_is_aligned_to_the_first_bar():
    a = [60, None, 62, None, 64, None, 62, None]
    b = [67, 67, None, 65, None, 64, None, 62]
    stray = [60, None, None, None, None, None, None, None]
    c = choose_riff([stray] + [a, b] * 4)
    assert c.unit == 2 and c.notes == b + a  # bar 0 and the even bars play the figure's second bar


def test_unsteady_bars_fail_on_agreement_with_a_reason():
    rng = random.Random(3)
    bars = [[rng.choice([None, 55, 57, 60, 62, 64]) for _ in range(16)] for _ in range(8)]
    c = choose_riff(bars)
    ok, reason = gate(c, named_share=0.8, riff_flag=True)
    assert not ok and reason.startswith("agreement")


def test_gate_rejects_a_strum_even_when_steady():
    bars = [[43] + [None] * 7] * 8
    assert gate(choose_riff(bars), named_share=0.95, riff_flag=False) == (False, "not a riff")


def test_note_jaccard_is_exact_on_pitch():
    assert note_jaccard([None, None], [None, None]) == 1.0
    assert note_jaccard([60, 62], [60, 63]) == 1 / 2
    assert note_jaccard([60, None], [None, 60]) == 0.0


def test_gate_reasons_in_order_and_format():
    c = choose_riff([NYT] * 4)
    assert gate(c, 0.5, True) == (False, "named 0.50 < 0.60")
    c2 = choose_riff([[60, None], [62, None], [64, None], [65, None]])
    assert gate(c2, 0.9, True)[1].startswith("agreement ")
