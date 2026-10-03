"""Synthetic WAV helpers shared by stage tests (numpy plus soundfile only)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf

_NOTE_SEMITONES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def _write(path: Path, data: np.ndarray, sr: int) -> None:
    sf.write(str(path), data.astype(np.float32), sr, subtype="PCM_16")


def write_sine_wav(
    path: Path, seconds: float, sr: int = 44100, freq: float = 220.0, channels: int = 2
) -> None:
    t = np.arange(int(seconds * sr)) / sr
    mono = 0.3 * np.sin(2 * np.pi * freq * t)
    _write(path, np.tile(mono[:, None], (1, channels)), sr)


def write_click_track(path: Path, seconds: float, bpm: float, sr: int = 44100) -> None:
    n = int(seconds * sr)
    data = np.zeros(n)
    burst_len = int(0.02 * sr)
    t = np.arange(burst_len) / sr
    burst = 0.8 * np.sin(2 * np.pi * 1000.0 * t) * np.linspace(1.0, 0.0, burst_len)
    step = 60.0 / bpm
    k = 0
    while (start := int(round(k * step * sr))) < n:
        end = min(start + burst_len, n)
        data[start:end] = burst[: end - start]
        k += 1
    _write(path, data[:, None], sr)


def _chord_freqs(label: str) -> list[float]:
    root, _, quality = label.partition(":")
    semis = _NOTE_SEMITONES[root[0]]
    for ch in root[1:]:
        semis += 1 if ch == "#" else -1
    third = 3 if quality.startswith("min") else 4
    midi = 48 + semis
    return [440.0 * 2 ** ((m - 69) / 12) for m in (midi, midi + third, midi + 7)]


def write_chord_loop(
    path: Path, labels: list[str], bar_seconds: float, sr: int = 44100, bars: int | None = None
) -> None:
    """Each label becomes a triad of summed sines for one bar, cycling through labels."""
    n_bars = bars if bars is not None else len(labels)
    bar_n = int(bar_seconds * sr)
    t = np.arange(bar_n) / sr
    parts = []
    for i in range(n_bars):
        freqs = _chord_freqs(labels[i % len(labels)])
        parts.append(sum(np.sin(2 * np.pi * f * t) for f in freqs) * 0.15)
    _write(path, np.concatenate(parts)[:, None], sr)


def drum_track(
    sr: int, bpm: float, seconds: float, hit_beats: tuple[int, ...], beats_per_bar: int = 4
) -> np.ndarray:
    """Mono noise bursts (20 ms, 2 to 5 kHz) on the given 0-based beat indices of each bar."""
    rng = np.random.default_rng(0)
    n = int(seconds * sr)
    data = np.zeros(n)
    if hit_beats:  # faint room noise so quiet beats are not exactly zero
        data += 0.002 * rng.standard_normal(n)
    burst_len = int(0.02 * sr)
    noise = rng.standard_normal(burst_len + 2048)
    spec = np.fft.rfft(noise)
    freqs = np.fft.rfftfreq(len(noise), 1 / sr)
    spec[(freqs < 2000) | (freqs > 5000)] = 0
    burst = np.fft.irfft(spec, len(noise))[:burst_len]
    burst = 0.8 * burst / np.abs(burst).max() * np.linspace(1.0, 0.0, burst_len)
    step = 60.0 / bpm
    k = 0
    while (start := int(round(k * step * sr))) < n:
        if k % beats_per_bar in hit_beats:
            end = min(start + burst_len, n)
            data[start:end] = burst[: end - start]
        k += 1
    return data


def write_drum_stem(
    path: Path,
    seconds: float,
    bpm: float = 150,
    hit_beats: tuple[int, ...] = (),
    sr: int = 22050,
) -> None:
    """A drums stem; with no hit beats it is digital silence."""
    path.parent.mkdir(parents=True, exist_ok=True)
    _write(path, drum_track(sr, bpm, seconds, hit_beats)[:, None], sr)
