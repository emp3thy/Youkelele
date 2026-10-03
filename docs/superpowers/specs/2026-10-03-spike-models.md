# Spike findings: models and segmentation (plan Tasks 5, 8, 9, 14)

Date: 2026-10-03. Plan: `docs/superpowers/plans/2026-10-03-ukulele-tab-chain.md`. Verified facts relied on: `2026-10-03-assumption-checks-tools.md` items A1, A2, A4, A5.

Environment: Python 3.12 venv at `<scratchpad>\venv_ytdlp` (torch 2.14.1 CPU, librosa 1.0.0, beat-this 1.1.0, soundfile 0.14.0, h5py 3.16.0, joblib 1.6.0, mir_eval 0.8.2, static-ffmpeg 3.0, scikit-learn 1.9.1, numpy 2.5.3, scipy 1.18.1, pydub 0.25.1, pretty_midi 0.2.11.post0). **No package had to be installed for any spike.** Scripts and outputs live in `<scratchpad>\spike_models\`; real-song audio and `beats.json` were produced by the download spike in `<scratchpad>\spike_audio\{s69,pssom}\`.

## Summary

| Task | Old | New | One-line justification |
|---|---|---|---|
| 5 Preflight | 88% | 95% | static-ffmpeg exposes a deterministic install dir and a crumb file; presence can be tested without any download, proven by calling the functions. |
| 9 Harmony | 80% | 90% | Clone, SHA, hashes, patch and the plan's exact subprocess form all ran on Windows (spaces in paths included) on the synthetic clip and both full songs; two missing dependencies (`pydub`, `pretty_midi`) found and must be added. |
| 14 End to end | 70% | 88% | The synthetic clip gives Beat This! exactly 120.00 bpm with every downbeat on a bar start and the chord model returns C:maj, G:maj, A:min, F:maj with a single 23 ms spurious `N`; the remaining risk is the untried separation and render stages in the same run. |
| 8 Grid | 75% | 82% | Laplacian segmentation on bar features recovers 7 of 8 hard section boundaries within 2 bars on both songs at k=4, but the plan's `k` rule and the chorus heuristic are both wrong and need the replacements given below; no human-timed reference exists yet (the reference used is derived from chord changes). |

---

## Spike A: static-ffmpeg location API (Task 5)

**Question.** Which static-ffmpeg function returns the ffmpeg/ffprobe paths, does it download when they are missing, and can presence be checked without downloading?

**What was run.** Read `venv_ytdlp\Lib\site-packages\static_ffmpeg\{__init__.py,_add_paths.py,run.py}` (version 3.0). Called the functions from `spike_models\spike_a_ffmpeg.py`.

**Results.**

- `static_ffmpeg.run.get_or_fetch_platform_executables_else_raise(fix_permissions=True, download_dir=None) -> tuple[str, str]` returns `(ffmpeg_exe, ffprobe_exe)` as **strings**. It takes a `FileLock` on `static_ffmpeg/lock.file` (10 min timeout), then checks **one gate**: `os.path.exists(os.path.join(exe_dir, "installed.crumb"))`. If the crumb is absent it downloads `https://github.com/zackees/ffmpeg_bins/raw/main/v8.0/win32.zip` (about 100 MB), extracts it one level above `exe_dir`, writes the crumb. If the crumb is present it returns immediately (0.044 s measured). It never checks that the `.exe` files themselves exist.
- `static_ffmpeg.run.get_platform_dir() -> str` is pure (no I/O beyond `check_system()`), returning `os.path.join(SELF_DIR, "bin", get_platform_key())`; `get_platform_key()` is `"win32"` on Windows.
- `static_ffmpeg.add_paths(weak=False, download_dir=None) -> bool` calls the fetch function (so it **does** download when missing), prepends the directory to `os.environ["PATH"]`, returns `True`; with `weak=True` it returns `False` without touching anything when `shutil.which("ffmpeg")` and `which("ffprobe")` already succeed. `remove_paths()` also exists.
- There is **no** dedicated "is installed" function. The deterministic presence test is:

  ```python
  from pathlib import Path
  from static_ffmpeg import run
  d = Path(run.get_platform_dir())
  present = (d / "installed.crumb").exists() and (d / "ffmpeg.exe").exists() and (d / "ffprobe.exe").exists()
  ```

- Exact paths on this machine (venv `venv_ytdlp`):
  - dir: `...\venv_ytdlp\Lib\site-packages\static_ffmpeg\bin\win32`
  - `ffmpeg.exe`, `ffprobe.exe`, `installed.crumb` all present; `ffmpeg version 8.0.1-essentials_build-www.gyan.dev`, `ffprobe version 8.0.1-essentials_build-www.gyan.dev`.
  - In the project the path will be `<project>\.venv\Lib\site-packages\static_ffmpeg\bin\win32\`.
- `download_dir` overrides `exe_dir`; the zip is still extracted into `dirname(download_dir)`, so a custom dir must end in a platform-named folder (`.../win32`) to line up. Not needed by the plan.

**Recommended plan changes (Task 5 and Task 6).**

- `Probes.ffmpeg_dir(fetch: bool = False) -> Path | None`: without `fetch`, apply the three-file test above against `Path(static_ffmpeg.run.get_platform_dir())` and return the dir or `None`; with `fetch=True` return `Path(run.get_or_fetch_platform_executables_else_raise()[0]).parent`.
- `models/ffmpeg.py::ffmpeg_paths()` should wrap the str tuple in `Path`.
- Preflight fix text for a missing ffmpeg: "run `youkelele setup` (downloads ffmpeg 8.0, about 100 MB, once)".
- Before launching the chord model subprocess (Task 9) call `static_ffmpeg.add_paths()` in the parent; the child inherits PATH and pydub's warning disappears (see Spike B).

**New confidence: 95%.** The API is tiny and fully read; the only unverified piece is the Linux/macOS permission-fixing branch, which does not apply here.

---

## Spike B: vendoring the chord model (Task 9)

**Question.** Does the pinned clone, hash recording, NumPy patch and `subprocess.run([python, "chord_recognition.py", wav, out.lab, "submission"], cwd=repo)` work on Windows, and what does the output look like?

**What was run.** `git clone --depth 1` into `spike_models\chord_cnn_lstm`; `sha256sum`; regex patch via Python; `spike_models\run_chords.py` (the plan's exact subprocess form, `capture_output=True`) on the synthetic clip, on a copy at a path with spaces, and on both downloaded songs.

**Results.**

- **Commit.** `HEAD` = `master` = `481f4ce703f8822b99f4037e9104ba1760e21ea3` (2024-04-09, "Update README.MD"); `git ls-remote origin master` agrees. Pin `CHORD_MODEL_COMMIT = "481f4ce703f8822b99f4037e9104ba1760e21ea3"`.
- **`cache_data/` contents** (exactly five files, 28.7 MB):

  | file | bytes | sha256 |
  |---|---|---|
  | `joint_chord_net_ismir_naive_v1.0_reweight(0.0,10.0)_s0.best.sdict` | 5 746 183 | `921b42d5d1cf9ce1c0c0e45a74d409b8066e0acec46058ef74e24ee0fb540761` |
  | `..._s1.best.sdict` | 5 746 175 | `bcb75859e0efa256696cf5da396b320093317b9b1d9560c304f46c25fe1f8b17` |
  | `..._s2.best.sdict` | 5 746 179 | `acddf85c3fff29954c4877021177d72e2cba9f729ce80c1010f054c477bf3f61` |
  | `..._s3.best.sdict` | 5 746 175 | `65d81a3ab73435aaaade586981b4cabdf57b8953d76052703e6968c32ef8421c` |
  | `..._s4.best.sdict` | 5 746 227 | `5ff6b0ec85640e17a09a9b3de68c93fdd45adc24488e8fa9be5715c28d561122` |

- **NumPy patch.** `\bnp\.int\b -> int` replaced 7 in `extractors/xhmm_ismir.py`, 7 in `extractors/xhmm_decoder.py`, 1 in `results_ismir2017.py` (15 total; A2 said "10 occurrences", the true count is 15). A repo-wide grep for `np.int\b`, `np.float\b`, `np.bool\b` found **two more** `np.int` in `extractors/beat_preprocess.py` (lines 271, 273) and no `np.float`/`np.bool`. `beat_preprocess.py` is imported only by `datasets.py` (lazily, inside a function) and `storage_creation.py`, neither of which `chord_recognition.py` touches, so inference works without patching it. Recommend patching it anyway for a clean repo (add it to the file list, expected count 2) so the patch function's "files touched" assertion is exact.
- **Dependencies actually imported by a run** (checked with `python -X importtime`): `torch`, `librosa`, `h5py`, `joblib`, **`pydub`**, **`pretty_midi`**. The plan's Global Constraints list `h5py` and `joblib` but **not `pydub` or `pretty_midi`**; both were already in this venv (from the assumption-check session) which is why nothing had to be installed. `jams`, `pumpp`, `figures`, `matplotlib` from `requirements.txt` are not imported during inference and are **not** needed.
- **Runs** (ensemble of 5 models, CPU):

  | input | duration | wall | return | lines |
  |---|---|---|---|---|
  | synthetic clip (iter 1) | 30 s | 4.9 s | 0 | 10 |
  | synthetic clip (iter 2) | 30 s | 4.9 s | 0 | 9 |
  | `out\dir with spaces\my clip 2.wav` -> `out file.lab` | 30 s | 4.6 s | 0 | 9 (identical labels) |
  | Summer of '69 `audio.wav` | 207 s | 13.3 s | 0 | 76 |
  | Pour Some Sugar On Me `audio.wav` | 267 s | 14.7 s | 0 | 87 |

  Absolute paths with a drive letter and spaces work for both the input and the output; the `.lab` is written exactly where asked.
- **stdout**: five lines `Inference: <model name> on <path>`. **stderr noise**: exactly one `RuntimeWarning: Couldn't find ffmpeg or avconv` from `pydub\utils.py:170` when ffmpeg is not on PATH; with `static_ffmpeg.add_paths()` in the parent process `shutil.which("ffmpeg")` resolves and the warning goes. Under `-W error` pydub also trips `DeprecationWarning: 'audioop' is deprecated` (3.12 only; audioop is gone in 3.13, one more reason for the `==3.12.*` pin).
- **First 20 lines, synthetic clip iteration 2** (`out\iter2.lab`, tab separated, 9 lines total):

  ```
  0.0	0.023219954648526078	N
  0.023219954648526078	4.2260317460317465	C:maj
  4.2260317460317465	8.057324263038549	G:maj
  8.057324263038549	12.004716553287983	A:min
  12.004716553287983	16.764807256235827	F:maj
  16.764807256235827	20.456780045351476	C:maj
  20.456780045351476	24.03265306122449	G:maj
  24.03265306122449	28.00326530612245	A:min
  28.00326530612245	30.00018140589569	F:maj
  ```

- **First 20 lines, Summer of '69** (`out\s69.lab`; label counts A:maj 27, D:maj 25, B:min 9, G:maj 6, Bb:maj 3, N 2, F:maj 2, C:maj 2, matching Hooktheory's D-A verse, Bm-A-D-G chorus, F-Bb-C bridge):

  ```
  0.0	0.9984580498866213	N
  0.9984580498866213	7.337505668934241	D:maj
  7.337505668934241	10.936598639455783	A:maj
  10.936598639455783	14.210612244897959	D:maj
  14.210612244897959	17.786485260770977	A:maj
  17.786485260770977	21.153378684807258	D:maj
  21.153378684807258	24.729251700680273	A:maj
  24.729251700680273	28.11936507936508	D:maj
  28.11936507936508	31.60235827664399	A:maj
  31.60235827664399	33.2974149659864	B:min
  33.2974149659864	35.062131519274374	A:maj
  35.062131519274374	36.826848072562356	D:maj
  36.826848072562356	38.568344671201814	G:maj
  38.568344671201814	40.26340136054422	B:min
  40.26340136054422	42.00489795918367	A:maj
  42.00489795918367	43.769614512471655	D:maj
  43.769614512471655	45.51111111111111	G:maj
  45.51111111111111	47.206167800453514	B:min
  47.206167800453514	48.99410430839002	A:maj
  48.99410430839002	52.360997732426306	D:maj
  ```

  Pour Some Sugar On Me (`out\pssom.lab`): E:maj 23, B:maj 22, A:maj 20, N 8, F#:maj 5, C#:maj 4, C#:min 2; the power-chord verses come back as `C#:maj`/`N`, the pre-chorus as `F#`/`B`, the chorus as `E A B`, which is consistent with Hooktheory (no-third chords are read as major).

**Recommended plan changes (Task 9 and Global Constraints).**

- Add `pydub` and `pretty_midi` to the dependency list (both resolve on 3.12 with numpy 2.5; `pretty_midi 0.2.11.post0`, `pydub 0.25.1`).
- `CHORD_MODEL_COMMIT = "481f4ce703f8822b99f4037e9104ba1760e21ea3"`; `CHORD_MODEL_CHECKPOINT_SHA256` as in the table.
- `patch_numpy_aliases` file list: `extractors/xhmm_ismir.py` (7), `extractors/xhmm_decoder.py` (7), `results_ismir2017.py` (1), `extractors/beat_preprocess.py` (2); make it idempotent (zero replacements on a second run is fine) so `ensure_chord_model` can re-run safely.
- Clone with `git clone --depth 1 --branch master` then `git checkout <sha>` is not enough for a shallow clone of a non-HEAD commit; since the pin **is** current master, `git clone --depth 1` followed by `git rev-parse HEAD == CHORD_MODEL_COMMIT` check is sufficient today, with `git fetch --depth 1 origin <sha> && git checkout <sha>` as the fallback when master moves.
- In `recognise_chords`, call `static_ffmpeg.add_paths()` before `subprocess.run`, pass `capture_output=True, text=True`, and treat a non-zero return code as a stage failure quoting the stderr tail; filter the pydub line from the log rather than failing on it.
- Note for `snap_to_beats` (Task 9): the model's HMM boundaries lag the true change by 0.1 to 0.4 s on the clean clip (C->G at 4.23 s, true 4.0; F->C at 16.76, true 16.0), so the "largest share of the beat" rule is the right one; do not expect boundaries on beat lines.

**New confidence: 90%.** Everything in the task has now been executed once on Windows; the remaining 10% is the new code (`vendoring.py` plumbing, `snap_to_beats`) and the fact that the full-song `.lab` quality has not been scored against hand annotations.

---

## Spike C: the synthetic test clip (Task 14)

**Question.** Can a synthetic clip be made musical enough that Beat This! finds 118 to 122 bpm with downbeats on bar starts and the chord model recovers C:maj, G:maj, A:min, F:maj with at most two spurious labels?

**What was run.** `spike_models\make_clip.py` (source below); `spike_models\eval_clip.py` (writes the clip, runs `Audio2Beats(checkpoint_path="final0", device="cpu", dbn=False)` on the mono mix at 44.1 kHz, reports bpm from the median interval and downbeat offsets); `spike_models\run_chords.py` for labels.

**Iterations.**

| iter | change | Beat This! | chord model |
|---|---|---|---|
| 1 | Karplus-Strong strings, decay 0.9 s, 10 ms stagger, kick 0.35, snare 0.16 | 120.00 bpm, 61 beats, 16 downbeats at 0, 2, 4, ... 30 s (offset 0 ms) | C, G, Am, F all found; **2 spurious**: `N` 0 to 0.023 s and `C:maj` 24.03 to 24.98 s inside the Am segment (ring-out of G blending with Am reads as C) |
| 2 | decay 0.9 -> 0.6 s | identical: 120.00 bpm, interval std 0.0 ms, every downbeat within 0 ms of a bar start, none missed | C, G, Am, F; **1 spurious** (`N`, 23 ms at the start); boundaries within 0.03 to 0.76 s of the true 4 s changes |

Both criteria met at iteration 2. Beat This! ran in 0.9 to 1.0 s on CPU for the 30 s clip; clip synthesis takes 1.4 s after vectorising the Karplus-Strong loop (a per-sample Python loop was the first draft and would have taken tens of seconds).

**Observations for the end-to-end test.** The clip's first 23 ms are labelled `N`; the end-to-end assertion `{"C:maj","G:maj","A:min","F:maj"} <= {e.triad ...}` is a superset test so this does not matter, but any "no `N`" assertion would fail. The chord model's segment boundaries lag by 0.1 to 0.4 s (see Spike B), so `snap_to_beats` gets a majority vote per beat rather than clean edges. Beat This! places a downbeat at exactly 30.0 s (the clip end) as well as 0.0 s; `build_bars` must tolerate a downbeat equal to the duration.

**Recommended plan change (Task 14).** Use the source below as `tests/fixtures/make_clip.py` verbatim. Keep `make_clip(path, seconds=30)`; it writes 44.1 kHz stereo 16-bit PCM via soundfile.

```python
"""Synthetic ukulele test clip: 120 bpm, 4/4, C G Am F, island strum, light drums.

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
SNARE_GAIN = 0.16
HAT_GAIN = 0.0         # off by default


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
        # drums: kick on 1 and 3, snare on 2 and 4
        for beat in range(BEATS_PER_BAR):
            t0 = int((bar_start + beat * beat_s) * SR)
            if t0 >= n_total:
                break
            if beat in (0, 2):
                k = _kick(int(0.25 * SR)) * KICK_GAIN * (1.0 if beat == 0 else 0.85)
                mix[t0:t0 + len(k), 0] += k
                mix[t0:t0 + len(k), 1] += k
            else:
                sn = _snare(int(0.18 * SR), rng) * SNARE_GAIN
                mix[t0:t0 + len(sn), 0] += sn
                mix[t0:t0 + len(sn), 1] += sn
            if HAT_GAIN > 0:
                for half in (0, 1):
                    th = int((bar_start + (beat + 0.5 * half) * beat_s) * SR)
                    h = rng.normal(0, 1, int(0.03 * SR)) * np.exp(-np.arange(int(0.03 * SR)) / SR * 120)
                    mix[th:th + len(h), 0] += h * HAT_GAIN
                    mix[th:th + len(h), 1] += h * HAT_GAIN

    mix = mix[:n_total]
    peak = np.max(np.abs(mix))
    if peak > 0:
        mix = mix / peak * 0.89
    # small fade out at the end
    fade = int(0.05 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
    sf.write(str(path), mix.astype(np.float32), SR, subtype="PCM_16")


if __name__ == "__main__":
    import sys

    make_clip(sys.argv[1] if len(sys.argv) > 1 else "clip.wav")
```

**New confidence: 88%.** The two model-dependent assertions are now demonstrated with margin (bpm exact, downbeats exact, four triads with one harmless `N`). What is still untried in one run is Demucs separation on this clip (expected to be benign, the guitar stem may be near-silent since the strings are synthetic, which exercises the "mix" fallback) and the alphaTab/PDF render of its output.

---

## Spike D: section segmentation on real songs (Task 8)

**Question.** Does the Laplacian segmentation on bar-synchronous chroma+MFCC recover the section boundaries of the two target songs, which `k` rule works, and do the plan's labeller rules name the sections sensibly?

**Reference caveat.** `research_notes` contains **no timed section list** for either song; the Hooktheory notes give only section names and progressions (Summer of '69: verse I-V, pre-chorus/chorus vi-V-I-IV, bridge I-IV-V-IV in F; Pour Some Sugar: verse C#m power chords, pre-chorus F#, chorus E, bridge E Mixolydian), and the YouTube `source.info.json` files have no chapters. The reference used here (`spike_models\out\ref_s69.json`, `ref_pssom.json`) was therefore **derived from the chord model's progression changes** (Spike B `.lab` files), which fall exactly where Hooktheory's progressions change, plus song form for boundaries inside a shared progression (intro->verse, solo->verse 4), marked `soft`. Hard boundaries: Summer of '69 at 31.6, 49.0, 69.7, 87.1, 100.9, 114.7, 142.4, 159.8 s (8); Pour Some Sugar at 51.2, 56.9, 79.6, 130.4, 136.0, 158.7, 209.5, 215.0 s (8). The owner's hand annotations (plan Task 15) should replace this.

**What was run.** `spike_models\segment.py <audio.wav> <beats.json> <ref.json> <tag>`: `librosa.feature.chroma_cqt` (bins_per_octave 36) + 20 MFCCs at hop 512, `librosa.util.sync` to the beats from the download spike's `beats.json` (Beat This! final0: Summer of '69 477 beats, 121 downbeats, 136.4 bpm against 139 nominal; Pour Some Sugar 373 beats, 134 downbeats, 85.7 bpm against 85), bar features = mean of beat features between consecutive downbeats; then the librosa tutorial pipeline on bar features: `stack_memory(chroma, 4)` -> `recurrence_matrix(width=3, mode="affinity", sym=True)` -> `timelag_filter(median_filter, size=(1,7))` -> MFCC path similarity blended by the tutorial's `mu` -> `csgraph.laplacian(normed=True)` -> `eigh` -> row-normalised first `k` eigenvectors -> `KMeans(k, n_init=10, random_state=0)`; boundaries at label changes, 2-bar minimum enforced by merging. Feature extraction 4.3 s and 7.4 s per song; each `k` under a second.

**Results: boundary recall against the 8 hard boundaries.**

| k | Summer of '69 segments | hard within 1 bar | hard within 2 bars | precision (1 bar) | Pour Some Sugar segments | hard within 1 bar | hard within 2 bars | precision (1 bar) |
|---|---|---|---|---|---|---|---|---|
| 3 | 4 | 1/8 | 1/8 | 0.33 | 10 | 6/8 | 7/8 | 0.67 |
| **4** | 10 | 4/8 | **7/8** | 0.44 | 11 | 6/8 | **7/8** | 0.60 |
| 5 | 11 | 4/8 | 7/8 | 0.40 | 11 | 2/8 | 8/8 | 0.20 |
| 6 | 13 | 4/8 | 7/8 | 0.33 | 13 | 6/8 | 7/8 | 0.50 |
| 7 | 14 | 4/8 | 7/8 | 0.31 | 16 | 3/8 | 7/8 | 0.20 |
| 8 (plan rule) | 15 | 4/8 | 7/8 | 0.36 | 14 | 3/8 | 7/8 | 0.23 |

Summer of '69 at k=4 (boundaries in seconds, cluster): 0.0 (1), 33.4 (2), 52.4 (1), 69.8 (2), 90.6 (1), 100.9 (0), 118.3 (1), 142.5 (2), 163.3 (1), 192.7 (3). Cluster 2 is the three pre-chorus/choruses, cluster 0 the bridge, cluster 3 the fade, cluster 1 everything on the I-V progression. The four "misses" at 1 bar (52.4 vs 49.0, 90.6 vs 87.1, 118.3 vs 114.7, 163.3 vs 159.8) are all **exactly 2 bars late and all at chorus-to-verse transitions**; the chorus ends on two bars of D that the chord-derived reference counts as verse, so the segmenter is arguably right and the reference early. Recall on all 11 boundaries including the soft intro/verse ones is 4/11 at k=4 (intro->verse 1->verse 2 share both progression and texture and are not separable by these features).

Pour Some Sugar at k=4: 0.4 (1), 51.3 (2), 54.8 (0), 84.5 (2), 86.6 (1), 130.4 (2), 136.0 (0), 161.4 (2), 209.5 (2), 213.7 (0), 261.0 (3). Cluster 0 is the three choruses (E A B), cluster 1 intro+verse 1 and verse 2, cluster 2 the short pre-chorus/transition bars, cluster 3 the final fade. Only the bridge->pre-chorus boundary at 158.7 is off (found at 161.4, 1.3 bars late) and the pre-chorus->chorus at 215.0 is found at 213.7 (0.6 bar early, counted as a hit).

**`k` rule.** The plan's `max(3, min(8, round(n_bars / 8)))` gives **8** for both songs (121 and 134 bars) and over-segments (15 and 14 segments, precision 0.36 and 0.23, singleton clusters of 4 to 7 bars). The eigengap heuristic chose 3 (Summer of '69) and 5 (Pour Some Sugar), neither good. `k = max(3, min(6, round(n_bars / 30)))` gives **4** for both and is the best row in both tables. Recommend that rule; a 3 to 4 minute 4/4 pop song has 90 to 140 bars and three to five distinct section types.

**Labeller rules (plan Task 8) against these clusterings at k=4.**

| rule | Summer of '69 | Pour Some Sugar | verdict |
|---|---|---|---|
| most repeated cluster = chorus | cluster 1 (I-V material: intro, verse 3, riff, solo, outro; 5 occurrences, 67 bars) named chorus; real chorus cluster 2 (3 occurrences) named verse | cluster 2 (short pre-chorus/transition bars, 5 occurrences, 29 bars) named chorus; real chorus cluster 0 (3 occurrences, 65 bars) named verse | **wrong on both songs** |
| most bars = chorus | cluster 1 (67 bars) wrong | cluster 0 (65 bars) right | unreliable |
| **loudest cluster (mean bar RMS) among clusters occurring at least twice = chorus** | cluster 2 at -12.1 dB vs cluster 1 at -12.9 dB: **right** | cluster 0 at -11.9 dB vs cluster 2 at -12.4 dB vs cluster 1 at -14.0 dB: **right** | right on both |
| first segment = intro if not the chorus cluster | first segment is the verse-progression cluster (intro, verse 1 and 2 merged) | same (intro and verse 1 merged) | acceptable: it would be labelled verse, not intro, because the cluster recurs; name it "intro" only when its cluster occurs once |
| lone middle cluster = bridge | cluster 0 at 100.9 s (bridge, F-Bb-C) occurs once in the middle: **right** | no lone middle cluster; the bridge (158.7 to 209.5, breakdown on E) was absorbed into the "transition" cluster 2 | right where it fires; misses a long bridge that shares chords with the chorus |
| last new cluster = outro | cluster 3 at 192.7 s (fade): right | cluster 3 at 261.0 s (fade): right (4 bars) | right on both |

**Recommended plan changes (Task 8).**

- `segment_boundaries(..., k=None)`: `k = max(3, min(6, round(n_bars / 30)))`.
- `label_sections` needs a loudness input: change the signature to `label_sections(boundaries, cluster_ids, n_bars, bar_loudness_db: Sequence[float]) -> list[Section]` (the grid stage already has the audio; compute `librosa.feature.rms` per bar). Rules in order: (1) chorus = the cluster with the highest mean bar loudness among clusters that occur at least twice (fallback: most bars); (2) verse = the remaining recurring cluster with the most bars; (3) a cluster occurring once: first segment -> "intro", last segment -> "outro", otherwise -> "bridge"; (4) other recurring clusters -> "verse 2", "verse 3", ...; (5) if the first segment's cluster recurs, label it by its cluster (verse), not intro. Keep confidence 0.5. Update `test_label_sections_names_most_repeated_cluster_chorus` to `..._names_loudest_recurring_cluster_chorus` and add a test where the most repeated cluster is quiet and short.
- Features: keep chroma+MFCC; `bins_per_octave=36` for the CQT chroma and `stack_memory(n_steps=4)` on the chroma worked; no change needed. Bar aggregation by mean over beats is adequate.
- Tolerance in `test_segment_boundaries_recovers_abab_structure`: "within +-1 bar" is right for the synthetic test, but tell the implementer that on real songs 2 bars is the realistic accuracy at chorus-to-verse transitions.
- The 2-bar minimum merges a short segment into the previous one; on Pour Some Sugar this left the 3-bar pre-chorus segments intact, which is the desired behaviour.
- Beat This! bpm on Summer of '69 was 136.4 against the 139 nominal (its median beat interval is 0.44 s; the song is 139 bpm, so some beats are 0.42 and some 0.44 s, which at 10 ms quantisation is expected); `bpm_from_beats` should round to the nearest integer in the sheet header.

**New confidence: 82%.** The pipeline runs end to end on real songs and recovers 7 of 8 hard boundaries within 2 bars on both with a single `k`; the labeller needed a rule change which is now specified and verified against two songs. It is not higher because the reference was chord-derived rather than human-timed, two songs is a small sample, and intro-versus-verse and long bridges that share the chorus's chords are not separable by these features.

---

## Files produced

- `<scratchpad>\spike_models\spike_a_ffmpeg.py` - Spike A proof.
- `<scratchpad>\spike_models\chord_cnn_lstm\` - clone at `481f4ce7`, patched (git diff: 3 files, 15 lines).
- `<scratchpad>\spike_models\run_chords.py`, `out\iter1.lab`, `out\iter2.lab`, `out\s69.lab`, `out\pssom.lab`, `out\dir with spaces\out file.lab`.
- `<scratchpad>\spike_models\make_clip.py`, `eval_clip.py`, `clip.wav` (iteration 1), `clip2.wav` (iteration 2, final).
- `<scratchpad>\spike_models\segment.py`, `out\ref_s69.json`, `out\ref_pssom.json`, `out\seg_s69.json`, `out\seg_pssom.json`.
