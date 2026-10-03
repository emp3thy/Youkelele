"""Render stage: write the sheet page (with its alphaTab assets) and print it to PDF."""

from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path

from youkelele.jsonio import load_model
from youkelele.paths import vendor_dir
from youkelele.render.html import render_html
from youkelele.render.pdf import html_to_pdf
from youkelele.schemas import Score
from youkelele.stage import Stage, StageContext

ALPHATAB_VERSION = "1.8.4"


class RenderStage(Stage):
    name = "render"
    requires = ("score/score.json", "score/score.alphatex")
    produces = ("render/sheet.html", "render/sheet.pdf")

    def __init__(self, pdf_writer: Callable[[Path, Path], None] = html_to_pdf) -> None:
        self.pdf_writer = pdf_writer

    def run(self, ctx: StageContext) -> None:
        score = load_model(ctx.input("score/score.json"), Score)
        alphatex = ctx.input("score/score.alphatex").read_text(encoding="utf-8")
        html_path = ctx.output("render/sheet.html")
        shutil.copytree(vendor_dir("alphatab"), html_path.parent / "assets", dirs_exist_ok=True)
        ctx.note("assets", f"alphatab {ALPHATAB_VERSION}")
        html_path.write_text(render_html(score, alphatex, assets_rel="assets"), encoding="utf-8")
        self.pdf_writer(html_path, ctx.output("render/sheet.pdf"))
