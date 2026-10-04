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


def _recogniser(spans, seen=None):
    """A fake recogniser that writes out.lab into work_dir, as the real one does."""
    seen = [] if seen is None else seen

    def recognise(wav, work_dir, log=print, beats=None):
        seen.append(beats)
        (work_dir / "out.lab").write_text(
            "".join(f"{s.start}\t{s.end}\t{s.label}\n" for s in spans), encoding="utf-8"
        )
        return spans

    return recognise


def test_harmony_stage_writes_chords_with_triads(tmp_path):
    labels = ["C:maj", "G:maj7", "A:min7", "F:maj"]
    spans = [LabelSpan(i * 2.0, (i + 1) * 2.0, lab) for i, lab in enumerate(labels)]
    stage = HarmonyStage(
        recogniser=_recogniser(spans),
        chroma=lambda wav: np.eye(12)[0] + 0.1,
    )
    ctx, out = _ctx(tmp_path, stage, 4, 2.0, lambda p: write_chord_loop(p, ["C:maj"], 2.0, bars=4))
    stage.run(ctx)
    chords = load_model(ctx.output("harmony/chords.json"), Chords)
    assert [e.triad for e in chords.events] == ["C:maj", "G:maj", "A:min", "F:maj"]
    assert chords.key.tonic
    assert sorted(p.name for p in out.rglob("*") if p.is_file()) == ["chords.json", "spans.lab"]


def test_harmony_stage_passes_beats_and_notes_decoding(tmp_path):
    seen: list = []
    spans = [LabelSpan(0.0, 2.0, "C:maj"), LabelSpan(2.0, 4.0, "G:maj")]
    stage = HarmonyStage(recogniser=_recogniser(spans, seen), chroma=lambda wav: np.eye(12)[0] + 0.1)
    ctx, out = _ctx(tmp_path, stage, 2, 2.0, lambda p: write_chord_loop(p, ["C:maj"], 2.0, bars=2))
    stage.run(ctx)
    assert len(seen) == 1
    assert seen[0] == [(i * 0.5, i % 4 + 1) for i in range(8)]
    assert ctx.notes["decoding"] == "beats+downbeats"


def test_harmony_stage_notes_plain_decoding_without_beats(tmp_path, monkeypatch):
    from youkelele.stages import harmony

    monkeypatch.setattr(harmony, "beat_positions", lambda grid: [])
    spans = [LabelSpan(0.0, 2.0, "C:maj")]
    stage = HarmonyStage(recogniser=_recogniser(spans), chroma=lambda wav: np.eye(12)[0] + 0.1)
    ctx, out = _ctx(tmp_path, stage, 1, 2.0, lambda p: write_chord_loop(p, ["C:maj"], 2.0, bars=1))
    stage.run(ctx)
    assert ctx.notes["decoding"] == "plain"


def test_harmony_stage_keeps_raw_spans(tmp_path):
    from youkelele.models.chords import parse_lab

    spans = [LabelSpan(0.0, 2.0, "C:maj7"), LabelSpan(2.0, 4.0, "G:maj"), LabelSpan(4.0, 6.0, "N")]
    stage = HarmonyStage(recogniser=_recogniser(spans), chroma=lambda wav: np.eye(12)[0] + 0.1)
    ctx, out = _ctx(tmp_path, stage, 3, 2.0, lambda p: write_chord_loop(p, ["C:maj"], 2.0, bars=3))
    stage.run(ctx)
    assert "harmony/spans.lab" in HarmonyStage.produces
    assert parse_lab(ctx.output("harmony/spans.lab")) == spans
    assert not list(out.rglob("work-*"))


def test_harmony_stage_requires_harmonic_stems_and_fills(tmp_path):
    assert {f"separate/stems/{s}.wav" for s in HARMONIC_STEMS} <= set(HarmonyStage.requires)
    spans = [
        LabelSpan(0.0, 2.0, "C:maj"),
        LabelSpan(2.0, 4.0, "G:maj"),
        LabelSpan(6.0, 8.0, "G:maj"),
    ]
    stage = HarmonyStage(
        recogniser=_recogniser(spans),
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
    assert sorted(p.name for p in out.rglob("*") if p.is_file()) == ["chords.json", "spans.lab"]


def test_harmony_stage_key_from_chords_and_notes(tmp_path):
    labels = ["D:maj", "G:maj", "A:maj", "D:maj", "B:min", "G:maj", "A:maj", "D:maj"]
    spans = [LabelSpan(i * 2.0, (i + 1) * 2.0, lab) for i, lab in enumerate(labels)]
    logged: list[str] = []
    stage = HarmonyStage(
        recogniser=_recogniser(spans),
        chroma=lambda wav: np.eye(12)[0] + 0.1,  # the mix estimate points away from D
    )

    def guitar(stem_path):
        write_chord_loop(stem_path("guitar"), labels, 2.0)

    ctx, out = _ctx(
        tmp_path, stage, 8, 2.0, lambda p: write_chord_loop(p, labels, 2.0), guitar
    )
    ctx.log = logged.append
    stage.run(ctx)
    key = load_model(ctx.output("harmony/chords.json"), Chords).key
    assert (key.tonic, key.mode, key.method) == ("D", "major", "chords_stems")
    assert key.mix is not None and key.mix.tonic != "D"
    assert key.runner_up is not None and key.margin is not None and key.mode_margin > 0.05
    assert key.confidence == key.mode_margin
    assert ctx.notes["key_method"] == "chords_stems"
    assert ctx.notes["key_margin"] == f"{key.margin:.3f}"
    assert ctx.notes["tonic_pair_rule"].startswith("D by ")
    assert any("key D major (or" in line and "chords+stems, margin" in line for line in logged)


def test_harmony_stage_key_falls_back_to_the_mix_with_few_chords(tmp_path):
    spans = [LabelSpan(0.0, 2.0, "C:maj"), LabelSpan(2.0, 4.0, "G:maj")]
    stage = HarmonyStage(recogniser=_recogniser(spans), chroma=lambda wav: np.eye(12)[0] + 0.1)
    ctx, out = _ctx(tmp_path, stage, 2, 2.0, lambda p: write_chord_loop(p, ["C:maj"], 2.0, bars=2))
    stage.run(ctx)
    key = load_model(ctx.output("harmony/chords.json"), Chords).key
    assert key.method == "mix_krumhansl" and key.margin is None and key.mix is None
    assert ctx.notes["key_method"] == "mix_krumhansl"
    assert ctx.notes["tonic_pair_rule"] == "none"


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
    assert sorted(p.name for p in out.rglob("*") if p.is_file()) == ["chords.json", "spans.lab"]


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
