"""ffmpeg and ffprobe adapters, using binaries provided by static-ffmpeg."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

_PATHS: tuple[Path, Path] | None = None


def ffmpeg_paths() -> tuple[Path, Path]:
    """Return (ffmpeg, ffprobe); the binaries are fetched on the first call."""
    global _PATHS
    if _PATHS is None:
        from static_ffmpeg.run import get_or_fetch_platform_executables_else_raise

        ffmpeg, ffprobe = get_or_fetch_platform_executables_else_raise()
        _PATHS = (Path(ffmpeg), Path(ffprobe))
    return _PATHS


def to_wav(src: Path, dst: Path) -> None:
    ffmpeg, _ = ffmpeg_paths()
    subprocess.run(
        [
            str(ffmpeg), "-y", "-loglevel", "error", "-i", str(src),
            "-ac", "2", "-ar", "44100", "-sample_fmt", "s16", str(dst),
        ],
        check=True,
    )


def probe_duration(path: Path) -> float:
    _, ffprobe = ffmpeg_paths()
    result = subprocess.run(
        [
            str(ffprobe), "-v", "error", "-show_entries", "format=duration",
            "-of", "json", str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])
