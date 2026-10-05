from __future__ import annotations

import re
from pathlib import Path

from youkelele.jsonio import load_model
from youkelele.render.html import display_names, render_html
from youkelele.schemas import (
    ChordDiagram,
    Instrument,
    Meter,
    Score,
    ScoreBar,
    ScoreChord,
    ScoreSection,
    Shape,
    Stroke,
    TabNote,
)

FIXTURES = Path(__file__).parent / "fixtures"
ISLAND = list("D-DU-UDU")
C = Shape(frets=[0, 0, 0, 3], fingers=[0, 0, 0, 3], base_fret=1, barres=[])
G = Shape(frets=[0, 2, 3, 2], fingers=[0, 1, 3, 2], base_fret=1, barres=[])
RIFF = [TabNote(slot=0, midi=60, string=1, fret=0), TabNote(slot=3, midi=62, string=1, fret=2)]


def _strokes(pattern=ISLAND, rings=True) -> list[Stroke]:
    return [Stroke(slot=j, kind=k, rings=rings) for j, k in enumerate(pattern) if k != "-"]


def _section(
    label, n_bars, start, names=("C",), state="", grey=False, tab=False, pattern=ISLAND,
    no_instrument=False, octave_shift=0,
):
    bars = [
        ScoreBar(
            index=start + i,
            chords=[ScoreChord(name=names[i % len(names)], diagram=0, start_slot=0, slots=list(pattern))],
            strokes=[] if no_instrument else _strokes(pattern),
            tab=list(RIFF) if tab else None,
            grey=grey,
        )
        for i in range(n_bars)
    ]
    return ScoreSection(
        label=label, pattern=list(pattern), uncertain=grey, bars=bars, bar_repeat=0.875,
        no_instrument=no_instrument, state=state, octave_shift=octave_shift,
    )


def _score(sections, strum_source="other_stem", slots_per_bar=8, capo=0):
    return Score(
        instrument=Instrument(name="Ukulele", strings=4, tuning=["G4", "C4", "E4", "A4"], capo=capo),
        title="Song & Dance",
        artist="Band",
        key="C major",
        bpm=100.4,
        meter=Meter(numerator=4, denominator=4),
        tier="easy",
        slots_per_bar=slots_per_bar,
        strum_source=strum_source,
        strums_uncertain=False,
        chord_diagrams=[ChordDiagram(name="C", shape=C), ChordDiagram(name="G", shape=G)],
        sections=sections,
    )


def _two_sections(**kwargs):
    return _score([_section("Verse 1", 8, 0), _section("Chorus", 4, 8)], **kwargs)


def _section_html(html: str, label: str) -> str:
    start = html.index(f"<h2>{label}</h2>")
    end = html.find("</section>", start)
    return html[start:end]


def _chord_names(html: str) -> list[str]:
    """The chord row's names in page order, the power badge's tspan kept as written."""
    return re.findall(r'class="chord[^"]*">(.*?)</text>', html)


# the brief's tests


def test_render_html_prints_every_bar_in_order_with_state_phrases_and_no_strip():
    score = _score([_section("verse", 12, 0), _section("chorus", 4, 12, state="pattern uncertain", grey=True)])
    html = render_html(score)
    diagrams = score.chord_diagrams
    assert html.count("<svg") >= 16 + len(diagrams) and "worked-example" not in html and "×" not in html
    assert "pattern uncertain" in html and "play " not in html
    assert html.count('class="bar"') == 16
    # the uncertain chorus draws its strokes in grey; the verse in black
    chorus = _section_html(html, "Chorus")
    assert 'stroke="#999"' in chorus and 'class="arrow down"' in chorus
    assert re.search(r'<span class="strum-label">pattern uncertain</span>', chorus)
    assert "strum-label" not in _section_html(html, "Verse")  # a certain section prints no phrase


def test_render_html_folds_identical_lines_and_prints_the_tab_legend_once():
    html = render_html(_score([_section("outro", 24, 0, names=("G",))]))  # eight-bar lines, three identical
    assert html.count("play three times") == 1
    outro = _section_html(html, "Outro")
    assert outro.count('class="line"') == 1 and outro.count('class="bar"') == 8
    html_tab = render_html(_score([_section("verse", 8, 0, tab=True, state="riff")]))
    assert html_tab.count("Tab: A E C G top to bottom; numbers are frets.") == 1 and "written an octave" not in html_tab
    assert html_tab.index("Tab: A E C G") < html_tab.index('class="sections"')
    assert "Tab: A E C G" not in html


def test_v15_score_fixture_renders():
    html = render_html(load_model(FIXTURES / "v15_score.json", Score))
    assert "<svg" in html  # bars with empty strokes draw their chords' slots as strokes, all ringing
    assert 'class="arrow down"' in html and 'class="sustain"' in html


# the page around the bars


def test_octave_shift_is_named_after_the_state_phrase():
    up = render_html(_score([_section("verse", 4, 0, tab=True, state="riff", octave_shift=1)]))
    assert '<span class="strum-label">riff</span>' in up and "written an octave up" in up
    down = render_html(_score([_section("verse", 4, 0, tab=True, state="riff", octave_shift=-1)]))
    assert "written an octave down" in down
    two = render_html(_score([_section("verse", 4, 0, tab=True, state="riff", octave_shift=2)]))
    assert "written two octaves up" in two


def test_tab_lines_draw_the_tab_block_and_labels_once_per_line():
    html = render_html(_score([_section("verse", 8, 0, tab=True, state="riff")]))
    verse = _section_html(html, "Verse")
    assert verse.count('class="line"') == 1
    assert verse.count('class="string-label"') == 4  # A E C G on the line's first bar only
    assert verse.count('class="fret"') == 16
    assert verse.count('class="count beat"') == 4  # one count row per line


def test_no_instrument_section_prints_its_phrase_and_empty_stroke_rows():
    score = _score(
        [_section("Intro", 2, 0, no_instrument=True, state="no strummed instrument detected"), _section("Verse", 2, 2)]
    )
    intro = _section_html(render_html(score), "Intro")
    assert "no strummed instrument detected" in intro
    assert intro.count('class="bar"') == 2 and 'class="arrow' not in intro


def test_html_nc_and_pickup_bars():
    pickup = ScoreBar(
        index=0, pickup=True, chords=[ScoreChord(name="N.C.", diagram=-1, start_slot=0, slots=ISLAND)],
        strokes=_strokes(),
    )
    split = ScoreBar(
        index=1,
        chords=[
            ScoreChord(name="C", diagram=0, start_slot=0, slots=ISLAND[:4]),
            ScoreChord(name="G", diagram=1, start_slot=4, slots=ISLAND[4:]),
        ],
        strokes=_strokes(),
    )
    section = ScoreSection(
        label="Intro", pattern=ISLAND, uncertain=False, bars=[pickup, split], bar_repeat=1.0,
        no_instrument=False,
    )
    html = render_html(_score([section]))
    assert _chord_names(html) == ["N.C.", "C", "G"]
    assert html.count('class="pickup-label"') == 1


def test_html_has_no_scripts_and_no_assets():
    html = render_html(_two_sections())
    assert "<script" not in html
    assert "alphaTab" not in html and "alphatab" not in html
    assert "assets/" not in html
    assert "<link" not in html
    assert "Song &amp; Dance" in html


def test_html_strum_source_note():
    html = render_html(_two_sections(strum_source="mix"))
    assert "Strum detected from full mix" in html
    assert "Strum detected from full mix" not in render_html(_two_sections())


def test_html_capo_header_notes():
    html = render_html(_two_sections(capo=4))
    head = html[html.index('<header class="sheet-head">'):html.index("</header>")]
    assert "fret 4" in head
    assert "Shapes are relative to the capo" in head
    assert "Sounding key: C major" in head
    plain = render_html(_two_sections())
    assert "Shapes are relative to the capo" not in plain
    assert "Sounding key" not in plain


def test_html_capo_shows_shape_key_and_sounding_key():
    score = _two_sections(capo=4).model_copy(update={"key": "C# major"})
    html = render_html(score)
    head = html[html.index('<header class="sheet-head">'):html.index("</header>")]
    assert "A major (shapes)" in head
    assert "Sounding key: C# major" in head


def test_html_no_capo_shows_key_once():
    score = _two_sections().model_copy(update={"key": "C# major"})
    head = render_html(score)
    head = head[head.index('<header class="sheet-head">'):head.index("</header>")]
    assert head.count("C# major") == 1
    assert "(shapes)" not in head


def _head(html: str) -> str:
    return html[html.index('<header class="sheet-head">'):html.index("</header>")]


def test_header_hedges_key_and_shape_key_under_capo():
    score = _two_sections().model_copy(update={"key": "G major", "key_hedge": "D major"})
    head = _head(render_html(score))
    assert "<b>Key</b> G major (or D major)" in head
    capo = _two_sections(capo=2).model_copy(update={"key": "G major", "key_hedge": "D major"})
    head = _head(render_html(capo))
    assert "F major (or C major) (shapes)" in head
    assert "Sounding key: G major (or D major)" in head
    plain = _head(render_html(_two_sections().model_copy(update={"key": "G major"})))
    assert "(or" not in plain


def test_html_fixed_sheet_width_for_print():
    html = render_html(_two_sections())
    assert ".sheet { width: 182mm; margin: 0 auto }" in html
    print_block = html[html.index("@media print"):]
    assert "html, body { width: 182mm }" in print_block
    assert ".no-print { display: none }" in print_block
    assert "@page { size: A4; margin: 14mm }" in html
    assert ".section-head { break-after: avoid }" in html
    assert ".line { display: flex; gap: 1.5mm; break-inside: avoid; margin-bottom: 1.5mm }" in html
    for gone in (".row {", ".cell {", ".block {", ".strum-box", ".section-body"):
        assert gone not in html


def test_html_has_one_legend_diagram_per_chord():
    html = render_html(_two_sections())
    legend = html[html.index('class="legend"'):html.index('class="sections"')]
    assert legend.count("<svg") == 2


def test_html_escapes_hostile_title():
    score = _two_sections().model_copy(
        update={"title": "My </script><script>alert(1)</script> Song", "artist": "<!-- x"}
    )
    html = render_html(score)
    assert "<script" not in html
    assert "&lt;/script&gt;" in html and "&lt;!-- x" in html


def test_html_escapes_hostile_chord_names():
    section = _section("Verse", 1, 0, names=("<b>X</b>",))
    html = render_html(_score([section]))
    assert "<b>X</b>" not in html and "&lt;b&gt;X&lt;/b&gt;" in html


STRUMS_NOTE = "Strum detection uncertain for this song (onsets fit the beat grid poorly)"


def test_html_shows_song_level_strum_uncertainty_note():
    score = _two_sections().model_copy(update={"strums_uncertain": True})
    html = render_html(score)
    head = html[html.index('<header class="sheet-head">'):html.index("</header>")]
    assert STRUMS_NOTE in head
    assert STRUMS_NOTE not in render_html(_two_sections())


B = Shape(frets=[4, 3, 2, 2], fingers=[3, 2, 1, 1], base_fret=1, barres=[2])
FILLED_NOTE = "Italic chords were inferred where the recording had no clear chord"


def _bars(names: list[str], start: int = 0, filled: bool = False) -> list[ScoreBar]:
    return [
        ScoreBar(
            index=start + i,
            chords=[ScoreChord(name=n, diagram=0, start_slot=0, slots=ISLAND, filled=filled)],
            strokes=_strokes(),
        )
        for i, n in enumerate(names)
    ]


def _plain_section(label: str, bars: list[ScoreBar]) -> ScoreSection:
    return ScoreSection(
        label=label, pattern=ISLAND, uncertain=False, bars=bars, bar_repeat=1.0, no_instrument=False
    )


def test_passing_chord_omitted_from_legend_and_listed():
    score = _two_sections().model_copy(
        update={
            "chord_diagrams": [
                ChordDiagram(name="C", shape=C),
                ChordDiagram(name="G", shape=G),
                ChordDiagram(name="B", shape=B, passing=True),
            ]
        }
    )
    html = render_html(score)
    legend = html[html.index('class="legend"'):html.index("Passing:")]
    assert legend.count("<svg") == 2
    assert ">B<" not in legend
    assert "Passing: B 4322" in html
    assert html.index('class="legend"') < html.index("Passing: B 4322") < html.index('class="sections"')
    assert "Passing:" not in render_html(_two_sections())


def test_passing_line_lists_every_passing_chord():
    e7 = Shape(frets=[1, 2, 0, 2], fingers=[1, 2, 0, 3], base_fret=1, barres=[])
    score = _two_sections().model_copy(
        update={
            "chord_diagrams": [
                ChordDiagram(name="C", shape=C),
                ChordDiagram(name="B", shape=B, passing=True),
                ChordDiagram(name="E7", shape=e7, passing=True),
            ]
        }
    )
    assert "Passing: B 4322, E7 1202" in render_html(score)


def _power_score(tier: str) -> Score:
    split = ScoreBar(
        index=1,
        chords=[
            ScoreChord(name="C#m", diagram=0, start_slot=0, slots=ISLAND[:4], power=True),
            ScoreChord(name="G", diagram=1, start_slot=4, slots=ISLAND[4:]),
        ],
        strokes=_strokes(),
    )
    whole = ScoreBar(
        index=0,
        chords=[ScoreChord(name="C#m", diagram=0, start_slot=0, slots=ISLAND, power=True)],
        strokes=_strokes(),
    )
    plain = ScoreBar(
        index=2, chords=[ScoreChord(name="G", diagram=1, start_slot=0, slots=ISLAND)], strokes=_strokes(),
    )
    section = ScoreSection(
        label="Verse", pattern=ISLAND, uncertain=False, bars=[whole, split, plain],
        bar_repeat=1.0, no_instrument=False,
    )
    return _score([section]).model_copy(
        update={
            "tier": tier,
            "chord_diagrams": [
                ChordDiagram(name="C#m", shape=C, power=True),
                ChordDiagram(name="G", shape=G),
            ],
        }
    )


BADGE = re.compile(r'C#m<tspan [^>]*class="power"[^>]*>5</tspan>')


def test_html_power_badge_and_legend_line():
    html = render_html(_power_score("full"))
    names = _chord_names(html)
    assert len(names) == 4 and BADGE.fullmatch(names[0]) and BADGE.fullmatch(names[1])
    assert names[2:] == ["G", "G"]
    legend_line = "C#m is a power chord on the record"
    assert html.count(legend_line) == 1
    assert html.index('class="legend"') < html.index(legend_line) < html.index('class="sections"')


def test_html_power_legend_line_follows_the_passing_line():
    score = _power_score("full")
    diagrams = [*score.chord_diagrams, ChordDiagram(name="B", shape=B, passing=True)]
    html = render_html(score.model_copy(update={"chord_diagrams": diagrams}))
    assert html.index("Passing: B 4322") < html.index("C#m is a power chord on the record")


def test_html_easy_tier_prints_the_plain_name_without_badge_and_the_triad_line():
    html = render_html(_power_score("easy"))
    assert 'class="power"' not in html
    # the easy tier names the power chord once, with the triad clause, not the full tier's line
    assert html.count("power chord") == 1
    assert "C#m is a power chord on the record" not in html
    assert _chord_names(html) == ["C#m", "C#m", "G", "G"]


def test_html_power_legend_line_once_per_name():
    # two shapes of one name, both used as a power chord: one legend line
    score = _power_score("full")
    diagrams = [*score.chord_diagrams, ChordDiagram(name="C#m", shape=B, power=True)]
    html = render_html(score.model_copy(update={"chord_diagrams": diagrams}))
    assert html.count("C#m is a power chord on the record") == 1


def test_html_without_power_has_no_badge_markup():
    html = render_html(_two_sections())
    assert 'class="power"' not in html and "power chord" not in html


def test_easy_tier_prints_the_power_line_with_the_triad_clause():
    html = render_html(_power_score("easy"))
    line = "C#m is a power chord (root and fifth) on the record; this sheet prints the triad."
    assert line in html
    assert html.count(line) == 1
    assert html.index('class="legend"') < html.index(line) < html.index('class="sections"')


def test_full_tier_power_line_unchanged():
    html = render_html(_power_score("full"))
    assert "C#m is a power chord on the record" in html
    assert "root and fifth" not in html and "prints the triad" not in html


def test_filled_chord_italic_and_header_note():
    bars = _bars(["C", "G"]) + _bars(["G"], start=2, filled=True)
    html = render_html(_score([_plain_section("Verse", bars)]))
    assert re.findall(r'font-style="italic"[^>]*class="chord">([^<]*)<', html) == ["G"]
    assert html.count('font-style="italic"') == 1
    head = html[html.index('<header class="sheet-head">'):html.index("</header>")]
    assert FILLED_NOTE in head
    assert FILLED_NOTE not in render_html(_two_sections())


def test_a_line_with_two_chords_in_a_bar_holds_four_bars():
    bars = _bars(["C", "G", "C", "G"]) + [
        ScoreBar(
            index=4,
            chords=[
                ScoreChord(name="C", diagram=0, start_slot=0, slots=ISLAND[:4]),
                ScoreChord(name="G", diagram=1, start_slot=4, slots=ISLAND[4:]),
            ],
            strokes=_strokes(),
        ),
        *_bars(["C", "G", "C"], start=5),
    ]
    verse = _section_html(render_html(_score([_plain_section("Verse", bars)])), "Verse")
    assert verse.count('class="line"') == 2
    widths = re.findall(r'<svg [^>]*class="bar"[^>]*width="(\d+)"|<svg [^>]*width="(\d+)"[^>]*class="bar"', verse)
    assert {a or b for a, b in widths} == {"168"}  # four bars a line: 21 px a slot


def test_eight_bar_lines_use_the_narrow_slot_and_sixteenths_too():
    verse = _section_html(render_html(_score([_section("Verse", 8, 0, names=("C", "G"))])), "Verse")
    assert verse.count('class="line"') == 1 and 'width="80"' in verse
    sixteenths = list("D-DU-UDU" * 2)
    fast = _section_html(
        render_html(_score([_section("Verse", 4, 0, names=("C", "G"), pattern=sixteenths)], slots_per_bar=16)),
        "Verse",
    )
    assert fast.count('class="line"') == 1 and fast.count('width="160"') == 4


def test_display_names_number_by_occurrence():
    assert display_names(["verse", "chorus", "verse", "bridge"]) == [
        "Verse 1", "Chorus", "Verse 2", "Bridge",
    ]
    assert display_names(
        ["intro", "verse", "chorus", "verse", "instrumental", "chorus", "instrumental", "outro"]
    ) == [
        "Intro", "Verse 1", "Chorus 1", "Verse 2", "Instrumental 1", "Chorus 2", "Instrumental 2",
        "Outro",
    ]
    assert display_names([]) == []
    # a hand-capitalised label counts as the same label
    assert display_names(["Verse", "verse"]) == ["Verse 1", "Verse 2"]


def test_html_headings_use_display_names():
    score = _score(
        [
            _section("verse", 4, 0),
            _section("chorus", 4, 4),
            _section("verse", 4, 8),
            _section("bridge", 4, 12),
            _section("verse", 2, 16),
        ]
    )
    html = render_html(score)
    headings = re.findall(r"<h2>(.*?)</h2>", html)
    assert headings == ["Verse 1", "Chorus", "Verse 2", "Bridge", "Verse 3"]


CSHARP = Shape(frets=[1, 1, 1, 4], fingers=[1, 1, 1, 4], base_fret=1, barres=[1])
FSHARP = Shape(frets=[3, 1, 2, 4], fingers=[3, 1, 2, 4], base_fret=1, barres=[])


def _alternative_score(capo: int) -> Score:
    return _two_sections(capo=capo).model_copy(
        update={
            "alternative_diagrams": [
                ChordDiagram(name="C#", shape=CSHARP),
                ChordDiagram(name="F#", shape=FSHARP),
                ChordDiagram(name="B", shape=B),
            ]
        }
    )


def test_html_no_capo_line_in_fret_notation_with_barre_marks():
    html = render_html(_alternative_score(3))
    assert "Without a capo: C# 1114 (barre), F# 3124, B 4322 (barre)" in html
    assert html.index('class="legend"') < html.index("Without a capo:") < html.index('class="sections"')
    # under the Passing line when there is one
    passing = _alternative_score(3).model_copy(
        update={"chord_diagrams": [ChordDiagram(name="C", shape=C), ChordDiagram(name="B", shape=B, passing=True)]}
    )
    shown = render_html(passing)
    assert shown.index("Passing:") < shown.index("Without a capo:")


def test_html_no_capo_line_absent_without_a_capo():
    assert "Without a capo" not in render_html(_alternative_score(0))
    assert "Without a capo" not in render_html(_two_sections(capo=3))
