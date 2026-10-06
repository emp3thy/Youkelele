from __future__ import annotations

from youkelele.render.lines import fold_repeats, line_width, pack_lines, repeat_text
from youkelele.schemas import Meter, ScoreBar, ScoreChord, ScoreSection, Stroke, TabNote

M44 = Meter(numerator=4, denominator=4)
ISLAND = list("D-DU-UDU")


def _chord(name: str, start: int = 0, end: int = 8) -> ScoreChord:
    return ScoreChord(
        name=name, diagram=-1 if name == "N.C." else 0, start_slot=start, slots=ISLAND[start:end],
    )


def _bar(
    index: int, *names: str, pickup: bool = False, grey: bool = False,
    strokes: list[Stroke] | None = None, tab: list[TabNote] | None = None,
) -> ScoreBar:
    chords = [_chord(n) for n in names]
    return ScoreBar(
        index=index, chords=chords, pickup=pickup, grey=grey, strokes=strokes or [], tab=tab,
    )


def _section(bars: list[ScoreBar]) -> ScoreSection:
    return ScoreSection(
        label="Verse", pattern=ISLAND, uncertain=False, bars=bars, bar_repeat=1.0,
        no_instrument=False,
    )


def _cycle(
    names: str, count: int, start: int = 0, grey: bool = False, rings: bool | None = None,
) -> list[ScoreBar]:
    seq = names.split()
    strokes = None if rings is None else [Stroke(slot=0, kind="D", rings=rings)]
    return [
        _bar(start + i, seq[i % len(seq)], grey=grey, strokes=strokes) for i in range(count)
    ]


def test_eighth_grid_line_of_single_chord_bars_holds_eight():
    section = _section(_cycle("G", 16))  # one chord per bar
    lines = pack_lines(section, 8, M44)
    assert [len(l.bars) for l in lines] == [8, 8]


def test_a_split_bar_in_the_window_drops_the_line_to_four():
    bars = _cycle("G", 5) + [_bar(5, "D", "G")] + _cycle("G", 10, start=6)
    assert [len(l.bars) for l in pack_lines(_section(bars), 8, M44)] == [4, 4, 8]


def test_sixteenth_grid_and_pickup_lines_hold_four():
    assert all(len(l.bars) == 4 for l in pack_lines(_section(_cycle("C", 8)), 16, M44))
    bars = [_bar(0, "C", pickup=True)] + _cycle("C", 7, start=1)
    lines = pack_lines(_section(bars), 8, M44)
    assert len(lines[0].bars) == 4 and lines[0].bars[0].pickup


def test_identical_lines_fold_with_a_count_in_words():
    lines = fold_repeats(pack_lines(_section(_cycle("G", 24)), 8, M44))
    assert len(lines) == 1 and lines[0].repeat == 3 and repeat_text(3) == "play three times"
    assert repeat_text(2) == "play twice" and repeat_text(4) == "play 4 times"


def test_lines_that_differ_only_in_a_ring_flag_or_grey_do_not_fold():
    a = pack_lines(_section(_cycle("G", 8)), 8, M44)
    b = pack_lines(_section(_cycle("G", 8, grey=True)), 8, M44)
    assert len(fold_repeats(a + b)) == 2
    c = pack_lines(_section(_cycle("G", 8, rings=True)), 8, M44)
    d = pack_lines(_section(_cycle("G", 8, rings=False)), 8, M44)
    assert len(fold_repeats(c + d)) == 2
    assert len(fold_repeats(c + c)) == 1


def test_lines_of_different_widths_never_fold():
    wide = pack_lines(_section(_cycle("G", 8)), 8, M44)
    narrow = pack_lines(_section(_cycle("G", 8)), 16, M44)
    assert [len(l.bars) for l in narrow] == [4, 4]
    folded = fold_repeats(wide + narrow)
    assert [(len(l.bars), l.repeat) for l in folded] == [(8, 1), (4, 2)]


def test_a_labelled_bar_in_the_window_drops_the_line_to_four():
    # an eight-bar box is 80 px wide: "riff heard" alone fills it and pushed the chord name out
    # of the box (Wet Leg bar 58 in the 1.7 validation); four wide boxes hold both
    bars = _cycle("C", 16)
    bars[5] = bars[5].model_copy(update={"label": "riff heard"})
    assert line_width(bars, 0, 8, M44) == 4
    assert [len(l.bars) for l in pack_lines(_section(bars), 8, M44)] == [4, 4, 8]


def test_a_labelled_line_never_folds_into_an_unlabelled_one():
    plain = pack_lines(_section(_cycle("C", 4)), 16, M44)
    labelled = pack_lines(_section(_cycle("C", 4)), 16, M44)
    labelled[0].bars[0] = labelled[0].bars[0].model_copy(update={"label": "riff heard"})
    folded = fold_repeats(plain + labelled)
    assert [l.repeat for l in folded] == [1, 1] and folded[1].bars[0].label == "riff heard"


def test_line_width_and_a_short_tail():
    bars = _cycle("G", 11)
    assert line_width(bars, 0, 8, M44) == 8
    assert [len(l.bars) for l in pack_lines(_section(bars), 8, M44)] == [8, 3]
    assert all(l.repeat == 1 for l in pack_lines(_section(bars), 8, M44))
