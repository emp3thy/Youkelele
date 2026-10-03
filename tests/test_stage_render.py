from __future__ import annotations

from pathlib import Path

import pytest

from youkelele.jsonio import save_model
from youkelele.layout import RunLayout
from youkelele.music.alphatex import score_to_alphatex
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
ISLAND = list("D-DU-UDU")


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
        instrument=Instrument(name="Ukulele", strings=4, tuning=["G4", "C4", "E4", "A4"], capo=0),
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


def _prepare(tmp_path: Path) -> tuple[RunLayout, Path]:
    layout = RunLayout(
        tmp_path / "run",
        ["ingest", "separate", "grid", "harmony", "strums", "arrange", "score", "render"],
    )
    score = _two_section_score()
    score_json = layout.path("score/score.json")
    score_json.parent.mkdir(parents=True)
    save_model(score_json, score)
    layout.path("score/score.alphatex").write_text(score_to_alphatex(score), encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    return layout, out


def test_render_stage_writes_html_and_calls_pdf_writer(tmp_path):
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
    assert 'data-start-bar="3"' in html
    assert layout.path("score/score.alphatex").read_text(encoding="utf-8") in html
    assert (out / "assets" / "alphaTab.min.js").is_file()
    assert (out / "assets" / "font" / "Bravura.woff2").is_file()
    assert (out / "assets" / "LICENSE").is_file()
    assert ctx.notes["assets"] == "alphatab 1.8.4"


def test_render_stage_declares_contract():
    assert RenderStage.name == "render"
    assert RenderStage.requires == ("score/score.json", "score/score.alphatex")
    assert RenderStage.produces == ("render/sheet.html", "render/sheet.pdf")


@pytest.mark.slow
def test_real_chromium_renders_pdf_from_two_bar_example(tmp_path):
    from youkelele.render import pdf as pdf_module

    layout, out = _prepare(tmp_path)
    errors: list[str] = []
    stage = RenderStage(pdf_writer=lambda h, p: pdf_module.html_to_pdf(h, p, console=errors))
    ctx = StageContext(layout, RunOptions(source="x.mp3"), out, lambda m: None, stage)
    stage.run(ctx)

    pdf_path = out / "sheet.pdf"
    assert pdf_path.is_file()
    assert pdf_path.stat().st_size > 10 * 1024
    assert pdf_path.read_bytes().startswith(b"%PDF")
    assert not [e for e in errors if "alphatab" in e.lower()], errors
