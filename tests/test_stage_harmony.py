from __future__ import annotations

import numpy as np
import pytest
import soundfile as sf

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


HARMONIC_STEMS = ("guitar", "bass", "piano", "other")


def _write_silence(path, seconds, sr=44100):
    sf.write(str(path), np.zeros((int(seconds * sr), 1), dtype=np.float32), sr, subtype="PCM_16")


def _ctx(tmp_path, stage, n_bars, bar_seconds, write_audio, write_stems=None):
    layout = RunLayout(tmp_path / "run", ["ingest", "separate", "grid", "harmony"])
    audio = layout.path("ingest/audio.wav")
    audio.parent.mkdir(parents=True)
    write_audio(audio)
    for stem in HARMONIC_STEMS:
        path = layout.path(f"separate/stems/{stem}.wav")
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_silence(path, n_bars * bar_seconds)
    if write_stems is not None:
        write_stems(lambda stem: layout.path(f"separate/stems/{stem}.wav"))
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


def test_harmony_stage_requires_harmonic_stems_and_fills(tmp_path):
    assert {f"separate/stems/{s}.wav" for s in HARMONIC_STEMS} <= set(HarmonyStage.requires)
    spans = [
        LabelSpan(0.0, 2.0, "C:maj"),
        LabelSpan(2.0, 4.0, "G:maj"),
        LabelSpan(6.0, 8.0, "G:maj"),
    ]
    stage = HarmonyStage(
        recogniser=lambda wav, work_dir, log=print: spans,
        chroma=lambda wav: np.eye(12)[0] + 0.1,
    )

    def guitar(stem_path):
        write_chord_loop(stem_path("guitar"), ["C:maj", "G:maj", "C:maj", "G:maj"], 2.0)

    ctx, out = _ctx(
        tmp_path, stage, 4, 2.0, lambda p: write_chord_loop(p, ["C:maj"], 2.0, bars=4), guitar
    )
    stage.run(ctx)
    chords = load_model(ctx.output("harmony/chords.json"), Chords)
    assert [(e.bar, e.label, e.filled) for e in chords.events] == [
        (0, "C:maj", False),
        (1, "G:maj", False),
        (2, "C:maj", True),
        (3, "G:maj", False),
    ]
    assert ctx.notes["filled"] == "1"
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


def test_recognise_chords_failure_includes_stderr(tmp_path, monkeypatch):
    import subprocess

    from youkelele.models import chords

    def fake_run(argv, **kwargs):
        return subprocess.CompletedProcess(argv, 3, stdout="", stderr="Traceback\nValueError: bad model\n")

    monkeypatch.setattr(chords.subprocess, "run", fake_run)
    logged: list[str] = []
    with pytest.raises(RuntimeError, match="code 3") as info:
        chords.recognise_chords(tmp_path / "a.wav", tmp_path, logged.append)
    assert "ValueError: bad model" in str(info.value)
    assert "ValueError: bad model" in logged


def test_recognise_chords_passes_absolute_paths_to_child(tmp_path, monkeypatch):
    import subprocess
    from pathlib import Path

    from youkelele.models import chords

    monkeypatch.chdir(tmp_path)
    wav = Path("runs/x/00_ingest/audio.wav")
    wav.parent.mkdir(parents=True)
    wav.write_bytes(b"")
    work_dir = Path("runs/x/03_harmony")
    work_dir.mkdir(parents=True)
    (work_dir / "out.lab").write_text("0.0\t1.0\tC:maj\n", encoding="utf-8")
    seen: list[list[str]] = []

    def fake_run(argv, **kwargs):
        seen.append(list(argv))
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    monkeypatch.setattr(chords.subprocess, "run", fake_run)
    spans = chords.recognise_chords(wav, work_dir, lambda m: None)
    assert [s.label for s in spans] == ["C:maj"]
    wav_arg, lab_arg = Path(seen[0][2]), Path(seen[0][3])
    assert wav_arg.is_absolute() and lab_arg.is_absolute()
    assert wav_arg == (tmp_path / wav).resolve()
    assert lab_arg == (tmp_path / work_dir / "out.lab").resolve()
