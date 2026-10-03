"""Build the instrument-neutral Score from the stage artifacts."""

from __future__ import annotations

from youkelele.profiles.base import Tuning
from youkelele.schemas import (
    ArrangedChord,
    Arrangement,
    ChordDiagram,
    Chords,
    Grid,
    Instrument,
    Score,
    ScoreBar,
    ScoreChord,
    ScoreSection,
    SourceInfo,
    Strums,
)

_EPS = 1e-6


def _place_events(grid: Grid, chords: Chords, spb: int) -> list[tuple[int, int, int]]:
    """Return (bar, slot, event index) for every event that lands inside the grid."""
    bars = grid.bars
    placed: list[tuple[int, int, int]] = []
    for i, event in enumerate(chords.events):
        bar_idx = next((b.index for b in bars if b.start - _EPS <= event.start < b.end - _EPS), None)
        if bar_idx is None:
            continue
        bar = bars[bar_idx]
        slot = round((event.start - bar.start) / (bar.end - bar.start) * spb)
        slot = max(0, slot)
        if slot >= spb:
            bar_idx += 1
            slot = 0
            if bar_idx >= len(bars):
                continue
        placed.append((bar_idx, slot, i))
    return placed


def _bar_starts(
    grid: Grid, chords: Chords, arranged: dict[int, ArrangedChord], spb: int
) -> list[dict[int, ArrangedChord]]:
    """Per bar, slot -> arranged chord starting there (continuations included at slot 0)."""
    placed = _place_events(grid, chords, spb)
    per_bar: list[dict[int, ArrangedChord | None]] = [{} for _ in grid.bars]
    for bar_idx, slot, event_idx in placed:
        per_bar[bar_idx][slot] = arranged.get(event_idx)  # later event replaces earlier

    result: list[dict[int, ArrangedChord]] = []
    for bar in grid.bars:
        slots = per_bar[bar.index]
        if 0 not in slots:
            before = [p for p in placed if (p[0], p[1]) < (bar.index, 0)]
            if before:
                event_idx = max(before, key=lambda p: (p[0], p[1], p[2]))[2]
                if event_idx in arranged and chords.events[event_idx].end > bar.start + _EPS:
                    slots[0] = arranged[event_idx]
        result.append({s: a for s, a in slots.items() if a is not None})
    return result


def build_score(
    source: SourceInfo,
    grid: Grid,
    chords: Chords,
    strums: Strums,
    arrangement: Arrangement,
    tuning: Tuning,
    instrument_name: str,
) -> Score:
    spb = strums.slots_per_bar
    arranged = {a.event: a for a in arrangement.chords}
    starts = _bar_starts(grid, chords, arranged, spb)

    diagrams: list[ChordDiagram] = []

    def diagram_index(a: ArrangedChord) -> int:
        for i, d in enumerate(diagrams):
            if d.name == a.name and d.shape == a.shape:
                return i
        diagrams.append(ChordDiagram(name=a.name, shape=a.shape))
        return len(diagrams) - 1

    sections: list[ScoreSection] = []
    for k, section in enumerate(grid.sections):
        pattern = strums.patterns[k]
        bars: list[ScoreBar] = []
        for bar_idx in range(section.start_bar, section.end_bar):
            slot_map = starts[bar_idx]
            ordered = sorted(slot_map)
            chord_list: list[ScoreChord] = []
            for j, slot in enumerate(ordered):
                end = ordered[j + 1] if j + 1 < len(ordered) else spb
                a = slot_map[slot]
                chord_list.append(
                    ScoreChord(
                        name=a.name, diagram=diagram_index(a), start_slot=slot,
                        slots=list(pattern.slots[slot:end]),
                    )
                )
            if chord_list and chord_list[0].start_slot > 0:
                lead = chord_list[0].start_slot
                chord_list.insert(
                    0,
                    ScoreChord(name="N.C.", diagram=-1, start_slot=0, slots=list(pattern.slots[:lead])),
                )
            if not chord_list:
                chord_list.append(
                    ScoreChord(name="N.C.", diagram=-1, start_slot=0, slots=list(pattern.slots))
                )
            bars.append(ScoreBar(index=bar_idx, chords=chord_list))
        sections.append(
            ScoreSection(
                label=section.label, pattern=list(pattern.slots), uncertain=pattern.uncertain,
                bars=bars, bar_repeat=pattern.bar_repeat, no_instrument=pattern.no_instrument,
            )
        )

    return Score(
        instrument=Instrument(
            name=instrument_name, strings=len(tuning.pitches), tuning=list(tuning.pitches),
            capo=arrangement.capo,
        ),
        title=source.title,
        artist=source.artist,
        key=f"{chords.key.tonic} {chords.key.mode}",
        bpm=grid.bpm,
        meter=grid.meter,
        tier=arrangement.tier,
        slots_per_bar=spb,
        strum_source=strums.source,
        strums_uncertain=strums.uncertain,
        chord_diagrams=diagrams,
        sections=sections,
    )
