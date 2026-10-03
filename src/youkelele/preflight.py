"""Environment checks run before any stage starts. Never downloads anything."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from youkelele.options import RunOptions

_NOT_IMPLEMENTED = "not implemented in this version; use the default"


@dataclass
class Problem:
    what: str
    fix: str


@dataclass
class Probes:
    ffmpeg_dir: Callable[[], Path | None]
    deno_bin: Callable[[], Path | None]
    chromium_present: Callable[[], bool]
    chord_model_present: Callable[[], bool]


def _ffmpeg_dir() -> Path | None:
    import static_ffmpeg.run

    folder = Path(static_ffmpeg.run.get_platform_dir())
    needed = ("installed.crumb", "ffmpeg.exe", "ffprobe.exe")
    return folder if all((folder / name).exists() for name in needed) else None


def _deno_bin() -> Path | None:
    import deno

    path = Path(deno.find_deno_bin())
    return path if path.exists() else None


def _chromium_present() -> bool:
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            return Path(p.chromium.executable_path).exists()
    except Exception:
        return False


def _chord_model_present() -> bool:
    return False


def default_probes() -> Probes:
    return Probes(_ffmpeg_dir, _deno_bin, _chromium_present, _chord_model_present)


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
    if stages & {"ingest", "separate"} and probes.ffmpeg_dir() is None:
        problems.append(Problem("ffmpeg is not installed", "youkelele setup"))
    if (
        "ingest" in stages
        and options.source.startswith("http")
        and probes.deno_bin() is None
    ):
        problems.append(Problem("Deno is not installed", "uv sync"))
    if "render" in stages and not probes.chromium_present():
        problems.append(
            Problem("Chromium is not installed", "uv run playwright install chromium")
        )
    if "harmony" in stages and not probes.chord_model_present():
        problems.append(Problem("chord model is not installed", "youkelele setup"))
    return problems
