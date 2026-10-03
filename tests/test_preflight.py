from pathlib import Path

from youkelele.options import RunOptions
from youkelele.preflight import Probes, check_environment


def make_probes(ffmpeg=Path("ff"), deno=Path("deno"), chromium="present", chord=True) -> Probes:
    return Probes(
        ffmpeg_dir=lambda: ffmpeg,
        deno_bin=lambda: deno,
        chromium_state=lambda: chromium,
        chord_model_present=lambda: chord,
    )


def test_preflight_requires_ffmpeg_for_ingest():
    problems = check_environment(
        RunOptions(source="song.wav"), ["ingest"], make_probes(ffmpeg=None)
    )
    assert len(problems) == 1
    assert "ffmpeg" in problems[0].what
    assert problems[0].fix == "youkelele setup"


def test_preflight_skips_ffmpeg_when_starting_at_grid():
    problems = check_environment(
        RunOptions(source="song.wav"), ["grid", "harmony"], make_probes(ffmpeg=None)
    )
    assert problems == []


def test_preflight_rejects_roformer():
    options = RunOptions(source="song.wav", separator="roformer-sw")
    problems = check_environment(options, [], make_probes())
    assert len(problems) == 1
    assert "separator" in problems[0].what
    assert "not implemented in this version; use the default" in problems[0].fix


def test_preflight_rejects_chordmini():
    options = RunOptions(source="song.wav", chord_model="chordmini")
    problems = check_environment(options, [], make_probes())
    assert "chord_model" in problems[0].what


def test_preflight_deno_only_for_url_ingest():
    probes = make_probes(deno=None)
    url = RunOptions(source="https://youtu.be/abcdefghijk")
    assert "Deno" in check_environment(url, ["ingest"], probes)[0].what
    assert check_environment(RunOptions(source="a.wav"), ["ingest"], probes) == []


def test_preflight_chromium_and_chord_model():
    probes = make_probes(chromium="missing", chord=False)
    options = RunOptions(source="a.wav")
    assert "Chromium" in check_environment(options, ["render"], probes)[0].what
    problem = check_environment(options, ["harmony"], probes)[0]
    assert problem.fix == "youkelele setup"


def test_preflight_chromium_present_is_fine():
    assert check_environment(RunOptions(source="a.wav"), ["render"], make_probes()) == []


def test_preflight_chromium_missing_gives_install_fix():
    problems = check_environment(
        RunOptions(source="a.wav"), ["render"], make_probes(chromium="missing")
    )
    assert problems[0].what == "Chromium is not installed"
    assert problems[0].fix == "uv run playwright install chromium"


def test_preflight_chromium_driver_failure_is_reported_distinctly():
    problems = check_environment(
        RunOptions(source="a.wav"), ["render"], make_probes(chromium="failed")
    )
    assert problems[0].what == "Playwright could not start"
    assert problems[0].fix == "uv sync, then uv run playwright install chromium"
