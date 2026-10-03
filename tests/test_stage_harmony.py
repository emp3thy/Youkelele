from __future__ import annotations

import numpy as np
import pytest

from tests.audio_fixtures import write_chord_loop
from youkelele.jsonio import load_model, save_model
from youkelele.layout import RunLayout
from youkelele.models.chords import LabelSpan
from youkelele.options import RunOptions
from youkelele.schemas import Bar, Chords, Grid, Meter, Section
from youkelele.stage import StageContext
from youkelele.stages.harmony import HarmonyStage


def _grid(n_bars: int, bar_seconds: float) -> Grid:
    beat = bar_seconds / 4
    beats = [i * beat for i in range(n_bars * 4)]
    bars = [
        Bar(index=i, start=i * bar_seconds, end=(i + 1) * bar_seconds, beats=list(range(4 * i, 4 * i + 4)))
        for i in range(n_bars)
    ]
    return Grid(
        bpm=60 / beat, meter=Meter(numerator=4, denominator=4), beats=beats,
        downbeats=[4 * i for i in range(n_bars)], bars=bars,
        sections=[Section(label="verse", start_bar=0, end_bar=n_bars, confidence=1.0)],
        octave_decision="none", bar_loudness_db=[-20.0] * n_bars, sections_k=1,
        largest_cluster_share=1.0, chorus_margin_db=None, labels_low_confidence=False,
    )


def _ctx(tmp_path, stage, n_bars, bar_seconds, write_audio):
    layout = RunLayout(tmp_path / "run", ["ingest", "separate", "grid", "harmony"])
    audio = layout.path("ingest/audio.wav")
    audio.parent.mkdir(parents=True)
    write_audio(audio)
    grid_path = layout.path("grid/grid.json")
    grid_path.parent.mkdir(parents=True)
    save_model(grid_path, _grid(n_bars, bar_seconds))
    out = tmp_path / "out"
    out.mkdir()
    ctx = StageContext(layout, RunOptions(source="x.mp3"), out, lambda m: None, stage)
    return ctx, out


def test_harmony_stage_writes_chords_with_triads(tmp_path):
    labels = ["C:maj", "G:maj7", "A:min7", "F:maj"]
    spans = [LabelSpan(i * 2.0, (i + 1) * 2.0, lab) for i, lab in enumerate(labels)]
    stage = HarmonyStage(
        recogniser=lambda wav, work_dir, log=print: spans,
        chroma=lambda wav: np.eye(12)[0] + 0.1,
    )
    ctx, out = _ctx(tmp_path, stage, 4, 2.0, lambda p: write_chord_loop(p, ["C:maj"], 2.0, bars=4))
    stage.run(ctx)
    chords = load_model(ctx.output("harmony/chords.json"), Chords)
    assert [e.triad for e in chords.events] == ["C:maj", "G:maj", "A:min", "F:maj"]
    assert chords.key.tonic
    assert [p.name for p in out.rglob("*") if p.is_file()] == ["chords.json"]


@pytest.mark.slow
def test_harmony_real_model_on_synthetic_loop(tmp_path):
    from youkelele.vendoring import chord_model_ready

    if not chord_model_ready():
        pytest.skip("chord model not installed")
    stage = HarmonyStage()
    ctx, out = _ctx(
        tmp_path, stage, 8, 2.0,
        lambda p: write_chord_loop(p, ["C:maj", "G:maj", "A:min", "F:maj"], 2.0, bars=8),
    )
    stage.run(ctx)
    chords = load_model(ctx.output("harmony/chords.json"), Chords)
    assert {"C:maj", "G:maj", "A:min", "F:maj"} <= {e.triad for e in chords.events}
    assert [p.name for p in out.rglob("*") if p.is_file()] == ["chords.json"]
