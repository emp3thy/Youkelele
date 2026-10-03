"""Synthetic ukulele test clip: 120 bpm, 4/4, C G Am F, island strum, light drums.

The kick plays on beat 1 only: a kick on beat 3 lands on the island strum's rest
and reads as a strike.

make_clip(path, seconds=30) writes a 44.1 kHz stereo 16-bit WAV.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf

SR = 44100
BPM = 120.0
BEATS_PER_BAR = 4
BARS_PER_CHORD = 2
CHORDS = ["C", "G", "Am", "F"]
# gCEA open shapes, frets per string in G C E A order.
SHAPES = {"C": (0, 0, 0, 3), "G": (0, 2, 3, 2), "Am": (2, 0, 0, 0), "F": (2, 0, 1, 0)}
TUNING_MIDI = (67, 60, 64, 69)  # G4 C4 E4 A4
# Island strum over eight eighth-note slots: D - D U - U D U
ISLAND = "D-DU-UDU"
# Per-slot accent (down strokes slightly louder, beat 1 loudest).
ACCENT = {0: 1.0, 2: 0.8, 3: 0.65, 5: 0.6, 6: 0.85, 7: 0.65}

# Tunable synthesis parameters (iterated against Beat This! and the chord model).
STAGGER_S = 0.010      # between strings in one strum
STRING_DECAY_S = 0.6   # amplitude e-folding time of a plucked string
STRING_GAIN = 0.22
KICK_GAIN = 0.35
SNARE_GAIN = 0.08  # 0.16 (the spike value) bleeds into the other stem and reads as mutes


def _midi_to_hz(m: float) -> float:
    return 440.0 * 2 ** ((m - 69) / 12)


def _pluck(freq: float, n: int, decay_s: float, rng: np.random.Generator) -> np.ndarray:
    """Karplus-Strong plucked string, mono, length n samples."""
    period = int(round(SR / freq))
    buf = rng.uniform(-1.0, 1.0, period)
    # Loop-filter gain chosen so the amplitude falls by 1/e over decay_s.
    g = float(np.exp(-period / (decay_s * SR)))
    blocks = []
    total = 0
    while total < n:
        blocks.append(buf)
        total += period
        # One pass round the delay line: two-point average, then damping.
        buf = 0.5 * (buf + np.roll(buf, -1)) * g
    out = np.concatenate(blocks)[:n]
    # Gentle attack to avoid a click, and soften the brightest transient.
    attack = min(n, int(0.002 * SR))
    out[:attack] *= np.linspace(0, 1, attack)
    return out


def _strum(chord: str, direction: str, n: int, rng: np.random.Generator) -> np.ndarray:
    """One strum of a four-string voicing; returns stereo (n, 2)."""
    frets = SHAPES[chord]
    pitches = [_midi_to_hz(t + f) for t, f in zip(TUNING_MIDI, frets)]
    order = list(range(4)) if direction == "D" else list(range(3, -1, -1))
    stereo = np.zeros((n, 2), dtype=np.float64)
    stag = int(STAGGER_S * SR)
    pans = [0.35, 0.45, 0.55, 0.65]  # G left-ish ... A right-ish
    for k, s in enumerate(order):
        offset = k * stag
        length = n - offset
        if length <= 0:
            continue
        tone = _pluck(pitches[s], length, STRING_DECAY_S, rng)
        if direction == "U":
            tone *= 0.8  # up strokes a little softer
        stereo[offset:, 0] += tone * (1 - pans[s])
        stereo[offset:, 1] += tone * pans[s]
    return stereo


def _kick(n: int) -> np.ndarray:
    t = np.arange(n) / SR
    f = 120 * np.exp(-t * 25) + 45
    env = np.exp(-t * 18)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env


def _snare(n: int, rng: np.random.Generator) -> np.ndarray:
    t = np.arange(n) / SR
    noise = rng.normal(0, 1, n)
    # crude band-pass by differencing then smoothing
    noise = np.diff(noise, prepend=0.0)
    noise = np.convolve(noise, np.ones(4) / 4, mode="same")
    body = np.sin(2 * np.pi * 185 * t) * np.exp(-t * 40)
    return (noise * np.exp(-t * 22) + 0.6 * body) * 0.6


def make_clip(path: Path | str, seconds: int = 30) -> None:
    rng = np.random.default_rng(42)
    n_total = int(seconds * SR)
    beat_s = 60.0 / BPM
    bar_s = beat_s * BEATS_PER_BAR
    slot_s = bar_s / len(ISLAND)
    strum_len = int(1.6 * SR)
    mix = np.zeros((n_total + strum_len, 2), dtype=np.float64)

    n_bars = int(np.ceil(seconds / bar_s))
    for bar in range(n_bars):
        chord = CHORDS[(bar // BARS_PER_CHORD) % len(CHORDS)]
        bar_start = bar * bar_s
        for slot, tok in enumerate(ISLAND):
            if tok == "-":
                continue
            t0 = int((bar_start + slot * slot_s) * SR)
            if t0 >= n_total:
                break
            s = _strum(chord, tok, strum_len, rng) * STRING_GAIN * ACCENT[slot]
            mix[t0:t0 + strum_len] += s
        # drums: kick on beat 1 only, snare on beats 2 and 4
        for beat in range(BEATS_PER_BAR):
            t0 = int((bar_start + beat * beat_s) * SR)
            if t0 >= n_total:
                break
            if beat == 0:
                k = _kick(int(0.25 * SR)) * KICK_GAIN
                mix[t0:t0 + len(k), 0] += k
                mix[t0:t0 + len(k), 1] += k
            elif beat in (1, 3):
                sn = _snare(int(0.18 * SR), rng) * SNARE_GAIN
                mix[t0:t0 + len(sn), 0] += sn
                mix[t0:t0 + len(sn), 1] += sn

    mix = mix[:n_total]
    peak = np.max(np.abs(mix))
    if peak > 0:
        mix = mix / peak * 0.89
    # small fade out at the end
    fade = int(0.05 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
    sf.write(str(path), mix.astype(np.float32), SR, subtype="PCM_16")

