import json
import subprocess
import sys

import pytest

from tests.fakes import make_fake_stage
from youkelele import __version__, commands
from youkelele.cli import main
from youkelele.manifest import load_manifest
from youkelele.preflight import Problem


def test_version_flag_prints_version(capsys):
    assert main(["--version"]) == 0
    assert __version__ in capsys.readouterr().out


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


def test_stages_command_lists_nine_ukulele_stages(capsys):
    assert main(["stages"]) == 0
    out = capsys.readouterr().out
    numbers = [line[:2] for line in out.splitlines() if line[:2].isdecimal()]
    assert numbers == ["00", "01", "02", "03", "04", "05", "06", "07", "08"]
    assert "08 render" in out


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
    monkeypatch.setattr(commands, "fetch_metadata", _fake_fetch)
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
    proc = subprocess.run([sys.executable, "-m", module, "--version"], capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0 and __version__ in proc.stdout


def test_evaluate_truth_is_optional_and_compare_accepted():
    from youkelele.cli import build_parser

    args = build_parser().parse_args(["evaluate", "abc"])
    assert args.truth is None and args.compare is None
    args = build_parser().parse_args(["evaluate", "abc", "--compare", "def", "--truth", "t"])
    assert args.compare == "def" and args.truth == "t"


def test_run_parser_debug_defaults_to_none():
    from youkelele.cli import build_parser

    assert build_parser().parse_args(["run", "song.wav"]).debug is None
    assert build_parser().parse_args(["run", "song.wav", "--debug"]).debug is True
    assert build_parser().parse_args(["run", "song.wav", "--no-debug"]).debug is False


def test_run_no_debug_switches_a_saved_debug_off(tmp_path, monkeypatch):
    seen = recording_chain(monkeypatch)
    runs = ["--runs-dir", str(tmp_path)]
    assert main(["run", "song.wav", "--debug", *runs]) == 0
    assert seen[-1].debug is True
    assert main(["run", "song.wav", "--from", "1", "--no-debug", *runs]) == 0
    assert seen[-1].debug is False
    assert main(["run", "song.wav", "--from", "1", *runs]) == 0
    assert seen[-1].debug is False  # the switch-off is saved like any other option


def test_run_debug_flag_reaches_options_and_is_saved(tmp_path, monkeypatch):
    seen = recording_chain(monkeypatch)
    runs = ["--runs-dir", str(tmp_path)]
    assert main(["run", "song.wav", *runs]) == 0
    assert seen[-1].debug is False
    assert main(["run", "song.wav", "--debug", *runs]) == 0
    assert seen[-1].debug is True
    assert main(["run", "song.wav", "--from", "1", *runs]) == 0
    assert seen[-1].debug is True


def _fake_fetch(url):
    return {"id": "abcdefghijk", "title": "A Song", "uploader": "A Band", "artist": None, "duration": 1.0}


def test_run_command_reports_metadata_failure_as_problem(tmp_path, capsys, monkeypatch):
    from youkelele.models.ytdl import MetadataError

    seen = recording_chain(monkeypatch)

    def fail(url):
        raise MetadataError(url, RuntimeError("Video unavailable"))

    monkeypatch.setattr(commands, "fetch_metadata", fail)
    url = "https://youtu.be/abcdefghijk"
    assert main(["run", url, "--runs-dir", str(tmp_path)]) == 2
    out = capsys.readouterr().out
    assert out.splitlines() == [
        "could not read the video's details: Video unavailable",
        "  fix: check the link and your connection",
    ]
    assert seen == [] and list(tmp_path.iterdir()) == []


def test_run_command_checks_stage_names_before_fetching(tmp_path, capsys, monkeypatch):
    recording_chain(monkeypatch)
    monkeypatch.setattr(commands, "fetch_metadata", _no_fetch)
    url = "https://youtu.be/abcdefghijk"
    assert main(["run", url, "--to", "nope", "--runs-dir", str(tmp_path)]) == 1
    assert "unknown stage 'nope'" in capsys.readouterr().out
    assert not tmp_path.exists() or list(tmp_path.iterdir()) == []


def _no_fetch(url):
    raise AssertionError("fetch must not be called")


def test_run_command_checks_the_environment_before_fetching(tmp_path, capsys, monkeypatch):
    recording_chain(monkeypatch)
    monkeypatch.setattr(
        commands, "check_environment", lambda *a, **k: [Problem("Deno is not installed", "uv sync")]
    )
    monkeypatch.setattr(commands, "fetch_metadata", _no_fetch)
    url = "https://youtu.be/abcdefghijk"
    assert main(["run", url, "--runs-dir", str(tmp_path)]) == 2
    assert "Deno is not installed" in capsys.readouterr().out
    assert not tmp_path.exists() or list(tmp_path.iterdir()) == []


def test_run_command_refuses_a_cut_link_before_naming_a_folder(tmp_path, capsys, monkeypatch):
    from youkelele.preflight import Probes, check_environment

    recording_chain(monkeypatch)
    probes = Probes(
        ffmpeg_dir=lambda: tmp_path, deno_bin=lambda: tmp_path,
        chromium_state=lambda: "present", chord_model_present=lambda: True,
        source_exists=lambda path: False,
    )
    monkeypatch.setattr(
        commands, "check_environment", lambda options, names: check_environment(options, names, probes)
    )
    monkeypatch.setattr(commands, "fetch_metadata", _no_fetch)
    # cmd.exe cut the link at the = sign; yt-dlp would have fetched the front page
    assert main(["run", "https://www.youtube.com/watch?v", "--runs-dir", str(tmp_path)]) == 2
    assert capsys.readouterr().out.splitlines() == [
        "YouTube link has no 11-character video id",
        "  fix: paste the whole link, for example https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    ]
    assert not tmp_path.exists() or list(tmp_path.iterdir()) == []


def test_run_command_names_the_folder_after_the_song(tmp_path, capsys, monkeypatch):
    recording_chain(monkeypatch)
    calls = []
    monkeypatch.setattr(commands, "fetch_metadata", lambda url: calls.append(url) or _fake_fetch(url))
    url = "https://youtu.be/abcdefghijk"
    runs = ["--runs-dir", str(tmp_path)]
    assert main(["run", url, *runs]) == 0
    manifest = load_manifest(tmp_path / "a-song")
    assert (manifest.video_id, manifest.title_slug, manifest.slug) == ("abcdefghijk", "a-song", "a-song")
    assert main(["run", url, "--from", "1", *runs]) == 0
    assert main(["run", url, *runs]) == 0
    assert "Existing run a-song will be overwritten from stage 0" in capsys.readouterr().out
    assert calls == [url]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["a-song"]


def test_status_and_evaluate_accept_folder_name_or_id(tmp_path, capsys, monkeypatch):
    from youkelele import evaluate

    fake_chain(monkeypatch)
    monkeypatch.setattr(commands, "fetch_metadata", _fake_fetch)
    runs = ["--runs-dir", str(tmp_path)]
    assert main(["run", "https://youtu.be/abcdefghijk", *runs]) == 0
    old = tmp_path / "zyxwvutsrqp"  # a pre-1.4 folder: named by id, no video_id recorded
    old.mkdir()
    saved = json.loads((tmp_path / "a-song" / "manifest.json").read_text(encoding="utf-8"))
    for field in ("video_id", "title_slug"):
        del saved[field]
    saved.update(slug="zyxwvutsrqp", source="https://www.youtube.com/watch?v=zyxwvutsrqp")
    (old / "manifest.json").write_text(json.dumps(saved), encoding="utf-8")
    capsys.readouterr()
    for name in ("a-song", "abcdefghijk"):
        assert main(["status", name, *runs]) == 0
        assert capsys.readouterr().out.splitlines() == ["00 ingest  done", "01 grid  done"]

    seen = []
    monkeypatch.setattr(evaluate, "evaluate_run", lambda run_dir, truth: seen.append(run_dir) or "report")
    monkeypatch.setattr(evaluate, "format_report", lambda report: report)
    monkeypatch.setattr(evaluate, "compare_runs", lambda a, b: seen.append(b) or "cmp")
    monkeypatch.setattr(evaluate, "format_comparison", lambda c: c)
    assert main(["evaluate", "abcdefghijk", "--compare", "zyxwvutsrqp", *runs]) == 0
    assert main(["evaluate", "a-song", "--compare", "ZYXWVUTSRQP", *runs]) == 0
    assert seen == [tmp_path / "a-song", old, tmp_path / "a-song", old]
    assert main(["evaluate", "nothing-here", *runs]) == 1
    assert f"no run folder at {tmp_path / 'nothing-here'}" in capsys.readouterr().out


def test_status_and_evaluate_help_names_folder_or_id():
    from youkelele.cli import build_parser

    parser = build_parser()
    sub = next(a for a in parser._actions if a.dest == "command")
    for name in ("status", "evaluate"):
        help_text = sub.choices[name].format_help()
        assert "run folder name (or video id)" in help_text
