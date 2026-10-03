"""Load and save pydantic artifacts as JSON files."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


class ArtifactError(Exception):
    def __init__(self, path: Path, detail: str) -> None:
        super().__init__(f"{path}: {detail}")
        self.path = path
        self.detail = detail


def _describe(exc: ValidationError) -> str:
    parts = []
    for err in exc.errors():
        loc = ".".join(str(p) for p in err["loc"]) or "<root>"
        msg = err["msg"].removeprefix("Value error, ")
        parts.append(f"{loc}: {msg}")
    return "; ".join(parts)


def load_model(path: Path, model: type[T]) -> T:
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ArtifactError(path, f"cannot read file ({exc.strerror or exc})") from exc
    try:
        return model.model_validate_json(text)
    except ValidationError as exc:
        raise ArtifactError(path, _describe(exc)) from exc


def save_model(path: Path, obj: BaseModel) -> None:
    path = Path(path)
    data = obj.model_dump_json(by_alias=True, indent=2)
    try:
        fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    except OSError as exc:
        raise ArtifactError(path, f"cannot write file ({exc.strerror or exc})") from exc
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(data)
        os.replace(tmp_name, path)
    except OSError as exc:
        Path(tmp_name).unlink(missing_ok=True)
        raise ArtifactError(path, f"cannot write file ({exc.strerror or exc})") from exc
