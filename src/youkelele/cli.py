"""Command-line entry point for youkelele."""

import argparse

from youkelele import __version__

SUBCOMMANDS = ("run", "stages", "status", "setup", "evaluate")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="youkelele",
        description="Turn a YouTube URL into a ukulele chord-and-strum sheet.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command")
    for name in SUBCOMMANDS:
        subparsers.add_parser(name, help=f"{name} (not implemented yet)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 1
    return 0
