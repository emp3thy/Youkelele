import pytest

from youkelele import vendoring


def test_patch_numpy_aliases_rewrites_only_np_int(tmp_path):
    for rel in vendoring.PATCH_SITES:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text("np.int(3) np.int64 np.integer\n")
    counts = vendoring.patch_numpy_aliases(tmp_path)
    assert counts == {rel: 1 for rel in vendoring.PATCH_SITES}
    assert (tmp_path / "results_ismir2017.py").read_text() == "int(3) np.int64 np.integer\n"
    assert set(vendoring.patch_numpy_aliases(tmp_path).values()) == {0}


@pytest.mark.slow
def test_patch_counts_on_real_clone():
    if not vendoring.chord_model_ready():
        pytest.skip("chord model not installed")
    root = vendoring.chord_model_dir()
    for rel in vendoring.PATCH_SITES:
        assert "np.int(" not in (root / rel).read_text(), rel
    assert vendoring.PATCH_SITES == {
        "extractors/xhmm_ismir.py": 7, "extractors/xhmm_decoder.py": 7,
        "results_ismir2017.py": 1, "extractors/beat_preprocess.py": 2,
    }


class _Runner:
    def __init__(self, head=vendoring.CHORD_MODEL_COMMIT, fail_on=None, missing=False):
        self.calls = []
        self.head = head
        self.fail_on = fail_on
        self.missing = missing

    def __call__(self, argv, cwd=None, **kwargs):
        import subprocess
        from pathlib import Path

        self.calls.append((argv, cwd))
        if self.missing:
            raise FileNotFoundError("git")
        if argv[1] == self.fail_on:
            raise subprocess.CalledProcessError(1, argv, stderr="boom")
        if argv[1] == "clone":
            Path(argv[3]).mkdir(parents=True)
            (Path(argv[3]) / "chord_recognition.py").write_text("")
        return subprocess.CompletedProcess(argv, 0, stdout=self.head + "\n", stderr="")


@pytest.fixture
def fake_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("YOUKELELE_CACHE", str(tmp_path))
    monkeypatch.setattr(vendoring, "patch_numpy_aliases", lambda root: {})
    monkeypatch.setattr(vendoring, "verify_checkpoints", lambda root: None)
    return tmp_path


def _existing_clone():
    root = vendoring.chord_model_dir()
    root.mkdir(parents=True)
    (root / "chord_recognition.py").write_text("")
    return root


def test_clone_checks_out_pinned_commit_then_renames(fake_cache):
    run = _Runner()
    root = vendoring.ensure_chord_model(log=lambda m: None, run=run)
    partial = root.with_name("chord_cnn_lstm.partial")
    assert [c[0] for c in run.calls] == [
        ["git", "clone", vendoring.CHORD_MODEL_REPO, str(partial)],
        ["git", "checkout", vendoring.CHORD_MODEL_COMMIT],
        ["git", "rev-parse", "HEAD"],
    ]
    assert [c[1] for c in run.calls] == [None, partial, partial]
    assert (root / "chord_recognition.py").exists() and not partial.exists()


def test_existing_clone_is_checked_with_rev_parse(fake_cache):
    root = _existing_clone()
    run = _Runner()
    vendoring.ensure_chord_model(log=lambda m: None, run=run)
    assert run.calls == [(["git", "rev-parse", "HEAD"], root)]


def test_unpinned_head_raises_and_is_not_ready(fake_cache):
    _existing_clone()
    with pytest.raises(vendoring.VendoringError, match="expected 481f4ce7"):
        vendoring.ensure_chord_model(log=lambda m: None, run=_Runner(head="abc"))
    assert not vendoring.chord_model_ready(run=_Runner(head="abc"))


def test_ready_is_false_when_patch_sites_are_absent(fake_cache):
    _existing_clone()
    run = _Runner()
    assert not vendoring.chord_model_ready(run=run)
    assert run.calls == [(["git", "rev-parse", "HEAD"], vendoring.chord_model_dir())]


def test_failed_checkout_leaves_no_complete_looking_clone(fake_cache):
    with pytest.raises(vendoring.VendoringError, match="checkout"):
        vendoring.ensure_chord_model(log=lambda m: None, run=_Runner(fail_on="checkout"))
    assert not (vendoring.chord_model_dir() / "chord_recognition.py").exists()
    vendoring.ensure_chord_model(log=lambda m: None, run=_Runner())
    assert (vendoring.chord_model_dir() / "chord_recognition.py").exists()


def test_missing_git_raises_vendoring_error(fake_cache):
    with pytest.raises(vendoring.VendoringError, match="git is not installed"):
        vendoring.ensure_chord_model(log=lambda m: None, run=_Runner(missing=True))


def test_stale_read_only_partial_is_removed_before_clone(fake_cache):
    import os
    import stat

    partial = vendoring.chord_model_dir().with_name("chord_cnn_lstm.partial")
    (partial / ".git" / "objects").mkdir(parents=True)
    pack = partial / ".git" / "objects" / "x.pack"
    pack.write_text("data")
    os.chmod(pack, stat.S_IREAD)
    root = vendoring.ensure_chord_model(log=lambda m: None, run=_Runner())
    assert (root / "chord_recognition.py").exists()
    assert not partial.exists()


def test_failed_checkout_removes_partial_immediately(fake_cache):
    partial = vendoring.chord_model_dir().with_name("chord_cnn_lstm.partial")
    with pytest.raises(vendoring.VendoringError):
        vendoring.ensure_chord_model(log=lambda m: None, run=_Runner(fail_on="checkout"))
    assert not partial.exists()
    with pytest.raises(vendoring.VendoringError):
        vendoring.ensure_chord_model(log=lambda m: None, run=_Runner(head="abc"))
    assert not partial.exists()
