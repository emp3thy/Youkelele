"""`scripts/band_sweep.py` on two small synthetic runs with truth folders, never the real runs."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

from tests.test_stage_strums import A, B, SILENT, _run_stage
from tests.test_stage_strums import _chords as _stage_chords
from tests.test_stage_strums import _grid as _stage_grid
from youkelele.jsonio import save_model
from youkelele.music import as_played, rests
from youkelele.music.pitch import PitchTrack
import youkelele.stages.strums as strums_module
from youkelele.schemas import (
    Bar,
    BarStrums,
    ChordEvent,
    Chords,
    Grid,
    Key,
    Meter,
    PlannedSection,
    Section,
    SectionPattern,
    Strums,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import band_sweep  # noqa: E402  (a script, not a package module)

EXAMPLE = Path(__file__).parent / "fixtures" / "ground_truth" / "example"
FIGURE = list("D-DU-UDU")


def _grid(n: int) -> Grid:
    bars = [Bar(index=i, start=i * 2.0, end=(i + 1) * 2.0, beats=list(range(4 * i, 4 * i + 4))) for i in range(n)]
    return Grid(
        bpm=120.0, meter=Meter(numerator=4, denominator=4), beats=[i * 0.5 for i in range(4 * n)],
        downbeats=[4 * i for i in range(n)], bars=bars,
        sections=[Section(label="verse", start_bar=0, end_bar=n, confidence=0.5)],
        octave_decision="none", bar_loudness_db=[-20.0] * n, sections_k=1,
        largest_cluster_share=1.0, chorus_margin_db=None, labels_low_confidence=False,
    )


def _chords(n: int) -> Chords:
    events = [
        ChordEvent(bar=i, beat=0, start=i * 2.0, end=(i + 1) * 2.0, label="C:maj", triad="C:maj", confidence=0.9)
        for i in range(n)
    ]
    return Chords(key=Key(tonic="C", mode="major", confidence=0.9), events=events)


def _run(path: Path, energy: list[float], onsets: list[list[str]] | None = None) -> Path:
    """One planned section of one member, every bar printing the figure and holding at the
    stage's constants; each bar carries its energy ratio and a low share well over the floor."""
    n = len(energy)
    onsets = onsets or [FIGURE] * n
    bars = [
        BarStrums(
            index=i, member=0, strokes=[], pattern=FIGURE, uncertain=False,
            rests=not rests.bar_holds(e, 0.1), energy_ratio=e, low_share=0.1,
        )
        for i, e in enumerate(energy)
    ]
    pattern = SectionPattern(
        section=0, slots=FIGURE, confidence=1.0, bar_repeat=1.0, uncertain=False,
        no_instrument=False, inherited_from=None,
    )
    strums = Strums(
        slots_per_bar=8, source="guitar_stem", source_ratio=1.0, grid_fit=0.9, uncertain=False,
        patterns=[pattern], bar_onsets=onsets,
        plan=[PlannedSection(start_bar=0, end_bar=n, label="verse", members=[0])], bars=bars,
    )
    for folder in ("02_grid", "03_harmony", "04_strums"):
        (path / folder).mkdir(parents=True)
    save_model(path / "02_grid" / "grid.json", _grid(n))
    save_model(path / "03_harmony" / "chords.json", _chords(n))
    save_model(path / "04_strums" / "strums.json", strums)
    return path


def _two_songs(tmp_path: Path) -> tuple[dict[str, Path], dict[str, Path]]:
    """`example` is the ground-truth fixture (bar 3 rests); `second` rests in bars 2 and 3
    and plays in bars 0, 1, 4 and 5."""
    example = _run(tmp_path / "runs" / "example", [0.20, 0.30, 0.25, 0.03])
    second = _run(tmp_path / "runs" / "second", [0.12, 0.09, 0.045, 0.055, 0.15, 0.10])
    truth = tmp_path / "truth" / "second"
    truth.mkdir(parents=True)
    (truth / "rests.txt").write_text("0 2 play\n2 4 rest\n4 6 play\n", encoding="utf-8")
    return {"example": example, "second": second}, {"example": EXAMPLE, "second": truth}


VALUES = [0.02, 0.04, 0.06, 0.08, 0.10]


def test_sweep_rest_ratio_reports_pooled_curve_and_per_song_best(tmp_path):
    runs, truths = _two_songs(tmp_path)
    r = band_sweep.sweep("REST_RATIO_MIN", VALUES, runs, truths)

    assert r.current == 0.05 and r.songs == ["example", "second"]
    # pooled per-bar rest F: hits, false rests and false holds summed over the two songs
    assert [round(p.objective, 3) for p in r.pooled] == [0.0, 0.5, 1.0, 1.0, 0.857]
    assert [(p.counts["hits"], p.counts["false rests"], p.counts["false holds"]) for p in r.pooled] == [
        (0, 0, 3), (1, 0, 2), (3, 0, 0), (3, 0, 0), (3, 1, 0),
    ]
    # leave one song out: the best value over the other song, and the band of values tying it
    held = {h.song: h for h in r.held_out}
    assert (held["example"].best, held["example"].band) == (0.06, (0.06, 0.08))
    assert (held["second"].best, held["second"].band) == (0.06, (0.04, 0.10))
    assert r.inside is False  # 0.05 sits below the band 0.06 to 0.08 left when `example` is held out

    text = band_sweep.format_sweep(r)
    lines = text.splitlines()
    assert lines[0] == "REST_RATIO_MIN (youkelele.music.rests), current 0.05"
    assert "per-bar rest F" in lines[1] and "2 songs" in lines[1]
    assert any(line.split()[:2] == ["0.06", "1.000"] for line in lines)
    assert "  example held out: best 0.06, band 0.06 to 0.08, F 1.000" in lines
    assert "  second held out: best 0.06, band 0.04 to 0.1, F 1.000" in lines
    assert lines[-1] == "Current 0.05 inside every held-out band: no (outside: example)"


def test_sweep_restores_the_constant_after_running(tmp_path, monkeypatch):
    runs, truths = _two_songs(tmp_path)
    band_sweep.sweep("REST_RATIO_MIN", VALUES, runs, truths)
    assert rests.REST_RATIO_MIN == 0.05

    # a vote constant, re-voted from `bar_onsets`: eight identical bars print certain until the
    # floor on voted bars passes eight
    run = _run(tmp_path / "runs" / "steady", [0.2] * 8)
    truth = tmp_path / "truth" / "steady"
    truth.mkdir()
    (truth / "patterns.txt").write_text("0 8 YES D-DU-UDU\n", encoding="utf-8")
    r = band_sweep.sweep("MIN_VOTE_BARS", [4, 8, 9], {"steady": run}, {"steady": truth})
    assert [(p.counts["false certain"], p.counts["false grey"]) for p in r.pooled] == [(0, 0), (0, 0), (0, 1)]
    assert as_played.MIN_VOTE_BARS == 4 and isinstance(as_played.MIN_VOTE_BARS, int)

    # a sweep that fails part way still puts the constant back
    def boom(*args, **kwargs):
        raise RuntimeError("scorer failed")

    monkeypatch.setattr(band_sweep, "score_rests", boom)
    with pytest.raises(RuntimeError, match="scorer failed"):
        band_sweep.sweep("REST_RATIO_MIN", VALUES, runs, truths)
    assert rests.REST_RATIO_MIN == 0.05


@pytest.mark.parametrize(
    "stem_bars",
    [
        ["S-------"] + [A, B] * 4,  # a downbeat bar, then a two-bar figure whose pairs start at bar 1
        [SILENT] + [A, B] * 4,  # the first bar rests: the two-bar phase starts at bar 1
        [A, B] * 4 + [A, SILENT, A, B],  # an interior resting bar (9), the figure carrying on after it
    ],
    ids=["odd-phase", "odd-phase-after-a-rest", "interior-rest"],
)
def test_revote_reproduces_the_strums_stage(tmp_path, monkeypatch, stem_bars):
    """`revote` claims to vote every member as the stage does; at the stage's own constants it
    must give back the stage's printed patterns, certainty and every bar's printed row."""
    monkeypatch.setattr(strums_module, "track_pitch", lambda y, sr: PitchTrack(times=np.zeros(0), midi=np.zeros(0)))
    strums = _run_stage(tmp_path, stem_bars)
    grid = _stage_grid([len(stem_bars)])
    again = band_sweep.revote(strums, grid, _stage_chords(grid))
    assert strums.patterns[0].unit == 2  # the cases exercise the two-bar phase
    assert [p.slots for p in again.patterns] == [p.slots for p in strums.patterns]
    assert [p.uncertain for p in again.patterns] == [p.uncertain for p in strums.patterns]
    assert [b.pattern for b in again.bars] == [b.pattern for b in strums.bars]
    assert [b.rests for b in again.bars] == [b.rests for b in strums.bars]


def test_sweep_unknown_constant_is_a_clear_error(tmp_path, capsys):
    runs, truths = _two_songs(tmp_path)
    with pytest.raises(ValueError, match=r"unknown constant 'REST_RATIO'; expected one of .*REST_RATIO_MIN"):
        band_sweep.sweep("REST_RATIO", VALUES, runs, truths)
    with pytest.raises(SystemExit) as exit_:
        band_sweep.main(["--runs", str(tmp_path / "runs"), "--truth", str(tmp_path / "truth"),
                         "--constant", "REST_RATIO", "--from", "0.02", "--to", "0.1", "--step", "0.01"])
    assert exit_.value.code == 2
    assert "invalid choice: 'REST_RATIO'" in capsys.readouterr().err
