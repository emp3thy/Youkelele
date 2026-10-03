"""The per-run manifest recording which stages finished and with what inputs."""

from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path

from youkelele.jsonio import load_model, save_model
from youkelele.options import RunOptions
from youkelele.schemas import _Artifact

MANIFEST_NAME = "manifest.json"


class StageRecord(_Artifact):
    name: str
    number: int
    finished_at: datetime
    version: str
    input_hashes: dict[str, str]
    notes: dict[str, str]


class Manifest(_Artifact):
    slug: str
    source: str
    instrument: str
    options: RunOptions
    stages: dict[str, StageRecord]


def load_manifest(run_dir: Path) -> Manifest | None:
    path = Path(run_dir) / MANIFEST_NAME
    if not path.exists():
        return None
    return load_model(path, Manifest)


def save_manifest(run_dir: Path, m: Manifest) -> None:
    save_model(Path(run_dir) / MANIFEST_NAME, m)


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()
