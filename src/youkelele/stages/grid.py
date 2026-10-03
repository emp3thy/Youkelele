"""Stage 3: beats, tempo, bars and sections from the mixed audio."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import numpy as np
import soundfile as sf

from youkelele.jsonio import save_model
from youkelele.music.backbeat import backbeat_ratio as measure_backbeat, drums_silent as is_drums_silent
from youkelele.models.beats import CHECKPOINT, BeatResult, detect_beats
from youkelele.music.sections import (
    LOW_MARGIN_DB,
    bar_features,
    beat_chroma,
    boundaries_from_clusters,
    label_sections,
    segment_bars,
)
from youkelele.music.tempo import (
    bpm_from_beats,
    build_bars,
    decide_octave,
    double_beats,
    downbeat_indices,
    fill_gaps,
    normalise_octave,
)
from youkelele.schemas import Grid, Meter
from youkelele.stage import Stage, StageContext


def _backbeat_text(ratio: float | None) -> str:
    return "  backbeat ratio n/a" if ratio is None else f"  backbeat ratio {ratio:.2f}"


class GridStage(Stage):
    name = "grid"
    requires = ("ingest/audio.wav", "separate/stems/drums.wav")
    produces = ("grid/grid.json",)

    def __init__(self, detector: Callable[[Path], BeatResult] = detect_beats) -> None:
        self._detector = detector

    def run(self, ctx: StageContext) -> None:
        wav = ctx.input("ingest/audio.wav")
        detected = self._detector(wav)
        signal, sr = sf.read(str(wav), dtype="float32", always_2d=True)
        y = signal.mean(axis=1)
        duration = len(y) / sr

        # a beat or downbeat at the exact end of the clip cannot start a bar
        beats = [b for b in detected.beats if b < duration]
        downbeats = [d for d in detected.downbeats if d < duration]
        if len(beats) < 2:
            raise ValueError(f"only {len(beats)} beat(s) detected; cannot build a grid")

        beats = fill_gaps(beats)
        detected_bpm = bpm_from_beats(beats)
        meter = Meter.parse(ctx.options.meter)
        drums_signal, drums_sr = sf.read(
            str(ctx.input("separate/stems/drums.wav")), dtype="float32", always_2d=True
        )
        drums = drums_signal.mean(axis=1)
        silent = is_drums_silent(drums)
        db_idx = downbeat_indices(beats, downbeats)
        first_downbeat = db_idx[0] if db_idx else 0  # bar phase: first detected downbeat is beat 0
        ratio = None if silent else measure_backbeat(drums, drums_sr, beats[first_downbeat:], meter.numerator)
        ctx.log("  drums silent" if silent else _backbeat_text(ratio))
        octave = decide_octave(
            detected_bpm, ctx.options.beat_octave, backbeat_ratio=ratio, drums_silent=silent
        )
        if octave == "half":
            beats, db_idx = normalise_octave(beats, db_idx, target_period=2 * 60.0 / detected_bpm)
        elif octave == "double":
            beats, db_idx = double_beats(beats, db_idx)
        bpm = bpm_from_beats(beats)

        chroma = beat_chroma(y, sr, beats) if octave == "half" else None
        bars = build_bars(beats, db_idx, meter, duration, chroma)
        features, loudness = bar_features(y, sr, bars, beats)
        cluster_ids, k, share = segment_bars(features, ctx.options.sections_k)
        boundaries, merged_ids = boundaries_from_clusters(cluster_ids)
        sections, margin = label_sections(boundaries, merged_ids, loudness)

        full_bars = [bar for bar in bars if len(bar.beats) == meter.numerator] or bars
        bar_len = float(np.median([bar.end - bar.start for bar in full_bars]))
        ctx.log(
            f"  {detected_bpm:.1f} bpm detected, octave {octave}, {bpm:.1f} bpm; "
            f"{len(bars)} bars, median bar {bar_len:.2f} s"
        )
        margin_text = "n/a" if margin is None else f"{margin:.1f} dB"
        ctx.log(f"  {len(sections)} sections, k {k}, chorus margin {margin_text}")

        grid = Grid(
            bpm=bpm,
            meter=meter,
            beats=beats,
            downbeats=[bar.beats[0] for bar in bars if not bar.pickup],
            bars=bars,
            sections=sections,
            octave_decision=octave,
            bar_loudness_db=loudness,
            sections_k=k,
            largest_cluster_share=share,
            chorus_margin_db=margin,
            labels_low_confidence=margin is not None and margin < LOW_MARGIN_DB,
            backbeat_ratio=ratio,
            drums_silent=silent,
        )
        save_model(ctx.output("grid/grid.json"), grid)
        ctx.note("model", f"Beat This! {CHECKPOINT}")
