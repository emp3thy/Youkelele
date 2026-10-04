"""Command bodies for the youkelele CLI."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from youkelele.jsonio import ArtifactError
from youkelele.layout import find_run_by_name, resolve_run_dir
from youkelele.manifest import MANIFEST_NAME, load_manifest
from youkelele.models.ytdl import MetadataError, fetch_metadata
from youkelele.options import RunOptions
from youkelele.preflight import check_environment, metadata_problem
from youkelele.profiles import get_profile
from youkelele.runner import StageFailed, build_chain, resolve_stage, run_chain, status
from youkelele.stage import MissingArtifact, Stage


def _chain(instrument: str) -> list[Stage]:
    return build_chain(get_profile(instrument))


_METER = re.compile(r"^([0-9]+)/([0-9]+)$")
_CHOICE_FLAGS = ("instrument", "tier", "beat_octave", "separator", "chord_model", "debug")


def _option_overrides(args: argparse.Namespace) -> dict[str, object] | str:
    """The option flags given explicitly, or a one-line error for an invalid value."""
    overrides: dict[str, object] = {
        name: getattr(args, name) for name in _CHOICE_FLAGS if getattr(args, name) is not None
    }
    if args.meter is not None:
        match = _METER.match(args.meter.strip())
        if not match or int(match.group(1)) < 1 or int(match.group(2)) < 1:
            return f"invalid --meter {args.meter!r}: expected N/D with positive whole numbers, such as 4/4"
        overrides["meter"] = f"{int(match.group(1))}/{int(match.group(2))}"
    if args.sections_k is not None:
        text = args.sections_k.strip()
        if text == "auto":
            overrides["sections_k"] = None
        elif text.isdecimal() and int(text) >= 1:
            overrides["sections_k"] = int(text)
        else:
            return f"invalid --sections-k {args.sections_k!r}: expected a whole number of at least 1, or auto"
    return overrides


def run_command(args: argparse.Namespace) -> int:
    overrides = _option_overrides(args)
    if isinstance(overrides, str):
        print(overrides)
        return 2
    try:
        run_dir, _ = resolve_run_dir(Path(args.runs_dir), args.source, fetch=fetch_metadata)
    except MetadataError as exc:
        problem = metadata_problem(exc.cause)
        print(problem.what)
        print(f"  fix: {problem.fix}")
        return 2
    slug = run_dir.name
    try:
        manifest = load_manifest(run_dir)
    except ArtifactError as exc:
        print(f"cannot read the saved run: {exc}")
        return 1
    saved = manifest.options.model_dump() if manifest is not None else {}
    options = RunOptions.model_validate({**saved, **overrides, "source": args.source})
    chain = _chain(options.instrument)
    try:
        start = resolve_stage(chain, args.start) if args.start is not None else 0
        end = resolve_stage(chain, args.end) if args.end is not None else len(chain) - 1
    except ValueError as exc:
        print(str(exc))
        return 1
    names = [s.name for s in chain[start : end + 1]]
    problems = check_environment(options, names)
    for problem in problems:
        print(problem.what)
        print(f"  fix: {problem.fix}")
    if problems:
        return 2
    if not chain:
        print("nothing to run: no stages are registered")
        return 0
    if args.start is None and (run_dir / MANIFEST_NAME).exists():
        print(f"Existing run {slug} will be overwritten from stage 0")
    try:
        run_chain(
            run_dir, chain, options, start, end, log=print,
            runs_dir=args.runs_dir, instrument=options.instrument,
        )
    except StageFailed as exc:
        print(f"stage {exc.stage} ({exc.number:02d}) failed: {exc.cause}")
        print(f"resume with: {exc.resume_command}")
        return 1
    except MissingArtifact as exc:
        print(f"missing artifact {exc.key} (produced by stage {exc.producer})")
        return 1
    return 0


def stages_command(args: argparse.Namespace) -> int:
    for number, stage in enumerate(_chain(args.instrument)):
        reads = ", ".join(stage.requires)
        writes = ", ".join(stage.produces)
        print(f"{number:02d} {stage.name}  reads: {reads}  writes: {writes}")
    return 0


def _named_run_dir(runs_dir: str, name: str) -> Path:
    """A run folder by name or video id; the plain path when neither is found."""
    return find_run_by_name(Path(runs_dir), name) or Path(runs_dir) / name


def status_command(args: argparse.Namespace) -> int:
    chain = _chain(args.instrument)
    run_dir = _named_run_dir(args.runs_dir, args.slug)
    for number, (name, state) in enumerate(status(run_dir, chain)):
        print(f"{number:02d} {name}  {state}")
    return 0


def setup_command(args: argparse.Namespace) -> int:
    from youkelele.models.ffmpeg import ffmpeg_paths
    from youkelele.vendoring import VendoringError, ensure_chord_model

    try:
        ensure_chord_model(log=print)
    except VendoringError as exc:
        print(f"setup failed: {exc}")
        return 1
    ffmpeg, ffprobe = ffmpeg_paths()
    print(f"ffmpeg ready at {ffmpeg}")
    return 0


def evaluate_command(args: argparse.Namespace) -> int:
    from youkelele.evaluate import (
        TruthFormatError,
        compare_runs,
        evaluate_run,
        format_comparison,
        format_report,
    )
    from youkelele.jsonio import ArtifactError

    run_dir = _named_run_dir(args.runs_dir, args.slug)
    if not run_dir.is_dir():
        print(f"no run folder at {run_dir}")
        return 1
    other_dir = _named_run_dir(args.runs_dir, args.compare) if args.compare else None
    if other_dir is not None and not other_dir.is_dir():
        print(f"no run folder at {other_dir}")
        return 1
    try:
        report = evaluate_run(run_dir, Path(args.truth) if args.truth else None)
        comparison = compare_runs(run_dir, other_dir) if other_dir is not None else None
    except (ArtifactError, TruthFormatError) as exc:
        print(f"cannot evaluate: {exc}")
        return 1
    print(format_report(report))
    if comparison is not None:
        print(f"Compared with {args.compare} (reference: {args.slug})")
        print(format_comparison(comparison))
    return 0
