"""Run the vendored Chord-CNN-LSTM in a child process and parse its .lab output."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from youkelele.vendoring import chord_model_dir


@dataclass
class LabelSpan:
    start: float
    end: float
    label: str


def parse_lab(path: Path) -> list[LabelSpan]:
    spans: list[LabelSpan] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.strip().split("\t")
        if len(parts) == 3:
            spans.append(LabelSpan(float(parts[0]), float(parts[1]), parts[2]))
    return spans


def recognise_chords(
    wav: Path, work_dir: Path, log: Callable[[str], None] = print
) -> list[LabelSpan]:
    import static_ffmpeg

    static_ffmpeg.add_paths()  # the child's pydub then finds ffmpeg and stays silent
    out_lab = work_dir / "out.lab"
    result = subprocess.run(
        [sys.executable, "chord_recognition.py", str(wav), str(out_lab), "submission"],
        cwd=chord_model_dir(),
        capture_output=True,
        text=True,
    )
    stderr_lines = [line for line in result.stderr.splitlines() if line.strip()]
    for line in stderr_lines:
        log(line)
    for line in result.stdout.splitlines()[-5:]:
        if line.strip():
            log(line)
    if result.returncode != 0:
        tail = "\n".join(stderr_lines[-20:])
        raise RuntimeError(f"chord model exited with code {result.returncode}:\n{tail}")
    return parse_lab(out_lab)
