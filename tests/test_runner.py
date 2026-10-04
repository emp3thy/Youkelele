import pytest

from tests.fakes import make_fake_stage as fake
from youkelele.manifest import Manifest, load_manifest
from youkelele.options import RunOptions
from youkelele.profiles import get_profile
from youkelele.runner import (
    StageFailed,
    build_chain,
    resolve_stage,
    run_chain,
    status,
)
from youkelele.stage import MissingArtifact
from youkelele.stages.render import RenderStage


@pytest.fixture
def opts():
    return RunOptions(source="song.wav", tier="full")


def two_stages():
    return [fake("a", (), ("a/a.txt",)), fake("b", ("a/a.txt",), ("b/b.txt",))]


def quiet(_msg):
    pass


def test_run_from_zero_creates_numbered_folders_and_manifest(tmp_path, opts):
    m = run_chain(tmp_path, two_stages(), opts, log=quiet)
    assert (tmp_path / "00_a" / "a.txt").read_text() == "a/a.txt"
    assert (tmp_path / "01_b" / "b.txt").read_text() == "b/b.txt"
    assert set(m.stages) == {"a", "b"}
    assert set(load_manifest(tmp_path).stages) == {"a", "b"}
    rec = m.stages["b"]
    assert rec.number == 1 and list(rec.input_hashes) == ["a/a.txt"]
    assert rec.finished_at.tzinfo is not None


def test_from_refuses_when_input_missing(tmp_path, opts):
    with pytest.raises(MissingArtifact) as e:
        run_chain(tmp_path, two_stages(), opts, start=1, log=quiet)
    assert e.value.key == "a/a.txt" and e.value.producer == "a"


def test_failure_leaves_earlier_outputs_and_no_tmp(tmp_path, opts):
    chain = [fake("a", (), ("a/a.txt",)), fake("b", ("a/a.txt",), ("b/b.txt",), fail=True)]
    with pytest.raises(StageFailed) as e:
        run_chain(tmp_path, chain, opts, log=quiet)
    assert "--from 1" in e.value.resume_command
    assert e.value.stage == "b" and e.value.number == 1
    assert isinstance(e.value.cause, RuntimeError)
    assert (tmp_path / "00_a" / "a.txt").exists()
    assert not list(tmp_path.glob(".tmp_*"))
    assert not (tmp_path / "01_b").exists()


def test_failed_rerun_keeps_previous_output(tmp_path, opts):
    run_chain(tmp_path, two_stages(), opts, log=quiet)
    bad = [two_stages()[0], fake("b", ("a/a.txt",), ("b/b.txt",), fail=True)]
    with pytest.raises(StageFailed):
        run_chain(tmp_path, bad, opts, start=1, log=quiet)
    assert (tmp_path / "01_b" / "b.txt").exists()


def test_rerun_replaces_existing_folder(tmp_path, opts):
    run_chain(tmp_path, two_stages(), opts, log=quiet)
    (tmp_path / "01_b" / "stale.txt").write_text("x")
    run_chain(tmp_path, two_stages(), opts, start=1, log=quiet)
    assert not (tmp_path / "01_b" / "stale.txt").exists()
    assert (tmp_path / "01_b" / "b.txt").exists()


def test_rerun_from_later_stage_reuses_saved_options(tmp_path, opts):
    seen = []
    chain = [
        fake("a", (), ("a/a.txt",)),
        fake("b", ("a/a.txt",), ("b/b.txt",), body=lambda ctx: seen.append(ctx.options.tier)),
    ]
    run_chain(tmp_path, chain, opts, log=quiet)
    run_chain(tmp_path, chain, None, start=1, log=quiet)
    assert seen == ["full", "full"]


def test_given_options_win_over_manifest(tmp_path, opts):
    run_chain(tmp_path, two_stages(), opts, log=quiet)
    run_chain(
        tmp_path, two_stages(), opts.model_copy(update={"tier": "easy"}), start=1, log=quiet
    )
    assert load_manifest(tmp_path).options.tier == "easy"


def test_no_options_and_no_manifest_is_error(tmp_path):
    with pytest.raises(ValueError):
        run_chain(tmp_path, two_stages(), None, log=quiet)


def test_notes_recorded(tmp_path, opts):
    chain = [fake("a", (), ("a/a.txt",), body=lambda ctx: ctx.note("k", "v"))]
    assert run_chain(tmp_path, chain, opts, log=quiet).stages["a"].notes == {"k": "v"}


def test_end_limits_stages(tmp_path, opts):
    m = run_chain(tmp_path, two_stages(), opts, end=0, log=quiet)
    assert set(m.stages) == {"a"}


def test_status_reports_stale_after_input_edit(tmp_path, opts):
    chain = two_stages()
    assert status(tmp_path, chain) == [("a", "missing"), ("b", "missing")]
    run_chain(tmp_path, chain, opts, log=quiet)
    assert status(tmp_path, chain) == [("a", "done"), ("b", "done")]
    (tmp_path / "00_a" / "a.txt").write_text("edited")
    assert status(tmp_path, chain) == [("a", "done"), ("b", "stale")]
    (tmp_path / "00_a" / "a.txt").unlink()
    assert status(tmp_path, chain)[1] == ("b", "stale")


def test_status_is_stale_when_a_required_input_was_never_recorded(tmp_path, opts):
    old = [fake("a", (), ("a/a.txt", "a/x.txt")), fake("b", ("a/a.txt",), ("b/b.txt",))]
    run_chain(tmp_path, old, opts, log=quiet)
    assert status(tmp_path, old) == [("a", "done"), ("b", "done")]
    # the same stage now also requires a/x.txt, which its recorded run never hashed
    new = [old[0], fake("b", ("a/a.txt", "a/x.txt"), ("b/b.txt",))]
    assert status(tmp_path, new) == [("a", "done"), ("b", "stale")]


def test_resolve_stage_by_name_and_number():
    chain = two_stages()
    assert resolve_stage(chain, "b") == 1
    assert resolve_stage(chain, "0") == 0
    for bad in ("zzz", "5", "-1"):
        with pytest.raises(ValueError):
            resolve_stage(chain, bad)


def test_get_profile_unknown_lists_names():
    assert get_profile("ukulele").tuning.pitches == ("G4", "C4", "E4", "A4")
    with pytest.raises(KeyError, match="ukulele"):
        get_profile("banjo")


def test_build_chain_appends_render_after_profile_stages():
    a, b = fake("a"), fake("b")
    profile = get_profile("ukulele")
    chain = build_chain(type(profile)("x", profile.tuning, (b,)), [a])
    assert chain[:2] == [a, b]
    assert [s.name for s in chain] == ["a", "b", "render"]
    assert isinstance(chain[-1], RenderStage)


def test_resume_command_names_non_default_runs_dir_and_instrument(tmp_path):
    chain = [fake("a", (), ("a/a.txt",), fail=True)]
    opts = RunOptions(source='my "song".wav')
    with pytest.raises(StageFailed) as e:
        run_chain(tmp_path, chain, opts, log=quiet, runs_dir="out", instrument="guitar")
    assert e.value.resume_command == (
        'youkelele run "my \\"song\\".wav" --from 0 --runs-dir "out" --instrument guitar'
    )


def test_resume_command_omits_defaults(tmp_path):
    chain = [fake("a", (), ("a/a.txt",), fail=True)]
    with pytest.raises(StageFailed) as e:
        run_chain(tmp_path, chain, RunOptions(source="song.wav"), log=quiet)
    assert e.value.resume_command == 'youkelele run "song.wav" --from 0'


def test_manifest_records_video_id_and_title_slug(tmp_path):
    run_dir = tmp_path / "summer-of-69"
    opts = RunOptions(source="https://www.youtube.com/watch?v=eFjjO_lhf9c")
    m = run_chain(run_dir, two_stages(), opts, log=quiet)
    assert (m.slug, m.video_id, m.title_slug) == ("summer-of-69", "eFjjO_lhf9c", "summer-of-69")
    saved = load_manifest(run_dir)
    assert (saved.video_id, saved.title_slug) == ("eFjjO_lhf9c", "summer-of-69")
    run_chain(run_dir, two_stages(), None, start=1, log=quiet)
    assert (load_manifest(run_dir).video_id, load_manifest(run_dir).title_slug) == (
        "eFjjO_lhf9c", "summer-of-69",
    )
    local = run_chain(tmp_path / "clip", two_stages(), RunOptions(source="clip.wav"), log=quiet)
    assert (local.video_id, local.title_slug) == (None, "clip")


def test_manifest_without_new_fields_loads():
    old = {
        "schema": 1,
        "slug": "9f06qzcvuhg",
        "source": "https://www.youtube.com/watch?v=9f06QZCVUHg",
        "instrument": "ukulele",
        "options": {"source": "https://www.youtube.com/watch?v=9f06QZCVUHg"},
        "stages": {},
    }
    m = Manifest.model_validate(old)
    assert (m.video_id, m.title_slug, m.schema_version) == (None, None, 1)


def test_runner_leaves_source_meta_alone(tmp_path, opts):
    (tmp_path / "source_meta.json").write_text("{}", encoding="utf-8")
    run_chain(tmp_path, two_stages(), opts, log=quiet)
    run_chain(tmp_path, two_stages(), opts, start=1, log=quiet)
    assert (tmp_path / "source_meta.json").read_text(encoding="utf-8") == "{}"
    assert status(tmp_path, two_stages()) == [("a", "done"), ("b", "done")]
