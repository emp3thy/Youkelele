"""Stage 4: chord labels snapped to the beat grid, reduced to triads, plus the key."""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Callable
from pathlib import Path

import numpy as np

from youkelele.jsonio import load_model, save_model
from youkelele.models.chords import LabelSpan, recognise_chords
from youkelele.music.key import chroma_mean_for, estimate_key
from youkelele.music.snap import snap_to_beats
from youkelele.schemas import Chords, Grid
from youkelele.stage import Stage, StageContext
from youkelele.vendoring import CHORD_MODEL_CHECKPOINT_SHA256, CHORD_MODEL_COMMIT


class HarmonyStage(Stage):
    name = "harmony"
    requires = ("ingest/audio.wav", "grid/grid.json")
    produces = ("harmony/chords.json",)

    def __init__(
        self,
        recogniser: Callable[..., list[LabelSpan]] = recognise_chords,
        chroma: Callable[[Path], np.ndarray] = chroma_mean_for,
    ) -> None:
        self._recogniser = recogniser
        self._chroma = chroma

    def run(self, ctx: StageContext) -> None:
        wav = ctx.input("ingest/audio.wav")
        grid = load_model(ctx.input("grid/grid.json"), Grid)
        out = ctx.output("harmony/chords.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        work_dir = Path(tempfile.mkdtemp(dir=out.parent, prefix="work-"))
        try:
            spans = self._recogniser(wav, work_dir, ctx.log)
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)
        events = snap_to_beats(spans, grid)
        key = estimate_key(self._chroma(wav))
        ctx.log(f"  {len(events)} chord events, key {key.tonic} {key.mode}")
        save_model(out, Chords(key=key, events=events))
        ctx.note("model", f"chord_cnn_lstm@{CHORD_MODEL_COMMIT}")
        prefixes = ",".join(h[:8] for h in CHORD_MODEL_CHECKPOINT_SHA256.values())
        ctx.note("checkpoints", prefixes)
