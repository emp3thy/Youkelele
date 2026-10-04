import json
import os
from pathlib import Path

import pytest

from youkelele.layout import (
    SOURCE_META_NAME,
    RunLayout,
    resolve_run_dir,
    slug_for,
    title_slug,
)
from youkelele.manifest import Manifest, save_manifest
from youkelele.options import RunOptions
from youkelele.paths import cache_dir, package_data, vendor_dir
from youkelele.stage import MissingArtifact, Stage, StageContext


def test_slug_for_youtube_variants():
    for url in [
        "https://www.youtube.com/watch?v=eFjjO_lhf9c",
        "https://youtu.be/eFjjO_lhf9c",
        "https://youtube.com/shorts/eFjjO_lhf9c",
    ]:
        assert slug_for(url) == "efjjo_lhf9c"


def test_slug_for_local_path():
    assert slug_for(r"C:\music\Summer Of 69.mp3") == "summer-of-69"


def test_layout_maps_key_to_numbered_folder(tmp_path):
    lay = RunLayout(tmp_path, ["ingest", "separate", "grid"])
    assert lay.path("grid/grid.json") == tmp_path / "02_grid" / "grid.json"
    assert lay.producer("grid/grid.json") == "grid"
    assert lay.number("separate") == 1
    assert lay.folder("ingest") == tmp_path / "00_ingest"
    assert lay.producer("separate/stems/guitar.wav") == "separate"
    assert lay.path("separate/stems/guitar.wav") == tmp_path / "01_separate" / "stems" / "guitar.wav"


class _Grid(Stage):
    name = "grid"
    requires = ("separate/stems/guitar.wav",)
    produces = ("grid/grid.json", "grid/extra/x.txt")

    def run(self, ctx):
        pass


def _ctx(tmp_path):
    lay = RunLayout(tmp_path, ["separate", "grid"])
    out = lay.folder("grid")
    return lay, StageContext(lay, RunOptions(source="x"), out, lambda m: None, _Grid()), out


def test_context_input_missing_raises(tmp_path):
    _, ctx, _ = _ctx(tmp_path)
    with pytest.raises(MissingArtifact) as exc:
        ctx.input("separate/stems/guitar.wav")
    assert exc.value.key == "separate/stems/guitar.wav"
    assert exc.value.producer == "separate"


def test_context_input_resolves_existing(tmp_path):
    lay, ctx, _ = _ctx(tmp_path)
    p = lay.path("separate/stems/guitar.wav")
    p.parent.mkdir(parents=True)
    p.write_bytes(b"x")
    assert ctx.input("separate/stems/guitar.wav") == p


def test_context_output_creates_parents_and_checks_produces(tmp_path):
    _, ctx, out = _ctx(tmp_path)
    assert ctx.output("grid/extra/x.txt") == out / "extra" / "x.txt"
    assert (out / "extra").is_dir()
    with pytest.raises(AssertionError):
        ctx.output("grid/other.json")


def test_context_note_records(tmp_path):
    _, ctx, _ = _ctx(tmp_path)
    ctx.note("k", "v")
    assert ctx.notes == {"k": "v"}


def test_stage_is_abstract():
    with pytest.raises(TypeError):
        Stage()


def test_options_defaults():
    o = RunOptions(source="x")
    assert (o.instrument, o.tier, o.beat_octave, o.sections_k, o.meter) == ("ukulele", "easy", "auto", None, "4/4")
    assert (o.separator, o.chord_model) == ("demucs", "cnn-lstm")


def test_paths(monkeypatch, tmp_path):
    monkeypatch.setenv("YOUKELELE_CACHE", str(tmp_path))
    assert cache_dir() == tmp_path
    monkeypatch.delenv("YOUKELELE_CACHE")
    assert cache_dir().name == ".youkelele"
    assert package_data("a", "b").parts[-3:] == ("data", "a", "b")
    assert vendor_dir("v").parts[-2:] == ("vendor", "v")


def test_slug_for_keeps_unicode_word_characters():
    assert slug_for(r"C:\music\夜に駆ける.mp3") == "夜に駆ける"
    assert slug_for("Café del Mar.wav") == "café-del-mar"


def test_slug_for_falls_back_to_a_hash_when_nothing_is_left():
    slug = slug_for("♪.wav")
    assert slug.startswith("song-") and len(slug) == len("song-") + 8
    assert slug == slug_for(r"D:\other\♪.wav")
    assert slug != slug_for("♫.wav")


def test_title_slug_rules():
    assert title_slug("Summer Of '69") == "summer-of-69"
    assert title_slug("mangetout") == "mangetout"
    assert title_slug("Déjà Vu") == "deja-vu"
    assert title_slug("Pour Some Sugar On Me") == "pour-some-sugar-on-me"
    assert title_slug("  Chelsea   Dagger!! ") == "chelsea-dagger"
    assert title_slug("夜に駆ける") == ""
    assert title_slug("") == ""


URL = "https://www.youtube.com/watch?v=eFjjO_lhf9c"


def _write_manifest(folder, source, video_id=None):
    folder.mkdir(parents=True, exist_ok=True)
    save_manifest(
        folder,
        Manifest(
            slug=folder.name, source=source, instrument="ukulele",
            options=RunOptions(source=source), stages={}, video_id=video_id,
        ),
    )


def _no_network(url):
    raise AssertionError("fetch must not be called")


def _meta(title="Summer Of '69 (Official Music Video)", uploader="Bryan Adams", vid="eFjjO_lhf9c"):
    def fetch(url):
        fetch.calls.append(url)
        return {"id": vid, "title": title, "uploader": uploader, "artist": None, "duration": 200.0}

    fetch.calls = []
    return fetch


def test_resolve_run_dir_finds_existing_folder_by_source_without_network(tmp_path):
    old = tmp_path / "efjjo_lhf9c"
    _write_manifest(old, URL)
    assert resolve_run_dir(tmp_path, URL, fetch=_no_network) == (old, None)
    # a different spelling of the same video matches by the id in the saved source
    assert resolve_run_dir(tmp_path, "https://youtu.be/eFjjO_lhf9c", fetch=_no_network) == (old, None)
    # a title-named folder matches by its recorded video id
    named = tmp_path / "other-song"
    _write_manifest(named, "https://youtu.be/abcdefghijk", video_id="abcdefghijk")
    found = resolve_run_dir(tmp_path, "https://www.youtube.com/watch?v=abcdefghijk&t=5", fetch=_no_network)
    assert found == (named, None)
    # an unreadable manifest is skipped, not fatal
    (tmp_path / "broken").mkdir()
    (tmp_path / "broken" / "manifest.json").write_text("{not json", encoding="utf-8")
    assert resolve_run_dir(tmp_path, URL, fetch=_no_network) == (old, None)


def test_resolve_run_dir_names_new_folder_from_metadata(tmp_path):
    fetch = _meta()
    run_dir, meta = resolve_run_dir(tmp_path, URL, fetch=fetch)
    assert run_dir == tmp_path / "summer-of-69"
    assert fetch.calls == [URL]
    assert meta["title"] == "Summer Of '69 (Official Music Video)"
    saved = json.loads((run_dir / SOURCE_META_NAME).read_text(encoding="utf-8"))
    assert saved == meta
    assert set(saved) == {"id", "title", "uploader", "artist", "duration"}
    # the wider artist prefix keeps the artist out of the folder name
    fetch = _meta("Pat Benatar - All Fired Up (Official Music Video)", "Benatar Giraldo", "abcdefghijk")
    run_dir, _ = resolve_run_dir(tmp_path, "https://youtu.be/abcdefghijk", fetch=fetch)
    assert run_dir == tmp_path / "all-fired-up"
    # a title with nothing left after folding falls back to the video id
    fetch = _meta("夜に駆ける", "YOASOBI", "x8VYWazR5mE")
    run_dir, _ = resolve_run_dir(tmp_path, "https://youtu.be/x8VYWazR5mE", fetch=fetch)
    assert run_dir == tmp_path / "x8vywazr5me"


def test_resolve_run_dir_collision_gets_suffix(tmp_path):
    _write_manifest(tmp_path / "fame", "https://youtu.be/aaaaaaaaaaa")
    _write_manifest(tmp_path / "fame-2", "https://youtu.be/bbbbbbbbbbb")
    fetch = _meta("Fame (2016 Remaster)", "David Bowie", "ccccccccccc")
    run_dir, _ = resolve_run_dir(tmp_path, "https://youtu.be/ccccccccccc", fetch=fetch)
    assert run_dir == tmp_path / "fame-3"
    # a folder left by a fetch whose run never started is reused by the same video only
    assert not (run_dir / "manifest.json").exists()
    fetch = _meta("Fame (2016 Remaster)", "David Bowie", "ccccccccccc")
    assert resolve_run_dir(tmp_path, "https://youtu.be/ccccccccccc", fetch=fetch)[0] == run_dir
    fetch = _meta("Fame (2016 Remaster)", "David Bowie", "ddddddddddd")
    assert resolve_run_dir(tmp_path, "https://youtu.be/ddddddddddd", fetch=fetch)[0] == tmp_path / "fame-4"
    # once the run has a manifest, the same source finds its folder without a fetch
    _write_manifest(run_dir, "https://youtu.be/ccccccccccc", video_id="ccccccccccc")
    assert resolve_run_dir(tmp_path, "https://youtu.be/ccccccccccc", fetch=_no_network) == (
        run_dir, None,
    )


def test_resolve_run_dir_local_file_matches_other_spellings_of_its_path(tmp_path, monkeypatch):
    runs = tmp_path / "runs"
    clip = tmp_path / "music" / "clip.wav"
    clip.parent.mkdir()
    clip.write_bytes(b"x")
    _write_manifest(runs / "clip", str(clip))
    monkeypatch.chdir(clip.parent)
    spellings = [
        "clip.wav",
        str(Path(".") / "clip.wav"),
        str(tmp_path / "music" / ".." / "music" / "clip.wav"),
        str(clip).upper() if os.name == "nt" else str(clip),
    ]
    for spelling in spellings:
        assert resolve_run_dir(runs, spelling, fetch=_no_network) == (runs / "clip", None), spelling
    # a manifest saved with a relative spelling is found from the absolute one too
    _write_manifest(runs / "clip", "clip.wav")
    assert resolve_run_dir(runs, str(clip), fetch=_no_network) == (runs / "clip", None)
    # a different file with the same stem still gets its own folder
    assert resolve_run_dir(runs, str(tmp_path / "clip.wav"), fetch=_no_network)[0] == runs / "clip-2"


def test_resolve_run_dir_local_file_uses_stem(tmp_path):
    runs = tmp_path / "runs"
    assert resolve_run_dir(runs, str(tmp_path / "clip.wav"), fetch=_no_network) == (runs / "clip", None)
    assert resolve_run_dir(runs, r"C:\music\Summer Of 69.mp3", fetch=_no_network)[0] == runs / "summer-of-69"
    # a stem with nothing left after folding keeps today's unicode slug
    assert resolve_run_dir(runs, "夜に駆ける.mp3", fetch=_no_network)[0] == runs / "夜に駆ける"
    _write_manifest(runs / "clip", str(tmp_path / "elsewhere" / "clip.wav"))
    assert resolve_run_dir(runs, str(tmp_path / "clip.wav"), fetch=_no_network)[0] == runs / "clip-2"
