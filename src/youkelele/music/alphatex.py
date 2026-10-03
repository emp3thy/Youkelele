"""Render a Score as alphaTex (slash staff, per-beat direction tokens)."""

from __future__ import annotations

from youkelele.schemas import ChordDiagram, Score, ScoreChord, Shape


def _q(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _absolute(shape: Shape) -> list[int]:
    """Absolute frets in alphaTex string order (reversed diagram order); -1 is muted."""
    return [f + shape.base_fret - 1 if f > 0 else f for f in reversed(shape.frets)]


def _chord_definition(diagram: ChordDiagram) -> str:
    frets = " ".join("x" if f < 0 else str(f) for f in _absolute(diagram.shape))
    options = ["showdiagram false"]
    if diagram.shape.base_fret > 1:
        options.append(f"firstfret {diagram.shape.base_fret}")
    options += [f"barre {b + diagram.shape.base_fret - 1}" for b in diagram.shape.barres]
    return f"\\chord ({_q(diagram.name)} {frets}) {{{' '.join(options)}}}"


def _beats(chord: ScoreChord, score: Score) -> list[str]:
    frets = _absolute(score.chord_diagrams[chord.diagram].shape) if chord.diagram >= 0 else []
    notes = " ".join(f"{f}.{i + 1}" for i, f in enumerate(frets) if f >= 0)
    beats = []
    for i, slot in enumerate(chord.slots):
        props = []
        played = slot in ("D", "U") and bool(notes)
        if played:
            props.append("bd" if slot == "D" else "bu")
        elif slot == "x":
            props.append("ds")
        if i == 0:
            props.append(f"ch {_q(chord.name)}")
        props.append(f'lyrics "{slot}"')
        body = " ".join(props)
        if played:
            beats.append(f"({notes}){{{body}}}")
        elif slot == "x":
            beats.append(f"(){{{body}}}")
        else:
            beats.append(f"r{{{body}}}")
    return beats


def score_to_alphatex(score: Score) -> str:
    lines = [f"\\title {_q(score.title)}"]
    if score.artist:
        lines.append(f"\\artist {_q(score.artist)}")
    lines += [
        f"\\tempo {round(score.bpm)}",
        "\\hideDynamics",
        ".",
        f"\\track {_q(score.instrument.name)}",
        "\\staff {slash}",
        f"\\tuning ({' '.join(reversed(score.instrument.tuning))}) {{ hide }}",
    ]
    if score.instrument.capo > 0:
        lines.append(f"\\capo {score.instrument.capo}")
    lines += [_chord_definition(d) for d in score.chord_diagrams]
    lines.append(f"\\ts {score.meter.numerator} {score.meter.denominator}")

    ratio = score.slots_per_bar / score.meter.numerator
    prefix = ":8 " if ratio == 2 else ":16 " if ratio == 4 else ""
    for section in score.sections:
        lines.append(f"\\section {_q(section.label)}")
        for bar in section.bars:
            beats = [b for chord in bar.chords for b in _beats(chord, score)]
            lines.append(f"{prefix}{' '.join(beats)} |")
    return "\n".join(lines) + "\n"
