"""Fetch and verify the vendored Chord-CNN-LSTM model (pinned commit, patched, hash-checked)."""

from __future__ import annotations

import hashlib
import re
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


def ensure_chord_model(log: Callable[[str], None] = print) -> Path:
    root = chord_model_dir()
    if not (root / "chord_recognition.py").exists():
        log(f"cloning {CHORD_MODEL_REPO} into {root}")
        root.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", CHORD_MODEL_REPO, str(root)], check=True)
        subprocess.run(["git", "checkout", CHORD_MODEL_COMMIT], cwd=root, check=True)
    counts = patch_numpy_aliases(root)
    changed = {rel: n for rel, n in counts.items() if n}
    log(f"patched np.int in {sum(changed.values())} places" if changed else "np.int patch already applied")
    verify_checkpoints(root)
    log(f"chord model ready at commit {CHORD_MODEL_COMMIT[:8]}, checkpoints verified")
    return root


def chord_model_ready() -> bool:
    root = chord_model_dir()
    if not (root / "chord_recognition.py").exists():
        return False
    try:
        verify_checkpoints(root)
        text = [(root / rel).read_text(encoding="utf-8") for rel in PATCH_SITES]
    except (VendoringError, OSError):
        return False
    return not any(_NP_INT.search(t) for t in text)
