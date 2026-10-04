from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
import soundfile as sf

from tests.audio_fixtures import write_sine_wav
from youkelele.jsonio import load_model
from youkelele.layout import SOURCE_META_NAME, RunLayout
from youkelele.models import ytdl
from youkelele.models.ffmpeg import to_wav
from youkelele.models.ytdl import (
    DownloadError,
    DownloadResult,
    MetadataError,
    download_audio,
    fetch_metadata,
)
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
    assert info.title == "My Song" and info.raw_title == "My Song"
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


def test_ingest_url_stores_raw_and_clean_title(tmp_path):
    def downloader(url, out_dir):
        audio = out_dir / "source.webm"
        audio.write_bytes(b"x")
        return DownloadResult(
            audio, {"id": "abc", "title": "X - Y (Official Video)", "artist": "X"}
        )

    stage = IngestStage(downloader=downloader, converter=_copy, prober=lambda _p: 3.0)
    ctx = _ctx(tmp_path, "https://youtu.be/abc", stage)
    stage.run(ctx)
    info = load_model(ctx.out_dir / "source.json", SourceInfo)
    assert info.raw_title == "X - Y (Official Video)"
    assert (info.title, info.artist) == ("Y", "X")


def test_ingest_url_title_cases_capitalised_artist(tmp_path):
    def downloader(url, out_dir):
        audio = out_dir / "source.webm"
        audio.write_bytes(b"x")
        return DownloadResult(
            audio, {"id": "abc", "title": "DEF LEPPARD - Song", "uploader": "DEF LEPPARD"}
        )

    stage = IngestStage(downloader=downloader, converter=_copy, prober=lambda _p: 3.0)
    ctx = _ctx(tmp_path, "https://youtu.be/abc", stage)
    stage.run(ctx)
    info = load_model(ctx.out_dir / "source.json", SourceInfo)
    assert (info.title, info.artist) == ("Song", "Def Leppard")


_FETCHED = {
    "id": "xyz",
    "title": "Pat Benatar - All Fired Up (Official Music Video)",
    "uploader": "Benatar Giraldo",
    "artist": None,
    "duration": 250.0,
}


def _run_with_saved_details(tmp_path, downloaded_id, source="https://youtu.be/xyz"):
    def downloader(url, out_dir):
        audio = out_dir / "source.webm"
        audio.write_bytes(b"x")
        return DownloadResult(audio, {"id": downloaded_id, "title": "Other - Thing", "uploader": "Other"})

    stage = IngestStage(downloader=downloader, converter=_copy, prober=lambda _p: 3.0)
    ctx = _ctx(tmp_path, source, stage)
    run_dir = ctx.layout.run_dir
    run_dir.mkdir()
    (run_dir / SOURCE_META_NAME).write_text(json.dumps(_FETCHED), encoding="utf-8")
    stage.run(ctx)
    return load_model(ctx.out_dir / "source.json", SourceInfo)


def test_ingest_url_reuses_fetched_metadata(tmp_path):
    info = _run_with_saved_details(tmp_path, "xyz")
    assert (info.video_id, info.title, info.artist) == ("xyz", "All Fired Up", "Pat Benatar")
    assert info.raw_title == _FETCHED["title"]


def test_ingest_ignores_saved_details_for_another_video(tmp_path):
    info = _run_with_saved_details(tmp_path, "abc")
    assert (info.video_id, info.title, info.artist) == ("abc", "Thing", "Other")
    assert info.raw_title == "Other - Thing"


def test_ingest_accepts_saved_details_matching_the_url_id(tmp_path):
    saved = {**_FETCHED, "id": "eFjjO_lhf9c"}
    url = "https://www.youtube.com/watch?v=eFjjO_lhf9c"

    def downloader(url, out_dir):
        audio = out_dir / "source.webm"
        audio.write_bytes(b"x")
        return DownloadResult(audio, {"title": "Other - Thing", "uploader": "Other"})

    stage = IngestStage(downloader=downloader, converter=_copy, prober=lambda _p: 3.0)
    ctx = _ctx(tmp_path, url, stage)
    ctx.layout.run_dir.mkdir()
    (ctx.layout.run_dir / SOURCE_META_NAME).write_text(json.dumps(saved), encoding="utf-8")
    stage.run(ctx)
    info = load_model(ctx.out_dir / "source.json", SourceInfo)
    assert (info.video_id, info.title) == ("eFjjO_lhf9c", "All Fired Up")


def test_fetch_metadata_reads_details_without_downloading(monkeypatch):
    seen = {}

    class FakeYDL:
        def __init__(self, opts):
            seen["opts"] = opts

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def extract_info(self, url, download=True):
            seen["download"] = download
            return {"id": "abc", "title": "T", "uploader": "U", "duration": 9.0, "formats": []}

    monkeypatch.setattr(ytdl.yt_dlp, "YoutubeDL", FakeYDL)
    meta = fetch_metadata("https://youtu.be/abc")
    assert meta == {"id": "abc", "title": "T", "uploader": "U", "artist": None, "duration": 9.0}
    assert seen["download"] is False and seen["opts"]["skip_download"] is True


def test_fetch_metadata_options_match_the_download_runtime(monkeypatch):
    seen = []

    class FakeYDL:
        def __init__(self, opts):
            seen.append(opts)

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def extract_info(self, url, download=True):
            return {"id": "abc", "title": "T"}

    monkeypatch.setattr(ytdl.yt_dlp, "YoutubeDL", FakeYDL)
    fetch_metadata("https://youtu.be/abc")
    opts = seen[0]
    assert opts["ignore_no_formats_error"] is True
    assert opts["js_runtimes"] == ytdl._common_options()["js_runtimes"]
    assert set(opts["js_runtimes"]) == {"deno"} and opts["js_runtimes"]["deno"]["path"]
    assert opts["quiet"] is True and opts["no_warnings"] is True


def test_fetch_metadata_failure_raises_metadata_error(monkeypatch):
    attempts = []

    class FakeYDL:
        def __init__(self, opts):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def extract_info(self, url, download=True):
            attempts.append(url)
            raise ytdl.YtDlpError("Video unavailable")

    monkeypatch.setattr(ytdl.yt_dlp, "YoutubeDL", FakeYDL)
    sleeps = []
    with pytest.raises(MetadataError) as exc:
        fetch_metadata("https://youtu.be/abc", sleep=sleeps.append)
    assert exc.value.url == "https://youtu.be/abc"
    assert "Video unavailable" in str(exc.value.cause)
    assert len(attempts) == 3 and sleeps == [2, 4]


def test_fetch_metadata_retries_then_succeeds(monkeypatch):
    attempts = []

    class FakeYDL:
        def __init__(self, opts):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def extract_info(self, url, download=True):
            attempts.append(url)
            if len(attempts) < 2:
                raise ytdl.YtDlpError("timed out")
            return {"id": "abc", "title": "T"}

    monkeypatch.setattr(ytdl.yt_dlp, "YoutubeDL", FakeYDL)
    sleeps = []
    assert fetch_metadata("https://youtu.be/abc", sleep=sleeps.append)["title"] == "T"
    assert len(attempts) == 2 and sleeps == [2]


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
