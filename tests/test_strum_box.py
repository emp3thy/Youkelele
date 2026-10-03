from __future__ import annotations

import re

from youkelele.render.strum_box import strum_pattern_svg
from youkelele.schemas import Meter


def _labels(svg: str) -> list[str]:
    return re.findall(r'class="beat-label[^"]*">([^<]*)</text>', svg)


def test_island_strum_box_has_three_down_three_up_arrows():
    svg = strum_pattern_svg(list("D-DU-UDU"), Meter(numerator=4, denominator=4))
    assert svg.startswith("<svg") and svg.endswith("</svg>")
    assert svg.count('class="arrow down"') == 3
    assert svg.count('class="arrow up"') == 3
    assert 'class="arrow muted"' not in svg
    assert 'width="224"' in svg
    assert _labels(svg) == ["1", "&", "2", "&", "3", "&", "4", "&"]


def test_3_4_box_has_six_columns_and_beat_labels_1_2_3():
    svg = strum_pattern_svg(list("D-DUxU"), Meter(numerator=3, denominator=4))
    assert svg.count('class="slot"') == 6
    assert 'width="168"' in svg
    assert _labels(svg) == ["1", "&", "2", "&", "3", "&"]
    assert svg.count('class="arrow muted"') == 1


def test_sixteen_slots_label_1_e_and_a():
    svg = strum_pattern_svg(list("D-DU-UDU" * 2), Meter(numerator=4, denominator=4))
    assert _labels(svg)[:8] == ["1", "e", "&", "a", "2", "e", "&", "a"]
    assert svg.count('class="slot"') == 16
