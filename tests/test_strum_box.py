from __future__ import annotations

import re

from youkelele.render.strum_box import example_bars, slot_px, worked_example_svg
from youkelele.schemas import Meter, ScoreBar, ScoreChord, ScoreSection

FOUR_FOUR = Meter(numerator=4, denominator=4)
ISLAND = list("D-DU-UDU")
TEXT_WIDTH_PX = 688  # 182 mm at 96 px per inch


def _labels(svg: str) -> list[str]:
    return re.findall(r'class="beat-label[^"]*">([^<]*)</text>', svg)


def test_island_strip_bar_has_three_down_three_up_arrows():
    svg = worked_example_svg(ISLAND, [_bar(0, ("C", 0))], FOUR_FOUR, 28)
    assert svg.startswith("<svg") and svg.endswith("</svg>")
    assert svg.count('class="arrow down"') == 3
    assert svg.count('class="arrow up"') == 3
    assert 'class="arrow muted"' not in svg
    assert 'width="224"' in svg
    assert _labels(svg) == ["1", "&", "2", "&", "3", "&", "4", "&"]


def test_3_4_strip_bar_has_six_columns_and_beat_labels_1_2_3():
    svg = worked_example_svg(list("D-DUxU"), [_bar(0, ("C", 0))], Meter(numerator=3, denominator=4), 28)
    assert svg.count('class="slot"') == 6
    assert 'width="168"' in svg
    assert _labels(svg) == ["1", "&", "2", "&", "3", "&"]
    assert svg.count('class="arrow muted"') == 1


def test_sixteen_slots_label_1_e_and_a():
    svg = worked_example_svg(list("D-DU-UDU" * 2), [_bar(0, ("C", 0))], FOUR_FOUR, 20)
    assert _labels(svg)[:8] == ["1", "e", "&", "a", "2", "e", "&", "a"]
    assert svg.count('class="slot"') == 16


def test_strip_labels_every_bar_of_two():
    svg = worked_example_svg(ISLAND, [_bar(0, ("C", 0)), _bar(1, ("G", 0))], FOUR_FOUR, 28)
    assert _labels(svg) == ["1", "&", "2", "&", "3", "&", "4", "&"] * 2


def _bar(index: int, *chords: tuple[str, int]) -> ScoreBar:
    return ScoreBar(
        index=index,
        chords=[ScoreChord(name=n, diagram=0, start_slot=start, slots=[]) for n, start in chords],
    )


def _section(bars: list[ScoreBar], pattern: list[str] = ISLAND) -> ScoreSection:
    return ScoreSection(
        label="Verse", pattern=pattern, uncertain=False, bars=bars, bar_repeat=1.0, no_instrument=False
    )


def _chords(svg: str) -> list[tuple[float, str]]:
    found = re.findall(r'<text x="([\d.]+)"[^>]*class="chord">([^<]*)</text>', svg)
    return [(float(x), name) for x, name in found]


def test_example_bars_prefers_a_bar_with_a_mid_bar_change():
    bars = [_bar(0, ("C", 0)), _bar(1, ("C", 0)), _bar(2, ("G", 0)), _bar(3, ("D", 0), ("A", 4))]
    assert [b.index for b in example_bars(_section(bars))] == [0, 3]
    # a change in the first two bars keeps them
    early = [_bar(0, ("C", 0)), _bar(1, ("C", 0), ("G", 6)), _bar(2, ("D", 0), ("A", 4))]
    assert [b.index for b in example_bars(_section(early))] == [0, 1]
    assert [b.index for b in example_bars(_section([_bar(5, ("C", 0))]))] == [5]


def test_example_bars_skips_a_leading_pickup():
    pickup = _bar(0, ("N.C.", 0), ("D", 6)).model_copy(update={"pickup": True})
    bars = [pickup, _bar(1, ("D", 0)), _bar(2, ("A", 0)), _bar(3, ("G", 0))]
    assert [b.index for b in example_bars(_section(bars))] == [1, 2]
    # the substitution rule still applies to the full bars
    changing = [pickup, _bar(1, ("D", 0)), _bar(2, ("A", 0)), _bar(3, ("G", 0), ("D", 4))]
    assert [b.index for b in example_bars(_section(changing))] == [1, 3]
    assert [b.index for b in example_bars(_section([pickup, _bar(1, ("D", 0))]))] == [1]
    # a section that is only a pickup still shows it
    assert [b.index for b in example_bars(_section([pickup]))] == [0]


def test_example_bars_first_two_when_no_change():
    bars = [_bar(i, (name, 0)) for i, name in enumerate(["C", "G", "Am", "F"])]
    assert [b.index for b in example_bars(_section(bars))] == [0, 1]


def test_worked_example_svg_places_second_chord_at_its_slot():
    svg = worked_example_svg(ISLAND, [_bar(0, ("D", 0), ("A", 4))], FOUR_FOUR, 28)
    assert svg.startswith("<svg") and svg.endswith("</svg>")
    assert 'width="224"' in svg  # one bar, no gap
    chords = _chords(svg)
    assert [name for _, name in chords] == ["D", "A"]
    d_x, a_x = (x for x, _ in chords)
    assert a_x - d_x == 4 * 28  # left-aligned on slot 4, the same inset as slot 0
    assert svg.count('class="change"') == 1  # a divider at A, none at the bar's first chord
    assert svg.count('class="held"') > 0
    assert svg.count('class="arrow down"') == 3 and svg.count('class="arrow up"') == 3
    assert 'font-size="14" font-weight="bold" fill="#111"' in svg
    # in a second bar the same chord sits one bar plus the 12 px gap further on
    two = worked_example_svg(ISLAND, [_bar(0, ("C", 0)), _bar(1, ("D", 0), ("A", 4))], FOUR_FOUR, 28)
    assert dict((name, x) for x, name in _chords(two))["A"] == d_x + 8 * 28 + 12 + 4 * 28


def test_worked_example_svg_two_bars_have_a_bar_line():
    bars = [_bar(0, ("N.C.", 0), ("D", 2)), _bar(1, ("D", 0))]
    svg = worked_example_svg(ISLAND, bars, FOUR_FOUR, 28)
    assert 'width="460"' in svg  # 2 * 8 * 28 + 12
    assert svg.count('class="bar-line"') == 1
    assert [name for _, name in _chords(svg)] == ["N.C.", "D", "D"]
    assert svg.count('class="arrow down"') == 6
    one = worked_example_svg(ISLAND, bars[:1], FOUR_FOUR, 28)
    assert 'class="bar-line"' not in one


def test_strip_with_no_bars_still_draws_the_pattern():
    svg = worked_example_svg(ISLAND, [], FOUR_FOUR, 28)
    assert 'width="224"' in svg
    assert svg.count('class="arrow down"') == 3


def test_slot_px_narrows_for_sixteenths():
    assert slot_px(8) == 28
    assert slot_px(6) == 28
    assert slot_px(16) == 20
    sixteenths = list("D-DU-UDU" * 2)
    svg = worked_example_svg(sixteenths, [_bar(0, ("D", 0)), _bar(1, ("Dm", 12))], FOUR_FOUR, slot_px(16))
    width = int(re.search(r'width="(\d+)"', svg).group(1))
    assert width == 2 * 16 * 20 + 12
    assert width <= TEXT_WIDTH_PX
