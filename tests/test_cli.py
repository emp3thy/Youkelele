import subprocess
import sys

import pytest

from tests.fakes import make_fake_stage
from youkelele import commands
from youkelele.cli import main
from youkelele.manifest import load_manifest
from youkelele.preflight import Problem


def test_version_flag_prints_version(capsys):
    assert main(["--version"]) == 0
    assert "0.1.0" in capsys.readouterr().out


def fake_chain(monkeypatch, **kw):
    chain = [
        make_fake_stage("ingest", produces=("ingest/a.txt",)),
        make_fake_stage("grid", requires=("ingest/a.txt",), produces=("grid/b.txt",), **kw),
    ]
    monkeypatch.setattr(commands, "_chain", lambda instrument: chain)
    monkeypatch.setattr(commands, "check_environment", lambda *a, **k: [])
    return chain


def test_stages_command_lists_numbered_stages(capsys, monkeypatch):
    fake_chain(monkeypatch)
    assert main(["stages"]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "00 ingest  reads:   writes: ingest/a.txt",
        "01 grid  reads: ingest/a.txt  writes: grid/b.txt",
    ]


def test_stages_command_empty_chain_exits_zero(capsys):
    assert main(["stages"]) == 0


def test_status_command_prints_state_per_stage(tmp_path, capsys, monkeypatch):
    fake_chain(monkeypatch)
    assert main(["status", "abc", "--runs-dir", str(tmp_path)]) == 0
    assert capsys.readouterr().out.splitlines() == ["00 ingest  missing", "01 grid  missing"]


def test_run_prints_stage_failure_and_resume_command(tmp_path, capsys, monkeypatch):
    fake_chain(monkeypatch, fail=True)
    assert main(["run", "song.wav", "--runs-dir", str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "stage grid (01) failed: boom" in out
    assert 'resume with: youkelele run "song.wav" --from 1' in out


def test_run_prints_missing_artifact(tmp_path, capsys, monkeypatch):
    fake_chain(monkeypatch)
    assert main(["run", "song.wav", "--from", "1", "--runs-dir", str(tmp_path)]) == 1
    assert "missing artifact ingest/a.txt (produced by stage ingest)" in capsys.readouterr().out


def test_run_unknown_stage_returns_1(tmp_path, capsys, monkeypatch):
    fake_chain(monkeypatch)
    assert main(["run", "song.wav", "--to", "nope", "--runs-dir", str(tmp_path)]) == 1
    assert "unknown stage 'nope'" in capsys.readouterr().out


def test_status_command_runs_on_empty_chain(tmp_path):
    assert main(["status", "abc", "--runs-dir", str(tmp_path)]) == 0


def test_run_returns_2_and_prints_fix_when_preflight_fails(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(
        commands, "check_environment", lambda *a, **k: [Problem("ffmpeg missing", "youkelele setup")]
    )
    code = main(["run", "song.wav", "--runs-dir", str(tmp_path)])
    out = capsys.readouterr().out
    assert code == 2
    assert "ffmpeg missing\n  fix: youkelele setup" in out


def test_run_with_empty_chain_reports_nothing_to_run(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(commands, "_chain", lambda instrument: [])
    monkeypatch.setattr(commands, "check_environment", lambda *a, **k: [])
    assert main(["run", "song.wav", "--runs-dir", str(tmp_path)]) == 0
    assert "nothing to run" in capsys.readouterr().out


def test_setup_command_runs_ensure_and_ffmpeg(monkeypatch, capsys):
    from pathlib import Path

    from youkelele import vendoring
    from youkelele.cli import main
    from youkelele.models import ffmpeg

    calls = []
    monkeypatch.setattr(vendoring, "ensure_chord_model", lambda log=print: calls.append("model") or Path("m"))
    monkeypatch.setattr(ffmpeg, "ffmpeg_paths", lambda: calls.append("ffmpeg") or (Path("ff"), Path("fp")))
    assert main(["setup"]) == 0
    assert calls == ["model", "ffmpeg"]
    assert "ff" in capsys.readouterr().out


def test_stages_command_lists_eight_ukulele_stages(capsys):
    assert main(["stages"]) == 0
    out = capsys.readouterr().out
    numbers = [line[:2] for line in out.splitlines() if line[:2].isdecimal()]
    assert numbers == ["00", "01", "02", "03", "04", "05", "06", "07"]
    assert "07 render" in out


def recording_chain(monkeypatch):
    seen = []
    chain = [
        make_fake_stage("ingest", produces=("ingest/a.txt",)),
        make_fake_stage(
            "grid",
            requires=("ingest/a.txt",),
            produces=("grid/b.txt",),
            body=lambda ctx: seen.append(ctx.options),
        ),
    ]
    monkeypatch.setattr(commands, "_chain", lambda instrument: chain)
    monkeypatch.setattr(commands, "check_environment", lambda *a, **k: [])
    return seen


def test_run_from_reuses_saved_options(tmp_path, monkeypatch):
    seen = recording_chain(monkeypatch)
    runs = ["--runs-dir", str(tmp_path)]
    assert main(["run", "song.wav", "--tier", "full", "--meter", "3/4", "--sections-k", "3", *runs]) == 0
    assert main(["run", "song.wav", "--from", "1", *runs]) == 0
    saved = load_manifest(tmp_path / "song").options
    assert (saved.tier, saved.meter, saved.sections_k) == ("full", "3/4", 3)
    assert (seen[-1].tier, seen[-1].meter, seen[-1].sections_k) == ("full", "3/4", 3)


def test_run_from_with_flag_overrides_and_saves_it(tmp_path, monkeypatch):
    seen = recording_chain(monkeypatch)
    runs = ["--runs-dir", str(tmp_path)]
    assert main(["run", "song.wav", "--tier", "full", "--meter", "3/4", "--sections-k", "3", *runs]) == 0
    assert main(["run", "song.wav", "--from", "1", "--tier", "easy", "--sections-k", "auto", *runs]) == 0
    saved = load_manifest(tmp_path / "song").options
    assert (saved.tier, saved.meter, saved.sections_k) == ("easy", "3/4", None)
    assert (seen[-1].tier, seen[-1].meter, seen[-1].sections_k) == ("easy", "3/4", None)


def test_first_run_uses_defaults(tmp_path, monkeypatch):
    seen = recording_chain(monkeypatch)
    assert main(["run", "song.wav", "--runs-dir", str(tmp_path)]) == 0
    assert (seen[0].tier, seen[0].meter, seen[0].instrument) == ("easy", "4/4", "ukulele")


def test_rerun_from_zero_prints_overwrite_notice(tmp_path, capsys, monkeypatch):
    recording_chain(monkeypatch)
    assert main(["run", "song.wav", "--runs-dir", str(tmp_path)]) == 0
    assert "will be overwritten" not in capsys.readouterr().out
    assert main(["run", "song.wav", "--runs-dir", str(tmp_path)]) == 0
    assert "Existing run song will be overwritten from stage 0" in capsys.readouterr().out
    assert main(["run", "song.wav", "--from", "1", "--runs-dir", str(tmp_path)]) == 0
    assert "will be overwritten" not in capsys.readouterr().out


def test_resume_command_quotes_source_and_keeps_runs_dir(tmp_path, capsys, monkeypatch):
    fake_chain(monkeypatch, fail=True)
    url = "https://www.youtube.com/watch?v=abcdefghijk&t=5"
    runs = str(tmp_path / "my runs")
    assert main(["run", url, "--runs-dir", runs]) == 1
    out = capsys.readouterr().out
    assert f'resume with: youkelele run "{url}" --from 1 --runs-dir "{runs}"' in out


@pytest.mark.parametrize(
    "flags, message",
    [
        (["--meter", "3-4"], "invalid --meter '3-4'"),
        (["--meter", "0/4"], "invalid --meter '0/4'"),
        (["--meter", "x/y"], "invalid --meter 'x/y'"),
        (["--sections-k", "0"], "invalid --sections-k '0'"),
        (["--sections-k", "many"], "invalid --sections-k 'many'"),
    ],
)
def test_run_rejects_bad_meter_and_sections_k(tmp_path, capsys, monkeypatch, flags, message):
    seen = recording_chain(monkeypatch)
    assert main(["run", "song.wav", *flags, "--runs-dir", str(tmp_path)]) == 2
    out = capsys.readouterr().out
    assert message in out
    assert len(out.strip().splitlines()) == 1
    assert seen == [] and not (tmp_path / "song").exists()


def test_run_rejects_unknown_instrument(tmp_path, capsys):
    assert main(["run", "song.wav", "--instrument", "banjo", "--runs-dir", str(tmp_path)]) == 2
    assert "invalid choice: 'banjo'" in capsys.readouterr().err


def test_setup_reports_vendoring_error_in_one_line(monkeypatch, capsys):
    from youkelele import vendoring

    def fail(log=print):
        raise vendoring.VendoringError("git is not installed or not on PATH; install git and retry")

    monkeypatch.setattr(vendoring, "ensure_chord_model", fail)
    assert main(["setup"]) == 1
    out = capsys.readouterr().out
    assert out.strip().splitlines() == [
        "setup failed: git is not installed or not on PATH; install git and retry"
    ]


@pytest.mark.parametrize("module", ["youkelele", "youkelele.cli"])
def test_module_entry_point_runs_main(module):
    proc = subprocess.run([sys.executable, "-m", module, "--version"], capture_output=True, text=True)
    assert proc.returncode == 0 and "0.1.0" in proc.stdout
