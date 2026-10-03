import pytest

from youkelele.layout import RunLayout, slug_for
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
