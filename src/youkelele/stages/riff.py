"""Riff stage (ukulele profile): names a pitch at each trusted onset of a riff and maps the line to tab."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import numpy as np
import soundfile as sf

from youkelele.jsonio import load_model, save_model
from youkelele.music.pitch import PitchTrack, name_notes, track_pitch
from youkelele.music.riff_line import RIFF_NAMED_MIN, NoteBar, choose_riff, gate
from youkelele.music.tab import to_tab, tuning_midis
from youkelele.profiles.base import Tuning
from youkelele.schemas import BarStrums, Grid, PlannedSection, RiffNote, Riffs, RiffSection, Strums
from youkelele.stage import Stage, StageContext

_STEMS = {
    "guitar_stem": "separate/stems/guitar.wav",
    "other_stem": "separate/stems/other.wav",
    "mix": "ingest/audio.wav",
}


def _read_mono(path: Path) -> tuple[np.ndarray, int]:
    data, sr = sf.read(str(path), dtype="float32", always_2d=True)
    return data.mean(axis=1), int(sr)


def _member_spans(section: PlannedSection, grid: Grid) -> list[tuple[int, int]]:
    """Each member grid section's bar range; a section with no members list is its own single member."""
    spans = [(grid.sections[m].start_bar, grid.sections[m].end_bar) for m in section.members]
    return spans or [(section.start_bar, section.end_bar)]


class RiffStage(Stage):
    name = "riff"
    requires = (
        "separate/stems/guitar.wav",
        "separate/stems/other.wav",
        "ingest/audio.wav",
        "grid/grid.json",
        "strums/strums.json",
    )
    produces = ("riff/riff.json",)

    def __init__(
        self, tuning: Tuning, pitch_tracker: Callable[[np.ndarray, int], PitchTrack] = track_pitch
    ) -> None:
        self._tuning = tuning
        self._track = pitch_tracker

    def run(self, ctx: StageContext) -> None:
        grid = load_model(ctx.input("grid/grid.json"), Grid)
        strums = load_model(ctx.input("strums/strums.json"), Strums)
        by_index = {b.index: b for b in strums.bars}

        # (planned section, start, end, the member's riff-flagged bars)
        members: list[tuple[int, int, int, list[BarStrums]]] = []
        for k, section in enumerate(strums.plan):
            for start, end in _member_spans(section, grid):
                bars = [by_index[i] for i in range(start, end) if i in by_index]
                if any(b.riff for b in bars):
                    members.append((k, start, end, bars))

        sections: list[RiffSection] = []
        if members:
            y, sr = _read_mono(ctx.input(_STEMS[strums.source]))
            track = self._track(y, sr)
            pitches = tuning_midis(self._tuning.pitches)
            for k, start, end, bars in members:
                sections.append(self._member(ctx, grid, strums, track, pitches, k, start, end, bars))
        save_model(ctx.output("riff/riff.json"), Riffs(sections=sections))

    def _member(
        self,
        ctx: StageContext,
        grid: Grid,
        strums: Strums,
        track: PitchTrack,
        pitches: list[int],
        k: int,
        start: int,
        end: int,
        bars: list[BarStrums],
    ) -> RiffSection:
        slots = strums.slots_per_bar
        note_bars: list[NoteBar] = []
        onsets: list[list[RiffNote]] = []
        named = total = 0
        for bar_strums in bars:
            bar = grid.bars[bar_strums.index]
            width = (bar.end - bar.start) / slots
            times = [bar.start + s.slot * width for s in bar_strums.strokes]
            ends = [min(nxt, bar.end) for nxt in [*times[1:], bar.end]]
            midis = name_notes(track, times, ends)
            note_bar: NoteBar = [None] * slots
            for stroke, midi in zip(bar_strums.strokes, midis):
                note_bar[stroke.slot] = midi
            note_bars.append(note_bar)
            onsets.append([RiffNote(slot=s.slot, midi=m) for s, m in zip(bar_strums.strokes, midis)])
            named += sum(1 for m in midis if m is not None)
            total += len(midis)
        named_share = named / total if total else 0.0
        rings = next((s.rings for b in bars for s in b.strokes), True)

        choice = choose_riff(note_bars)
        printable, reason = gate(choice, named_share, True)
        if named == 0:
            # no pitch heard at all: agreement and support of empty bars say nothing, name the real cause
            printable, reason = False, f"named {named_share:.2f} < {RIFF_NAMED_MIN:.2f}"
        tab, shift = to_tab(choice.notes, rings, pitches) if printable else ([], 0)
        figures = f"agreement {choice.agreement:.2f} support {choice.support:.2f} named {named_share:.2f}"
        verdict = "printable" if printable else f"not transcribed ({reason})"
        ctx.log(f"section {k} bars {start}-{end - 1}: {figures}: {verdict}")
        return RiffSection(
            section=k, start_bar=start, end_bar=end, unit=choice.unit, onsets=onsets, riff=tab,
            agreement=choice.agreement, support=choice.support, named_share=named_share,
            candidate=choice.candidate, octave_shift=shift, printable=printable, reason=reason,
        )
