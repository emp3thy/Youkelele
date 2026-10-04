from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

from youkelele.models import chords
from youkelele.schemas import Bar, Grid, Meter, Section


def _grid(bars: list[list[int]], n_beats: int, pickup_first: bool = False) -> Grid:
    beats = [i * 0.5 for i in range(n_beats)]
    bar_models = [
        Bar(
            index=i,
            start=beats[idx[0]],
            end=beats[idx[-1]] + 0.5,
            beats=idx,
            pickup=pickup_first and i == 0,
        )
        for i, idx in enumerate(bars)
    ]
    return Grid(
        bpm=120.0, meter=Meter(numerator=4, denominator=4), beats=beats,
        downbeats=[idx[0] for idx in bars], bars=bar_models,
        sections=[Section(label="verse", start_bar=0, end_bar=len(bars), confidence=1.0)],
        octave_decision="none", bar_loudness_db=[-20.0] * len(bars), sections_k=1,
        largest_cluster_share=1.0, chorus_margin_db=None, labels_low_confidence=False,
    )


def test_beat_positions_numbers_pickup_beat_last():
    grid = _grid([[0], [1, 2, 3, 4], [5, 6, 7, 8]], 9, pickup_first=True)
    assert chords.beat_positions(grid) == [
        (0.0, 4),
        (0.5, 1), (1.0, 2), (1.5, 3), (2.0, 4),
        (2.5, 1), (3.0, 2), (3.5, 3), (4.0, 4),
    ]


def test_beat_positions_numbers_short_pickup_from_the_end():
    grid = _grid([[0, 1], [2, 3, 4, 5]], 6, pickup_first=True)
    assert [p for _, p in chords.beat_positions(grid)] == [3, 4, 1, 2, 3, 4]


def test_beat_positions_numbers_short_final_bar_from_one():
    grid = _grid([[0, 1, 2, 3], [4, 5]], 6)
    assert [p for _, p in chords.beat_positions(grid)] == [1, 2, 3, 4, 1, 2]


def test_write_beat_file_three_tab_columns(tmp_path):
    path = tmp_path / "beats.lab"
    chords.write_beat_file([(0.25, 4), (0.75, 1), (1.25, 2)], path)
    assert path.read_text(encoding="utf-8").splitlines() == [
        "0.2500\t1\t4",
        "0.7500\t2\t1",
        "1.2500\t3\t2",
    ]


def _capture_run(monkeypatch, work_dir: Path) -> list[list[str]]:
    seen: list[list[str]] = []

    def fake_run(argv, **kwargs):
        seen.append(list(argv))
        (work_dir / "out.lab").write_text("0.0\t1.0\tC:maj\n", encoding="utf-8")
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    monkeypatch.setattr(chords.subprocess, "run", fake_run)
    return seen


def test_recognise_chords_passes_beats_file_to_driver(monkeypatch, tmp_path):
    seen = _capture_run(monkeypatch, tmp_path)
    spans = chords.recognise_chords(
        tmp_path / "a.wav", tmp_path, lambda m: None, beats=[(0.5, 1), (1.0, 2)]
    )
    assert [s.label for s in spans] == ["C:maj"]
    argv = seen[0]
    assert argv[0] == sys.executable
    driver = Path(argv[1])
    assert driver.is_absolute() and driver.name == "chord_driver.py" and driver.exists()
    assert argv[4] == "submission"
    beats_lab = Path(argv[5])
    assert beats_lab.is_absolute() and beats_lab == (tmp_path / "beats.lab").resolve()
    assert beats_lab.read_text(encoding="utf-8").splitlines() == ["0.5000\t1\t1", "1.0000\t2\t2"]


def test_recognise_chords_without_beats_runs_the_models_own_script(monkeypatch, tmp_path):
    seen = _capture_run(monkeypatch, tmp_path)
    chords.recognise_chords(tmp_path / "a.wav", tmp_path, lambda m: None)
    argv = seen[0]
    assert argv[:2] == [sys.executable, "chord_recognition.py"]
    assert argv[4] == "submission" and len(argv) == 5
    assert not (tmp_path / "beats.lab").exists()


def test_chord_driver_is_valid_python():
    driver = Path(chords.__file__).with_name("chord_driver.py")
    ast.parse(driver.read_text(encoding="utf-8"))


def test_recognise_chords_with_empty_beats_runs_the_models_own_script(monkeypatch, tmp_path):
    seen = _capture_run(monkeypatch, tmp_path)
    chords.recognise_chords(tmp_path / "a.wav", tmp_path, lambda m: None, beats=[])
    assert seen[0][:2] == [sys.executable, "chord_recognition.py"] and len(seen[0]) == 5
    assert not (tmp_path / "beats.lab").exists()
