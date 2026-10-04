"""yt-dlp adapter: download the best audio stream with retries, or read the details only."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import yt_dlp
from yt_dlp.utils import DownloadError as YtDlpError

from youkelele.models.ffmpeg import ffmpeg_paths

BACKOFF_SECONDS = (2, 4, 8)


class DownloadError(Exception):
    def __init__(self, url: str, last_error: BaseException) -> None:
        super().__init__(f"could not download {url}: {last_error}")
        self.url = url
        self.last_error = last_error


@dataclass
class DownloadResult:
    audio_path: Path
    info: dict


def _options(out_dir: Path) -> dict:
    import deno

    return {
        "format": "bestaudio/best",
        "outtmpl": str(out_dir / "source.%(ext)s"),
        "writeinfojson": True,
        "quiet": True,
        "no_warnings": True,
        "ffmpeg_location": str(ffmpeg_paths()[0].parent),
        "js_runtimes": {"deno": {"path": str(deno.find_deno_bin())}},
    }


def download_audio(
    url: str,
    out_dir: Path,
    retries: int = 3,
    sleep: Callable[[float], None] = time.sleep,
) -> DownloadResult:
    last_error: BaseException | None = None
    for attempt in range(retries):
        try:
            with yt_dlp.YoutubeDL(_options(Path(out_dir))) as ydl:
                info = ydl.extract_info(url, download=True)
            path = Path(info["requested_downloads"][0]["filepath"])
            return DownloadResult(path, info)
        except (YtDlpError, OSError) as exc:
            last_error = exc
            if attempt < retries - 1:
                sleep(BACKOFF_SECONDS[min(attempt, len(BACKOFF_SECONDS) - 1)])
    assert last_error is not None
    raise DownloadError(url, last_error)


class MetadataError(Exception):
    def __init__(self, url: str, cause: BaseException) -> None:
        super().__init__(f"could not read the details of {url}: {cause}")
        self.url = url
        self.cause = cause


_METADATA_FIELDS = ("id", "title", "uploader", "artist", "duration")


def fetch_metadata(url: str) -> dict:
    """The video's id, title, uploader, artist and duration, without downloading anything."""
    options = {"skip_download": True, "quiet": True, "no_warnings": True}
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)
    except (YtDlpError, OSError) as exc:
        raise MetadataError(url, exc) from exc
    if not isinstance(info, dict):
        raise MetadataError(url, ValueError("no details returned"))
    return {field: info.get(field) for field in _METADATA_FIELDS}
