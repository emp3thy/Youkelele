from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests.pdfpages import count_pages
from youkelele.jsonio import load_model, save_model
from youkelele.layout import RunLayout
from youkelele.options import RunOptions
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
from youkelele.stage import StageContext
from youkelele.stages.render import RenderStage

C = Shape(frets=[0, 0, 0, 3], fingers=[0, 0, 0, 3], base_fret=1, barres=[])
G = Shape(frets=[0, 2, 3, 2], fingers=[0, 1, 3, 2], base_fret=1, barres=[])
AM = Shape(frets=[2, 0, 0, 0], fingers=[2, 0, 0, 0], base_fret=1, barres=[])
F = Shape(frets=[2, 0, 1, 0], fingers=[2, 0, 1, 0], base_fret=1, barres=[])
B = Shape(frets=[4, 3, 2, 2], fingers=[3, 2, 1, 1], base_fret=1, barres=[2])
ISLAND = list("D-DU-UDU")
UKULELE = Instrument(name="Ukulele", strings=4, tuning=["G4", "C4", "E4", "A4"], capo=0)


def _two_section_score() -> Score:
    """Task 12's verified two-bar example, plus a section with an N.C. bar."""
    bar1 = ScoreBar(
        index=0,
        chords=[
            ScoreChord(name="C", diagram=0, start_slot=0, slots=list("D-D")),
            ScoreChord(name="G", diagram=1, start_slot=3, slots=list("U-UDU")),
        ],
    )
    bar2 = ScoreBar(
        index=1, chords=[ScoreChord(name="G", diagram=1, start_slot=0, slots=list("xxDU-UDU"))]
    )
    bar3 = ScoreBar(index=2, chords=[ScoreChord(name="N.C.", diagram=-1, start_slot=0, slots=ISLAND)])
    bar4 = ScoreBar(index=3, chords=[ScoreChord(name="C", diagram=0, start_slot=0, slots=ISLAND)])
    return Score(
        instrument=UKULELE,
        title="Song",
        artist="Band",
        key="C major",
        bpm=100.4,
        meter=Meter(numerator=4, denominator=4),
        tier="easy",
        slots_per_bar=8,
        strum_source="mix",
        strums_uncertain=True,
        chord_diagrams=[ChordDiagram(name="C", shape=C), ChordDiagram(name="G", shape=G)],
        sections=[
            ScoreSection(label="Verse 1", pattern=ISLAND, uncertain=False, bars=[bar1, bar2],
                         bar_repeat=1.0, no_instrument=False),
            ScoreSection(label="Chorus", pattern=ISLAND, uncertain=True, bars=[bar3, bar4],
                         bar_repeat=0.5, no_instrument=False),
        ],
    )


# (label, bar count, chord cycle, uncertain); 120 bars in all.
_PLAN = [
    ("Intro", 8, "C G", False),
    ("Verse 1", 16, "C G Am F", False),
    ("Pre-chorus", 8, "Am F", True),
    ("Chorus", 12, "F C G", False),
    ("Verse 2", 16, "C G Am F", False),
    ("Chorus", 12, "F C G", False),
    ("Bridge", 8, "Am G F G", False),
    ("Verse 3", 16, "C G Am F", False),
    ("Chorus", 12, "F C G", False),
    ("Outro", 12, "C G", False),
]


def _realistic_120_bar_score() -> Score:
    """A synthetic song: pickup bar, intro, verses, choruses, one uncertain section, one N.C. bar."""
    names = ["C", "G", "Am", "F"]
    diagrams = [ChordDiagram(name=n, shape=s) for n, s in zip(names, (C, G, AM, F), strict=True)]
    nc = ScoreChord(name="N.C.", diagram=-1, start_slot=0, slots=ISLAND)
    sections: list[ScoreSection] = []
    index = 0
    for label, count, cycle, uncertain in _PLAN:
        seq = cycle.split()
        bars: list[ScoreBar] = []
        for i in range(count):
            name = seq[i % len(seq)]
            chord = ScoreChord(name=name, diagram=names.index(name), start_slot=0, slots=ISLAND)
            bars.append(ScoreBar(index=index, chords=[chord]))
            index += 1
        sections.append(
            ScoreSection(label=label, pattern=ISLAND, uncertain=uncertain, bars=bars,
                         bar_repeat=0.5 if uncertain else 0.9, no_instrument=False)
        )
    sections[0].bars[0] = ScoreBar(index=0, chords=[nc], pickup=True)
    # a mid-bar change and an N.C. bar in the bridge
    bridge = sections[6].bars
    bridge[3] = ScoreBar(
        index=bridge[3].index,
        chords=[
            ScoreChord(name="G", diagram=1, start_slot=0, slots=ISLAND[:4]),
            ScoreChord(name="F", diagram=3, start_slot=4, slots=ISLAND[4:]),
        ],
    )
    bridge[7] = ScoreBar(index=bridge[7].index, chords=[nc])
    # a passing B in the bridge and a filled (inferred) bar in the intro's short last row
    bridge[5] = ScoreBar(
        index=bridge[5].index,
        chords=[
            ScoreChord(name="F", diagram=3, start_slot=0, slots=ISLAND[:6]),
            ScoreChord(name="B", diagram=4, start_slot=6, slots=ISLAND[6:], passing=True),
        ],
    )
    intro = sections[0].bars
    intro[5] = ScoreBar(
        index=intro[5].index,
        chords=[ScoreChord(name="G", diagram=1, start_slot=0, slots=ISLAND, filled=True)],
    )
    diagrams.append(ChordDiagram(name="B", shape=B, passing=True))
    assert index == 120
    return Score(
        instrument=UKULELE.model_copy(update={"capo": 2}),
        title="Synthetic Song",
        artist="Test Band",
        key="D major",
        bpm=120.0,
        meter=Meter(numerator=4, denominator=4),
        tier="easy",
        slots_per_bar=8,
        strum_source="other_stem",
        strums_uncertain=False,
        chord_diagrams=diagrams,
        sections=sections,
    )


def _prepare(tmp_path: Path, score: Score | None = None) -> tuple[RunLayout, Path]:
    layout = RunLayout(
        tmp_path / "run",
        ["ingest", "separate", "grid", "harmony", "strums", "arrange", "score", "render"],
    )
    score_json = layout.path("score/score.json")
    score_json.parent.mkdir(parents=True)
    save_model(score_json, score or _two_section_score())
    out = tmp_path / "out"
    out.mkdir()
    return layout, out


def test_render_stage_writes_html_and_pdf_without_assets(tmp_path):
    layout, out = _prepare(tmp_path)
    calls: list[tuple[Path, Path]] = []

    def fake_pdf(html_path: Path, pdf_path: Path) -> None:
        calls.append((html_path, pdf_path))
        pdf_path.write_bytes(b"%PDF-fake")

    stage = RenderStage(pdf_writer=fake_pdf)
    ctx = StageContext(layout, RunOptions(source="x.mp3"), out, lambda m: None, stage)
    stage.run(ctx)

    html_path = out / "sheet.html"
    assert calls == [(html_path, out / "sheet.pdf")]
    assert (out / "sheet.pdf").read_bytes() == b"%PDF-fake"
    html = html_path.read_text(encoding="utf-8")
    assert ">C<" in html and ">G<" in html and ">N.C.<" in html
    assert html.count('class="bar"') == 4  # one box per bar
    assert "<script" not in html
    assert not (out / "assets").exists()
    assert sorted(p.name for p in out.iterdir()) == ["sheet.html", "sheet.pdf"]
    assert "assets" not in ctx.notes


def test_render_stage_needs_no_alphatex(tmp_path):
    layout, out = _prepare(tmp_path)
    assert not layout.path("score/score.alphatex").exists()
    stage = RenderStage(pdf_writer=lambda h, p: p.write_bytes(b"%PDF-fake"))
    stage.run(StageContext(layout, RunOptions(source="x.mp3"), out, lambda m: None, stage))
    assert (out / "sheet.html").is_file()


def test_render_stage_sheet_has_repeats_passing_line_filled_note_and_pickup(tmp_path):
    layout, out = _prepare(tmp_path, _realistic_120_bar_score())
    stage = RenderStage(pdf_writer=lambda h, p: p.write_bytes(b"%PDF-fake"))
    stage.run(StageContext(layout, RunOptions(source="x.mp3"), out, lambda m: None, stage))
    html = (out / "sheet.html").read_text(encoding="utf-8")
    assert "Passing: B 4322" in html
    assert "Italic chords were inferred where the recording had no clear chord" in html
    assert html.count('font-style="italic" fill="#111" class="chord"') == 1
    assert html.count('class="pickup-label"') == 1
    assert html.count("play twice") == 3  # each 16-bar C G Am F verse is one eight-bar line played twice
    assert "×" not in html


def test_render_stage_sheet_draws_every_bar_in_order(tmp_path):
    layout, out = _prepare(tmp_path, _realistic_120_bar_score())
    stage = RenderStage(pdf_writer=lambda h, p: p.write_bytes(b"%PDF-fake"))
    stage.run(StageContext(layout, RunOptions(source="x.mp3"), out, lambda m: None, stage))
    html = (out / "sheet.html").read_text(encoding="utf-8")
    # 120 bars less the three verses' folded second lines (8 bars each)
    assert html.count('class="bar"') == 120 - 3 * 8
    assert "worked-example" not in html and "strum-box" not in html
    # the bridge is two four-bar lines (bars change chord inside them): Am, G, F, G / F, then
    # Am, F / B, F, N.C.; the 1.5 score has no strokes, so its chords' slots are drawn
    bridge = html[html.index("<h2>Bridge</h2>"):]
    bridge = bridge[:bridge.index("</section>")]
    assert bridge.count('class="line"') == 2
    names = re.findall(r'class="chord[^"]*">([^<]*)<', bridge)
    assert names == ["Am", "G", "F", "G", "F", "Am", "F", "B", "F", "N.C."]
    assert 'class="arrow down"' in bridge
    # the uncertain pre-chorus prints greyed
    pre = html[html.index("<h2>Pre-chorus</h2>"):]
    pre = pre[:pre.index("</section>")]
    assert 'stroke="#999"' in pre and 'class="arrow down"' in pre


def test_a_1_6_score_renders_without_sustain_or_labels(tmp_path):
    fixture = load_model(Path(__file__).parent / "fixtures" / "v16_score.json", Score)
    layout, out = _prepare(tmp_path, fixture)
    stage = RenderStage(pdf_writer=lambda h, p: p.write_bytes(b"%PDF-fake"))
    stage.run(StageContext(layout, RunOptions(source="x.mp3"), out, lambda m: None, stage))
    html = (out / "sheet.html").read_text(encoding="utf-8")
    assert "<svg" in html and 'class="arrow' in html
    assert 'class="sustain"' not in html and 'class="chord label"' not in html


def test_render_stage_declares_contract():
    assert RenderStage.name == "render"
    assert RenderStage.requires == ("score/score.json",)
    assert RenderStage.produces == ("render/sheet.html", "render/sheet.pdf")


@pytest.mark.slow
def test_real_chromium_renders_pdf_from_two_bar_example(tmp_path):
    from youkelele.render import pdf as pdf_module

    layout, out = _prepare(tmp_path)
    errors: list[str] = []
    stage = RenderStage(pdf_writer=lambda h, p: pdf_module.html_to_pdf(h, p, console=errors))
    ctx = StageContext(layout, RunOptions(source="x.mp3"), out, lambda m: None, stage)
    stage.run(ctx)

    data = (out / "sheet.pdf").read_bytes()
    assert data.startswith(b"%PDF")
    assert count_pages(data) == 1
    assert errors == []


@pytest.mark.slow
def test_real_chromium_prints_120_bar_score_in_at_most_three_pages(tmp_path):
    from youkelele.render import pdf as pdf_module

    layout, out = _prepare(tmp_path, _realistic_120_bar_score())
    errors: list[str] = []
    stage = RenderStage(pdf_writer=lambda h, p: pdf_module.html_to_pdf(h, p, console=errors))
    ctx = StageContext(layout, RunOptions(source="x.mp3"), out, lambda m: None, stage)
    stage.run(ctx)

    data = (out / "sheet.pdf").read_bytes()
    assert data.startswith(b"%PDF")
    assert 1 <= count_pages(data) <= 3
    assert errors == []


def _long_score(rows: int) -> Score:
    """One certain section of `rows` distinct four-bar rows (one chord a bar), so no line folds
    into a repeat and the section is as long as its bar count."""
    names = ["C", "G", "Am", "F"]
    diagrams = [ChordDiagram(name=n, shape=s) for n, s in zip(names, (C, G, AM, F), strict=True)]
    bars: list[ScoreBar] = []
    for r in range(rows):
        # the row's first three chords spell r in base 4, so no two rows (and no two eight-bar
        # lines) match
        for k in range(4):
            name = names[(r // 4**k) % 4] if k < 3 else "C"
            chord = ScoreChord(name=name, diagram=names.index(name), start_slot=0, slots=ISLAND)
            bars.append(ScoreBar(index=len(bars), chords=[chord]))
    section = ScoreSection(
        label="Verse", pattern=ISLAND, uncertain=False, bars=bars, bar_repeat=0.9,
        no_instrument=False, explained=0.9,
    )
    return _two_section_score().model_copy(update={"chord_diagrams": diagrams, "sections": [section]})


# one page holds 20 such rows (80 bars on ten eight-bar lines) and two hold 50, probed with the
# bar-box renderer: 35 sits mid-way
ROWS_OVER_A_PAGE = 35


@pytest.mark.slow
def test_real_chromium_breaks_a_long_section_across_pages(tmp_path):
    from youkelele.render import pdf as pdf_module

    layout, out = _prepare(tmp_path, _long_score(ROWS_OVER_A_PAGE))
    errors: list[str] = []
    stage = RenderStage(pdf_writer=lambda h, p: pdf_module.html_to_pdf(h, p, console=errors))
    ctx = StageContext(layout, RunOptions(source="x.mp3"), out, lambda m: None, stage)
    stage.run(ctx)

    html = (out / "sheet.html").read_text(encoding="utf-8")
    assert html.count("<h2>") == 1 and html.count('class="line"') == 18  # 140 bars, eight a line
    assert count_pages((out / "sheet.pdf").read_bytes()) == 2
    assert errors == []
