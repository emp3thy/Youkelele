# Spike: audio chain on the two target songs (plan Tasks 6, 7 and 10)

Date: 2026-10-03. Machine: CPU-only Windows 11 (Core Ultra 9 285H), Python 3.12 venv with yt-dlp 2026.08.19, deno 2.9.7 (PyPI), static-ffmpeg 3.0 (ffmpeg 8.0.1 gyan.dev essentials), audio-separator 0.47.0, torch 2.14.1+cpu, librosa 1.0.0, beat_this 1.1.0.

Everything below was run against real downloads of the two target songs, not fixtures. Scripts live in `SP\spike_audio\scripts\` (SP is the session scratchpad `C:\Users\gethi\AppData\Local\Temp\claude\C--Users-gethi-sources-Youkelele\220af8bd-a800-4337-8952-bc02c39eceb8\scratchpad`); outputs are in `SP\spike_audio\s69\` and `SP\spike_audio\pssom\`, including `audio.wav`, `beats.json`, the stems, `onsets_*.json`, `bars_*.txt` and `spike3*.json`.

| Task | Before | After | One-line reason |
|---|---|---|---|
| 6 Ingest | 85% | 95% | The exact `YoutubeDL` option keys were read from source and proven end to end on both songs; the only residual risk is YouTube itself changing. |
| 7 Separate | 85% | 95% | Default and custom output naming observed on real runs, mapping rule and return-value shape pinned down; the only untested branch is `chunk_duration`, which the plan does not use. |
| 10 Strums | 65% | 75% | Grid choice, RMS threshold, emission and uncertainty floor are now grounded in measurements, but the mute detector needs a different feature than the plan says, and one of the two songs' guitar stems is too smeared for pattern inference regardless of code quality. |

---

## Spike 1: yt-dlp Python API options (Task 6)

### Question

Which keys in the `yt_dlp.YoutubeDL` options dictionary correspond to the CLI flags `--js-runtimes` and `--ffmpeg-location`, what is the structure of the `js_runtimes` value, and does the library path work for the two target songs with the pip-installed Deno and ffmpeg?

### What was run

- Read `yt_dlp/options.py` (lines 460 to 500, 1765), `yt_dlp/YoutubeDL.py` (docstring lines 520 to 555, `_clean_js_runtimes` 863, `_js_runtimes` 886, debug line 4170 to 4180), `yt_dlp/__init__.py` (784 to 786, 944 to 956) and `yt_dlp/utils/_jsruntime.py` (`JsRuntime.__init__(path=None)`, `DenoJsRuntime._info`).
- `scripts/s1_search.py`: `ytsearch3:` and `ytsearch5:` queries with `extract_flat`, listing id, duration, channel and title.
- `scripts/s1_download.py <video_id> <out_dir>`: downloads best audio plus info JSON through `yt_dlp.YoutubeDL`, then converts with the static-ffmpeg binary to 44.1 kHz stereo 16-bit `audio.wav` and probes it with ffprobe. Logs in `s69/spike1_log.txt`, `pssom/spike1_log.txt`; results in `spike1_result.json`.

### Results

Option keys (from source):

- `--ffmpeg-location` is `ffmpeg_location` (str): "either the path to the binary or its containing directory". The CLI also sets `FFmpegPostProcessor._ffmpeg_location` from it, which the library path does not need.
- `--js-runtimes` is `js_runtimes`: a dict `{runtime_name_lower: {config}}`. The CLI builds it as `{runtime.lower(): {'path': path}}` from `deno:<path>` strings. The only config key is `path` (optional; a directory is also accepted and the executable name appended). Supported names: `deno`, `node`, `bun`, `quickjs`. If the key is absent the default is `{'deno': {}}` (found on PATH). A non-dict value raises `ValueError('Invalid js_runtimes format, expected a dict of {runtime: {config}}')`.
- `remote_components` (list, default empty) corresponds to `--remote-components`; not needed because `yt-dlp-ejs` 0.8.0 is installed by the `default` extra.
- `YoutubeDL.__init__` mutates the dict it is given (`remote_components` and `compat_opts` become sets, `http_headers` is added), so log a copy, not the dict passed in.

Options dict that worked, verbatim from the debug `params` line:

```python
{
    "format": "bestaudio/best",
    "outtmpl": str(out_dir / "source.%(ext)s"),
    "writeinfojson": True,
    "ffmpeg_location": r"...\site-packages\static_ffmpeg\bin\win32",   # directory from static_ffmpeg
    "js_runtimes": {"deno": {"path": r"...\venv\Scripts\deno.exe"}},   # str(deno.find_deno_bin())
    "noplaylist": True,
    "verbose": True,                                                     # only for the spike
    "logger": <object with debug/info/warning/error>,
}
```

The ffmpeg directory is `os.path.dirname(static_ffmpeg.run.get_or_fetch_platform_executables_else_raise()[0])` after `static_ffmpeg.add_paths()`; this function returns `(ffmpeg, ffprobe)` paths and is the API Task 5 was unsure about (it fetches on first call, so the preflight should check the directory `static_ffmpeg/bin/win32` exists rather than calling it).

Debug lines proving the runtime and ffmpeg were picked up:

```
[debug] yt-dlp version stable@2026.08.19 from yt-dlp/yt-dlp [594bd50c2] (pip) API
[debug] exe versions: ffmpeg 8.0.1-essentials_build-www.gyan.dev (setts), ffprobe 8.0.1-essentials_build-www.gyan.dev
[debug] Optional libraries: ... yt_dlp_ejs-0.8.0
[debug] JS runtimes: deno-2.9.7
[debug] [youtube] [jsc] JS Challenge Providers: bun (unavailable), deno, node (unavailable), quickjs (unavailable)
```

The downloaded file path is `info["requested_downloads"][0]["filepath"]` (not `info["filepath"]`), and the info JSON lands at `source.info.json` beside it.

Videos chosen (search results inspected by title, channel and duration):

| Song | Candidates seen (id, s) | Chosen | Why |
|---|---|---|---|
| Summer Of '69 | 9f06QZCVUHg 207, 1i0i5lG6Ojc 249 (2022 re-recording), sOmovvrwNWc 301 (live 2024), HtipPCt317Y 418 (live 1996), 3uOXjXG1OEA 261 (stage-screen video), G4QJ5ggLmuA 241 (album trailer) | **9f06QZCVUHg**, 207 s, Bryan Adams channel, "Official Music Video", uploaded 2008-11-04 | The 1984 studio recording; nearest official upload to the 3:34 to 3:40 album length (the video edit shortens the intro: vocals enter at 3.9 s, the 215 s album version has them at about 14 s). No 3:36 album audio exists on the official channel. |
| Pour Some Sugar On Me | Rqs4cMyMLnY 268, 0UIB9Y4OFPs 296 (music video), UrZRpXoKoFQ 274 (UK concept version), KXM2teV1tek 337 (extended) | **Rqs4cMyMLnY**, 267 s, DEF LEPPARD channel, "Provided to YouTube by Universal Music Group ... Hysteria ... 1987" | Album version at 4:27. |

Downloads: both resolved to format 251 (webm/opus, 128 and 123 kbps), 4.5 s and 2.8 s. ffprobe on the converted files: `sample_fmt s16, sample_rate 44100, channels 2`, durations 207.25 s and 267.31 s.

What failed first:

- `json.dump` of the options dict after the run: `TypeError: Object of type set is not JSON serializable` because `YoutubeDL` had mutated it (see above).
- Printing titles on the Windows console: `UnicodeEncodeError: 'charmap' codec` (cp1252) on a title containing `ă`; fixed with `PYTHONIOENCODING=utf-8`. The CLI must not print arbitrary titles without an encoding-safe path.

### Recommended plan changes (Task 6)

- Keep the interface in the plan; the keys are exactly `ffmpeg_location` and `js_runtimes: {"deno": {"path": str(deno.find_deno_bin())}}`.
- Take the audio path from `info["requested_downloads"][0]["filepath"]`.
- Pass a fresh dict to each `YoutubeDL` and do not reuse it; pass `noplaylist: True`.
- Add `"quiet": True, "no_warnings": True` and a `logger` that forwards to the stage log; keep `verbose` off in production.
- In `models/ffmpeg.py`, `ffmpeg_paths()` is `static_ffmpeg.run.get_or_fetch_platform_executables_else_raise()`; the preflight probe checks `Path(static_ffmpeg.__file__).parent / "bin" / "win32" / "ffmpeg.exe"` (platform dir from `static_ffmpeg.run.get_platform_dir()`) without fetching.
- Test fixtures: the ingest test for a URL should use a fake `YoutubeDL` whose `extract_info` returns `{"id": ..., "title": ..., "requested_downloads": [{"filepath": ...}]}`.

### New confidence: 95%

The library path, option keys, runtime detection and conversion were all exercised on the two real songs; what remains is YouTube's own volatility.

---

## Spike 2: audio-separator output naming (Task 7)

### Question

What does `Separator.separate()` return, how are files named by default, and what does `custom_output_names` do?

### What was run

- Read `audio_separator/separator/separator.py` (`separate` 1042, `_separate_file` 1135, `_process_with_chunking` 1214 to 1330) and `common_separator.py` (`get_stem_output_path` 520 to 537), `architectures/demucs_separator.py` (175 to 184).
- `scripts/s2_separate.py <song_dir> default|custom`: `Separator(output_dir=..., model_file_dir=SP\t\models, output_format="WAV").load_model("htdemucs_6s.yaml").separate(audio.wav[, custom_output_names=...])` with `static_ffmpeg.add_paths()` first. Default naming on s69, custom names on pssom. Logs `spike2_log.txt`, results `spike2_default.json` / `spike2_custom.json`.

### Results

Default filename template (from `get_stem_output_path`): `f"{audio_file_base}_({stem_name})_{model_name}.{output_format.lower()}"` where `model_name` is the model filename without extension and the stem names are the Demucs source names capitalised: `Vocals, Drums, Bass, Guitar, Piano, Other`.

Run on s69 (`audio.wav`, 207 s): returned list, in this order and as **bare filenames, not joined with `output_dir`**:

```
['audio_(Bass)_htdemucs_6s.wav', 'audio_(Drums)_htdemucs_6s.wav', 'audio_(Other)_htdemucs_6s.wav',
 'audio_(Vocals)_htdemucs_6s.wav', 'audio_(Guitar)_htdemucs_6s.wav', 'audio_(Piano)_htdemucs_6s.wav']
```

On disk in `stems_default/`: the same six files. Timing: model load 0.1 s (weights already in `model_file_dir`), separation 102.1 s, i.e. 0.49x real time (the assumption check measured 1.0x on a 240 s file; this run had an otherwise idle CPU).

Run on pssom (267 s) with `custom_output_names={"vocals": "vocals", "drums": "drums", "bass": "bass", "guitar": "guitar", "piano": "piano", "other": "other"}`: returned `['bass.wav', 'drums.wav', 'other.wav', 'vocals.wav', 'guitar.wav', 'piano.wav']`, on disk exactly those six files. Timing: load 0.1 s, separation 148.0 s (0.55x real time).

How `custom_output_names` works:

- Normal (non-chunked) path: keys are compared case-insensitively (`{k.lower(): v}` versus `stem_name.lower()`), the value is passed through `sanitize_filename` and the output extension is appended, so `"guitar"` becomes `guitar.wav`. Stems absent from the dict fall back to the default template.
- Chunked path (only when `chunk_duration` is passed to the constructor and the file is longer than it): the merged filename is `custom_output_names[stem_name]` with a **case-sensitive** lookup against the capitalised stem name, otherwise `f"{base_name}_({stem_name})"` **without** the model name. A lower-case dict would silently produce `audio_(Guitar).wav` there.

### Recommended plan changes (Task 7)

- Pass `custom_output_names={"Vocals": "vocals", "Drums": "drums", "Bass": "bass", "Guitar": "guitar", "Piano": "piano", "Other": "other"}` (capitalised keys work in both code paths) and expect `out_dir/<stem>.wav` directly; no renaming needed.
- Treat the returned list as basenames: `paths = [Path(out_dir) / Path(p).name for p in returned]`, then verify that the six expected files exist and raise with the directory listing if not.
- Keep a defensive fallback mapper for the default template, regex `_\(([A-Za-z]+)\)` lower-cased, for the case where a future version ignores custom names; the plan's `test_stem_name_mapping_from_audio_separator_filenames` stays valid (`"source_(Guitar)_htdemucs_6s.wav" -> "guitar"`).
- Record the measured runtime (about 0.5x to 1.0x real time on this CPU) in the stage log message so users know what to expect.
- Do not set `chunk_duration`.

### New confidence: 95%

Both naming modes and the return value were observed on full-length real inputs; the mapping rule is now a one-liner with a verified fallback.

---

## Spike 3: strum onsets on the real guitar stems (Task 10)

### Question

Do the plan's slot quantisation, direction rule, mute threshold (spectral flatness 0.3), usable-stem threshold (RMS ratio 0.05), emission function, 37-pattern Viterbi with switch penalty 0.35 and uncertainty floor 0.45 behave sensibly on the real guitar stems of the two songs?

### What was run

- `scripts/s3_beats.py <song_dir>`: Beat This! `Audio2Beats(checkpoint_path="final0", device="cpu", dbn=False)` on the soundfile mono mix; writes `beats.json {beats, downbeats, bpm}` (bpm = 60 / median inter-beat interval).
- `scripts/s3_strums.py <song_dir> <guitar_stem> <sections_json>`: builds bars from the beat grid, computes guitar/mix RMS ratio overall and per section, runs `librosa.onset.onset_strength` + `onset_detect(units="frames", backtrack=False)` at hop 256 on the stem and on the mix, samples spectral flatness, centroid, rolloff, zero-crossing rate, >2 kHz energy share, RMS, onset strength and a 150 ms decay ratio at each onset, quantises onsets to 8 and 16 slots per bar (nearest slot; slot times interpolated between detected beats), builds 8-slot bar vectors (D even, U odd, x if flatness > 0.3), evaluates the plan's emission against four reference patterns and runs the plan's Viterbi per section. Env `ONSET_TUNED=1` or `ONSET_DELTA`/`ONSET_WAIT` change the peak-picking parameters. Outputs `spike3*.json`, `bars_<src>*.txt`, `onsets_<src>*.json`.
- `scripts/s3_threshold.py <onsets_json> <muted_sections> <open_sections>`: per-feature AUC and best balanced-accuracy threshold between muted and open sections.
- `scripts/s3_mute.py <song_dir> <onsets_json> <feature> abs|rel <thr>`: rebuilds bar vectors with an alternative mute rule and reruns emission and Viterbi, with and without added chug patterns.
- `scripts/s3_sixteen.py <song_dir> <onsets_json> 8|16` (env `EMIT=jaccard`): strike/rest-only emission on the 8 and 16 grids, with the 8-slot vocabulary expanded to 16 slots.
- `scripts/summarise.py <spike3.json>`: table printer.

Section boundaries were placed by hand on bar lines using the per-bar RMS of the vocal and guitar stems (`s69/sections.json`, `pssom/sections.json`). S69 (bar = 1.76 s): intro 0.4, verse 3.9, prechorus 31.6, chorus 45.5, riff 49.0, verse2 54.2, prechorus2 68.0, chorus2 83.6, riff2 99.2, bridge 100.9, solo 114.8, breakdown 128.6, outro 163.3. PSSOM (bar = 2.8 s): intro 0.4, riff 6.1, verse 17.4, verse_b 34.3, prechorus 45.6, chorus 56.9, verse2 85.2, prechorus2 113.4, chorus2 124.7, solo 164.3, breakdown 192.5, outro 203.8. "Muted" ground truth for S69 is the UG chart (intro and verse); "open" is chorus2 ("Standin' on your mama's porch") and the outro.

### Results

**Beat grid (input to everything else).** S69: 477 beats, 121 downbeats, 136.4 BPM (published 139), 118 of 120 downbeat-to-downbeat spans are 4 beats, 98% of downbeats sit on one 4-beat phase; 4.3 s on CPU. PSSOM: 373 beats, 134 downbeats, 85.7 BPM (published 85), but downbeat spans are 1, 2, 3 or 4 beats (24/41/6/62) and only 64% of downbeats agree with the majority phase; 5.9 s. The spike built bars as every fourth beat from the majority downbeat phase. Task 8's `build_bars` must do the same (take the modal phase, not each downbeat) or PSSOM gets 134 ragged bars.

**(e) RMS ratio guitar stem / mix.** S69 0.387 overall; per section 0.27 (prechorus2) to 0.94 (intro, where the guitar is alone). PSSOM 0.296 overall; 0.21 to 0.33 in guitar sections, 0.075 in the a cappella intro (drums and voice only, guitar bleed), 0.033 in the drum-and-voice breakdown. The 0.05 whole-song threshold is passed by a factor of 6 to 8 on both songs and is safe. Per section, a ratio below about 0.10 marks "no guitar here" (intro 0.075, breakdown 0.033) while real guitar sections never fell below 0.21.

**(a) Grid fit.** Share of onsets within 15% of a slot (deviation measured in slot widths), default librosa peak-picking:

| Song, source | onsets | eighth grid | sixteenth grid | nearer an odd sixteenth | onsets per bar |
|---|---|---|---|---|---|
| S69 guitar stem | 488 | **0.926** | 0.736 | **0.031** | 4.1 (intro 7.0, verse 6.3, outro 3.2) |
| S69 mix | 688 | 0.887 | 0.744 | 0.064 | 5.8 |
| PSSOM guitar stem | 560 | 0.455 | **0.575** | **0.461** | 6.0 |
| PSSOM mix | 872 | 0.685 | **0.917** | 0.305 | 9.4 |

Per S69 section the eighth-grid share was 0.81 (bridge) to 1.00 (chorus, verse2); PSSOM stem sections ranged 0.35 to 0.56 on the eighth grid and 0.40 to 0.77 on the sixteenth grid. The plan's `choose_slots_per_bar` rule (16 slots when more than 25% of onsets are nearer a sixteenth position) gives 8 for S69 (3%) and 16 for PSSOM (46%), which is musically right (85 BPM sixteenth chug versus 139 BPM eighths). Note the sixteenth-grid share can never be lower than the eighth-grid share, so the diagnostic for "is the grid right" is the odd-sixteenth share, and the diagnostic for "are the onsets any good" is the within-15% share on the chosen grid. By that measure the PSSOM guitar stem is poor (0.575) while its mix is clean (0.917): Demucs smears the attacks of the layered, compressed Rockman guitars, whereas the drum-dominated mix is locked to the grid.

Peak-picking parameters: lowering `delta` to 0.03 with `wait` 80 ms doubled the S69 stem onsets (488 to 1036), dropped the within-15% share to 0.65 and filled almost every slot, so every section decoded as `DUDUDUDU` with "confidence" 0.86 to 0.96. That is a degenerate result, not an improvement. `delta` 0.05 gave 699 onsets, within-15% 0.84, verse 7.25 onsets per bar. Keep librosa's defaults in version one and report the within-15% share in the stage notes.

**Direction rule.** Median onset strength on even versus odd eighth slots: S69 stem 0.996 / 0.942, S69 mix 1.42 / 1.11, PSSOM stem 1.048 / 0.995, PSSOM mix 1.66 / 1.41. Off-beat strikes are consistently a little weaker, which is compatible with up-strums or simply with unaccented off-beats. Nothing measurable contradicts the rule, but nothing confirms it either: the S69 verse is physically all down-strokes (UG), yet the rule writes U on the off-beats. Direction from metric position is a notation convention for the player, not a detection; the sheet should present it as the suggested direction.

**(b) Mute detection.** Spectral flatness on the guitar stem is tiny everywhere: S69 verse median 1.7e-5 (p90 5.4e-5), open sections median 4.9e-5 (p90 1.2e-4); PSSOM 1e-5 to 2e-4. On the mix it is 0.003 to 0.02. The plan's threshold 0.3 **never fires**, so no `x` is ever produced and the `x`-versus-`D/U` emission rule is dead code. Separation of S69 muted (intro + verse, 115 onsets) from open (chorus2 + outro, 121 onsets) per onset:

| Feature | muted p10/p50/p90 | open p10/p50/p90 | AUC | best threshold | balanced accuracy |
|---|---|---|---|---|---|
| spectral flatness | 7e-6 / 1.7e-5 / 5.4e-5 | 1.3e-5 / 4.9e-5 / 1.2e-4 | 0.77 | < 3.9e-5 | 0.75 |
| spectral centroid (Hz) | 940 / 1299 / 1974 | 1514 / 2085 / 2365 | **0.89** | < 1756 | **0.83** (tpr 0.83, tnr 0.83) |
| zero-crossing rate | 0.020 / 0.032 / 0.073 | 0.043 / 0.080 / 0.099 | **0.89** | < 0.048 | **0.83** (tpr 0.77, tnr 0.89) |
| energy share above 2 kHz | 0.013 / 0.053 / 0.231 | 0.087 / 0.303 / 0.486 | 0.88 | < 0.126 | 0.81 |
| spectral rolloff 85% (Hz) | 1986 / 2778 / 3635 | 3031 / 3575 / 4043 | 0.84 | < 3171 | 0.80 |
| RMS at onset | 0.021 / 0.036 / 0.058 | 0.042 / 0.064 / 0.091 | 0.87 | < 0.050 | 0.83 (level dependent, not portable) |
| onset strength | 0.80 / 1.11 / 1.88 | 0.81 / 0.94 / 1.16 | 0.71 | | 0.69 |
| 150 ms decay ratio | 0.60 / 0.81 / 1.08 | 0.71 / 0.91 / 1.12 | 0.64 | | 0.63 (does not separate) |

So flatness does separate weakly but at a scale ten thousand times below 0.3; centroid and zero-crossing rate separate well on S69. With `centroid < 1756 Hz` (or the relative rule `< 0.85 x song median`, median 2004 Hz) the S69 verse bars become 84 to 87% `x`, the intro 86%, chorus2 0%, prechorus 7%, but the outro 29 to 32% (quieter open chords misread as muted) and verse2 54 to 65% (plausible: verse 2 is also chugged). On PSSOM the per-section centroid medians are all 1870 to 2140 Hz (song median 2073) and `x` lands on 11 to 48% of onsets in every section with no section-level separation: the palm-muted riff and the open chorus chords are not distinguishable by timbre in that stem. Conclusion: a timbre-based mute detector works on one of the two songs and must be relative to the song, conservative, and allowed to fail silently.

**(c) Match against the published S69 patterns** (plan emission: equal strike direction, both rests or both mutes 1; strike versus rest 0; `x` versus `D/U` 0.5; mean share over the section's bars, guitar stem, default onsets):

| Section | `D-D-DUDU` (UkuTabs driving) | `DUDUDUDU` (UkuTabs simple) | `xxxxxxxx` (UG muted chug) | `DDDDDDDD` |
|---|---|---|---|---|
| verse, flatness rule (no `x` fires) | 0.633 | **0.742** | 0.371 | 0.328 |
| verse, centroid rule | 0.367 | 0.418 | **0.695** | 0.348 |
| intro, centroid rule | 0.438 | 0.500 | **0.812** | 0.438 |
| chorus2 (open) | 0.583 | **0.611** | 0.306 | 0.389 |
| outro (open) | 0.429 | 0.375 | 0.188 | 0.208 |

The record's guitar plays straight eighths; UkuTabs' "driving 4/4" is an arrangement suggestion and never scores best anywhere, so "agreement with a published ukulele pattern" is not a valid accuracy test for this stage. The UG chart (muted eighths) is reproduced once a working mute rule is used. `DDDDDDDD` can never be emitted because the direction rule puts U on odd slots; the detector's spelling of a chug is `DUDUDUDU` or `xxxxxxxx`.

**(d) Viterbi over the 37 patterns, switch penalty 0.35** (S69 guitar stem, default onsets, flatness rule, section pattern = mode of the path, confidence = mean emission x share of bars):

| Section | bars | pattern | confidence | musically |
|---|---|---|---|---|
| intro | 2 | `D-DUDUDU` | 0.875 | chug; one slot missed per bar |
| verse | 16 | `D-DUDUDU` | 0.594 | chug |
| prechorus | 8 | `--DU--D-` | 0.422 | arpeggiated; rightly uncertain |
| chorus | 3 | `--DU--D-` | 0.708 | too short to mean anything |
| riff | 3 | `D-DU-UD-` | 0.292 | |
| verse2 | 7 | `D-DUD-D-` | 0.321 | |
| prechorus2 | 9 | `D-DU-UD-` | 0.583 | |
| chorus2 | 9 | `DUDUDUD-` | 0.542 | open eighths |
| bridge | 9 | `D-DU-UD-` | 0.403 | |
| solo | 7 | `D-DUDUDU` | 0.589 | |
| breakdown | 21 | `D-------` | 0.506 | sparse picking |
| outro | 23 | `D-------` | 0.527 | sustained chords |

Steadily strummed sections score 0.51 to 0.59 (0.875 on the 2-bar intro), transitional or arpeggiated ones 0.29 to 0.42, so the 0.45 floor falls in the gap, but the gap is thin (0.422 versus 0.506) and sections of 2 or 3 bars give meaningless high scores. With the centroid mute rule the verse decodes to `DUxUDUxU` at 0.395 (the only `x` pattern in the vocabulary) and, once `xxxxxxxx` is added, to `xxxxxxxx` at 0.613. On the PSSOM stem at 16 slots the plan's emission picks sparse patterns (`S---------------`, `S-------S-------`) with confidence 0.6 to 0.8 in most sections because rest-rest matches count as much as strike matches, so a bar with six scattered onsets matches a near-empty pattern on 13 of 16 slots; that is an inflated confidence on a stem whose onsets are 57% on-grid.

A strike-overlap emission (`matched strikes / slots where either has a strike`, i.e. Jaccard, keeping 0.5 credit for `x` versus `D/U`) fixes the inflation: S69 steady sections still score intro 0.875, verse 0.671, solo 0.577, chorus2 0.524, while prechorus 0.25, verse2 0.31, bridge 0.33, breakdown 0.24 and outro 0.13 drop clearly below 0.45 (prechorus2 0.467 is the one borderline case); on the PSSOM stem every section but two falls to 0.09 to 0.40 (prechorus2 0.67 and solo 0.59 as all-sixteenths), which is the honest answer for that stem. On the PSSOM mix the same decoder gives `S-S-S-S-S-S-S---` at 0.61 to 0.77 in the vocal sections and all-sixteenths 0.77 in the solo, i.e. the drum pattern, which is why the mix must stay a fallback only.

**Vocabulary and direction observations.** Because the observed direction is a deterministic function of slot index and every pattern in the table except `-D-D-D-D` also has D on even and U on odd slots, direction carries no information in the emission; `-D-D-D-D` can never win against `-U-U-U-U`. On the 16 grid the plan's expansion of 8-slot patterns by inserting rests gives a U at every eighth off-beat (slot 2, 6, 10, 14) exactly where the sixteenth direction rule writes D, so no 8-slot pattern containing U could ever match an observation on the 16 grid. Both problems disappear if the emission compares strike, rest and mute classes only and the direction is rendered from position afterwards.

### Recommended plan changes (Task 10)

1. **Mute feature.** Replace `spectral_flatness > 0.3` with a relative timbre rule on the guitar stem: an onset is `x` when its spectral centroid (mean over the onset frame and the next three, hop 256, n_fft 2048) is below `0.85 x` the median onset centroid of the song **and** its zero-crossing rate is below `0.65 x` the song median (both measured: thresholds 1703 Hz and 0.048 on S69 correspond to 0.85 and 0.65 of the medians). Store `centroid` and `zcr` in `Onsets` instead of `flatness`. Document that this marks palm-muted or chunked strikes only when the stem exposes the timbre difference; on PSSOM it will mark scattered `x` that the Viterbi absorbs at 0.5 credit.
2. **Emission.** Compare classes only (strike = `D` or `U`, mute = `x`, rest = `-`), scored as matched strikes plus 0.5 for strike-versus-mute, divided by the number of slots where either side has a strike or mute (1.0 for two empty bars). Direction is applied to the decoded pattern from slot position, not compared. Keep the 0.45 floor; the measured gap with this emission is 0.47 to 0.52 versus 0.13 to 0.33.
3. **Vocabulary.** Add `xxxxxxxx` ("muted eighths, chug") and `x-x-x-x-` ("muted quarters") to the 4/4 rows so a detected chug has a target; drop `-D-D-D-D` or keep it as a display alias of `-U-U-U-U`. Add an all-sixteenths row `DUDUDUDUDUDUDUDU` for the 16 grid. Expansion of 8-slot rows to 16 slots stays as rest interleaving because directions are no longer compared.
4. **Section guard.** Sections shorter than 4 bars take the pattern of the previous section with `uncertain=True`; confidence from 2 or 3 bars is noise (S69 chorus 0.708 on an arpeggio fragment).
5. **Slot choice.** Keep `choose_slots_per_bar` at the 25% rule; measured 3% (S69) and 46% (PSSOM). Record the within-15% share on the chosen grid in the stage notes (`grid_fit`); below 0.6 the whole stage should set `uncertain=True` for every section regardless of Viterbi confidence (PSSOM stem 0.575, S69 stem 0.926).
6. **Onset detection.** Librosa defaults (`delta` 0.07, `wait` 0.03 s), `hop_length=256`, `backtrack=False`; no tuning. Lower `delta` inflates onsets and produces fake `DUDUDUDU` everywhere.
7. **Usable stem.** Keep 0.05 for the whole-song decision (measured 0.39 and 0.30). Add a per-section RMS ratio below 0.10 as "no guitar in this section" (measured 0.03 to 0.075 for the drum-and-voice sections versus 0.21 and up elsewhere), emitting the all-rest pattern with `uncertain=True` rather than decoding noise.
8. **Bars from downbeats.** This belongs to Task 8 but Task 10 depends on it: build bars from the modal downbeat phase (every `meter.numerator` beats from the beat index most often marked as a downbeat), not from each downbeat; Beat This! downbeats on PSSOM were only 64% consistent.
9. **Tests.** Replace `test_quantise_bar_marks_flat_onset_muted` by a centroid/zcr-relative test; add a test that the emission of a half-empty bar against the whole-bar pattern is not inflated (`"D-------"` versus `"D-D-----"` should score 0.5, not 0.875); add a 16-slot test that an eighth-note observation `D-U-D-U-...` matches the expanded `DUDUDUDU`.
10. **Expectation setting.** Do not assert agreement with UkuTabs' or UG's published patterns in tests. The S69 record gives straight eighths (muted in verses, open in choruses); PSSOM's guitar stem does not support pattern inference and the stage should say so through `uncertain`.

### New confidence: 75%

The grid, slot choice, RMS threshold, Viterbi floor and emission shape are now backed by numbers from two real songs and the required changes are specific; what keeps it from higher is that the mute detector is song dependent (works on S69, not on PSSOM) and that dense 1980s productions give a guitar stem whose onsets are only about 57% on-grid, so product quality on such songs is capped by separation rather than by this stage's code.

---

## Side findings for other tasks

- Task 5: `static_ffmpeg.run.get_or_fetch_platform_executables_else_raise()` returns `(ffmpeg_path, ffprobe_path)` and fetches on first call; the installed location is `site-packages/static_ffmpeg/bin/win32/` (from `get_platform_dir()`), which the preflight can test for without fetching.
- Task 8: Beat This! tempo was 136.4 (139 published) and 85.7 (85 published); PSSOM downbeats are inconsistent (see above). Full-song inference took 4.3 s and 5.9 s on CPU. Section boundaries derived by hand from per-bar vocal and guitar stem RMS were easy to place, which suggests stem RMS is a useful extra feature for `beat_sync_features` alongside chroma and MFCC.
- Task 14: the S69 video edit is 207 s with vocals from 3.9 s; the 215 s album timing in the research notes is offset by about 10 s for this upload.
- CLI output on Windows: any printing of YouTube titles needs an encoding-safe path (cp1252 console).
