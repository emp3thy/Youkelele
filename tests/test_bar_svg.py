from __future__ import annotations

import re
from html import unescape

from youkelele.render.bar_svg import _Cols, bar_svg, slot_px, string_label_rows
from youkelele.schemas import Meter, ScoreBar, ScoreChord, Stroke, TabNote

M44 = Meter(numerator=4, denominator=4)
ISLAND = list("D-DU-UDU")


def _chord(name: str, start: int, end: int, **kwargs) -> ScoreChord:
    return ScoreChord(
        name=name, diagram=-1 if name == "N.C." else 0, start_slot=start, slots=["-"] * (end - start),
        **kwargs,
    )


def _labels(svg: str) -> list[str]:
    return [unescape(t) for t in re.findall(r'class="count[^"]*">([^<]*)</text>', svg)]


def _string_labels(svg: str) -> list[str]:
    return re.findall(r'class="string-label">([^<]*)</text>', svg)


def _bar_with(rings: bool) -> ScoreBar:
    strokes = [Stroke(slot=j, kind=k, rings=rings) for j, k in enumerate(ISLAND) if k != "-"]
    return ScoreBar(index=0, chords=[_chord("C", 0, 8)], strokes=strokes)


def test_bar_svg_draws_chords_strokes_and_count():
    bar = ScoreBar(
        index=0, chords=[_chord("D", 0, 4), _chord("G", 4, 8)],
        strokes=[
            Stroke(slot=0, kind="D"), Stroke(slot=2, kind="D"), Stroke(slot=4, kind="D"),
            Stroke(slot=6, kind="D"), Stroke(slot=7, kind="U"),
        ],
    )
    svg = bar_svg(bar, M44, 8, 28, first_in_line=True, grey=False, tab_rows=False)
    assert svg.startswith("<svg") and svg.endswith("</svg>")
    assert svg.count('class="arrow down"') == 4 and svg.count('class="arrow up"') == 1
    assert ">D<" in svg and ">G<" in svg and _labels(svg) == ["1", "&", "2", "&", "3", "&", "4", "&"]
    assert 'class="sustain"' not in svg  # a ringing stroke draws no line over the empty slots after it


def test_grey_bars_use_grey_ink():
    svg = bar_svg(_bar_with(rings=True), M44, 8, 28, first_in_line=False, grey=True, tab_rows=False)
    assert 'class="sustain"' not in svg and 'stroke="#999"' in svg and 'stroke="#111"' not in svg.split("chord")[0]
    # grey reaches every arrow and nothing else: the chord name stays black
    assert 'stroke="#111"' not in svg and re.search(r'fill="#111"[^>]*class="chord"', svg)
    assert _labels(svg) == []  # the count row prints under the line's first bar only


def _strokes() -> list[Stroke]:
    return [Stroke(slot=j, kind=k) for j, k in enumerate(ISLAND) if k != "-"]


def _xs(svg: str) -> list[float]:
    return [float(v) for v in re.findall(r'[ML](-?[\d.]+),', svg)] + [
        float(v) for v in re.findall(r'x[12]="(-?[\d.]+)"', svg)
    ]


def _arrow_ys(svg: str, kind: str) -> tuple[float, float]:
    group = re.search(rf'<g class="arrow {kind}">(.*?)</g>', svg).group(1)
    ys = [float(v) for v in re.findall(r'y[12]="([\d.]+)"', group)]
    ys += [float(v) for v in re.findall(r'[ML][\d.]+,([\d.]+)', group)]
    return min(ys), max(ys)


def test_narrow_slots_keep_arrows_off_the_frame_and_crosses_apart():
    strokes = [Stroke(slot=j, kind=k) for j, k in enumerate("DxxUDUDU")]
    bar = ScoreBar(index=0, chords=[_chord("C", 0, 8)], strokes=strokes)
    svg = bar_svg(bar, M44, 8, 10, first_in_line=False, grey=False, tab_rows=False)
    arrows = "".join(re.findall(r'<g class="arrow.*?</g>', svg))
    assert min(_xs(arrows)) >= 3 and max(_xs(arrows)) <= 77  # the frame stands at 0.5 and 79.5
    crosses = re.findall(r'<line x1="([\d.]+)"[^>]*x2="([\d.]+)"[^>]*/>(?=<line x1="[\d.]+"[^>]*/></g>)', svg)
    widths = [abs(float(b) - float(a)) / 2 for a, b in crosses]
    assert widths and all(2 <= w <= 2.5 for w in widths)  # each cross 4 to 5 px wide
    # up and down arrows span the same height
    assert _arrow_ys(svg, "up") == _arrow_ys(svg, "down")


def test_tab_block_puts_frets_on_the_right_string_lines():
    strokes = [Stroke(slot=0, kind="D"), Stroke(slot=11, kind="D")]
    bar = ScoreBar(
        index=0, chords=[_chord("F", 0, 16)], strokes=strokes,
        tab=[TabNote(slot=0, midi=60, string=1, fret=0), TabNote(slot=11, midi=63, string=1, fret=3)],
    )
    svg = bar_svg(bar, M44, 16, 20, first_in_line=True, grey=False, tab_rows=True)
    assert 'class="fret" data-string="C"' in svg and svg.count('class="fret"') == 2 and ["A", "E", "C", "G"] == _string_labels(svg)
    assert _string_labels(bar_svg(bar, M44, 16, 20, first_in_line=False, grey=False, tab_rows=True)) == []
    # the C string is the third line from the top: both frets sit on it
    lines = [float(y) for y in re.findall(r'<line [^>]*y1="([\d.]+)"[^>]*class="string"', svg)]
    frets = {float(y) for y in re.findall(r'<text [^>]*y="([\d.]+)"[^>]*class="fret"', svg)}
    assert len(lines) == 4 and len(frets) == 1 and lines[1] < frets.pop() - 2 < lines[2] + 2
    assert re.findall(r'class="fret" data-string="C">([^<]*)<', svg) == ["0", "3"]


def test_a_labelled_bar_prints_the_label_left_of_the_chord_in_grey():
    bar = ScoreBar(index=8, chords=[_chord("C", 0, 8)], strokes=_strokes(), label="riff heard")
    svg = bar_svg(bar, M44, 8, 28, first_in_line=False, grey=False, tab_rows=False)
    label_x = float(re.search(r'<text x="([\d.]+)"[^>]*class="chord label">riff heard<', svg).group(1))
    chord_x = float(re.search(r'<text x="([\d.]+)"[^>]*class="chord">C<', svg).group(1))
    assert 'fill="#999" class="chord label"' in svg and chord_x > label_x + 8 * len("riff heard")


def test_a_labelled_bar_with_no_chord_prints_the_label_in_place_of_nc():
    bar = ScoreBar(index=8, chords=[_chord("N.C.", 0, 8)], strokes=[], label="riff")
    svg = bar_svg(bar, M44, 8, 28, first_in_line=False, grey=False, tab_rows=False)
    assert ">riff<" in svg and ">N.C.<" not in svg


def test_a_resting_bar_draws_a_chord_and_an_empty_black_row():
    bar = ScoreBar(index=0, chords=[_chord("G", 0, 8)], strokes=[], rests=True)
    svg = bar_svg(bar, M44, 8, 28, first_in_line=False, grey=False, tab_rows=False)
    assert 'class="arrow' not in svg and svg.count('class="rest"') == 8 and 'stroke="#999"' not in svg


def test_tab_notes_ring_on_their_string_and_an_empty_tab_still_draws_the_block():
    bar = ScoreBar(
        index=0, chords=[_chord("F", 0, 8)], strokes=[Stroke(slot=0, kind="D")],
        tab=[TabNote(slot=0, midi=69, string=3, fret=0), TabNote(slot=2, midi=69, string=3, fret=0, rings=False)],
    )
    svg = bar_svg(bar, M44, 8, 20, first_in_line=False, grey=False, tab_rows=True)
    assert 'data-string="A"' in svg
    assert 'class="sustain"' not in svg and svg.count('class="fret"') == 2 and svg.count('class="string"') == 4
    empty = ScoreBar(index=1, chords=[_chord("F", 0, 8)], strokes=[], tab=[])
    blank = bar_svg(empty, M44, 8, 20, first_in_line=False, grey=False, tab_rows=True)
    assert blank.count('class="string"') == 4 and 'class="fret"' not in blank


def test_no_chord_prints_muted_and_filled_chords_italic():
    nc = ScoreBar(index=0, chords=[])
    svg = bar_svg(nc, M44, 8, 20, first_in_line=False, grey=False, tab_rows=False)
    assert re.search(r'fill="#999"[^>]*class="chord nc">N\.C\.<', svg)
    filled = ScoreBar(index=0, chords=[_chord("G", 0, 8, filled=True)])
    assert 'font-style="italic"' in bar_svg(filled, M44, 8, 20, first_in_line=False, grey=False, tab_rows=False)


def test_count_row_on_sixteenths_and_three_four():
    bar = ScoreBar(index=0, chords=[_chord("C", 0, 16)])
    svg = bar_svg(bar, M44, 16, 10, first_in_line=True, grey=False, tab_rows=False)
    assert _labels(svg)[:8] == ["1", "e", "&", "a", "2", "e", "&", "a"]
    assert re.findall(r'class="count beat"', svg).__len__() == 4
    waltz = bar_svg(ScoreBar(index=0, chords=[_chord("C", 0, 6)]), Meter(numerator=3, denominator=4), 6, 20,
                    first_in_line=True, grey=False, tab_rows=False)
    assert _labels(waltz) == ["1", "&", "2", "&", "3", "&"]


def test_slot_px_fits_the_line_in_the_text_width():
    assert slot_px(8, 4) == 21 and slot_px(8, 8) == 10 and slot_px(16, 4) == 10
    assert slot_px(8, 1) == 28 and slot_px(6, 2) == 28
    assert string_label_rows() == ["A", "E", "C", "G"]
    svg = bar_svg(ScoreBar(index=0, chords=[_chord("C", 0, 8)]), M44, 8, 21, first_in_line=False, grey=False, tab_rows=False)
    assert 'width="168"' in svg


def test_a_partial_pickup_bar_draws_only_its_columns():
    # spec 3.2: a one-beat pickup on an eighth grid draws its last two columns, right-aligned
    bar = ScoreBar(index=0, pickup=True, chords=[_chord("C", 6, 8)], strokes=[], pickup_slots=2)
    svg = bar_svg(bar, M44, 8, 28, first_in_line=True, grey=False, tab_rows=False, pickup_slots=2)
    assert svg.count('class="rest"') == 2
    frame_x = float(re.search(r'<rect x="([\d.]+)"[^>]*class="frame"', svg).group(1))
    # the frame starts at cols.left(6) - 2.5, plus the half-pixel stroke inset every frame has
    assert frame_x == _Cols(ox=0, n=8, box_w=8 * 28).left(6) - 2.5 + 0.5
    assert _labels(svg) == ["4", "&"]
    # the label stays, left of the narrow frame so it never runs into the chord name
    label_x = float(re.search(r'<text x="([\d.]+)"[^>]*class="pickup-label">pickup<', svg).group(1))
    assert svg.count('class="pickup-label"') == 1 and label_x < frame_x
    full = bar_svg(ScoreBar(index=1, chords=[_chord("C", 0, 8)]), M44, 8, 28, first_in_line=False, grey=False, tab_rows=False)
    assert re.search(r'<rect x="0.5"[^>]*class="frame"', full)  # a full bar's frame is unchanged
