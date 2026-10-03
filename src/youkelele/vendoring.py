"""Fetch and verify the vendored Chord-CNN-LSTM model (pinned commit, patched, hash-checked)."""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

from youkelele.paths import cache_dir

CHORD_MODEL_REPO = "https://github.com/music-x-lab/ISMIR2019-Large-Vocabulary-Chord-Recognition"
CHORD_MODEL_COMMIT = "481f4ce703f8822b99f4037e9104ba1760e21ea3"

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


def _git(args: list[str], cwd: Path | None, run: Runner) -> str:
    try:
        result = run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise VendoringError("git is not installed or not on PATH; install git and retry") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "").strip()
        raise VendoringError(f"git {' '.join(args)} failed: {detail}") from exc
    return result.stdout or ""


def _check_commit(root: Path, run: Runner) -> None:
    head = _git(["rev-parse", "HEAD"], root, run).strip()
    if head != CHORD_MODEL_COMMIT:
        raise VendoringError(
            f"chord model at {root} is at {head or 'an unknown commit'}, "
            f"expected {CHORD_MODEL_COMMIT}; delete the folder and run youkelele setup"
        )


def _clone(root: Path, run: Runner, log: Callable[[str], None]) -> None:
    """Clone into a sibling folder and rename, so a partial clone never looks complete."""
    log(f"cloning {CHORD_MODEL_REPO} into {root}")
    root.parent.mkdir(parents=True, exist_ok=True)
    partial = root.with_name(root.name + ".partial")
    shutil.rmtree(partial, ignore_errors=True)
    _git(["clone", CHORD_MODEL_REPO, str(partial)], None, run)
    _git(["checkout", CHORD_MODEL_COMMIT], partial, run)
    _check_commit(partial, run)
    shutil.rmtree(root, ignore_errors=True)
    partial.rename(root)


def ensure_chord_model(
    log: Callable[[str], None] = print, run: Runner = subprocess.run
) -> Path:
    root = chord_model_dir()
    if (root / "chord_recognition.py").exists():
        _check_commit(root, run)
    else:
        _clone(root, run, log)
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
