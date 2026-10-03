"""Command-line entry point for youkelele."""

import argparse

from youkelele import __version__, commands

SUBCOMMANDS = ("run", "stages", "status", "setup", "evaluate")
HANDLERS = {
    "run": commands.run_command,
    "stages": commands.stages_command,
    "status": commands.status_command,
    "setup": commands.setup_command,
    "evaluate": commands.evaluate_command,
}


def _add_instrument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--instrument", default="ukulele")


def _add_runs_dir(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--runs-dir", default="runs")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="youkelele",
        description="Turn a YouTube URL into a ukulele chord-and-strum sheet.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command")
    for name in SUBCOMMANDS:
        if name not in HANDLERS:
            subparsers.add_parser(name, help=f"{name} (not implemented yet)")

    run = subparsers.add_parser("run", help="run the chain for a source")
    run.add_argument("source")
    _add_instrument(run)
    run.add_argument("--tier", choices=("easy", "full"), default="easy")
    run.add_argument(
        "--beat-octave", choices=("auto", "none", "half", "double"), default="auto"
    )
    run.add_argument("--sections-k", type=int, default=None)
    run.add_argument("--meter", default="4/4")
    run.add_argument("--separator", choices=("demucs", "roformer-sw"), default="demucs")
    run.add_argument(
        "--chord-model", choices=("cnn-lstm", "chordmini"), default="cnn-lstm"
    )
    run.add_argument("--from", dest="start", default=None)
    run.add_argument("--to", dest="end", default=None)
    _add_runs_dir(run)

    stages = subparsers.add_parser("stages", help="list the stages")
    _add_instrument(stages)

    status = subparsers.add_parser("status", help="show stage status for a run")
    status.add_argument("slug")
    _add_instrument(status)
    _add_runs_dir(status)
    subparsers.add_parser("setup", help="fetch the chord model and ffmpeg")

    evaluate = subparsers.add_parser(
        "evaluate", help="score a run against ground-truth annotations"
    )
    evaluate.add_argument("slug")
    evaluate.add_argument("--truth", required=True)
    _add_runs_dir(evaluate)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 1
    handler = HANDLERS.get(args.command)
    return handler(args) if handler else 0
