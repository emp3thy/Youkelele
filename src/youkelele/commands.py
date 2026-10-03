"""Command bodies for the youkelele CLI."""

from __future__ import annotations

import argparse
from pathlib import Path

from youkelele.layout import slug_for
from youkelele.options import RunOptions
from youkelele.preflight import check_environment
from youkelele.profiles import get_profile
from youkelele.runner import StageFailed, build_chain, resolve_stage, run_chain, status
from youkelele.stage import MissingArtifact, Stage


def _chain(instrument: str) -> list[Stage]:
    return build_chain(get_profile(instrument))


def run_command(args: argparse.Namespace) -> int:
    options = RunOptions(
        source=args.source,
        instrument=args.instrument,
        tier=args.tier,
        beat_octave=args.beat_octave,
        sections_k=args.sections_k,
        meter=args.meter,
        separator=args.separator,
        chord_model=args.chord_model,
    )
    run_dir = Path(args.runs_dir) / slug_for(args.source)
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
    try:
        run_chain(run_dir, chain, options, start, end, log=print)
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


def status_command(args: argparse.Namespace) -> int:
    chain = _chain(args.instrument)
    run_dir = Path(args.runs_dir) / args.slug
    for number, (name, state) in enumerate(status(run_dir, chain)):
        print(f"{number:02d} {name}  {state}")
    return 0
