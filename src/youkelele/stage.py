"""The contract every pipeline stage implements."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path
from typing import ClassVar

from youkelele.layout import RunLayout
from youkelele.options import RunOptions


class MissingArtifact(Exception):
    def __init__(self, key: str, producer: str) -> None:
        super().__init__(f"missing artifact {key!r} (produced by stage {producer!r})")
        self.key = key
        self.producer = producer


class Stage(ABC):
    name: ClassVar[str]
    requires: ClassVar[tuple[str, ...]]
    produces: ClassVar[tuple[str, ...]]

    @abstractmethod
    def run(self, ctx: StageContext) -> None: ...


class StageContext:
    def __init__(
        self,
        layout: RunLayout,
        options: RunOptions,
        out_dir: Path,
        log: Callable[[str], None],
        stage: Stage | None = None,
    ) -> None:
        self.layout = layout
        self.options = options
        self.out_dir = Path(out_dir)
        self.log = log
        self.stage = stage
        self.notes: dict[str, str] = {}

    def input(self, key: str) -> Path:
        path = self.layout.path(key)
        if not path.exists():
            raise MissingArtifact(key, self.layout.producer(key))
        return path

    def output(self, key: str) -> Path:
        if self.stage is not None:
            assert key in self.stage.produces, f"{key!r} is not declared in produces"
        _, _, rest = key.partition("/")
        path = self.out_dir / rest
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def note(self, key: str, value: str) -> None:
        self.notes[key] = value
