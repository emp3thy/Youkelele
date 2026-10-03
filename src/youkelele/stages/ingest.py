"""Stage 1: fetch or convert the source into a 44.1 kHz stereo WAV."""

from __future__ import annotations

import shutil
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from youkelele import jsonio
from youkelele.models.ffmpeg import probe_duration, to_wav
from youkelele.models.ytdl import DownloadResult, download_audio
from youkelele.schemas import SourceInfo
from youkelele.stage import Stage, StageContext
from youkelele.titles import clean_artist, clean_title


class IngestStage(Stage):
    name = "ingest"
    requires = ()
    produces = ("ingest/audio.wav", "ingest/source.json")

    def __init__(
        self,
        downloader: Callable[[str, Path], DownloadResult] = download_audio,
        converter: Callable[[Path, Path], None] = to_wav,
        prober: Callable[[Path], float] = probe_duration,
    ) -> None:
        self._downloader = downloader
        self._converter = converter
        self._prober = prober

    def run(self, ctx: StageContext) -> None:
        source = ctx.options.source
        wav = ctx.output("ingest/audio.wav")
        if source.startswith(("http://", "https://")):
            work = ctx.out_dir / "download"
            work.mkdir(parents=True, exist_ok=True)
            try:
                ctx.log("downloading audio")
                result = self._downloader(source, work)
                self._converter(result.audio_path, wav)
                info = result.info
                stem = result.audio_path.stem
                video_id = info.get("id")
                raw_title = info.get("title") or stem
                raw_artist = info.get("artist") or info.get("uploader")
                artist = clean_artist(raw_artist)
                title = clean_title(raw_title, raw_artist)
                url, path = source, None
            finally:
                shutil.rmtree(work, ignore_errors=True)
        else:
            src = Path(source)
            ctx.log("converting local file")
            self._converter(src, wav)
            video_id, raw_title, title, artist = None, src.stem, src.stem, None
            url, path = None, str(src)
        record = SourceInfo(
            url=url,
            path=path,
            video_id=video_id,
            title=title,
            raw_title=raw_title,
            artist=artist,
            duration=self._prober(wav),
            sample_rate=44100,
            channels=2,
            fetched_at=datetime.now(UTC),
        )
        jsonio.save_model(ctx.output("ingest/source.json"), record)
