from tests.fakes import make_fake_stage
from youkelele import commands
from youkelele.cli import main
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
    assert "resume with: youkelele run song.wav --from 1" in out


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
