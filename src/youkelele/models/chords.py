"""Run the vendored Chord-CNN-LSTM in a child process and parse its .lab output."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from youkelele.schemas import Grid
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


def beat_positions(grid: Grid) -> list[tuple[float, int]]:
    """Every gap-filled beat with its 1-based position in its bar.

    A bar with fewer beats than the meter's numerator (the pickup) numbers them from the
    end, so a lone pickup beat is the last position and is not read as a downbeat.
    """
    numerator = grid.meter.numerator
    out: list[tuple[float, int]] = []
    for bar in grid.bars:
        offset = max(numerator - len(bar.beats), 0)
        for pos, beat_index in enumerate(bar.beats):
            out.append((grid.beats[beat_index], offset + pos + 1))
    return out


def write_beat_file(beats: Sequence[tuple[float, int]], path: Path) -> None:
    """Write `time<TAB>running index<TAB>position in bar`, the layout the model's BeatLabIO reads."""
    lines = [f"{time:.4f}\t{i}\t{position}" for i, (time, position) in enumerate(beats, start=1)]
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def recognise_chords(
    wav: Path,
    work_dir: Path,
    log: Callable[[str], None] = print,
    beats: Sequence[tuple[float, int]] | None = None,
) -> list[LabelSpan]:
    import static_ffmpeg

    static_ffmpeg.add_paths()  # the child's pydub then finds ffmpeg and stays silent
    # The child runs in the model directory, so hand it absolute paths.
    wav = Path(wav).resolve()
    out_lab = (Path(work_dir) / "out.lab").resolve()
    if beats is None:
        argv = [sys.executable, "chord_recognition.py", str(wav), str(out_lab), "submission"]
    else:
        beats_lab = (Path(work_dir) / "beats.lab").resolve()
        write_beat_file(beats, beats_lab)
        driver = Path(__file__).with_name("chord_driver.py").resolve()
        argv = [sys.executable, str(driver), str(wav), str(out_lab), "submission", str(beats_lab)]
    result = subprocess.run(
        argv,
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
