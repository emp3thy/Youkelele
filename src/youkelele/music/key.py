"""Global key estimation with Krumhansl-Kessler profiles."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf

from youkelele.schemas import Key

KRUMHANSL_MAJOR = (6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88)
KRUMHANSL_MINOR = (6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17)
_TONICS = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


def estimate_key(chroma_mean: np.ndarray) -> Key:
    chroma = np.asarray(chroma_mean, dtype=float)
    scored: list[tuple[float, int, str]] = []
    for mode, profile in (("major", KRUMHANSL_MAJOR), ("minor", KRUMHANSL_MINOR)):
        for tonic in range(12):
            corr = np.corrcoef(chroma, np.roll(profile, tonic))[0, 1]
            scored.append((float(np.nan_to_num(corr)), tonic, mode))
    scored.sort(key=lambda s: s[0], reverse=True)
    best, second = scored[0][0], scored[1][0]
    confidence = float(np.clip((best - second) / best, 0.0, 1.0)) if best > 0 else 0.0
    return Key(tonic=_TONICS[scored[0][1]], mode=scored[0][2], confidence=confidence)


def chroma_mean_for(wav: Path) -> np.ndarray:
    import librosa

    signal, sr = sf.read(str(wav), dtype="float32", always_2d=True)
    chroma = librosa.feature.chroma_cqt(y=signal.mean(axis=1), sr=sr)
    return chroma.mean(axis=1)
