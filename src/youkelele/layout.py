"""Run directory layout: numbered stage folders and artifact keys."""

from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path

_YOUTUBE_ID = re.compile(r"(?:[?&]v=|youtu\.be/|shorts/)([A-Za-z0-9_-]{11})")


def slug_for(source: str) -> str:
    match = _YOUTUBE_ID.search(source)
    if match:
        return match.group(1).lower()
    name = re.split(r"[\\/]", source.rstrip("\\/"))[-1]
    stem = name.rsplit(".", 1)[0] if "." in name else name
    return re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")


class RunLayout:
    def __init__(self, run_dir: Path, stage_names: Sequence[str]) -> None:
        self.run_dir = Path(run_dir)
        self.stage_names = list(stage_names)

    def number(self, stage: str) -> int:
        return self.stage_names.index(stage)

    def folder(self, stage: str) -> Path:
        return self.run_dir / f"{self.number(stage):02d}_{stage}"

    def producer(self, key: str) -> str:
        return key.split("/", 1)[0]

    def path(self, key: str) -> Path:
        stage, _, rest = key.partition("/")
        return self.folder(stage) / rest
