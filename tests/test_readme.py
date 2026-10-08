"""The README's sample image exists, its local links resolve, and its commands parse."""

from __future__ import annotations

import argparse
import re
import shlex
from pathlib import Path
from urllib.parse import unquote

import pytest

from youkelele.cli import SUBCOMMANDS, build_parser

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
SAMPLE = ROOT / "docs" / "images" / "sample-sheet.png"
_FENCE = re.compile(r"^```[^\n]*\n(.*?)^```", re.MULTILINE | re.DOTALL)
_LINK = re.compile(r"\]\(([^)\s]+)\)")


def _readme() -> str:
    return README.read_text(encoding="utf-8")


def _command_lines() -> list[str]:
    lines: list[str] = []
    for block in _FENCE.findall(_readme()):
        for line in block.splitlines():
            line = line.strip()
            if line.startswith("uv run youkelele"):
                lines.append(line)
    return lines


def _subparsers(parser: argparse.ArgumentParser) -> dict[str, argparse.ArgumentParser]:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return dict(action.choices)
    raise AssertionError("the parser has no subcommands")


def test_sample_sheet_image_exists_and_is_small():
    assert SAMPLE.is_file()
    assert SAMPLE.stat().st_size < 600 * 1024
    assert "docs/images/sample-sheet.png" in _readme()


def test_readme_local_links_resolve():
    for target in _LINK.findall(_readme()):
        if re.match(r"[a-z]+:", target) or target.startswith("#"):
            continue
        path = unquote(target.split("#", 1)[0])
        assert (ROOT / path).exists(), f"README links to a missing file: {target}"


def test_readme_has_youkelele_commands():
    assert len(_command_lines()) >= 5


@pytest.mark.parametrize("line", _command_lines())
def test_readme_command_names_real_subcommand_and_flags(line):
    tokens = shlex.split(line)
    args = tokens[3:]
    assert args, f"no subcommand in {line!r}"
    if args[0].startswith("--"):
        assert args == ["--version"], f"unknown top-level flag in {line!r}"
        return
    command = args[0]
    assert command in SUBCOMMANDS, f"unknown subcommand {command!r} in {line!r}"
    parser = build_parser()
    known = set(_subparsers(parser)[command]._option_string_actions)
    for token in args[1:]:
        if token.startswith("--"):
            flag = token.split("=", 1)[0]
            assert flag in known, f"{command} has no flag {flag!r} (in {line!r})"
    try:
        parser.parse_args(args)
    except SystemExit as exc:  # argparse exits on a bad value or a missing argument
        pytest.fail(f"{line!r} does not parse (exit {exc.code})")


def test_readme_states_the_1_5_limitation_and_history():
    text = _readme()
    assert "splitting the onsets by pitch register" in text  # the two-guitar limitation, spec 4.2 wording
    assert "1.5" in text and "0.6.0" in text


def test_readme_describes_the_1_6_riff_phrase_and_bar_boxes():
    text = _readme()
    assert "riff heard, not transcribed" in text  # the 1.6 state phrase (spec 3.2)
    assert "strumming pattern of each section" not in text  # the 1.5 description
    assert "two-bar patterns" in text and "ring flag" in text  # the 1.6 history line


def test_readme_states_the_1_7_stage_limitation_and_history():
    text = _readme()
    assert "1.7" in text and "0.8.0" in text
    assert "sparser than it is played" in text and "follow the higher one" in text
    assert "| `05_riff` |" in text  # the stage table lists the riff stage
    assert "their notes interleave" in text  # the two-guitar sentence, 1.7 spec 6
    assert "2026-10-05-ukulele-tab-chain-v1-6-design.md" in text
    assert "2026-10-05-v1-6-validation.md" in text
