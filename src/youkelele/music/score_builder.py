"""Build the instrument-neutral Score from the stage artifacts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from youkelele.music.key import hedge_tonic
from youkelele.music.phrase import NO_CHORD, aligned_starts, bar_change_bars
from youkelele.music.relabel import refine_labels
from youkelele.music.trailing import trailing_silent_bars
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

if TYPE_CHECKING:  # profiles imports the score stage, which imports this module
    from youkelele.profiles.base import Tuning

_EPS = 1e-6


def check_strums_match_grid(grid: Grid, strums: Strums) -> None:
    """Fail clearly when grid.json was edited after strums.json was made from it."""
    n, m = len(strums.patterns), len(grid.sections)
    if n != m:
        raise ValueError(
            f"strums.json has {n} patterns for {m} sections in grid.json; re-run from strums"
        )
    indices = [p.section for p in strums.patterns]
    if indices != list(range(m)):
        raise ValueError(
            f"strums.json patterns are for sections {indices} but grid.json has sections "
            f"{list(range(m))}; re-run from strums"
        )
    num = grid.meter.numerator
    if strums.slots_per_bar not in (2 * num, 4 * num):
        raise ValueError(
            f"strums.json has slots_per_bar {strums.slots_per_bar} but grid.json meter "
            f"{num}/{grid.meter.denominator} needs {2 * num} or {4 * num}; re-run from strums"
        )


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


def _bar_ends(starts: list[dict[int, ArrangedChord]]) -> list[tuple[str, str]]:
    """(first chord, last chord) per bar as placed in the score, for phrase alignment.

    Passing chords are ignored unless they are all the bar holds; a bar with no chord
    is ("N", "N"), so a change into or out of silence counts as a change.
    """
    ends: list[tuple[str, str]] = []
    for slot_map in starts:
        placed = [slot_map[slot] for slot in sorted(slot_map)]
        names = [a.name for a in placed if not a.passing] or [a.name for a in placed]
        ends.append((names[0], names[-1]) if names else (NO_CHORD, NO_CHORD))
    return ends


def build_score(
    source: SourceInfo,
    grid: Grid,
    chords: Chords,
    strums: Strums,
    arrangement: Arrangement,
    tuning: Tuning,
    instrument_name: str,
) -> Score:
    check_strums_match_grid(grid, strums)
    spb = strums.slots_per_bar
    arranged = {a.event: a for a in arrangement.chords}
    starts = _bar_starts(grid, chords, arranged, spb)

    diagrams: list[ChordDiagram] = []

    def diagram_index(a: ArrangedChord) -> int:
        for i, d in enumerate(diagrams):
            if d.name == a.name and d.shape == a.shape:
                d.passing = d.passing and a.passing  # one full use makes a full diagram
                d.power = d.power and a.power  # one plain use drops the legend line
                return i
        diagrams.append(
            ChordDiagram(name=a.name, shape=a.shape, passing=a.passing, power=a.power)
        )
        return len(diagrams) - 1

    # rows follow the chord-change phrase; grid.json and the section count are unchanged
    aligned = aligned_starts(
        [(s.start_bar, s.end_bar) for s in grid.sections], bar_change_bars(_bar_ends(starts))
    )

    # the strums stage calls trailing_silent_bars the same way to leave these bars out of the
    # last section's pattern; the two calls must stay in step
    last = grid.sections[-1]
    drop = trailing_silent_bars(chords, grid.bars, cap=last.end_bar - last.start_bar)

    # the bridge is decided from the chords here; grid.json keeps the labeller's own names
    labels = refine_labels(grid, chords)

    sections: list[ScoreSection] = []
    dropped = 0
    for k, (label, (start_bar, end_bar, shifted)) in enumerate(zip(labels, aligned)):
        pattern = strums.patterns[k]
        if k == len(grid.sections) - 1:
            dropped = min(drop, max(end_bar - start_bar - 1, 0))  # phrase alignment may have shortened it
            end_bar -= dropped
        bars: list[ScoreBar] = []
        for bar_idx in range(start_bar, end_bar):
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
                        filled=chords.events[a.event].filled, passing=a.passing, power=a.power,
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
            bars.append(
                ScoreBar(index=bar_idx, chords=chord_list, pickup=grid.bars[bar_idx].pickup)
            )
        sections.append(
            ScoreSection(
                label=label, pattern=list(pattern.slots), uncertain=pattern.uncertain,
                bars=bars, bar_repeat=pattern.bar_repeat, no_instrument=pattern.no_instrument,
                inherited_from=pattern.inherited_from, shifted=shifted,
                explained=pattern.explained,
            )
        )

    other = hedge_tonic(chords.key)
    hedge = f"{other} {chords.key.mode}" if other is not None else None
    return Score(
        instrument=Instrument(
            name=instrument_name, strings=len(tuning.pitches), tuning=list(tuning.pitches),
            capo=arrangement.capo,
        ),
        title=source.title,
        artist=source.artist,
        key=f"{chords.key.tonic} {chords.key.mode}",
        key_hedge=hedge,
        bpm=grid.bpm,
        meter=grid.meter,
        tier=arrangement.tier,
        slots_per_bar=spb,
        strum_source=strums.source,
        strums_uncertain=strums.uncertain,
        chord_diagrams=diagrams,
        sections=sections,
        trailing_bars_dropped=dropped,
    )
