"""Render a Score and its alphaTex into a self-contained sheet page."""

from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from markupsafe import Markup

from youkelele.render.diagrams import chord_diagram_svg
from youkelele.render.strum_box import strum_pattern_svg
from youkelele.schemas import Score

_ENV = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=True,
    undefined=StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True,
)


def _capo(capo: int) -> str:
    return "none" if capo <= 0 else f"fret {capo}"


def render_html(score: Score, alphatex: str, assets_rel: str = "assets") -> str:
    labels = [p[0].upper() for p in score.instrument.tuning]
    diagrams = [
        Markup(chord_diagram_svg(d.name, d.shape, string_labels=labels)) for d in score.chord_diagrams
    ]
    sections = []
    start = 1
    for section in score.sections:
        count = len(section.bars)
        source = section.inherited_from
        inherited = (
            score.sections[source].label
            if source is not None and 0 <= source < len(score.sections)
            else None
        )
        sections.append(
            {
                "label": section.label,
                "uncertain": section.uncertain,
                "no_instrument": section.no_instrument,
                "repeat": f"{section.bar_repeat:.0%}",
                "inherited_from": inherited,
                "svg": Markup(strum_pattern_svg(section.pattern, score.meter)),
                "start_bar": start,
                "bar_count": count,
            }
        )
        start += count
    return _ENV.get_template("sheet.html.j2").render(
        score=score,
        capo=_capo(score.instrument.capo),
        tempo=round(score.bpm),
        tuning=" ".join(score.instrument.tuning),
        diagrams=diagrams,
        sections=sections,
        # The alphaTex carries untrusted title/artist text, so it is embedded as a JSON string in
        # <script type="application/json">; escaping every "<" as < means no "</script" or
        # "<!--" can appear inside the block, and JSON.parse restores the exact text.
        tex_json=Markup(json.dumps(alphatex).replace("<", "\\u003c")),
        assets_rel=assets_rel,
        font_directory=Markup(json.dumps(assets_rel + "/font/")),
        scale=0.75 if score.slots_per_bar == 16 else 0.85,
    )
