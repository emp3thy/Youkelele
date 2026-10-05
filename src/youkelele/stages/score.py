"""Score stage: merge grid, chords, strums and arrangement into score.json and alphaTex."""

from __future__ import annotations

from youkelele.jsonio import load_model, save_model
from youkelele.music.alphatex import score_to_alphatex
from youkelele.music.score_builder import build_score
from youkelele.profiles.base import Tuning
from youkelele.schemas import Arrangement, Chords, Grid, SourceInfo, Strums
from youkelele.stage import Stage, StageContext


class ScoreStage(Stage):
    name = "score"
    requires = (
        "grid/grid.json",
        "harmony/chords.json",
        "strums/strums.json",
        "arrange/arrangement.json",
        "riff/riff.json",
        "ingest/source.json",
    )
    produces = ("score/score.json", "score/score.alphatex")

    def __init__(self, tuning: Tuning, instrument_name: str) -> None:
        self.tuning = tuning
        self.instrument_name = instrument_name

    def run(self, ctx: StageContext) -> None:
        score = build_score(
            load_model(ctx.input("ingest/source.json"), SourceInfo),
            load_model(ctx.input("grid/grid.json"), Grid),
            load_model(ctx.input("harmony/chords.json"), Chords),
            load_model(ctx.input("strums/strums.json"), Strums),
            load_model(ctx.input("arrange/arrangement.json"), Arrangement),
            self.tuning,
            self.instrument_name,
        )
        save_model(ctx.output("score/score.json"), score)
        ctx.output("score/score.alphatex").write_text(score_to_alphatex(score), encoding="utf-8")
        ctx.note("bars", str(sum(len(s.bars) for s in score.sections)))
