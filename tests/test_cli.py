from youkelele import commands
from youkelele.cli import main
from youkelele.preflight import Problem


def test_version_flag_prints_version(capsys):
    assert main(["--version"]) == 0
    assert "0.1.0" in capsys.readouterr().out


def test_stages_command_lists_numbered_stages(capsys):
    assert main(["stages"]) == 0


def test_status_command_runs_on_empty_chain(tmp_path, capsys):
    assert main(["status", "abc", "--runs-dir", str(tmp_path)]) == 0


def test_run_returns_2_and_prints_fix_when_preflight_fails(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(
        commands, "check_environment", lambda *a, **k: [Problem("ffmpeg missing", "youkelele setup")]
    )
    code = main(["run", "song.wav", "--runs-dir", str(tmp_path)])
    out = capsys.readouterr().out
    assert code == 2
    assert "ffmpeg missing\n  fix: youkelele setup" in out


def test_run_with_empty_chain_reports_nothing_to_run(tmp_path, capsys):
    assert main(["run", "song.wav", "--runs-dir", str(tmp_path)]) == 0
    assert "nothing to run" in capsys.readouterr().out
