"""Stage 4: chord labels snapped to the beat grid, reduced to triads, plus the key.

No-chord bars where the harmonic stems clearly play one of the song's own chords are
then filled with that chord (`filled: true`); see `music/fill.py`.
"""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Callable
from pathlib import Path

import numpy as np
import soundfile as sf

from youkelele.jsonio import load_model, save_model
from youkelele.models.chords import LabelSpan, beat_positions, recognise_chords
from youkelele.music.fill import bar_chroma, bar_energy, fill_silent_bars
from youkelele.music.key import chroma_mean_for, estimate_key
from youkelele.music.snap import snap_to_beats
from youkelele.schemas import Chords, Grid
from youkelele.stage import Stage, StageContext
from youkelele.vendoring import CHORD_MODEL_CHECKPOINT_SHA256, CHORD_MODEL_COMMIT

HARMONIC_STEMS = ("guitar", "bass", "piano", "other")


def harmonic_mix(paths: list[Path]) -> tuple[np.ndarray, int]:
    """Sum the stems to one mono signal (shorter stems padded with silence)."""
    signals: list[np.ndarray] = []
    rate: int | None = None
    for path in paths:
        data, sr = sf.read(str(path), dtype="float32", always_2d=True)
        if rate is not None and sr != rate:
            raise ValueError(f"{path.name} is {sr} Hz but the other stems are {rate} Hz")
        rate = sr
        signals.append(data.mean(axis=1))
    mix = np.zeros(max(len(s) for s in signals), dtype=np.float32)
    for signal in signals:
        mix[: len(signal)] += signal
    return mix, int(rate)


class HarmonyStage(Stage):
    name = "harmony"
    requires = (
        "ingest/audio.wav",
        "grid/grid.json",
        *(f"separate/stems/{stem}.wav" for stem in HARMONIC_STEMS),
    )
    produces = ("harmony/chords.json", "harmony/spans.lab")

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
        stems = [ctx.input(f"separate/stems/{s}.wav") for s in HARMONIC_STEMS]
        out = ctx.output("harmony/chords.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        beats = beat_positions(grid)
        work_dir = Path(tempfile.mkdtemp(dir=out.parent, prefix="work-"))
        try:
            spans = self._recogniser(wav, work_dir, ctx.log, beats=beats)
            shutil.copyfile(work_dir / "out.lab", ctx.output("harmony/spans.lab"))  # the raw model output
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)
        events = snap_to_beats(spans, grid)
        mix, sr = harmonic_mix(stems)
        events = fill_silent_bars(
            events, grid.bars, bar_chroma(mix, sr, grid.bars), bar_energy(mix, sr, grid.bars)
        )
        filled = sum(e.filled for e in events)
        chorded = sum(e.label != "N" and not e.filled for e in events)
        key = estimate_key(self._chroma(wav))
        ctx.log(f"  {chorded} chord events, key {key.tonic} {key.mode}")
        ctx.log(f"  {filled} bars filled")
        save_model(out, Chords(key=key, events=events))
        ctx.note("model", f"chord_cnn_lstm@{CHORD_MODEL_COMMIT}")
        prefixes = ",".join(h[:8] for h in CHORD_MODEL_CHECKPOINT_SHA256.values())
        ctx.note("checkpoints", prefixes)
        ctx.note("filled", str(filled))
        ctx.note("decoding", "beats+downbeats" if beats else "plain")
