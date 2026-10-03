from __future__ import annotations

import re

from youkelele.music.alphatex import score_to_alphatex
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


def _section(label, n_bars, start, uncertain=False, no_instrument=False, pattern=ISLAND):
    bars = [
        ScoreBar(index=start + i, chords=[ScoreChord(name="C", diagram=0, start_slot=0, slots=list(pattern))])
        for i in range(n_bars)
    ]
    return ScoreSection(
        label=label, pattern=list(pattern), uncertain=uncertain, bars=bars, bar_repeat=0.875,
        no_instrument=no_instrument,
    )


def _score(sections, strum_source="other_stem", slots_per_bar=8):
    return Score(
        instrument=Instrument(name="Ukulele", strings=4, tuning=["G4", "C4", "E4", "A4"], capo=0),
        title="Song & Dance",
        artist="Band",
        key="C major",
        bpm=100.4,
        meter=Meter(numerator=4, denominator=4),
        tier="easy",
        slots_per_bar=slots_per_bar,
        strum_source=strum_source,
        strums_uncertain=any(s.uncertain for s in sections),
        chord_diagrams=[ChordDiagram(name="C", shape=C)],
        sections=sections,
    )


def _two_sections(**kwargs):
    return _score([_section("Verse 1", 8, 0), _section("Chorus", 4, 8)], **kwargs)


def test_html_inlines_tex_and_disables_workers():
    score = _two_sections()
    tex = score_to_alphatex(score)
    html = render_html(score, tex)
    assert "useWorkers: false" in html
    assert "playerMode: 0" in html
    assert "tex: true" in html
    assert 'fontDirectory: "assets/font/"' in html
    assert '<script src="assets/alphaTab.min.js"></script>' in html
    assert '\\chord ("C"' in html
    match = re.search(r'<script type="text/plain" id="tex">(.*?)</script>', html, re.S)
    assert match is not None
    assert match.group(1) == tex
    # other fields are escaped normally
    assert "Song &amp; Dance" in html


def test_html_one_api_per_section_with_bar_ranges():
    html = render_html(_two_sections(), "tex")
    starts = re.findall(r'data-start-bar="(\d+)"', html)
    counts = re.findall(r'data-bar-count="(\d+)"', html)
    assert starts == ["1", "9"]
    assert counts == ["8", "4"]
    assert html.count('class="at-section"') == 2
    assert html.count("new alphaTab.AlphaTabApi(") == 1  # one construction inside the per-section loop
    assert "postRenderFinished" in html
    assert "window.__rendered = true" in html
    assert "layoutMode: \"page\"" in html
    assert "scale: 0.85" in html
    for element in (
        "effectTempo", "trackNames", "scoreTitle", "scoreArtist", "chordDiagrams", "effectMarker", "effectCapo"
    ):
        assert f"{element}: false" in html
    # lazy partials are not in the DOM when page.pdf() runs, so later sections print blank
    assert "enableLazyLoading: false" in html
    # the "rendered by alphaTab" partial is cropped off by sizing the overflow-hidden wrapper
    assert "rendered by alphaTab" in html


def test_html_sixteen_slots_use_smaller_scale():
    pattern = list("D-DU-UDU" * 2)
    score = _score([_section("Verse", 2, 0, pattern=pattern)], slots_per_bar=16)
    html = render_html(score, "tex")
    assert "scale: 0.75" in html
    assert "scale: 0.85" not in html


def test_html_fixed_sheet_width_for_print():
    html = render_html(_two_sections(), "tex")
    assert ".sheet { width: 182mm; margin: 0 auto }" in html
    print_block = html[html.index("@media print"):]
    assert "html, body { width: 182mm }" in print_block
    assert ".no-print { display: none }" in print_block
    assert "@page { size: A4; margin: 14mm }" in html
    assert ".section-head { break-after: avoid }" in html
    assert ".section { break-inside: avoid-page }" in html
    assert "overflow: hidden" in html
    assert "<link" not in html


def test_html_shows_uncertain_badge_and_mix_note():
    score = _score(
        [_section("Verse 1", 2, 0, uncertain=True), _section("Chorus", 2, 2)], strum_source="mix"
    )
    html = render_html(score, "tex")
    assert html.count("Strum pattern uncertain") == 1
    assert "Strum detected from full mix" in html
    assert html.count("Strum as played") == 2
    assert "88%" in html
    assert html.count("(uncertain)") == 1

    plain = render_html(_two_sections(), "tex")
    assert "Strum pattern uncertain" not in plain
    assert "Strum detected from full mix" not in plain


def test_html_no_instrument_section_replaces_strum_box():
    score = _score([_section("Intro", 2, 0, no_instrument=True), _section("Verse", 2, 2)])
    html = render_html(score, "tex")
    assert "No strummed instrument detected" in html
    assert html.count('class="strum-box"') == 1
    assert html.count("Strum as played") == 1


def test_html_has_one_legend_diagram_per_chord():
    html = render_html(_two_sections(), "tex")
    legend = html[html.index('class="legend"'):html.index('class="sections"')]
    assert legend.count("<svg") == 1
