"""Beat and downbeat tracking with Beat This!."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import soundfile as sf

CHECKPOINT = "final0"


@dataclass
class BeatResult:
    beats: list[float]
    downbeats: list[float]


def detect_beats(wav: Path) -> BeatResult:
    """Beat and downbeat times in seconds for a WAV file (mono mix, native rate)."""
    from beat_this.inference import Audio2Beats

    signal, sr = sf.read(str(wav), dtype="float32", always_2d=True)
    mono = signal.mean(axis=1)
    model = Audio2Beats(checkpoint_path=CHECKPOINT, device="cpu", dbn=False)
    beats, downbeats = model(mono, sr)
    return BeatResult(
        beats=[float(b) for b in beats], downbeats=[float(d) for d in downbeats]
    )
