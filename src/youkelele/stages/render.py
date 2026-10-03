"""Render stage: write the chord-grid sheet page and print it to PDF."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from youkelele.jsonio import load_model
from youkelele.render.html import render_html
from youkelele.render.pdf import html_to_pdf
from youkelele.schemas import Score
from youkelele.stage import Stage, StageContext


class RenderStage(Stage):
    name = "render"
    requires = ("score/score.json",)
    produces = ("render/sheet.html", "render/sheet.pdf")

    def __init__(self, pdf_writer: Callable[[Path, Path], None] = html_to_pdf) -> None:
        self.pdf_writer = pdf_writer

    def run(self, ctx: StageContext) -> None:
        score = load_model(ctx.input("score/score.json"), Score)
        html_path = ctx.output("render/sheet.html")
        html_path.write_text(render_html(score), encoding="utf-8")
        self.pdf_writer(html_path, ctx.output("render/sheet.pdf"))
