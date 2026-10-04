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


_TOP = f"ISMIR2019-Large-Vocabulary-Chord-Recognition-{vendoring.CHORD_MODEL_COMMIT}"


class _Runner:
    """Stands in for subprocess.run; only `git rev-parse HEAD` is ever expected."""

    def __init__(self, head=vendoring.CHORD_MODEL_COMMIT, missing=False):
        self.calls = []
        self.head = head
        self.missing = missing

    def __call__(self, argv, cwd=None, **kwargs):
        import subprocess

        self.calls.append((argv, cwd))
        if self.missing:
            raise FileNotFoundError("git")
        return subprocess.CompletedProcess(argv, 0, stdout=self.head + "\n", stderr="")


def _forbid(*args, **kwargs):
    raise AssertionError(f"no subprocess expected, got {args!r}")


def _archive(files, top=_TOP):
    import io
    import zipfile

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr(f"{top}/", b"")
        for rel, data in files.items():
            zf.writestr(f"{top}/{rel}", data)
    return buffer.getvalue()


class _Opener:
    """Stands in for urllib.request.urlopen; serves bytes, optionally failing part way."""

    def __init__(self, payload, fail_after=None):
        self.urls = []
        self.payload = payload
        self.fail_after = fail_after

    def __call__(self, url, timeout=None):
        import io

        self.urls.append(url)
        if self.fail_after is None:
            return io.BytesIO(self.payload)
        fail_after = self.fail_after

        class _Broken(io.BytesIO):
            def read(self, size=-1):
                if self.tell() >= fail_after:
                    raise ConnectionResetError("connection reset by peer")
                limit = fail_after - self.tell()
                return super().read(limit if size is None or size < 0 else min(size, limit))

        return _Broken(self.payload)


def _model_files():
    files = {"chord_recognition.py": b"# entry point\n"}
    for rel in vendoring.PATCH_SITES:
        files[rel] = b"x = np.int(3)\n"
    for n, rel in enumerate(vendoring.CHORD_MODEL_CHECKPOINT_SHA256):
        files[rel] = f"checkpoint {n}".encode()
    return files


@pytest.fixture
def model_cache(tmp_path, monkeypatch):
    """A cache dir, and checkpoint hashes matching the fake archive's files."""
    import hashlib

    monkeypatch.setenv("YOUKELELE_CACHE", str(tmp_path))
    hashes = {
        rel: hashlib.sha256(data).hexdigest()
        for rel, data in _model_files().items()
        if rel in vendoring.CHORD_MODEL_CHECKPOINT_SHA256
    }
    monkeypatch.setattr(vendoring, "CHORD_MODEL_CHECKPOINT_SHA256", hashes)
    return tmp_path


@pytest.fixture
def fake_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("YOUKELELE_CACHE", str(tmp_path))
    monkeypatch.setattr(vendoring, "patch_numpy_aliases", lambda root: {})
    monkeypatch.setattr(vendoring, "verify_checkpoints", lambda root: None)
    return tmp_path


def _leftovers(root):
    return [p.name for p in root.parent.iterdir() if p.name.startswith(root.name + ".partial")]


def test_ensure_chord_model_fetches_archive_without_git(model_cache, monkeypatch):
    import subprocess

    monkeypatch.setattr(subprocess, "run", _forbid)
    monkeypatch.setattr(subprocess, "Popen", _forbid)
    opener = _Opener(_archive(_model_files()))
    root = vendoring.ensure_chord_model(log=lambda m: None, run=_forbid, opener=opener)
    assert vendoring.CHORD_MODEL_ARCHIVE == (
        f"{vendoring.CHORD_MODEL_REPO}/archive/{vendoring.CHORD_MODEL_COMMIT}.zip"
    )
    assert opener.urls == [vendoring.CHORD_MODEL_ARCHIVE]
    assert root == vendoring.chord_model_dir()
    assert (root / "chord_recognition.py").read_bytes() == b"# entry point\n"
    assert (root / "COMMIT").read_text(encoding="ascii").strip() == vendoring.CHORD_MODEL_COMMIT
    assert (root / "results_ismir2017.py").read_text() == "x = int(3)\n"
    assert _leftovers(root) == []
    assert vendoring.chord_model_ready(run=_forbid)
    # a second setup finds the model complete and fetches nothing
    vendoring.ensure_chord_model(log=lambda m: None, run=_forbid, opener=opener)
    assert opener.urls == [vendoring.CHORD_MODEL_ARCHIVE]


def test_check_commit_reads_marker_file(tmp_path):
    (tmp_path / "COMMIT").write_text(vendoring.CHORD_MODEL_COMMIT + "\n")
    vendoring._check_commit(tmp_path, run=_forbid)
    (tmp_path / "COMMIT").write_text("abc\n")
    with pytest.raises(vendoring.VendoringError, match="expected 481f4ce7"):
        vendoring._check_commit(tmp_path, run=_forbid)
    (tmp_path / "COMMIT").unlink()
    with pytest.raises(vendoring.VendoringError, match="delete the folder"):
        vendoring._check_commit(tmp_path, run=_forbid)


def test_existing_clone_without_marker_is_accepted_when_git_matches(fake_cache):
    root = vendoring.chord_model_dir()
    (root / ".git").mkdir(parents=True)
    (root / "chord_recognition.py").write_text("")
    run = _Runner()
    opener = _Opener(b"")
    vendoring.ensure_chord_model(log=lambda m: None, run=run, opener=opener)
    assert run.calls == [(["git", "rev-parse", "HEAD"], root)]
    assert opener.urls == []
    with pytest.raises(vendoring.VendoringError, match="expected 481f4ce7"):
        vendoring.ensure_chord_model(log=lambda m: None, run=_Runner(head="abc"), opener=opener)
    assert not vendoring.chord_model_ready(run=_Runner(head="abc"))
    # a clone on a machine without git cannot be checked: start again from the zip
    with pytest.raises(vendoring.VendoringError, match="delete the folder"):
        vendoring._check_commit(root, run=_Runner(missing=True))


def test_partial_download_never_looks_complete(model_cache):
    payload = _archive(_model_files())
    root = vendoring.chord_model_dir()
    half = len(payload) // 2
    # the connection drops part way; the server ends early and the zip is truncated
    for broken in (_Opener(payload, fail_after=half), _Opener(payload[:half])):
        with pytest.raises(vendoring.VendoringError):
            vendoring.ensure_chord_model(log=lambda m: None, run=_forbid, opener=broken)
        assert not (root / "chord_recognition.py").exists()
        assert _leftovers(root) == []
        assert not vendoring.chord_model_ready(run=_forbid)
    vendoring.ensure_chord_model(log=lambda m: None, run=_forbid, opener=_Opener(payload))
    assert vendoring.chord_model_ready(run=_forbid)


def test_archive_with_more_than_one_folder_is_refused(model_cache):
    import io
    import zipfile

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("one/chord_recognition.py", b"")
        zf.writestr("two/chord_recognition.py", b"")
    with pytest.raises(vendoring.VendoringError, match="one folder"):
        vendoring.ensure_chord_model(
            log=lambda m: None, run=_forbid, opener=_Opener(buffer.getvalue())
        )
    root = vendoring.chord_model_dir()
    assert not root.exists() and _leftovers(root) == []


def test_ready_is_false_when_patch_sites_are_absent(fake_cache):
    root = vendoring.chord_model_dir()
    root.mkdir(parents=True)
    (root / "chord_recognition.py").write_text("")
    (root / "COMMIT").write_text(vendoring.CHORD_MODEL_COMMIT)
    assert not vendoring.chord_model_ready(run=_forbid)


def test_stale_read_only_partial_is_removed_before_fetch(model_cache):
    import os
    import stat

    partial = vendoring.chord_model_dir().with_name("chord_cnn_lstm.partial")
    (partial / ".git" / "objects").mkdir(parents=True)
    pack = partial / ".git" / "objects" / "x.pack"
    pack.write_text("data")
    os.chmod(pack, stat.S_IREAD)
    opener = _Opener(_archive(_model_files()))
    root = vendoring.ensure_chord_model(log=lambda m: None, run=_forbid, opener=opener)
    assert (root / "chord_recognition.py").exists()
    assert not (root / ".git").exists()
    assert _leftovers(root) == []


def test_install_scripts_exist_and_reference_each_other():
    from pathlib import Path

    repo = Path(__file__).resolve().parents[1]
    install_cmd = (repo / "install.cmd").read_text(encoding="ascii")
    assert '"%~dp0install.ps1"' in install_cmd and "-ExecutionPolicy Bypass" in install_cmd
    install_ps1 = (repo / "install.ps1").read_text(encoding="ascii")
    for needle in (
        "[1/4] Installing uv", "[2/4] Installing the tool", "[3/4] Fetching the models",
        "[4/4] Installing the PDF printer", "already present",
        "https://astral.sh/uv/install.ps1", "uv sync", "youkelele setup",
        "playwright install chromium",
        "Send the text above to the person who gave you this tool",
        "Ready. Double-click run-youkelele.cmd to make a sheet.",
    ):
        assert needle in install_ps1, needle
    run_cmd = (repo / "run-youkelele.cmd").read_text(encoding="ascii")
    assert "youkelele run" in run_cmd and "%~dp0runs" in run_cmd
    assert "07_render" in run_cmd and "sheet.pdf" in run_cmd and 'start ""' in run_cmd
    for name in ("install.cmd", "run-youkelele.cmd", "install.ps1"):
        data = (repo / name).read_bytes()
        # cmd.exe misreads labels in LF-only batch files; keep the Windows scripts CRLF
        assert data.count(b"\n") == data.count(b"\r\n"), name
    install_sh = (repo / "install.sh").read_text(encoding="ascii")
    assert "https://astral.sh/uv/install.sh" in install_sh and "youkelele setup" in install_sh
    run_sh = (repo / "run-youkelele.sh").read_text(encoding="ascii")
    assert "youkelele run" in run_sh and "xdg-open" in run_sh
    for name in ("install.sh", "run-youkelele.sh"):
        assert b"\r" not in (repo / name).read_bytes(), name
    assert "MIT License" in (repo / "LICENSE").read_text(encoding="utf-8")
