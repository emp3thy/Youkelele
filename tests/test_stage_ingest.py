from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import soundfile as sf

from tests.audio_fixtures import write_sine_wav
from youkelele.jsonio import load_model
from youkelele.layout import RunLayout
from youkelele.models import ytdl
from youkelele.models.ffmpeg import to_wav
from youkelele.models.ytdl import DownloadError, DownloadResult, download_audio
from youkelele.options import RunOptions
from youkelele.schemas import SourceInfo
from youkelele.stage import StageContext
from youkelele.stages.ingest import IngestStage


def _ctx(tmp_path: Path, source: str, stage: IngestStage) -> StageContext:
    out = tmp_path / "out"
    out.mkdir()
    return StageContext(
        RunLayout(tmp_path / "run", ["ingest"]),
        RunOptions(source=source),
        out,
        lambda _msg: None,
        stage,
    )


def _copy(src: Path, dst: Path) -> None:
    shutil.copyfile(src, dst)


def test_ingest_local_file_writes_wav_and_source(tmp_path):
    src = tmp_path / "My Song.mp3"
    src.write_bytes(b"x")
    stage = IngestStage(converter=_copy, prober=lambda _p: 12.5)
    ctx = _ctx(tmp_path, str(src), stage)
    stage.run(ctx)
    assert sorted(p.name for p in ctx.out_dir.iterdir()) == ["audio.wav", "source.json"]
    info = load_model(ctx.out_dir / "source.json", SourceInfo)
    assert info.title == "My Song"
    assert info.path == str(src)
    assert info.url is None and info.artist is None and info.video_id is None
    assert (info.duration, info.sample_rate, info.channels) == (12.5, 44100, 2)


def test_ingest_url_uses_downloader_and_info(tmp_path):
    calls = []

    def downloader(url, out_dir):
        calls.append(url)
        audio = out_dir / "source.webm"
        audio.write_bytes(b"x")
        return DownloadResult(audio, {"id": "abc", "title": "T", "artist": "A"})

    stage = IngestStage(downloader=downloader, converter=_copy, prober=lambda _p: 3.0)
    ctx = _ctx(tmp_path, "https://youtu.be/abc", stage)
    stage.run(ctx)
    assert calls == ["https://youtu.be/abc"]
    assert sorted(p.name for p in ctx.out_dir.iterdir()) == ["audio.wav", "source.json"]
    info = load_model(ctx.out_dir / "source.json", SourceInfo)
    assert (info.video_id, info.title, info.artist) == ("abc", "T", "A")
    assert info.url == "https://youtu.be/abc" and info.path is None


def test_download_retries_three_times_then_raises(monkeypatch, tmp_path):
    attempts = []

    class FakeYDL:
        def __init__(self, opts):
            self.opts = opts

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def extract_info(self, url, download=True):
            attempts.append(url)
            raise ytdl.YtDlpError("boom")

    monkeypatch.setattr(ytdl, "ffmpeg_paths", lambda: (Path("ff/ffmpeg"), Path("ff/ffprobe")))
    monkeypatch.setattr(ytdl.yt_dlp, "YoutubeDL", FakeYDL)
    sleeps = []
    with pytest.raises(DownloadError) as exc:
        download_audio("https://example.test/v", tmp_path, sleep=sleeps.append)
    assert len(attempts) == 3
    assert sleeps == [2, 4]
    assert "https://example.test/v" in str(exc.value)


@pytest.mark.slow
def test_to_wav_real_ffmpeg_produces_44100_stereo(tmp_path):
    pytest.importorskip("static_ffmpeg")
    src = tmp_path / "in.wav"
    write_sine_wav(src, 1.0, sr=22050, channels=1)
    dst = tmp_path / "out.wav"
    to_wav(src, dst)
    info = sf.info(str(dst))
    assert (info.samplerate, info.channels) == (44100, 2)
