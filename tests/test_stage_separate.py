from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest
import soundfile as sf

from tests.audio_fixtures import write_chord_loop
from youkelele.layout import RunLayout
from youkelele.models.separator import STEMS, map_stem_filename, separate_stems
from youkelele.options import RunOptions
from youkelele.stage import StageContext
from youkelele.stages.separate import SeparateStage


def _fake_separator(wav: Path, out_dir: Path, **_kwargs) -> dict[str, Path]:
    result = {}
    for stem in STEMS:
        path = out_dir / f"{stem}.wav"
        path.write_bytes(b"RIFF")
        result[stem] = path
    return result


def _ctx(tmp_path: Path, stage: SeparateStage) -> StageContext:
    layout = RunLayout(tmp_path / "run", ["ingest", "separate"])
    audio = layout.path("ingest/audio.wav")
    audio.parent.mkdir(parents=True)
    audio.write_bytes(b"RIFF")
    out = tmp_path / "out"
    out.mkdir()
    return StageContext(layout, RunOptions(source="x.mp3"), out, lambda _m: None, stage)


def test_separate_stage_writes_six_named_stems(tmp_path):
    stage = SeparateStage(separator=_fake_separator)
    ctx = _ctx(tmp_path, stage)
    stage.run(ctx)
    for key in stage.produces:
        assert ctx.output(key).exists()
    assert len(stage.produces) == 6
    assert ctx.notes["model"] == "htdemucs_6s.yaml"
    assert ctx.notes["licence"].startswith("MIT")


def test_separate_stage_renames_files_not_at_plain_name(tmp_path):
    def odd(wav: Path, out_dir: Path, **_k) -> dict[str, Path]:
        result = {}
        for stem in STEMS:
            path = out_dir / f"weird_{stem}.wav"
            path.write_bytes(b"RIFF")
            result[stem] = path
        return result

    stage = SeparateStage(separator=odd)
    ctx = _ctx(tmp_path, stage)
    stage.run(ctx)
    for key in stage.produces:
        assert ctx.output(key).exists()
    assert not list(ctx.output("separate/stems/guitar.wav").parent.glob("weird_*"))


def test_stem_name_mapping_from_audio_separator_filenames():
    assert map_stem_filename("source_(Guitar)_htdemucs_6s.wav") == "guitar"
    assert map_stem_filename("source_(vocals)_htdemucs_6s.wav") == "vocals"
    assert map_stem_filename("source_(Other)_htdemucs_6s.wav") == "other"
    assert map_stem_filename("nonsense.wav") is None


def _install_fake_separator(monkeypatch, files_returned, seen):
    class FakeSeparator:
        def __init__(self, **kwargs):
            seen["init"] = kwargs
            self.out = Path(kwargs["output_dir"])

        def load_model(self, model_filename):
            seen["model"] = model_filename

        def separate(self, path, custom_output_names=None):
            seen["custom"] = custom_output_names
            for name in files_returned:
                (self.out / name).write_bytes(b"RIFF")
            return list(files_returned)

    mod = types.ModuleType("audio_separator.separator")
    mod.Separator = FakeSeparator
    pkg = types.ModuleType("audio_separator")
    pkg.separator = mod
    monkeypatch.setitem(sys.modules, "audio_separator", pkg)
    monkeypatch.setitem(sys.modules, "audio_separator.separator", mod)
    fake_ff = types.ModuleType("static_ffmpeg")
    fake_ff.add_paths = lambda: seen.setdefault("ffmpeg", True)
    monkeypatch.setitem(sys.modules, "static_ffmpeg", fake_ff)


def test_separate_passes_capitalised_custom_output_names(tmp_path, monkeypatch):
    seen: dict = {}
    _install_fake_separator(monkeypatch, [f"{s}.wav" for s in STEMS], seen)
    out = tmp_path / "o"
    out.mkdir()
    result = separate_stems(tmp_path / "in.wav", out, model_dir=tmp_path / "m")
    assert set(seen["custom"]) == {"Vocals", "Drums", "Bass", "Guitar", "Piano", "Other"}
    assert seen["ffmpeg"] is True
    assert seen["model"] == "htdemucs_6s.yaml"
    assert seen["init"]["output_format"] == "WAV"
    assert seen["init"]["model_file_dir"] == str(tmp_path / "m")
    assert result == {s: out / f"{s}.wav" for s in STEMS}


def test_separate_falls_back_to_default_filename_form(tmp_path, monkeypatch):
    seen: dict = {}
    names = [f"in_({s.capitalize()})_htdemucs_6s.wav" for s in STEMS]
    _install_fake_separator(monkeypatch, names, seen)
    out = tmp_path / "o"
    out.mkdir()
    result = separate_stems(tmp_path / "in.wav", out, model_dir=tmp_path / "m")
    assert set(result) == set(STEMS)
    assert all(p.parent == out and p.exists() for p in result.values())


def test_separate_default_model_dir(tmp_path, monkeypatch):
    seen: dict = {}
    monkeypatch.setenv("YOUKELELE_CACHE", str(tmp_path / "cache"))
    _install_fake_separator(monkeypatch, [f"{s}.wav" for s in STEMS], seen)
    out = tmp_path / "o"
    out.mkdir()
    separate_stems(tmp_path / "in.wav", out)
    assert seen["init"]["model_file_dir"] == str(
        tmp_path / "cache" / "models" / "audio-separator"
    )


@pytest.mark.slow
def test_separate_real_model_on_two_seconds(tmp_path):
    wav = tmp_path / "in.wav"
    write_chord_loop(wav, ["C", "G"], 1.0)
    out = tmp_path / "stems"
    out.mkdir()
    result = separate_stems(wav, out)
    assert set(result) == set(STEMS)
    frames = sf.info(str(wav)).frames
    for path in result.values():
        assert path.exists()
        assert sf.info(str(path)).frames == frames
