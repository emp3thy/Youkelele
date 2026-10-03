"""Arrange stage (ukulele profile): capo, simplification and one chord shape per label."""

from __future__ import annotations

from statistics import median

from youkelele.jsonio import load_model, save_model
from youkelele.music.arrange import (
    choose_capo,
    passing_labels,
    select_voicings,
    simplify_for_tier,
    transpose_label,
)
from youkelele.music.shapes import ShapeDB, display_name_for
from youkelele.schemas import ArrangedChord, Arrangement, Chords, Grid, Substitution
from youkelele.stage import Stage, StageContext

_BLANK = ("N", "X")


def _bar_seconds(grid: Grid) -> float:
    """Median length of the full bars (all bars if every one is a pickup)."""
    bars = [b for b in grid.bars if not b.pickup] or grid.bars
    return float(median(b.end - b.start for b in bars)) if bars else 0.0


class ArrangeStage(Stage):
    name = "arrange"
    requires = ("harmony/chords.json", "grid/grid.json")
    produces = ("arrange/arrangement.json",)

    def run(self, ctx: StageContext) -> None:
        chords = load_model(ctx.input("harmony/chords.json"), Chords)
        grid = load_model(ctx.input("grid/grid.json"), Grid)
        tier = ctx.options.tier
        db = ShapeDB.load()

        labels: list[str] = []
        substitutions: list[Substitution] = []
        for i, event in enumerate(chords.events):
            chosen, reason = simplify_for_tier(event.label, tier, db)
            labels.append(chosen)
            if reason is not None:
                substitutions.append(
                    Substitution(event=i, original=event.label, chosen=chosen, reason=reason)
                )

        # judged on the labels as played (after tier simplification) but before the capo moves them
        passing = passing_labels(
            [e.model_copy(update={"label": label}) for e, label in zip(chords.events, labels)],
            _bar_seconds(grid),
        )

        real = [label for label in labels if label not in _BLANK]
        capo, transpose = choose_capo(real, db)
        played = [label if label in _BLANK else transpose_label(label, transpose) for label in labels]
        played_shapes = select_voicings(played, db)
        arranged = [
            ArrangedChord(
                event=i, name=display_name_for(label, db), shape=played_shapes[label],
                passing=labels[i] in passing,
            )
            for i, label in enumerate(played)
            if label not in _BLANK
        ]

        no_capo: list[ArrangedChord] = []
        if capo > 0:
            open_shapes = select_voicings(real, db)
            no_capo = [
                ArrangedChord(
                    event=i, name=display_name_for(label, db), shape=open_shapes[label],
                    passing=label in passing,
                )
                for i, label in enumerate(labels)
                if label not in _BLANK
            ]

        save_model(
            ctx.output("arrange/arrangement.json"),
            Arrangement(
                capo=capo, transpose=transpose, tier=tier, chords=arranged,
                substitutions=substitutions, no_capo_alternative=no_capo,
            ),
        )
        ctx.note("capo", str(capo))
        ctx.note("tier", tier)
