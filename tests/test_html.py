from __future__ import annotations

import re

from youkelele.render.html import render_html
from youkelele.schemas import (
    ChordDiagram,
    Instrument,
    Meter,
    Score,
    ScoreBar,
    ScoreChord,
    ScoreSection,
    Shape,
)

ISLAND = list("D-DU-UDU")
C = Shape(frets=[0, 0, 0, 3], fingers=[0, 0, 0, 3], base_fret=1, barres=[])
G = Shape(frets=[0, 2, 3, 2], fingers=[0, 1, 3, 2], base_fret=1, barres=[])


def _section(
    label, n_bars, start, uncertain=False, no_instrument=False, pattern=ISLAND, inherited_from=None,
    names=("C",),
):
    bars = [
        ScoreBar(
            index=start + i,
            chords=[ScoreChord(name=names[i % len(names)], diagram=0, start_slot=0, slots=list(pattern))],
        )
        for i in range(n_bars)
    ]
    return ScoreSection(
        label=label, pattern=list(pattern), uncertain=uncertain, bars=bars, bar_repeat=0.875,
        no_instrument=no_instrument, inherited_from=inherited_from,
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
        strums_uncertain=any(s.uncertain for s in sections),
        chord_diagrams=[ChordDiagram(name="C", shape=C), ChordDiagram(name="G", shape=G)],
        sections=sections,
    )


def _two_sections(**kwargs):
    return _score([_section("Verse 1", 8, 0), _section("Chorus", 4, 8)], **kwargs)


def _section_html(html: str, label: str) -> str:
    start = html.index(f"<h2>{label}</h2>")
    end = html.find("</section>", start)
    return html[start:end]


def test_html_has_no_scripts_and_no_assets():
    html = render_html(_two_sections())
    assert "<script" not in html
    assert "alphaTab" not in html and "alphatab" not in html
    assert "assets/" not in html
    assert "<link" not in html
    assert "Song &amp; Dance" in html


def test_html_renders_grid_rows_with_repeat_marker():
    chorus = _section("Chorus", 12, 8, names=("G", "C"))
    html = render_html(_score([_section("Verse 1", 6, 0, names=("C", "G")), chorus]))
    verse = _section_html(html, "Verse 1")
    assert verse.count('class="row"') == 2  # 4 + 2 bars, different rows
    assert "×" not in verse
    body = _section_html(html, "Chorus")
    assert body.count('class="row"') == 1
    assert body.count('class="cell"') == 4
    assert "×3" in body
    assert re.findall(r'<div class="cell">([^<]*)</div>', body) == ["G", "C", "G", "C"]


def test_html_nc_and_pickup_cells():
    pickup = ScoreBar(
        index=0, pickup=True, chords=[ScoreChord(name="N.C.", diagram=-1, start_slot=0, slots=ISLAND)]
    )
    split = ScoreBar(
        index=1,
        chords=[
            ScoreChord(name="C", diagram=0, start_slot=0, slots=ISLAND[:4]),
            ScoreChord(name="G", diagram=1, start_slot=4, slots=ISLAND[4:]),
        ],
    )
    section = ScoreSection(
        label="Intro", pattern=ISLAND, uncertain=False, bars=[pickup, split], bar_repeat=1.0,
        no_instrument=False,
    )
    html = render_html(_score([section]))
    assert html.count('class="cell nc pickup"') == 1
    assert "pickup" in _section_html(html, "Intro").split('class="cell nc pickup"')[1][:80]
    assert ">C / G<" in html


def test_html_uncertain_section_has_heading_note_and_no_strum_box():
    score = _score(
        [_section("Verse 1", 2, 0, uncertain=True), _section("Chorus", 2, 2)], strum_source="mix"
    )
    html = render_html(score)
    verse = _section_html(html, "Verse 1")
    assert "(uncertain)" in verse
    assert "Strum as played, 88% repeatable" in verse
    assert 'class="strum-box"' not in verse and "<svg" not in verse
    assert 'class="row"' in verse
    chorus = _section_html(html, "Chorus")
    assert chorus.count('class="strum-box"') == 1 and "(uncertain)" not in chorus
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


def test_html_fixed_sheet_width_for_print():
    html = render_html(_two_sections())
    assert ".sheet { width: 182mm; margin: 0 auto }" in html
    print_block = html[html.index("@media print"):]
    assert "html, body { width: 182mm }" in print_block
    assert ".no-print { display: none }" in print_block
    assert "@page { size: A4; margin: 14mm }" in html
    assert ".section-head { break-after: avoid }" in html
    assert "avoid-page" not in html
    assert ".row { display: grid; grid-template-columns: repeat(4, 1fr) auto; break-inside: avoid; }" in html
    assert ".cell { border: 1px solid; padding: 2mm; font-size: 12pt; }" in html
    assert ".cell.nc { color: var(--muted); }" in html
    assert ".cell.pickup { grid-column: span 1; font-size: 9pt; }" in html
    assert ".repeat { font-size: 10pt; align-self: center; }" in html


def test_html_no_instrument_section_replaces_strum_box():
    score = _score([_section("Intro", 2, 0, no_instrument=True), _section("Verse", 2, 2)])
    html = render_html(score)
    intro = _section_html(html, "Intro")
    assert "No strummed instrument detected" in intro
    assert "Strum as played" not in intro and 'class="strum-box"' not in intro
    assert 'class="row"' in intro
    assert html.count('class="strum-box"') == 1


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


STRUMS_NOTE = "Strum detection uncertain for this song (onsets fit the beat grid poorly)"


def test_html_shows_song_level_strum_uncertainty_note():
    score = _two_sections().model_copy(update={"strums_uncertain": True})
    html = render_html(score)
    head = html[html.index('<header class="sheet-head">'):html.index("</header>")]
    assert STRUMS_NOTE in head
    assert STRUMS_NOTE not in render_html(_two_sections())


def test_html_names_the_section_a_pattern_was_inherited_from():
    score = _score(
        [_section("Verse", 4, 0), _section("Pre-chorus", 2, 4, inherited_from=0)]
    )
    html = render_html(score)
    assert html.count("inherited from") == 1
    assert "inherited from Verse" in _section_html(html, "Pre-chorus")
