from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from tests.audio_fixtures import write_chord_loop, write_click_track
from youkelele.jsonio import load_model
from youkelele.layout import RunLayout
from youkelele.models.beats import BeatResult
from youkelele.options import RunOptions
from youkelele.schemas import Grid
from youkelele.stage import StageContext
from youkelele.stages.grid import GridStage


def _fake_detector(period: float, beats_per_bar: int, seconds: float):
    def detect(wav: Path) -> BeatResult:
        beats = [round(i * period, 6) for i in range(int(seconds / period))]
        return BeatResult(beats=beats, downbeats=beats[::beats_per_bar])

    return detect


def _ctx(tmp_path: Path, stage: GridStage, options: RunOptions, write_audio) -> tuple[StageContext, list[str]]:
    layout = RunLayout(tmp_path / "run", ["ingest", "separate", "grid"])
    audio = layout.path("ingest/audio.wav")
    audio.parent.mkdir(parents=True)
    write_audio(audio)
    out = tmp_path / "out"
    out.mkdir()
    messages: list[str] = []
    return StageContext(layout, options, out, messages.append, stage), messages


def test_grid_stage_writes_valid_grid_with_fake_detector(tmp_path):
    stage = GridStage(detector=_fake_detector(0.5, 3, 24.0))
    options = RunOptions(source="x.mp3", meter="3/4")
    ctx, messages = _ctx(tmp_path, stage, options, lambda p: write_click_track(p, 24.0, 120))
    stage.run(ctx)
    grid = load_model(ctx.output("grid/grid.json"), Grid)
    assert grid.bpm == pytest.approx(120)
    assert grid.meter.numerator == 3
    assert grid.octave_decision == "none"
    assert len(grid.bars) == 16
    assert all(len(bar.beats) == 3 for bar in grid.bars)
    assert np.median([b.end - b.start for b in grid.bars]) == pytest.approx(1.5)
    assert grid.bars[-1].end == pytest.approx(24.0)
    assert len(grid.bar_loudness_db) == 16
    assert grid.sections[0].start_bar == 0 and grid.sections[-1].end_bar == 16
    assert 1 <= grid.sections_k <= 6
    log = "\n".join(messages)
    assert "median bar 1.50 s" in log
    assert "octave none" in log


def test_grid_stage_sections_k_override(tmp_path):
    stage = GridStage(detector=_fake_detector(0.5, 4, 32.0))
    options = RunOptions(source="x.mp3", sections_k=2)
    labels = ["C"] * 4 + ["F#"] * 4

    def audio(path: Path) -> None:
        write_chord_loop(path, labels, 2.0, bars=16)

    ctx, _ = _ctx(tmp_path, stage, options, audio)
    stage.run(ctx)
    grid = load_model(ctx.output("grid/grid.json"), Grid)
    assert grid.sections_k == 2
    assert len(grid.bars) == 16
    assert grid.largest_cluster_share == pytest.approx(0.5)


def test_grid_stage_halves_a_double_tempo_detection(tmp_path):
    # 240 bpm detection; auto would keep it (120 is outside 60..95), so halve explicitly
    stage = GridStage(detector=_fake_detector(0.25, 8, 24.0))
    options = RunOptions(source="x.mp3", beat_octave="half")
    ctx, messages = _ctx(tmp_path, stage, options, lambda p: write_click_track(p, 24.0, 120))
    stage.run(ctx)
    grid = load_model(ctx.output("grid/grid.json"), Grid)
    assert grid.octave_decision == "half"
    assert grid.bpm == pytest.approx(120)
    assert "octave half" in "\n".join(messages)


@pytest.mark.slow
def test_grid_stage_real_beat_this_on_click_track(tmp_path):
    stage = GridStage()
    options = RunOptions(source="x.mp3")
    ctx, _ = _ctx(tmp_path, stage, options, lambda p: write_click_track(p, 20.0, 120))
    stage.run(ctx)
    grid = load_model(ctx.output("grid/grid.json"), Grid)
    assert 118 <= grid.bpm <= 122
