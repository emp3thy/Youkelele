"""Environment checks run before any stage starts. Never downloads anything."""

from __future__ import annotations

from collections.abc import Callable, Sequence
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from youkelele.options import RunOptions

ChromiumState = Literal["present", "missing", "failed"]

_NOT_IMPLEMENTED = "not implemented in this version; use the default"


@dataclass
class Problem:
    what: str
    fix: str


@dataclass
class Probes:
    ffmpeg_dir: Callable[[], Path | None]
    deno_bin: Callable[[], Path | None]
    chromium_state: Callable[[], ChromiumState]
    chord_model_present: Callable[[], bool]
    source_exists: Callable[[str], bool] = lambda path: Path(path).is_file()


def _ffmpeg_dir() -> Path | None:
    import static_ffmpeg.run

    folder = Path(static_ffmpeg.run.get_platform_dir())
    needed = ("installed.crumb", "ffmpeg.exe", "ffprobe.exe")
    return folder if all((folder / name).exists() for name in needed) else None


def _deno_bin() -> Path | None:
    import deno

    path = Path(deno.find_deno_bin())
    return path if path.exists() else None


_CHROMIUM_SCRIPT = """
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    print(p.chromium.executable_path)
"""


def _chromium_state() -> ChromiumState:
    """Look up Chromium in a child process so a wedged driver cannot hang us."""
    try:
        result = subprocess.run(
            [sys.executable, "-c", _CHROMIUM_SCRIPT],
            timeout=30,
            capture_output=True,
            text=True,
        )
    except (subprocess.TimeoutExpired, OSError):
        return "failed"
    lines = result.stdout.strip().splitlines()
    if result.returncode != 0 or not lines:
        return "failed"
    return "present" if Path(lines[-1]).exists() else "missing"


def _chord_model_present() -> bool:
    from youkelele.vendoring import chord_model_ready

    return chord_model_ready()


def default_probes() -> Probes:
    return Probes(_ffmpeg_dir, _deno_bin, _chromium_state, _chord_model_present)


def check_environment(
    options: RunOptions,
    stages_to_run: Sequence[str],
    probes: Probes | None = None,
) -> list[Problem]:
    probes = probes or default_probes()
    stages = set(stages_to_run)
    problems: list[Problem] = []
    if options.separator == "roformer-sw":
        problems.append(Problem("separator 'roformer-sw' is unsupported", _NOT_IMPLEMENTED))
    if options.chord_model == "chordmini":
        problems.append(Problem("chord_model 'chordmini' is unsupported", _NOT_IMPLEMENTED))
    is_url = options.source.startswith("http")
    if "ingest" in stages and not is_url and not probes.source_exists(options.source):
        problems.append(
            Problem(
                f"source file not found: {options.source}",
                "check the path, or pass a YouTube URL",
            )
        )
    if stages & {"ingest", "separate"} and probes.ffmpeg_dir() is None:
        problems.append(Problem("ffmpeg is not installed", "youkelele setup"))
    if (
        "ingest" in stages
        and is_url
        and probes.deno_bin() is None
    ):
        problems.append(Problem("Deno is not installed", "uv sync"))
    if "render" in stages:
        state = probes.chromium_state()
        if state == "missing":
            problems.append(
                Problem("Chromium is not installed", "uv run playwright install chromium")
            )
        elif state == "failed":
            problems.append(
                Problem(
                    "Playwright could not start",
                    "uv sync, then uv run playwright install chromium",
                )
            )
    if "harmony" in stages and not probes.chord_model_present():
        problems.append(Problem("chord model is not installed", "youkelele setup"))
    return problems
