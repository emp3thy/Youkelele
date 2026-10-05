from __future__ import annotations

import re
from html import unescape

from youkelele.render.bar_svg import bar_svg, slot_px, string_label_rows
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
    # the brief wrote 4 here, but by its own rule (and spec 3.1) only the strokes on 0, 2 and 4
    # are followed by an empty slot: 6 is followed by the up stroke on 7, and 7 ends the bar
    assert svg.count('class="sustain"') == 3  # three strokes followed by an empty slot ring into it


def test_short_strokes_draw_no_sustain_and_grey_bars_use_grey_ink():
    svg = bar_svg(_bar_with(rings=False), M44, 8, 28, first_in_line=False, grey=True, tab_rows=False)
    assert 'class="sustain"' not in svg and 'stroke="#999"' in svg and 'stroke="#111"' not in svg.split("chord")[0]
    # grey reaches every arrow and nothing else: the chord name stays black
    assert 'stroke="#111"' not in svg and re.search(r'fill="#111"[^>]*class="chord"', svg)
    assert _labels(svg) == []  # the count row prints under the line's first bar only


def test_sustain_runs_to_the_next_stroke_or_the_bar_end():
    bar = ScoreBar(
        index=0, chords=[_chord("C", 0, 8)],
        strokes=[Stroke(slot=0, kind="D"), Stroke(slot=4, kind="x", rings=False), Stroke(slot=5, kind="U")],
    )
    svg = bar_svg(bar, M44, 8, 20, first_in_line=False, grey=False, tab_rows=False)
    # slot 0 rings through 1 to 3; the muted 4 is short; 5 rings through 6 and 7 to the bar end
    spans = [(float(a), float(b)) for a, b in re.findall(r'<line x1="([\d.]+)"[^>]*x2="([\d.]+)"[^>]*class="sustain"', svg)]
    assert len(spans) == 2
    assert spans[0][0] > 10 and 70 <= spans[0][1] <= 80  # from the first arrow to the end of slot 3
    assert spans[1][0] > 110 and 150 <= spans[1][1] <= 160  # from the up arrow to the bar end
    assert svg.count('class="arrow muted"') == 1
    # a muted strike never rings on, even when its flag says it rings
    chuck = ScoreBar(index=0, chords=[_chord("C", 0, 8)], strokes=[Stroke(slot=0, kind="x", rings=True)])
    assert 'class="sustain"' not in bar_svg(chuck, M44, 8, 20, first_in_line=False, grey=False, tab_rows=False)


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


def test_tab_notes_ring_on_their_string_and_an_empty_tab_still_draws_the_block():
    bar = ScoreBar(
        index=0, chords=[_chord("F", 0, 8)], strokes=[Stroke(slot=0, kind="D")],
        tab=[TabNote(slot=0, midi=69, string=3, fret=0), TabNote(slot=2, midi=69, string=3, fret=0, rings=False)],
    )
    svg = bar_svg(bar, M44, 8, 20, first_in_line=False, grey=False, tab_rows=True)
    assert 'data-string="A"' in svg
    assert svg.count('class="sustain"') == 2  # the ringing note over slot 1, the stroke over 1 to 7
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
