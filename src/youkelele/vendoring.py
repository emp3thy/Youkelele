"""Fetch and verify the vendored Chord-CNN-LSTM model (pinned commit, patched, hash-checked)."""

from __future__ import annotations

import hashlib
import http.client
import os
import re
import shutil
import stat
import subprocess
import urllib.request
import zipfile
from collections.abc import Callable
from pathlib import Path

from youkelele.paths import cache_dir

CHORD_MODEL_REPO = "https://github.com/music-x-lab/ISMIR2019-Large-Vocabulary-Chord-Recognition"
CHORD_MODEL_COMMIT = "481f4ce703f8822b99f4037e9104ba1760e21ea3"
# GitHub's zip of the pinned commit: its checkpoints hash identically to a clone's
CHORD_MODEL_ARCHIVE = f"{CHORD_MODEL_REPO}/archive/{CHORD_MODEL_COMMIT}.zip"
# written by the archive fetch: the commit the folder holds, since a zip has no git history
COMMIT_MARKER = "COMMIT"
_DOWNLOAD_TIMEOUT_S = 60

_CHECKPOINT = "cache_data/joint_chord_net_ismir_naive_v1.0_reweight(0.0,10.0)_s{n}.best.sdict"
CHORD_MODEL_CHECKPOINT_SHA256: dict[str, str] = {
    _CHECKPOINT.format(n=0): "921b42d5d1cf9ce1c0c0e45a74d409b8066e0acec46058ef74e24ee0fb540761",
    _CHECKPOINT.format(n=1): "bcb75859e0efa256696cf5da396b320093317b9b1d9560c304f46c25fe1f8b17",
    _CHECKPOINT.format(n=2): "acddf85c3fff29954c4877021177d72e2cba9f729ce80c1010f054c477bf3f61",
    _CHECKPOINT.format(n=3): "65d81a3ab73435aaaade586981b4cabdf57b8953d76052703e6968c32ef8421c",
    _CHECKPOINT.format(n=4): "5ff6b0ec85640e17a09a9b3de68c93fdd45adc24488e8fa9be5715c28d561122",
}

# file -> number of `np.int` aliases removed by NumPy 1.24
PATCH_SITES: dict[str, int] = {
    "extractors/xhmm_ismir.py": 7,
    "extractors/xhmm_decoder.py": 7,
    "results_ismir2017.py": 1,
    "extractors/beat_preprocess.py": 2,
}

_NP_INT = re.compile(r"\bnp\.int\b")

Runner = Callable[..., "subprocess.CompletedProcess[str]"]
Opener = Callable[..., object]


class VendoringError(Exception):
    pass


def chord_model_dir() -> Path:
    return cache_dir() / "models" / "chord_cnn_lstm"


def patch_numpy_aliases(root: Path) -> dict[str, int]:
    """Replace the removed `np.int` alias with `int`; returns replacements per file."""
    counts: dict[str, int] = {}
    for rel in PATCH_SITES:
        path = root / rel
        text = path.read_text(encoding="utf-8")
        patched, n = _NP_INT.subn("int", text)
        if n:
            path.write_text(patched, encoding="utf-8", newline="")
        counts[rel] = n
    return counts


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_checkpoints(root: Path) -> None:
    for rel, expected in CHORD_MODEL_CHECKPOINT_SHA256.items():
        path = root / rel
        if not path.exists():
            raise VendoringError(f"chord model checkpoint missing: {rel}")
        actual = _sha256(path)
        if actual != expected:
            raise VendoringError(
                f"chord model checkpoint {rel} has sha256 {actual}, expected {expected}"
            )


def _start_again(root: Path) -> str:
    return f"delete the folder {root} and run youkelele setup"


def _clone_head(root: Path, run: Runner) -> str:
    """The commit of a folder cloned by an earlier version; needs git only for such a folder."""
    try:
        result = run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
        )
    except FileNotFoundError as exc:
        raise VendoringError(
            f"the chord model at {root} was cloned with git, which is not on PATH, "
            f"so its commit cannot be checked; {_start_again(root)}"
        ) from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "").strip()
        raise VendoringError(
            f"git rev-parse HEAD failed in {root}: {detail}; {_start_again(root)}"
        ) from exc
    return (result.stdout or "").strip()


def _check_commit(root: Path, run: Runner = subprocess.run) -> None:
    """The commit recorded by the archive fetch, or an earlier version's clone's HEAD."""
    marker = root / COMMIT_MARKER
    if marker.exists():
        found = marker.read_text(encoding="ascii", errors="replace").strip()
    elif (root / ".git").exists():
        found = _clone_head(root, run)
    else:
        raise VendoringError(
            f"the chord model at {root} has no record of its commit; {_start_again(root)}"
        )
    if found != CHORD_MODEL_COMMIT:
        raise VendoringError(
            f"chord model at {root} is at {found or 'an unknown commit'}, "
            f"expected {CHORD_MODEL_COMMIT}; {_start_again(root)}"
        )


def _rmtree_force(path: Path) -> None:
    """Remove a tree including read-only files (an earlier version's git pack files on Windows)."""

    def _retry(func, failing, exc):
        os.chmod(failing, stat.S_IWRITE)
        func(failing)

    if not path.exists():
        return
    try:
        shutil.rmtree(path, onexc=_retry)
    except OSError as exc:
        raise VendoringError(f"could not remove {path}: {exc}") from exc


def _unpack_single_folder(archive: Path, dest: Path) -> None:
    """Extract the archive's one top-level folder so that its contents land directly in dest."""
    try:
        with zipfile.ZipFile(archive) as zf:
            members = zf.infolist()
            tops = {member.filename.split("/", 1)[0] for member in members}
            if len(tops) != 1:
                raise VendoringError(
                    f"the chord model archive should hold one folder, found {len(tops)} "
                    "top-level entries; run youkelele setup again"
                )
            dest.mkdir()
            for member in members:
                inner = member.filename.split("/", 1)[1] if "/" in member.filename else ""
                if not inner:
                    continue
                # zipfile reads by orig_filename and sanitises the new name when extracting
                member.filename = inner
                zf.extract(member, dest)
    except (zipfile.BadZipFile, EOFError) as exc:
        raise VendoringError(
            f"the downloaded chord model archive is damaged ({exc}); run youkelele setup again"
        ) from exc
    except OSError as exc:
        raise VendoringError(f"could not unpack the chord model into {dest}: {exc}") from exc


def _fetch_archive(
    root: Path, log: Callable[[str], None], opener: Opener = urllib.request.urlopen
) -> None:
    """Download the pinned commit as a zip and unpack it beside root, then rename into place,
    so an interrupted fetch never looks complete. Needs no git."""
    log(f"downloading {CHORD_MODEL_ARCHIVE}")
    root.parent.mkdir(parents=True, exist_ok=True)
    archive = root.with_name(root.name + ".partial.zip")
    partial = root.with_name(root.name + ".partial")
    _rmtree_force(partial)
    archive.unlink(missing_ok=True)
    try:
        try:
            with opener(CHORD_MODEL_ARCHIVE, timeout=_DOWNLOAD_TIMEOUT_S) as response:
                with archive.open("wb") as out:
                    shutil.copyfileobj(response, out, 1 << 20)
        except (OSError, http.client.HTTPException) as exc:
            raise VendoringError(
                f"could not download the chord model from {CHORD_MODEL_ARCHIVE}: {exc}; "
                "check the internet connection and run youkelele setup again"
            ) from exc
        log(f"downloaded {archive.stat().st_size / 1e6:.1f} MB, unpacking")
        _unpack_single_folder(archive, partial)
        if not (partial / "chord_recognition.py").exists():
            raise VendoringError(
                "the chord model archive has no chord_recognition.py; run youkelele setup again"
            )
        (partial / COMMIT_MARKER).write_text(CHORD_MODEL_COMMIT + "\n", encoding="ascii")
        _rmtree_force(root)
        try:
            partial.rename(root)
        except OSError as exc:
            raise VendoringError(f"could not move the chord model into {root}: {exc}") from exc
    except BaseException:
        _rmtree_force(partial)
        archive.unlink(missing_ok=True)
        raise
    archive.unlink(missing_ok=True)


def ensure_chord_model(
    log: Callable[[str], None] = print,
    run: Runner = subprocess.run,
    opener: Opener = urllib.request.urlopen,
) -> Path:
    root = chord_model_dir()
    if (root / "chord_recognition.py").exists():
        _check_commit(root, run)
    else:
        _fetch_archive(root, log, opener)
    counts = patch_numpy_aliases(root)
    changed = {rel: n for rel, n in counts.items() if n}
    log(f"patched np.int in {sum(changed.values())} places" if changed else "np.int patch already applied")
    verify_checkpoints(root)
    log(f"chord model ready at commit {CHORD_MODEL_COMMIT[:8]}, checkpoints verified")
    return root


def chord_model_ready(run: Runner = subprocess.run) -> bool:
    root = chord_model_dir()
    if not (root / "chord_recognition.py").exists():
        return False
    try:
        _check_commit(root, run)
        verify_checkpoints(root)
        text = [(root / rel).read_text(encoding="utf-8") for rel in PATCH_SITES]
    except (VendoringError, OSError):
        return False
    return not any(_NP_INT.search(t) for t in text)
