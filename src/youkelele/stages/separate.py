"""Stage 2: split the audio into six stems with Demucs htdemucs_6s."""

from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path

from youkelele.models.separator import MODEL, STEMS, separate_stems
from youkelele.stage import Stage, StageContext


class SeparateStage(Stage):
    name = "separate"
    requires = ("ingest/audio.wav",)
    produces = tuple(f"separate/stems/{s}.wav" for s in STEMS)

    def __init__(
        self,
        separator: Callable[..., dict[str, Path]] = separate_stems,
    ) -> None:
        self._separator = separator

    def run(self, ctx: StageContext) -> None:
        wav = ctx.input("ingest/audio.wav")
        out_dir = ctx.output("separate/stems/guitar.wav").parent
        stems = self._separator(wav, out_dir, log=ctx.log)
        for stem in STEMS:
            target = ctx.output(f"separate/stems/{stem}.wav")
            found = Path(stems[stem])
            if found != target:
                shutil.move(str(found), str(target))
        ctx.note("model", MODEL)
        ctx.note("licence", "MIT (Demucs repository; no separate weight statement)")
