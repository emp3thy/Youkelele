"""Drives stages in order with atomic outputs, resume and staleness status."""

from __future__ import annotations

import os
import shutil
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from youkelele import __version__
from youkelele.layout import DEFAULT_RUNS_DIR, RunLayout, video_id_for
from youkelele.manifest import (
    Manifest,
    StageRecord,
    hash_file,
    load_manifest,
    save_manifest,
)
from youkelele.options import RunOptions
from youkelele.profiles.base import InstrumentProfile
from youkelele.stage import MissingArtifact, Stage, StageContext
from youkelele.stages.ingest import IngestStage
from youkelele.stages.grid import GridStage
from youkelele.stages.harmony import HarmonyStage
from youkelele.stages.render import RenderStage
from youkelele.stages.separate import SeparateStage

GENERIC_STAGES: tuple[Stage, ...] = (IngestStage(), SeparateStage(), GridStage(), HarmonyStage())


class StageFailed(Exception):
    def __init__(
        self, stage: str, number: int, cause: Exception, resume_command: str
    ) -> None:
        super().__init__(f"stage {stage!r} ({number}) failed: {cause}")
        self.stage = stage
        self.number = number
        self.cause = cause
        self.resume_command = resume_command


def build_chain(
    profile: InstrumentProfile, generic: Sequence[Stage] = GENERIC_STAGES
) -> list[Stage]:
    return [*generic, *profile.stages, RenderStage()]


def resolve_stage(chain: Sequence[Stage], ref: str) -> int:
    names = [s.name for s in chain]
    if ref in names:
        return names.index(ref)
    try:
        number = int(ref)
    except ValueError:
        raise ValueError(f"unknown stage {ref!r}; known: {', '.join(names)}") from None
    if not 0 <= number < len(chain):
        raise ValueError(f"stage number {number} out of range 0..{len(chain) - 1}")
    return number


def check_requirements(
    chain: Sequence[Stage], layout: RunLayout, start: int, end: int
) -> list[MissingArtifact]:
    missing: list[MissingArtifact] = []
    for index in range(start, end + 1):
        for key in chain[index].requires:
            producer = layout.producer(key)
            produced_earlier = any(
                chain[j].name == producer for j in range(start, index)
            )
            if not produced_earlier and not layout.path(key).exists():
                missing.append(MissingArtifact(key, producer))
    return missing


def _quote(text: str) -> str:
    """Double-quote an argument so a pasted command survives "&" and spaces in any shell."""
    return '"' + text.replace('"', '\\"') + '"'


def resume_command(
    source: str, number: int, runs_dir: str | Path = DEFAULT_RUNS_DIR, instrument: str = "ukulele"
) -> str:
    parts = ["youkelele run", _quote(source), f"--from {number}"]
    if Path(runs_dir) != Path(DEFAULT_RUNS_DIR):
        parts.append(f"--runs-dir {_quote(str(runs_dir))}")
    if instrument != "ukulele":
        parts.append(f"--instrument {instrument}")
    return " ".join(parts)


def _move_into_place(tmp: Path, final: Path) -> None:
    if final.exists():
        shutil.rmtree(final)
    try:
        os.replace(tmp, final)
    except OSError:
        shutil.move(str(tmp), str(final))


def run_chain(
    run_dir: Path,
    chain: Sequence[Stage],
    options: RunOptions | None,
    start: int = 0,
    end: int | None = None,
    log: Callable[[str], None] = print,
    *,
    runs_dir: str | Path = DEFAULT_RUNS_DIR,
    instrument: str | None = None,
) -> Manifest:
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    last = len(chain) - 1 if end is None else end
    layout = RunLayout(run_dir, [s.name for s in chain])

    missing = check_requirements(chain, layout, start, last)
    if missing:
        raise missing[0]

    manifest = load_manifest(run_dir)
    if options is None:
        if manifest is None:
            raise ValueError("no saved options: pass options for the first run")
        options = manifest.options
    if manifest is None:
        # the folder name is the one layout.resolve_run_dir chose; a later run keeps these
        # fields as saved, so a manifest from before 1.4 leaves them unset
        manifest = Manifest(
            slug=run_dir.name,
            source=options.source,
            instrument=options.instrument,
            options=options,
            stages={},
            video_id=video_id_for(options.source),
            title_slug=run_dir.name,
        )
    else:
        manifest = manifest.model_copy(
            update={
                "options": options,
                "source": options.source,
                "instrument": options.instrument,
            }
        )
    save_manifest(run_dir, manifest)

    for number in range(start, last + 1):
        stage = chain[number]
        tmp = run_dir / f".tmp_{number:02d}_{stage.name}"
        if tmp.exists():
            shutil.rmtree(tmp)
        tmp.mkdir(parents=True)
        log(f"[{number:02d}] {stage.name}")
        ctx = StageContext(layout, options, tmp, log, stage)
        try:
            stage.run(ctx)
        except Exception as exc:
            shutil.rmtree(tmp, ignore_errors=True)
            raise StageFailed(
                stage.name,
                number,
                exc,
                resume_command(
                    options.source, number, runs_dir, instrument or options.instrument
                ),
            ) from exc
        _move_into_place(tmp, layout.folder(stage.name))
        manifest.stages[stage.name] = StageRecord(
            name=stage.name,
            number=number,
            finished_at=datetime.now(UTC),
            version=__version__,
            input_hashes={k: hash_file(layout.path(k)) for k in stage.requires},
            notes=dict(ctx.notes),
        )
        save_manifest(run_dir, manifest)
    return manifest


def status(
    run_dir: Path, chain: Sequence[Stage]
) -> list[tuple[str, Literal["done", "stale", "missing"]]]:
    run_dir = Path(run_dir)
    layout = RunLayout(run_dir, [s.name for s in chain])
    manifest = load_manifest(run_dir)
    result: list[tuple[str, Literal["done", "stale", "missing"]]] = []
    for stage in chain:
        record = manifest.stages.get(stage.name) if manifest else None
        if record is None:
            result.append((stage.name, "missing"))
            continue
        # an input the stage now requires but the record never hashed (an older version's
        # output) cannot be shown fresh
        fresh = all(key in record.input_hashes for key in stage.requires)
        for key, recorded in record.input_hashes.items():
            path = layout.path(key)
            if not path.exists() or hash_file(path) != recorded:
                fresh = False
                break
        result.append((stage.name, "done" if fresh else "stale"))
    return result
