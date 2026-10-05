"""Read older artifacts as the current version writes them (spec 1.6, section 7).

A strums.json written before 1.6 has no per-bar records. They are rebuilt from what it
does carry: each bar prints its planned section's pattern, its strokes are the bar's own
onsets, every stroke rings (the decay was never measured), and the certainty and riff
flags are the section's.
"""

from __future__ import annotations

from youkelele.schemas import BarStrums, Grid, Stroke, Strums


def _member_spans(strums: Strums, grid: Grid) -> list[list[tuple[int, int]]]:
    """Per planned section, its members' bar ranges in order.

    A planned section with no members list is its own single member; a file with no plan
    (before 1.5) has one planned section per grid section.
    """
    if not strums.plan:
        return [[(s.start_bar, s.end_bar)] for s in grid.sections]
    return [
        [(grid.sections[m].start_bar, grid.sections[m].end_bar) for m in p.members] or [(p.start_bar, p.end_bar)]
        for p in strums.plan
    ]


def backfill_bars(strums: Strums, grid: Grid) -> list[BarStrums]:
    """One record per bar of every planned section, for a strums.json with no `bars`.

    The patterns must match the plan (one per planned section, in order), as
    `check_strums_match_grid` requires. A bar past the end of `bar_onsets` has no strokes.
    """
    records: list[BarStrums] = []
    for pattern, spans in zip(strums.patterns, _member_spans(strums, grid), strict=True):
        for position, (start, end) in enumerate(spans):
            for b in range(start, end):
                onsets = strums.bar_onsets[b] if b < len(strums.bar_onsets) else []
                strokes = [
                    Stroke(slot=j, kind=cell, rings=True, decay_db=None)
                    for j, cell in enumerate(onsets)
                    if cell != "-"
                ]
                records.append(
                    BarStrums(
                        index=b, member=position, strokes=strokes, pattern=list(pattern.slots),
                        unit=pattern.unit, confidence=pattern.confidence, chance_p=pattern.chance_p,
                        uncertain=pattern.uncertain, riff=pattern.riff,
                    )
                )
    return sorted(records, key=lambda r: r.index)


def with_bars(strums: Strums, grid: Grid) -> Strums:
    """`strums` itself when it has bar records, else a copy with them backfilled."""
    if strums.bars:
        return strums
    return strums.model_copy(update={"bars": backfill_bars(strums, grid)})
