"""Stage 4: chord labels snapped to the beat grid, reduced to triads, plus the key.

No-chord bars where the harmonic stems clearly play one of the song's own chords are
then filled with that chord (`filled: true`); see `music/fill.py`. The key's tonic is
then taken from the chord stream and its mode from the harmonic-stem chroma; see
`music/key.py: key_from_chords`. The chroma is computed once and shared. After the key, a
minor tonic the model hears as major (a power chord) is relabelled `X:5` with the key's
quality as its triad and `power: true`; see `music/key.py: power_chord_events`.
"""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Callable
from pathlib import Path

import numpy as np
import soundfile as sf

from youkelele.jsonio import load_model, save_model
from youkelele.models.chords import LabelSpan, beat_positions, recognise_chords
from youkelele.music.chroma import harmonic_chroma
from youkelele.music.fill import (
    FILL_MIN_ENERGY,
    bar_energy,
    chorded_energy_reference,
    fill_silent_bars,
)
from youkelele.music.key import (
    TonicDecision,
    chroma_mean_for,
    estimate_key,
    key_and_decision,
    key_text,
    pair_rule_note,
    plain_major_root,
    power_chord_events,
    tonic_votes_note,
)
from youkelele.music.snap import snap_to_beats
from youkelele.schemas import ChordEvent, Chords, Grid, Key
from youkelele.stage import Stage, StageContext
from youkelele.vendoring import CHORD_MODEL_CHECKPOINT_SHA256, CHORD_MODEL_COMMIT

HARMONIC_STEMS = ("guitar", "bass", "piano", "other")


def read_stems(paths: list[Path]) -> tuple[list[np.ndarray], int]:
    """Each stem as a mono signal, and the shared sample rate."""
    signals: list[np.ndarray] = []
    rate: int | None = None
    for path in paths:
        data, sr = sf.read(str(path), dtype="float32", always_2d=True)
        if rate is not None and sr != rate:
            raise ValueError(f"{path.name} is {sr} Hz but the other stems are {rate} Hz")
        rate = sr
        signals.append(data.mean(axis=1))
    return signals, int(rate)


def _key_log(key: Key, decision: TonicDecision | None) -> str:
    if decision is None:
        return f"key {key_text(key)} (mix)"
    if decision.decided_by == "set":  # the margin is the set's over the votes' tonic
        whose = "set"
    else:
        whose = "pair" if decision.rule == "pair rule" else "score"
    return (
        f"key {key_text(key)} (chords+stems, {whose} margin {key.margin:.3f} by {decision.rule}, "
        f"decided by {decision.decided_by})"
    )


def relabel_power(events: list[ChordEvent], indices: list[int]) -> list[ChordEvent]:
    """The events at `indices` as power chords: label `<root>:5`, the key's quality (minor, the
    gate's precondition) as the triad, `power` set. The root is the parsed root in the model's
    spelling and nothing else changes. Only a plain major label is relabelled; any other
    event at an index (a seventh, an added degree, a slash chord) is left as it is."""
    chosen = set(indices)
    out: list[ChordEvent] = []
    for i, event in enumerate(events):
        root = plain_major_root(event.label) if i in chosen else None
        if root is not None:
            # model_copy skips validation, so the label is built only from a parsed root
            event = event.model_copy(
                update={"label": f"{root}:5", "triad": f"{root}:min", "power": True}
            )
        out.append(event)
    return out


class HarmonyStage(Stage):
    name = "harmony"
    requires = (
        "ingest/audio.wav",
        "grid/grid.json",
        *(f"separate/stems/{stem}.wav" for stem in HARMONIC_STEMS),
    )
    produces = ("harmony/chords.json", "harmony/spans.lab")

    def __init__(
        self,
        recogniser: Callable[..., list[LabelSpan]] = recognise_chords,
        chroma: Callable[[Path], np.ndarray] = chroma_mean_for,
    ) -> None:
        self._recogniser = recogniser
        self._chroma = chroma

    def run(self, ctx: StageContext) -> None:
        wav = ctx.input("ingest/audio.wav")
        grid = load_model(ctx.input("grid/grid.json"), Grid)
        stems = [ctx.input(f"separate/stems/{s}.wav") for s in HARMONIC_STEMS]
        out = ctx.output("harmony/chords.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        beats = beat_positions(grid)
        work_dir = Path(tempfile.mkdtemp(dir=out.parent, prefix="work-"))
        try:
            spans = self._recogniser(wav, work_dir, ctx.log, beats=beats)
            shutil.copyfile(work_dir / "out.lab", ctx.output("harmony/spans.lab"))  # the raw model output
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)
        events = snap_to_beats(spans, grid)
        signals, sr = read_stems(stems)
        chroma, mix = harmonic_chroma(signals, sr)  # computed once: the fill and the key share it
        energy = bar_energy(mix, sr, grid.bars)
        # the key's chroma counts only bars loud enough for the fill to consider them
        reference = chorded_energy_reference(events, grid.bars, energy)
        loud = (
            energy >= FILL_MIN_ENERGY * reference
            if reference is not None
            else np.zeros(len(grid.bars), dtype=bool)
        )
        events = fill_silent_bars(events, grid.bars, chroma.bar_means(grid.bars), energy)
        filled = sum(e.filled for e in events)
        chorded = sum(e.label != "N" and not e.filled for e in events)
        # after the fill, so filled chords count
        mix_key = estimate_key(self._chroma(wav))
        chroma_mean = chroma.mean(loud, grid.bars)
        key, decision = key_and_decision(events, grid.bars, grid.sections, chroma_mean, mix_key)
        ctx.log(f"  {chorded} chord events, {_key_log(key, decision)}")
        ctx.log(f"  {filled} bars filled")
        # after the key: a minor tonic the model hears as major is a power chord (spec 3.2)
        power = power_chord_events(events, key, chroma_mean)
        events = relabel_power(events, power)
        ctx.log(f"  {len(power)} power chord events")
        save_model(out, Chords(key=key, events=events))
        ctx.note("power_chords", str(len(power)))
        ctx.note("key_method", key.method)
        ctx.note("key_margin", "none" if key.margin is None else f"{key.margin:.3f}")
        ctx.note("tonic_pair_rule", pair_rule_note(decision))
        ctx.note("tonic_votes", tonic_votes_note(key))
        ctx.note("model", f"chord_cnn_lstm@{CHORD_MODEL_COMMIT}")
        prefixes = ",".join(h[:8] for h in CHORD_MODEL_CHECKPOINT_SHA256.values())
        ctx.note("checkpoints", prefixes)
        ctx.note("filled", str(filled))
        ctx.note("decoding", "beats+downbeats" if beats else "plain")
