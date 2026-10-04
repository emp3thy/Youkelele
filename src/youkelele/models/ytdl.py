"""yt-dlp adapter: download the best audio stream with retries, or read the details only."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

import yt_dlp
from yt_dlp.utils import DownloadError as YtDlpError

from youkelele.models.ffmpeg import ffmpeg_paths

BACKOFF_SECONDS = (2, 4, 8)

T = TypeVar("T")


class DownloadError(Exception):
    def __init__(self, url: str, last_error: BaseException) -> None:
        super().__init__(f"could not download {url}: {last_error}")
        self.url = url
        self.last_error = last_error


@dataclass
class DownloadResult:
    audio_path: Path
    info: dict


def _common_options() -> dict:
    """Options shared by the download and the details-only fetch."""
    import deno

    return {
        "quiet": True,
        "no_warnings": True,
        "js_runtimes": {"deno": {"path": str(deno.find_deno_bin())}},
    }


def _options(out_dir: Path) -> dict:
    return {
        **_common_options(),
        "format": "bestaudio/best",
        "outtmpl": str(out_dir / "source.%(ext)s"),
        "writeinfojson": True,
        "ffmpeg_location": str(ffmpeg_paths()[0].parent),
    }


def _metadata_options() -> dict:
    # format selection still runs without a download; a video with no usable format
    # should still give its details
    return {**_common_options(), "skip_download": True, "ignore_no_formats_error": True}


def _with_retries(
    attempt_once: Callable[[], T], retries: int, sleep: Callable[[float], None]
) -> T:
    """The first successful attempt; yt-dlp and OS errors are retried with backoff."""
    last_error: BaseException | None = None
    for attempt in range(retries):
        try:
            return attempt_once()
        except (YtDlpError, OSError) as exc:
            last_error = exc
            if attempt < retries - 1:
                sleep(BACKOFF_SECONDS[min(attempt, len(BACKOFF_SECONDS) - 1)])
    assert last_error is not None
    raise last_error


def download_audio(
    url: str,
    out_dir: Path,
    retries: int = 3,
    sleep: Callable[[float], None] = time.sleep,
) -> DownloadResult:
    def attempt_once() -> DownloadResult:
        with yt_dlp.YoutubeDL(_options(Path(out_dir))) as ydl:
            info = ydl.extract_info(url, download=True)
        return DownloadResult(Path(info["requested_downloads"][0]["filepath"]), info)

    try:
        return _with_retries(attempt_once, retries, sleep)
    except (YtDlpError, OSError) as exc:
        raise DownloadError(url, exc) from exc


class MetadataError(Exception):
    def __init__(self, url: str, cause: BaseException) -> None:
        super().__init__(f"could not read the details of {url}: {cause}")
        self.url = url
        self.cause = cause


_METADATA_FIELDS = ("id", "title", "uploader", "artist", "duration")


def fetch_metadata(
    url: str, retries: int = 3, sleep: Callable[[float], None] = time.sleep
) -> dict:
    """The video's id, title, uploader, artist and duration, without downloading anything."""

    def attempt_once() -> object:
        with yt_dlp.YoutubeDL(_metadata_options()) as ydl:
            return ydl.extract_info(url, download=False)

    try:
        info = _with_retries(attempt_once, retries, sleep)
    except (YtDlpError, OSError) as exc:
        raise MetadataError(url, exc) from exc
    if not isinstance(info, dict):
        raise MetadataError(url, ValueError("no details returned"))
    return {field: info.get(field) for field in _METADATA_FIELDS}
