# Code map for the reviewers (written 2026-10-08, main at the 1.7 merge, commit 74c11e0)

Each weak area, the modules that implement it today, the constants in play, and where the ear truth and measurements live. Reviewers read the code itself; this map only says where to look.

Package: `src/youkelele/`. Stages run in order: ingest, separate (Demucs htdemucs_6s via audio-separator, `models/separator.py`), grid, harmony, strums, riff, score, render. 822 tests under `tests/`. Measurement harness: `src/youkelele/evaluate.py` (`evaluate` and `evaluate --compare` read a run folder and print per-section figures).

Owner's rules that any suggestion must respect:
- Generality: no code path, constant or test may depend on which song is processed. Constants sit inside bands measured across every available section; the validation songs are where patterns are learnt, never what the program is built for.
- Every design spec ends with an Assumptions section: each assumption, its status (verified, measured, unverified) and what it costs if wrong.
- No timescales or hour estimates in plans; size by scope and risk.
- Spikes are welcome and run without asking when they would settle a design point or raise a plan task's confidence.
- Install stays pip-based on Windows (`install.ps1`, `uv`), with torch and librosa already present; model size and licence matter.

## 1. Onset detection and strike density

- `music/onsets.py`: `detect_onsets` (librosa `onset_strength`, mean aggregate, hop 512, then `onset_detect` with default peak picking, `backtrack=False`); `choose_slots_per_bar` (eighth versus sixteenth by `ODD_SIXTEENTH_SHARE` 0.25 and `SIXTEENTH_MIN_MS` 105); `grid_fit` (`GRID_FIT_TOLERANCE` 0.15); `mute_mask` (`MUTE_CENTROID` 0.85 and `MUTE_ZCR` 0.65 times the song median); `quantise_bar` → strike classes S, M, rest per slot; `direction_for_slot` assigns D on the beat and U off it (not measured).
- `music/recall.py`: the recall gate adds high-band (3 kHz) onsets to sparse sections on the eighth grid only (`SPARSE_SHARE` 0.4, `MERGE_MS` 60, `SILENT_BAR_SHARE` 0.25).
- `stages/strums.py`: `_slot_onsets`, `_onset_bars`, `_bar_records`, `MEMBER_AGREE` 0.35.
- Ear truth: `docs/superpowers/specs/2026-10-05-v1-6-validation.md` (listening pass, clips 11 to 29) and `2026-10-06-v1-7-validation.md` (clips 9 to 13). Spike: `docs/superpowers/research/2026-10-06-v1-7/strokes.md` sections 2 and 3 (over-density, under-firing).

## 2. Pattern vote and stroke direction

- `music/vote.py`: `choose_pattern` (majority versus medoid, `HYBRID_DELTA` 0.04, `MEDOID_MIN_STROKES` 2), `best_pair` and `period_margin` (`PERIOD2_MARGIN` 0.10, `PERIOD2_MIN_STRIKES` 2), `unit_and_phase`, `align_to_first_bar`.
- `music/members.py`: member figures inside merged sections, `aligned_agreement`.
- Chance test: `structure_test` in `stages/strums.py` or its helper (shuffle within bars, 1000 copies, alpha 0.05; density test when the vote is full).
- `music/onsets.py` `direction_for_slot` (parity rule).
- Ear truth: 1.6 validation clips 12 to 29; 1.7 clips 9 to 14. Spike: `docs/superpowers/research/2026-10-05-v1-6/pattern-vote.md`.

## 3. Stroke length (cut versus ringing)

- `music/ring.py`: `stroke_decay_db` (RMS frames 10 ms, hop 5 ms, decay in the first slot after the peak), `section_rings` (`RING_SECTION_DB` 5, `RING_MIN_GAP_SLOTS` 1.5). Data still written; renderer ignores it since 1.7.
- Ear truth: 1.6 validation clips 1 to 10 and 30 to 33. Spike: `docs/superpowers/research/2026-10-06-v1-7/strokes.md` section 1 (cut and rings overlap on every decay statistic).

## 4. Riff versus strum, riff tab

- `music/riff.py`: `onset_chroma`, `riff_features` (chroma entropy, single-pitch-class share), `is_riff` (`RIFF_ENTROPY_MAX` 0.82, `RIFF_SINGLE_PC_MIN` 0.45), `root_share`, `named_share`.
- `music/pitch.py`: `track_pitch` (librosa pyin, 82 to 1318 Hz, frame 2048, hop 256), `name_notes`, `pitch_change_share` (`PITCH_CHANGE_MIN` 0.26).
- `music/riff_line.py` and `stages/riff.py`: reduce the flagged section to a one- or two-bar figure, gate it (agreement 0.70, support 0.75, named 0.6) and map to ukulele strings and frets (`music/tab.py`).
- `stages/strums.py`: `_riff_test`, `_riff_features_member`, `_riff_inside`.
- Ear truth: 1.6 validation "Riff test, gate and tab" and clips 34 to 37; 1.7 validation "Riff flags that changed", "Ground truth from published sources", clips 8, 15, 16. Spikes: `research/2026-10-05-v1-6/riff-pitch.md`, `research/2026-10-06-v1-7/riff-test.md`, `acdc-ear-truth.md`.

## 5. Two parts in one stem

- No code separates parts. `models/separator.py` runs htdemucs_6s (six stems: vocals, drums, bass, guitar, piano, other); `cli.py` also offers a `roformer-sw` separator option. `music/onsets.py` `choose_source` picks guitar or other by RMS ratio (`SOURCE_MIN_RATIO` 0.05).
- Ear truth: Fame (two guitars), AC/DC (riff over chords, `acdc-ear-truth.md`), Day Tripper verse, Cream "Badge" (bass bleed, 1.7 clips 15 and 16). Spike: `research/2026-10-06-v1-7/two-part-split.md` (seventeen features; a MIDI 60 note split fitted to one song).

## 6. Rests and instrument activity

- `music/rests.py`: `bar_energy_ratio`, `bar_low_share` (`REST_RATIO_MIN` 0.05, `REST_LOW_SHARE_MIN` 0.005, `REST_LOW_HZ` 330), `bar_holds`.
- `music/onsets.py`: `section_has_instrument` (`SECTION_MIN_RATIO` 0.10, section-level cut).
- Ear truth: 1.7 validation "Resting bars", clips 1 to 7; A4 and A5 after validation. Spike: `research/2026-10-06-v1-7/rests.md`.

## 7. Key and metadata

- `music/key.py`: Krumhansl profiles, `decide_tonic` (three votes: profile fit, chord-set share with `FINAL_CHORD_BONUS` 0.10 and `SECTION_END_WEIGHT` 0.15, the stems' estimate), `KEY_HEDGE_MARGIN` 0.05, `mode_at`, `hedge_text`.
- `titles.py`: `clean_title`, `clean_artist_from` (strips an "Artist - " prefix only when it shares letters with the uploader), `UPLOAD_TAG_WORDS`.
- `stages/ingest.py`: yt-dlp download and metadata.
- Ear truth: the blind songs' title and artist lines (The Cars by "RHINO", Day Tripper by "Natan Santos"); Badge printed D major against published G major or E minor.
