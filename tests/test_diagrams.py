from __future__ import annotations

from youkelele.render.diagrams import chord_diagram_svg
from youkelele.schemas import Shape


def test_open_c_has_nut_one_dot_and_three_open_markers():
    svg = chord_diagram_svg("C", Shape(frets=[0, 0, 0, 3], fingers=[0, 0, 0, 3], base_fret=1, barres=[]))
    assert svg.startswith("<svg") and svg.endswith("</svg>")
    assert 'width="80" height="100"' in svg
    assert svg.count("<circle") == 1
    assert svg.count('class="open"') == 3
    assert 'class="nut"' in svg
    assert 'class="base-fret"' not in svg
    assert 'class="barre"' not in svg
    assert 'class="muted"' not in svg
    assert ">C</text>" in svg
    assert 'class="finger">3</text>' in svg


def test_barre_shape_draws_rect_and_first_fret_label():
    bb = Shape(frets=[3, 2, 1, 1], fingers=[3, 2, 1, 1], base_fret=1, barres=[1])
    svg = chord_diagram_svg("Bb", bb)
    assert svg.count('class="barre"') == 1
    assert 'class="nut"' in svg
    assert svg.count("<circle") == 4

    high = Shape(frets=[3, 2, 1, 1], fingers=[3, 2, 1, 1], base_fret=3, barres=[1])
    svg = chord_diagram_svg("C", high)
    assert 'class="base-fret">3</text>' in svg
    assert 'class="nut"' not in svg
    assert svg.count('class="barre"') == 1


def test_muted_string_draws_x():
    shape = Shape(frets=[-1, 2, 1, 0], fingers=[0, 2, 1, 0], base_fret=1, barres=[])
    svg = chord_diagram_svg("Fm", shape)
    assert svg.count('class="muted">x</text>') == 1
    assert svg.count('class="open"') == 1
    assert svg.count("<circle") == 2


def test_string_labels_read_g_c_e_a_left_to_right():
    svg = chord_diagram_svg("C", Shape(frets=[0, 0, 0, 3], fingers=[0, 0, 0, 3], base_fret=1, barres=[]))
    positions = [svg.index(f'class="string-label">{s}</text>') for s in "GCEA"]
    assert positions == sorted(positions)


def test_name_is_escaped():
    svg = chord_diagram_svg("A<b>", Shape(frets=[0, 0, 0, 0], fingers=[0, 0, 0, 0], base_fret=1, barres=[]))
    assert "A&lt;b&gt;" in svg
