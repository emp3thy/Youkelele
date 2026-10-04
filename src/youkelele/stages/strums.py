"""Strums stage (ukulele profile): the as-played strike pattern of each section."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import numpy as np
import soundfile as sf

from youkelele.jsonio import load_model, save_model
from youkelele.music.as_played import (
    MIN_SECTION_BARS,
    STAGE_UNCERTAIN_GRID_FIT,
    UNCERTAIN_BELOW,
    section_summary,
)
from youkelele.music.onsets import (
    Onsets,
    StrikeClass,
    choose_slots_per_bar,
    choose_source,
    detect_onsets,
    grid_fit,
    mute_mask,
    quantise_bar,
    render_directions,
    section_has_instrument,
)
from youkelele.schemas import Grid, SectionPattern, Strums
from youkelele.stage import Stage, StageContext


def _onset_label(muted: bool) -> str:
    """The Audacity label for one detected onset: S for a strike, x for a mute."""
    return "x" if muted else "S"


def _onsets_label_track(onsets: Onsets, muted: np.ndarray) -> str:
    """Audacity label track: start, end (equal, a point label) and label, tab separated."""
    return "".join(
        f"{t:.3f}\t{t:.3f}\t{_onset_label(bool(m))}\n" for t, m in zip(onsets.times, muted)
    )


def _read_mono(path: Path) -> tuple[np.ndarray, int]:
    data, sr = sf.read(str(path), dtype="float32", always_2d=True)
    return data.mean(axis=1), int(sr)


class StrumsStage(Stage):
    name = "strums"
    requires = (
        "separate/stems/guitar.wav",
        "separate/stems/other.wav",
        "ingest/audio.wav",
        "grid/grid.json",
    )
    produces = ("strums/strums.json",)

    def __init__(self, onset_detector: Callable[[np.ndarray, int], Onsets] = detect_onsets) -> None:
        self._detect = onset_detector

    def run(self, ctx: StageContext) -> None:
        guitar, sr_g = _read_mono(ctx.input("separate/stems/guitar.wav"))
        other, sr_o = _read_mono(ctx.input("separate/stems/other.wav"))
        mix, sr = _read_mono(ctx.input("ingest/audio.wav"))
        if sr_g != sr or sr_o != sr:
            raise ValueError(f"sample rates differ: guitar {sr_g}, other {sr_o}, mix {sr}")
        grid = load_model(ctx.input("grid/grid.json"), Grid)
        n = min(len(guitar), len(other), len(mix))
        guitar, other, mix = guitar[:n], other[:n], mix[:n]

        source, y, source_ratio = choose_source(guitar, other, mix)
        onsets = self._detect(y, sr)
        bars, meter = grid.bars, grid.meter
        slots = choose_slots_per_bar(onsets, bars, meter, grid.bpm)
        fit = grid_fit(onsets, bars, slots)
        muted = mute_mask(onsets, enabled=source != "mix")
        if ctx.options.debug:
            # optional diagnostic, so not in produces
            (ctx.out_dir / "onsets.txt").write_text(_onsets_label_track(onsets, muted), encoding="utf-8")
        classes: list[list[StrikeClass]] = [quantise_bar(onsets, muted, bar, slots) for bar in bars]

        patterns: list[SectionPattern | None] = [None] * len(grid.sections)
        short: list[int] = []
        for i, sec in enumerate(grid.sections):
            a = int(round(bars[sec.start_bar].start * sr))
            b = int(round(bars[sec.end_bar - 1].end * sr))
            if not section_has_instrument(y[a:b], mix[a:b]):
                patterns[i] = SectionPattern(
                    section=i, slots=["-"] * slots, confidence=0.0, bar_repeat=0.0,
                    uncertain=True, no_instrument=True, inherited_from=None,
                )
                continue
            rendered, confidence, repeat = section_summary(classes[sec.start_bar:sec.end_bar], slots, meter)
            long_enough = sec.end_bar - sec.start_bar >= MIN_SECTION_BARS
            patterns[i] = SectionPattern(
                section=i, slots=rendered, confidence=confidence, bar_repeat=repeat,
                uncertain=confidence < UNCERTAIN_BELOW or not long_enough,
                no_instrument=False, inherited_from=None,
            )
            if not long_enough:
                short.append(i)

        def donor(j: int) -> bool:
            if not 0 <= j < len(grid.sections) or j in short:
                return False
            return not patterns[j].no_instrument

        for i in short:
            neighbours = [j for j in (i - 1, i + 1) if donor(j)]
            if not neighbours:
                continue  # keeps its own majority vector, already uncertain
            sections = grid.sections
            j = max(neighbours, key=lambda k: sections[k].end_bar - sections[k].start_bar)
            src = patterns[j]
            patterns[i] = SectionPattern(
                section=i, slots=list(src.slots), confidence=src.confidence, bar_repeat=src.bar_repeat,
                uncertain=True, no_instrument=False, inherited_from=j,
            )

        uncertain = fit < STAGE_UNCERTAIN_GRID_FIT
        ctx.log(f"  source {source} (ratio {source_ratio:.2f}), {slots} slots per bar, grid fit {fit:.2f}")
        save_model(
            ctx.output("strums/strums.json"),
            Strums(
                slots_per_bar=slots, source=source, source_ratio=source_ratio, grid_fit=fit,
                uncertain=uncertain, patterns=patterns,
                bar_onsets=[render_directions(c, slots, meter) for c in classes],
            ),
        )
        ctx.note("source", source)
        ctx.note("grid_fit", f"{fit:.2f}")
