"""Command-line entry point for youkelele."""

import argparse

from youkelele import __version__, commands
from youkelele.layout import DEFAULT_RUNS_DIR
from youkelele.profiles import PROFILES

SUBCOMMANDS = ("run", "stages", "status", "setup", "evaluate")
HANDLERS = {
    "run": commands.run_command,
    "stages": commands.stages_command,
    "status": commands.status_command,
    "setup": commands.setup_command,
    "evaluate": commands.evaluate_command,
}


def _add_instrument(parser: argparse.ArgumentParser, default: str | None = "ukulele") -> None:
    parser.add_argument("--instrument", choices=sorted(PROFILES), default=default)


def _add_runs_dir(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--runs-dir", default=DEFAULT_RUNS_DIR)


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
    # Option flags default to None meaning "not given": a resumed run keeps the options saved
    # in the manifest and overlays only the flags given explicitly (commands.run_command).
    _add_instrument(run, default=None)
    run.add_argument("--tier", choices=("easy", "full"), default=None)
    run.add_argument("--beat-octave", choices=("auto", "none", "half", "double"), default=None)
    run.add_argument("--sections-k", default=None, help="a whole number of sections, or auto")
    run.add_argument("--meter", default=None, help="N/D, such as 4/4")
    run.add_argument("--separator", choices=("demucs", "roformer-sw"), default=None)
    run.add_argument("--chord-model", choices=("cnn-lstm", "chordmini"), default=None)
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
        "evaluate",
        help="report a run's diagnostics, score it against truth, or compare it with another run",
    )
    evaluate.add_argument("slug")
    evaluate.add_argument("--truth", default=None)
    evaluate.add_argument("--compare", default=None, help="slug of a run to score against this one")
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


if __name__ == "__main__":
    raise SystemExit(main())
