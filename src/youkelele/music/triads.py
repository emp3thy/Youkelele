"""Reduce Harte chord labels to major, minor, diminished, augmented or suspended triads."""

from __future__ import annotations

import mir_eval.chord

TRIAD_TEMPLATES: dict[str, frozenset[int]] = {
    "maj": frozenset({0, 4, 7}),
    "min": frozenset({0, 3, 7}),
    "dim": frozenset({0, 3, 6}),
    "aug": frozenset({0, 4, 8}),
    "sus4": frozenset({0, 5, 7}),
    "sus2": frozenset({0, 2, 7}),
}


def to_triad(label: str) -> str:
    """The triad of a Harte label; no-chord labels and power chords (`X:5`) come back as they are.

    The harmony stage relabels a minor tonic played as root and fifth as `X:5` and writes the
    key's quality as the event's triad itself; collapsing it to major here would undo that.
    """
    if label in ("N", "X"):
        return label
    try:
        root, quality, _degrees, _bass = mir_eval.chord.split(label, reduce_extended_chords=True)
        if quality == "5":
            return label
        bitmap = mir_eval.chord.quality_to_bitmap(quality)
    except mir_eval.chord.InvalidChordException:
        root = label.split(":", 1)[0].split("/", 1)[0]
        try:
            mir_eval.chord.encode(f"{root}:maj")
        except mir_eval.chord.InvalidChordException:
            return label
        return f"{root}:maj"
    notes = frozenset(i for i in range(8) if bitmap[i])
    chosen = next((name for name, tpl in TRIAD_TEMPLATES.items() if tpl == notes), None)
    if chosen is None:
        chosen = max(TRIAD_TEMPLATES, key=lambda n: len(TRIAD_TEMPLATES[n] & notes))
    return mir_eval.chord.join(root, chosen)
