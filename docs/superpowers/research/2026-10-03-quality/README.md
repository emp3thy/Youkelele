# Youkelele quality improvement research: synthesis

Date: 2026-10-03. This document merges five research strands (chord recognition and key; beat tracking and the bar grid; song structure; strumming extraction; ukulele arrangement) after each was checked against the real code in `src/youkelele/` and the four version 1.1 runs under `runs/` (Chelsea Dagger `sexhetcxqy4`, Summer of '69 `9f06qzcvuhg`, Pour Some Sugar On Me `0uib9y4ofps`, Wet Leg "mangetout" `lbc6ccztp5e`). Every number below was measured by an apply agent on those artefacts or on the spike audio; none is new here. Line numbers refer to the main checkout unless marked "worktree" (`.claude/worktrees/v1-2`), where `stages/harmony.py`, `stages/grid.py` and `music/fill.py` differ.

Version 1.2 is being built now (four-bar section minimum, mean tempo, title cleaning, chroma fill of no-chord bars, passing chords, phrase alignment, repeated row blocks, narrow pickup cell). Nothing below re-proposes those; several items amend or build on them.

The strand reports with full measurement tables are in `strands/`: `chords-applied.md`, `beats-applied.md`, `structure-applied.md`, `strums-applied.md`, `arrange-applied.md`, and the matching `*-research.md`.

---

## 1. State of the program

The chain is strong where the models are strong and weak where it reads their output without context. Beat tracking is octave-correct on all four songs and the vendored chord model is within about two points of the best published major/minor system. The failures are in the layers around them: an octave rule that is a genre prior, a key estimate that is a coin toss, section labels that ignore the vocal stem, a strum vote that erases strikes played in half the bars, and sheet decisions (capo alternative, hedges, spelling) that the code computes but never prints.

| Stage | Where it is weak, from the runs | Measured evidence |
|---|---|---|
| Grid: tempo octave | The octave rule (`bpm > 140 and 60 <= bpm/2 <= 95`, then backbeat ratio) is right on 7 of 7 songs but is a band prior: a doubled ballad detected at 130 or 200 bpm is never halved. The header carries no alternative tempo. | Backbeat ratio at the detected grid: 1.94 to 2.14 on the four rock songs, 0.56 and 0.14 on the two doubled spike songs (I'm Yours, Over the Rainbow). Over the Rainbow's drum stem reads "silent" today. |
| Grid: downbeats and pickup | Downbeats are strong (modal phase share 0.87 to 1.00). The defect is extra mid-bar downbeats (PSSOM: 22 two-beat spacings) and a one-beat `N` pickup bar on Summer of '69. | Raw downbeat spacings PSSOM `{1: 6, 2: 22, 3: 2, 4: 88}`; S69 bar 0 is 0.02 to 0.44 s, chords start at 0.88 s. |
| Grid: sections | Boundaries sit at the field's one-bar floor; labels are wrong wherever the vocal stem could have said otherwise. Every section carries `confidence: 0.3` and `labels_low_confidence` fires on 4 of 4. | F0.58 at one bar: S69 0.609 (8 of 13 boundaries), PSSOM 0.484 (4 of 12). Chelsea `chorus 9-38` while vocals are silent for bars 0 to 19; S69's F Bb C bridge prints `verse 2`; PSSOM's solo prints `verse 67-84`; Wet Leg's second half (35 bars) prints `bridge`. |
| Harmony: chords | Labels are only `maj`, `min`, `N` on all four songs (even with the 382-class dictionary). Changes land off the bar on Chelsea and PSSOM; sub-beat fragments exist only in PSSOM. Snap confidence carries no information. | Changes starting on beat 2: Chelsea 10 of 67, PSSOM 23 of 74 plus 5 sub-beat events. Median snap confidence 0.97 to 0.99. |
| Harmony: no-chord | A whole intro and most of a solo print `N.C.`; the v1.2 fill, restricted to the song's chord set, picks `A` where the record plays `D`. | PSSOM `N` share 0.271, 24 of 103 bars all-`N`. Bar 74 fills `A` at 0.334 while the unrestricted template best is `D:maj` at 0.56 and a stems-pass recogniser labels 195.1 to 200.6 s `D:maj`. |
| Harmony: key | Krumhansl on the mix is a coin toss on two songs and wrong on PSSOM's mode. The sheet prints the key with no hedge. | Confidences 0.006 (Chelsea), 0.056, 0.010 (PSSOM, printed C# major, truth C# minor), 0.136. |
| Harmony: power chords | The model has no `5` class; a no-third riff collapses onto `maj` and drags the key mode. | PSSOM `C#:maj` is 41.1 percent of chord time, printed `A` at capo 4 where the published chart has C#m. `to_triad("C#:5")` returns `C#:maj`; chords-db has no `5` shapes. |
| Strums | The strict `> n/2` vote erases strikes played in 41 to 54 percent of bars; the song-level stem choice misses the part Demucs routed to `other`; the printed "repeatable" number reads as failure. | Boxes at 75 percent or more rests: 4, 4, 4, 1. S69 sec 8 chorus: 1.8 strikes per bar on `guitar`, 7.0 on `other`. PSSOM: all 7 sections uncertain. `bar_repeat` 0.29 to 0.53 on S69's confident sections. |
| Arrange and render | Right on the validation set, but computes things it never shows and has latent bugs. | 74 `no_capo_alternative` entries written for PSSOM, 0 rendered. Capo margins 0.11 (Chelsea) to 0.50. `transpose_label` and `_shape_key` are sharps-only; all four transpositions happen to land on naturals. |
| Evaluation | `evaluate` needs hand truth that exists for none of the four songs; every number in the specs came from one-off scratchpad scripts. | No `chords.lab`, `beats.txt`, section or strum truth under `tests/fixtures/ground_truth/` for any run slug. |
| Cost | Separation is 76 to 84 percent of a 117 to 169 s run; harmony 9.5 to 12.6 s; beats 2.6 to 5.2 s; strums 1.7 to 2.8 s. | Any extra model pass must fit inside that budget. |

---

## 2. Ranked list

Ranked by impact per effort, then confidence. Effort is small, medium or large (no time estimates). "Strands" names the apply reports merged into the item.

| Rank | Improvement | Group | Strands | Effort | Impact | Confidence |
|---:|---|---|---|---|---|---:|
| 1 | Strike threshold > 1/3 with a density floor; `explained` as the uncertainty flag and the printed number | easy | strums 2.1, 2.4 | small | high | 85 |
| 2 | Decode chords with the chain's beats and downbeats | easy | chords 3.1 | small | medium-high | 88 |
| 3 | Key from the chord stream, mode from harmonic-stem chroma, one shared harmonic chroma, hedged header | medium | chords 3.2, arrange 1 (steps 1 to 5), 3, 4 | medium | high | 85 |
| 4 | Measurement harness: truth-free diagnostics, section and strum truth, persisted raw detector output | easy | chords 3.6, structure 3.4, strums 2.5, beats 2 | small-medium | medium (enabler) | 90 |
| 5 | Vocal-run boundaries and vocal-aware section labels | medium | structure 3.1 | medium | high | 85 |
| 6 | Render the no-capo alternative and record the capo margin | easy | arrange 2 | small | medium | 90 |
| 7 | Chart-conventional section names: bridge by chord novelty, no once-only bridge, numbering by occurrence | easy | structure 3.2, 3.3 | small | medium | 85 |
| 8 | Two-sided backbeat octave test replacing the band gate, with cues persisted and a tempo alternative | easy | beats 1, 3 | small | high (latent) | 75 |
| 9 | Per-section strum source between `guitar` and `other`, with the no-instrument rescue | medium | strums 2.2 | medium | high | 65 |
| 10 | Power chords: relabel the tonic major to the key's quality | medium | chords 3.4, arrange 1 (steps 6, 7) | medium | medium | 65 to 85 |
| 11 | One strum pattern per section label, per-section box only when it disagrees | easy | strums 2.3 | small | medium | 75 |
| 12 | Second recogniser pass on guitar+other for all-`N` bars | medium | chords 3.5 | medium | medium | 70 |
| 13 | Fill refinement: out-of-set chord by run agreement, `riff` instead of `N.C.` | easy | chords 3.3 | small | medium | 75 |
| 14 | Per-bar stem levels computed once in the grid stage and stored in `grid.json` | medium | structure 3.1, 3.5; chords 3.3; strums 2.2; worktree `fill.py` | small-medium | medium (enabler) | 85 |
| 15 | Pickup hygiene: drop a leading `N` partial bar, ignore opening downbeats in the phase vote | easy | beats 4 | small | low-medium | 65 |
| 16 | Spell roots by key | easy | arrange 5 | small | low-medium | 75 |
| 17 | Sheet hygiene: bold capo line, legend order, shared fret formatter, crowded cells | easy | arrange 6 | small | low-medium | 80 |
| 18 | A "not music" class for trailing non-song bars | easy | structure 3.5 | small | low-medium | 70 |
| 19 | Absorb one-beat fragments off the strong beats; position-dependent re-snap (after rank 2) | easy | arrange 7, beats 8 | small | low | 50 to 65 |
| 20 | `nearest_named` pattern hint from the UkuTabs and Roadie list | easy | strums 2.6 | small | low | 80 |
| 21 | Grid phase offset before quantising strums | easy | strums 2.7 | small | low | 70 |
| 22 | Tempo diagnostics: regression residual, section tempo range, "about" in the header | easy | beats 7 | small | low | 60 |
| 23 | Meter suggestion from downbeat spacing (`--meter auto` logs, does not switch) | easy | beats 6 | small | low-medium (latent) | 50 |
| 24 | Section confidence from cue agreement instead of the 1.5 dB flag | easy | structure 3.6 | small | low | 60 |
| 25 | Metrical-level regularisation before the global octave decision | medium | beats 5 | small-medium | medium (latent) | 55 |
| 26 | Keep every k level in `grid.json` for hand editing | medium | structure 3.7 | medium | medium (hand edit) | 65 |
| 27 | `medium` tier and slash-chord provenance | easy | arrange 8, 9 | small | low (nothing to act on yet) | 70 to 80 |
| 28 | Ordinal shape difficulty instead of a weighted sum | medium | arrange 10 | medium | low-medium | 60 |
| 29 | Multi-cue boundary candidates with a duration prior | larger | structure 3.8 | large | medium-high | 55 |
| 30 | Trained CRNN strum detector on synthetic stems | larger | strums 2.10 | large | high | 55 |
| 31 | Chord-level decoding over the beat grid with a duration prior | larger | chords 4.2 | large | low-medium | 55 |
| 32 | Beat This! checkpoint ensemble on logits | larger | beats 9 | medium | low-medium | 35 |
| 33 | Accents from the detrended envelope | larger (needs truth) | strums 2.8 | small | low | 45 |
| 34 | Swing grid (12 slots per bar) | larger | strums 2.9 | large | low today | 60 |
| 35 | Local key and the last-chorus lift | larger (deferred) | arrange 11 | large | low on this set | not assessable |

Deferred with no rank: Mauch-style voting across repeated sections (chords 4.1, 45), ChordMini as a second opinion (chords 4.3, 40), extra key profiles as a mode vote (chords 4.4, 60), pre-chorus rule (structure 3.9, 40), section fusion by lower-level vote (structure 3.10, 40).

---

## 3. Easy wins

### 3.1 Strike threshold > 1/3 with a density floor; `explained` as the flag and the printed number (rank 1)

Merged from strums 2.1 and 2.4.

**Touches.** `src/youkelele/music/as_played.py:40-53` (`majority_vector`), `:63-71` (`section_summary`), `:17` (`UNCERTAIN_BELOW`); `src/youkelele/stages/strums.py:81-87`; `src/youkelele/schemas.py:135-142` (`SectionPattern`), `:220-227` (`ScoreSection`); `src/youkelele/music/score_builder.py:144-149`; `render/templates/sheet.html.j2:83`; `render/html.py:60`; tests `tests/test_as_played.py:39-57` (asserts the old rule), `tests/test_html.py`.

**Evidence.** Slots struck in 41 to 54 percent of bars (Chelsea beats 1 and 3) are erased by the strict `> n/2` test. Measured with a `> 1/3` vote plus a floor of `round(0.6 x median strikes per bar)` filled from the highest-rate slots:

| Section | today | explained | > 1/3 + floor | explained |
|---|---|---:|---|---:|
| Chelsea sec 1 chorus | `--S---S-` | 0.54 | `S-S-S-S-` | 0.85 |
| Chelsea sec 6 bridge | `--S---S-` | 0.48 | `--SSS-SS` | 0.87 |
| Chelsea sec 7 chorus | `--S-S---` | 0.52 | `S-S-S-S-` | 0.88 |
| S69 sec 4 chorus | `S-------` | 0.31 | `S-S--SS-` | 0.77 |
| S69 sec 6 verse 2 | `S--S----` | 0.41 | `S-SSS-SS` | 0.87 |
| S69 sec 8 chorus | `S-------` | 0.45 | `S-------` | 0.45 (needs rank 9) |
| Wet Leg sec 22 | `SSSS--S-` | 0.73 | `SSSSSSSS` | 1.00 |

`explained` (share of detected strikes that fall on a pattern strike) is the one number that separates the boxes the validation called wrong (0.31 to 0.57) from the usable ones (0.69 to 1.00). Mean Jaccard, today's `confidence`, does not (0.45 to 0.53 against 0.46 to 0.83). `bar_repeat`, printed as "43% repeatable", is 0.29 to 0.53 on S69's confident sections and reads as failure for a pattern that explains 87 percent of what was heard.

**Design.** `majority_vector(bars, threshold=STRIKE_SHARE)` with `STRIKE_SHARE = 1/3` (strictly greater), then `_fill_to_floor(out, rates, floor)` with `DENSITY_FLOOR = 0.6`; the mute decision per slot stays `x if mutes > strikes / 2`. New `explained_onsets(bars, vector) -> float`; `SectionPattern.explained: float = 0.0` and `ScoreSection.explained` (defaults so old `strums.json` loads). `uncertain = confidence < UNCERTAIN_BELOW or explained < EXPLAINED_BELOW or not long_enough`, `EXPLAINED_BELOW = 0.6`, `UNCERTAIN_BELOW` stays 0.45. Template: "Strum heard in this section, covers {{ explained }} of detected strokes; up and down follow the beat", keeping "(uncertain)" and "same as {{ label }}". Keep `bar_repeat` in `score.json` for diagnostics.

**Measure.** Boxes at 75 percent or more rests go from 4, 4, 4, 1 to expected 0, 1, 2, 0; sections flagged by `explained`: Chelsea sec 0; S69 sec 8, 9, 10; all PSSOM; no Wet Leg section at or above 4 bars.

**Effort** small. **Impact** high. **Confidence** 85 (PSSOM stays uncertain; this item does not give it a box).

### 3.2 Decode chords with the chain's beats and downbeats (rank 2)

From chords 3.1.

**Touches.** `src/youkelele/models/chords.py:30-54` (`recognise_chords`); `src/youkelele/stages/harmony.py:41` (worktree `:66`); a new driver `src/youkelele/models/chord_driver.py`; `tests/test_stage_harmony.py:94-119`. No patch to the vendored model: `~/.youkelele/models/chord_cnn_lstm/extractors/xhmm_ismir.py:186` already accepts `use_beats` and `use_downbeats`; `io_new/beatlab_io.py:16` reads a three-column tab file (time, index, position in bar). Today `chord_recognition.py:27` passes `False`.

**Evidence.** Same posteriors decoded with beats and downbeats at the default penalties 30 / (15, 45, 100): S69 changes on bar starts 66/75 to 75/75; PSSOM events 84 to 75, changes on a beat 51/83 to 73/74, `N` 0.277 to 0.264; Chelsea on-bar changes 54/68 to 58/68. Chord sets unchanged. The removed PSSOM events are the sub-beat fragments (0.49 to 0.88 s slivers at 164.1, 164.6, 243.2, 243.7 s); the 1.42 s half-bar `E` / `A` chorus changes survive because they are on beats, as the published chart writes them. Lower penalties add fragments and inversions; keep the defaults.

**Design.** `chord_driver.py` builds the `DataEntry` as `chord_recognition.py:15-26` does, calls `entry.append_data(beats, BeatLabIO, "beat")` and `hmm.decode_to_chordlab(entry, probs, False, use_beats=True, use_downbeats=True)` (the scratchpad `beat_decode_experiment.py:76-105` is a working template). `recognise_chords(wav, work_dir, log, beats: Sequence[tuple[float, int]] | None = None)` writes `work_dir/beats.lab` from `grid.bars` (`for pos, bi in enumerate(bar.beats): (grid.beats[bi], pos + 1)`); a pickup bar gives position 1 alone, which `__get_beat_arr` tolerates. Use the gap-filled `grid.beats` list, since `decode` forbids changes between beat frames. `ctx.note("decoding", "beats+downbeats")`.

**Measure.** Re-run the four songs `--from harmony`: S69 75/75 on bar starts; PSSOM about 75 events, at most one under a beat; Chelsea 58 or more on-bar; chord sets and `N` outside PSSOM unchanged.

**Effort** small. **Impact** medium-high. **Confidence** 88 (Wet Leg not yet decoded this way).

**Note.** The chords report motivates today's per-beat vote in `music/snap.py:24` by a model lag of 0.1 to 0.4 s (spike B). The beats strand re-measured this on the four real songs and found boundaries are early, not late (median signed offset -44, -27, -39, -31 ms; none beyond half a beat); the lag came from the synthetic sine clip. This does not change the recommendation, but any fixed lag shift is refuted (see section 6).

### 3.3 Measurement harness (rank 4)

Merged from chords 3.6, structure 3.4, strums 2.5 and beats 2. Each strand put this first in its suggested order because the thresholds in every other item were fitted on four songs and cannot be re-fitted without it.

**Touches.** `src/youkelele/evaluate.py:23-29` (`Report`), `:51-68` (`_read_chords`, sibling parser for sections and strums), `:101-139` (`evaluate_run`, `format_report`); `src/youkelele/commands.py:126-137` (`evaluate_command`); `src/youkelele/stages/grid.py:43` (`produces`), `:48-115` (`GridStage.run`); `src/youkelele/stages/harmony.py:34-50` (copy `work_dir/out.lab` to `harmony/spans.lab` before `shutil.rmtree`); worktree `stages/harmony.py:76-82` (log and notes); `tests/fixtures/ground_truth/README.md`; `cli.py:62-66` needs no change.

**Evidence.** The owner's hand boundary lists exist (`spike_grid3/ref_s69.json`, 13 boundaries; `ref_pssom.json`, 12, shifted +25.2 s for the video upload) but are not under `tests/`. Without a harness the chroma-novelty snap would have shipped on its S69 gain (0.609 to 0.695) and dropped PSSOM from 0.484 to 0.121. Every strums decision was tuned against published beginner patterns the records do not play (0 of 14 sections in the round 2 spike). `grid.json` keeps only gap-filled beats and bar-derived downbeats, so the modal share and spacing histogram are lost and every beats measurement required re-running Beat This! (2.6 to 5.2 s per song) and the chord model (7.5 to 8.8 s).

**Design.**
1. Truth-free fields on `Report`, filled even with no `--truth`: `n_share`, `all_n_bars`, `changes_on_bar_share`, `sub_beat_events`, `key_confidence`, `key_mix`, `filled_by_source`, and the strum fields `strikes_per_bar`, `explained`, `rest_share` per section.
2. `evaluate --compare <other run dir>`: `mir_eval.chord.overseg`, `underseg`, `seg`, `majmin` between two `chords.json` files, as a regression guard without truth.
3. Section truth: optional `sections.txt` (`start<TAB>end<TAB>label`) scored with `mir_eval.segment.detection(ref, est, window=median_bar_seconds + 0.05, beta=0.58, trim=True)` and `mir_eval.segment.pairwise`; commit the owner's two hand lists as `tests/fixtures/ground_truth/9f06qzcvuhg/sections.txt` and `0uib9y4ofps/sections.txt` (not Hooktheory data, whose terms forbid redistribution). A `@pytest.mark.slow` test asserts the one-bar precision floor per song when `runs/` is present.
4. Strum truth: `strums.txt` with one onset time per line, optional `x` for a mute, first line `# window 30.0 60.0`; `strum_f`, `strum_precision`, `strum_recall` at 50 ms via `mir_eval.onset.f_measure` inside the window; a `--debug` flag on the strums stage writing `strums/onsets.txt` as an Audacity label track so the truth can be made by ear from the detector's own output. Target 30 s of each of the four songs plus the two blind songs.
5. Persist raw detector output: `grid/beats_raw.json` (detected beats and downbeats, `fill_gaps` insertions, `normalise_octave` drops), `harmony/spans.lab`, and on `Grid` the fields `octave_cues`, `downbeat_spacing`, `downbeat_modal_share`.
6. The harmony stage logs `N` share, all-`N` bars, on-bar share and the key with its margin, and notes `decoding`, `key_method`, `filled_stems`, `filled_template`.

**Measure.** Floors to record now: S69 section P 0.636, R 0.538, F0.58 0.609; PSSOM P 0.571, R 0.333, F0.58 0.484.

**Effort** small to medium (the code is small; annotating strum truth is listening work). **Impact** medium, as the enabler for every other item. **Confidence** 90.

### 3.4 Render the no-capo alternative and record the capo margin (rank 6)

From arrange 2.

**Touches.** `music/score_builder.py:91-168` (`Score.alternative_diagrams`, built from `arrangement.no_capo_alternative` with the same dedupe as `diagram_index` at line 107); `schemas.py:231-243`; `render/html.py:42-78`; `templates/sheet.html.j2:69-72`; `stages/arrange.py:65` (`ctx.note("capo_margin", ...)`, `ctx.note("capo_scores", ...)`); `music/arrange.py:47-49` (`choose_capo` returns scores or a `CapoChoice`); `tests/test_html.py` beside `test_html_capo_header_notes` (line 125).

**Evidence.** PSSOM `arrangement.json` carries 74 `no_capo_alternative` entries with six distinct shapes (C# 1114 barre, F# 3124, B 4322 barre, E 1402, A 2100, C#m 1444); `grep no_capo render/` finds nothing. Capo margins: Chelsea 0.11, S69 0.33, PSSOM 0.47, Wet Leg 0.50; Chelsea's capo-2 chart would print a barre A# where capo 0 prints barre Bm and B.

**Design.** One line under the legend, only when `capo > 0`: `Without a capo: C# 1114 (barre), F# 3124, B 4322 (barre), E 1402, A 2100, C#m 1444` in G C E A order, using the fret formatter v1.2 Task 6 adds for the `Passing:` line. Mark barre shapes in the text. Write the margin into `manifest.json`.

**Effort** small. **Impact** medium. **Confidence** 90.

### 3.5 Chart-conventional section names (rank 7)

Merged from structure 3.2 and 3.3.

**Touches.** `music/sections.py:235-242` (once-only branch), `:244` (`f"verse {others.index(c) + 2}"`); `music/score_builder.py:91-150` (`build_score`) or a new `music/relabel.py` with `refine_labels(grid, chords) -> list[str]`, feeding `ScoreSection.label` (`schemas.py:220-227`); `render/html.py:47-66` (display name by occurrence), `templates/sheet.html.j2:79`; `stages/strums.py:91-106` unaffected (inheritance uses indices); `tests/test_sections.py:157-173`.

**Evidence.** Bridge by chord novelty: per section, the fraction of chord-bars whose triad occurs in no other section is 0.73 for S69 bars 58-69 (F, Bb, C) and 0.00 to 0.05 for all other 49 sections on the four songs; the threshold 0.5 sits in an empty band. A chroma-only proxy in the grid stage also finds it (0.55) but fires on S69's fade (1.00), Wet Leg's tail (5.00) and Wet Leg bars 58-65 (0.43, the C# passing chord), so the chord-based rule belongs at the score stage, which is where v1.2 already moves section starts (phrase alignment). Once-only clusters: Wet Leg bars 65-100 (35 bars, 31 percent of the song) print `bridge` with the verse chord set (novelty 0.00); S69's intro and bridge both print `verse 2`; Wet Leg opens with `verse 3`. Charts number by occurrence, never by cluster id.

**Design.** `novelty(section) >= BRIDGE_NOVEL_CHORDS = 0.5`, not first or last, and (after rank 5) vocal share at least 0.5, gives `bridge`; at most one per song. A middle once-only segment is `verse`, not `bridge`; remove `n_bridge` and `bridge 2`. The cluster id leaves the label string; the renderer prints `Verse 1`, `Verse 2`, `Chorus`, `Instrumental 1` by occurrence; `score.json` and `grid.json` keep the bare label. Hand edits to `grid.json` labels still win (refine only labels in `{verse, chorus, bridge}`).

**Measure.** S69 bars 58-69 print `bridge`; no other section changes on the four songs; Wet Leg's 35-bar `bridge` becomes `Verse`.

**Effort** small. **Impact** medium. **Confidence** 85 to 90.

**Dependency flag.** Rank 11 (pool strum patterns by label) runs in the strums stage, before the score stage, and today relies on `verse 2` meaning a different cluster. See section 6.

### 3.6 Two-sided backbeat octave test, persisted cues, tempo alternative (rank 8)

Merged from beats 1 and 3.

**Touches.** `music/tempo.py:53-71` (`decide_octave`); `stages/grid.py:69-79`; `music/backbeat.py:28-71` unchanged; `schemas.py:58-72` (`Grid.octave_cues`, `tempo_alternative`, `tempo_ambiguous`); `schemas.Score:230-242` (`bpm_alternative`); `music/score_builder.py:160-163`; `render/html.py:74`, `sheet.html.j2:58`; `stages/grid.py:91-94` (log); `tests/test_tempo.py:37-47, 143-170`; `tests/test_stage_grid.py` with `write_drum_stem` (`tests/audio_fixtures.py:90`).

**Evidence.** Seven songs with drum stems:

| Song | detected bpm | truth | ratio at detected grid | ratio at halved grid (max over phases) |
|---|---:|---|---:|---:|
| Chelsea | 157.9 | keep | 2.06 | 1.03 |
| S69 | 136.4 | keep | 2.14 | 1.22 |
| PSSOM | 85.7 | keep | 2.14 | 1.57 |
| Wet Leg | 130.4 | keep | 1.94 | 1.03 |
| Riptide (spike) | 103.4 | keep | 1.12 | 1.15 |
| I'm Yours (spike) | 150.0 | halve | 0.56 | 2.39 |
| Over the Rainbow (spike) | 166.7 | halve | 0.14 (stem below `DRUMS_SILENT_RMS`) | 2.71 |

The doubled hypothesis scores 2 to 15 on every song, so any "pick the maximum over half, detected, double" rule picks double; onset autocorrelation is stronger at the half lag on three of four correct songs and cannot flag ambiguity. The lessons record the first Chelsea run halving 157.9 to 76.9 before the backbeat test existed.

**Design.** Constants `HALF_BAND = (50, 110)`, `DETECTED_MAX_RATIO = 1.0`, `HALF_MIN_RATIO = 1.5`, `AMBIGUOUS_MARGIN = 0.25`. `decide_octave(cues: OctaveCues, mode)` halves only when `half_bpm` is in the band, the detected-grid ratio is below 1.0 (or missing) and the halved-grid ratio is at least 1.5 (or missing); with no drum evidence at all it falls back to the old band prior. Compute `ratio_half` by running `normalise_octave` speculatively and taking the max of `backbeat_ratio` over the four phases; compute the cues even when `drums_silent` (Over the Rainbow's ratio is informative at RMS below 0.003). Store `octave_cues` in `grid.json`. `tempo_alternative = bpm / 2` when the decision was "none" and the halved tempo is in 60 to 110, or `bpm * 2` after a halve; the header prints "158 bpm (or 79 counted in half time)" only when `tempo_ambiguous`; the CLI always logs the alternative with the `--beat-octave half|none` hint. Do not score "double".

**Measure.** The seven-song table must read keep x5, halve x2 (it does: Riptide fails the band at 51.7 and its detected ratio 1.12 is above 1.0; PSSOM's half ratio 1.57 passes but its detected 2.14 blocks). New unit case: a 130 bpm detector with a 65 bpm backbeat stem must now halve. PSSOM's 1.57 against 1.5 is inside the 0.25 margin, so PSSOM would print the alternative; if unwanted, define the margin on the detected ratio only (PSSOM 2.14) and say so in the constant's comment.

**Effort** small. **Impact** high on unseen songs (right on 7 of 7 today). **Confidence** 75 (two doubled examples, both with a clear snare at the halved grid).

### 3.7 One strum pattern per section label (rank 11)

From strums 2.3.

**Touches.** `stages/strums.py:70-89` (per-section loop, needs `sec.label` from `grid.sections`), `:91-106` (inheritance, generalised); `schemas.py:135-142` (`SectionPattern.shared_with: list[int]` or `pooled: bool`); `render/html.py:48-65`.

**Evidence.** Bars pooled across same-label sections of at least 4 bars, `> 1/3` plus floor: S69 chorus (sec 2, 4, 8; 36 bars) `S-SS--S-`, explained 0.77, against three different per-section vectors today; S69 verse (60 bars) `SSSSSSS-`, 0.93; Chelsea chorus (82 bars) `S-S-S-S-`, 0.83; Wet Leg verse (31 bars) `SSSSSSSS`, 1.00; PSSOM chorus `S---S---S---S--S`, 0.58 (still weak). The research's rate-vector correlation merge (0.8) was measured and rejected: it links Chelsea's chorus to its verse (0.95) and S69's muted verse to the open chorus (0.91), because correlation ignores density and the mute class.

**Design.** For each label with two or more sections at or above 4 bars, compute the pooled vector and its `explained`. A section takes the pooled vector when its own `explained` is below 0.6 or Jaccard(own, pooled) is at least 0.5; it keeps its own when it clearly differs (Jaccard below 0.5 and own `explained` at least 0.6), preserving S69's muted verse 1 (`xxxU-xxx`, 72 percent `x`) against the open later verses (0 to 14 percent `x`). The mute class must be handled in the pooled vote. Short sections take the pooled vector of their label before falling back to a neighbour.

**Measure.** Distinct patterns per label per song (S69 choruses today 3, expected 1).

**Effort** small. **Impact** medium. **Confidence** 75. Group by cluster id rather than the label string once rank 7 removes the id from the label (section 6).

### 3.8 Fill refinement: out-of-set chord by run agreement, `riff` instead of `N.C.` (rank 13)

From chords 3.3; amends the v1.2 fill, does not re-propose it.

**Touches.** Worktree `music/fill.py:107-118` (`_song_chords`), `:121-131` (`_best_match`), `:160-175` (fill loop); `render/grid.py:26-31` (`cell_for`); `tests/test_fill.py`.

**Evidence.** Restricting to the song's chord set picks the wrong chord where the record plays an out-of-set chord: PSSOM bar 74 fills `A` at 0.334 (margin 0.081) while the unrestricted best is `D:maj` at 0.56; bars 69 and 73 pick `D` at 0.37 and 0.39 unrestricted against in-set 0.23 and 0.19; bar 67 would be `A` 0.442 but is energy-gated. The stems recogniser independently labels 195.1 to 200.6 s and 205.8 to 210.5 s `D:maj`. The research's advice to raise `FILL_MIN_MATCH` to 0.5 and `FILL_MIN_MARGIN` to 0.15 is contradicted: Chelsea's barre `B` on bars 2 and 6 is already rejected by energy (ratios 0.106 and 0.013), and the doubtful fills that pass (PSSOM 44, 45 at 0.655 and 0.719; S69 118, 119 at 0.464, 0.476) pass any threshold up to 0.46, so a higher match would only remove true positives (bars 70 and 74 at 0.38 and 0.33). Keep 0.32 / 0.05 / 0.2.

**Design.** `_best_match` returns both the in-set best and the overall best over 24 templates. Accept an out-of-set winner only when it beats the in-set best by `FILL_OUT_OF_SET_MARGIN = 0.15` and the same label wins in at least one other candidate bar of the same `N` run (PSSOM 67, 69, 73, 74 all pick `D`; Wet Leg 109-112 pick in-set `C#` at 0.22 to 0.30 so no run agreement). Use this run-agreement gate instead of a diatonic gate, because `D` is not diatonic to C# minor (it is bVII of the E Mixolydian bridge). A bar that passes energy but fails the match (PSSOM 69, 73; Wet Leg 109-112) gets `ChordEvent.riff: bool = True` and `cell_for` prints "riff" rather than "N.C.". Chelsea bars 0-2 and 5-7 stay `N.C.`: their stems are drums only (guitar at most 0.004 RMS).

**Measure.** PSSOM bars 69, 73, 74 (67 if energy allows after rank 12) print `D` or `riff`, never `A`; the other songs' fills unchanged.

**Effort** small. **Impact** medium. **Confidence** 75 (one song, two independent methods; the gate is tuned on it). After rank 12 the stems pass settles most of these bars first.

### 3.9 Pickup hygiene (rank 15)

From beats 4.

**Touches.** `music/tempo.py:201-203, 217` (`build_bars`), `:93-99` (`modal_phase`) or `:159-177` (`_choose_phase`); `music/score_builder.py` around line 164 (`ScoreBar(..., pickup=...)`); `render/grid.py:34-52` (v1.2 replaces the pickup row with a narrow cell).

**Evidence.** S69 bar 0 is one beat at 0.02 to 0.44 s, labelled `N`; the chart has no pickup. Downbeats at 0.02 and 0.44 s are one beat apart. The energy test is ambiguous on the only example (mix RMS 0.144 against 10th percentile 0.183 says drop; drum stem 0.121 against 0.0066 says keep); the chord test says drop.

**Design.** (a) Exclude downbeat indices below 2 from the modal phase vote when more than 8 downbeats exist (no effect on the seven songs). (b) In `build_score`, when `grid.bars[0].pickup` and every event in bar 0 is `N`, omit bar 0 and shift `ScoreSection` starts by one (keep `grid.json` unchanged, since `Grid` validation requires `sections[0].start_bar == 0`). (c) Keep a pickup that has a chord. Log the drop.

**Effort** small. **Impact** low-medium. **Confidence** 65 (one example).

### 3.10 Spell roots by key (rank 16)

From arrange 5.

**Touches.** `music/arrange.py:14, 20-26` (`transpose_label(label, semitones, prefer_flats=False)`); `music/shapes.py:35-40, 100-106` (`display_name_for(label, db, prefer_flats)`); `render/html.py:11, 31-39` (`_shape_key` stops importing `_SHARPS`); `stages/arrange.py:41, 44, 53`; `tests/test_shapes.py:74` replaced by key-based cases.

**Evidence.** `transpose_label` and `_shape_key` are sharps-only; the model itself wrote `Bb:maj` (S69) and `C#:maj` (Wet Leg, PSSOM), and chords-db keys are flat-spelt. No current run prints a wrong spelling because every transposition landed on a natural (PSSOM capo 4: C# to A, F# to D, B to G, E to C, A to F). A song in Eb with capo 1 would print "D" shapes and a legend mixing `A#` with `Bb`.

**Design.** `FLAT_KEYS = {F, Bb, Eb, Ab, Db, Gb} major, {D, G, C, F, Bb} minor`; the shape key (sounding key moved down by the capo) decides. A chromatic chord between two known neighbours spells by direction (Wet Leg's C# between C and Dm stays C#). Apply in legend, cells, passing line and no-capo line via `display_name_for`. Depends on rank 3 for the key.

**Effort** small. **Impact** low on this set, certain on flat-key songs. **Confidence** 75.

### 3.11 Sheet hygiene (rank 17)

From arrange 6.

**Touches.** `templates/sheet.html.j2:52-67` (bold `Capo 4` line under the artist when `capo > 0`); `music/score_builder.py:105-112` (legend order: shape-key I, IV, V, vi first when diatonic, then first appearance); `render/grid.py:26-31` (crowded cells drop a one-beat fragment's name when rank 19 did not merge it); `schemas.ChordDiagram.frets: str` (e.g. `"0232"`) so legend, `Passing:` and `Without a capo:` share one formatter.

**Evidence.** PSSOM shows the capo only in the facts row; the v1.1 validation called the capo "the first thing a player needs to set". PSSOM has one three-name cell (bar 58, `C / F / G`). Legend order is first appearance (PSSOM A D G C F Am).

**Effort** small. **Impact** low-medium. **Confidence** 80.

### 3.12 A "not music" class for trailing non-song bars (rank 18)

From structure 3.5. **Conflicts with strums 2.2 on Wet Leg's outro; see section 6.**

**Touches.** `music/sections.py` (`label_sections` gains `stems_present: Sequence[bool]`); `stages/grid.py` (reads drums, bass, guitar stems; `GridStage.requires`); `music/score_builder.py:114-150` (skip or mark); `render/html.py:47-66` (one line: "4 bars of non-song audio omitted").

**Evidence.** Wet Leg bars 109-112: drums 0.00 to 0.01, bass 0.00, guitar 0.00 of the mix, `other` 0.82 to 0.83, against song bars at drums 0.3 to 0.6 and bass 0.3 to 0.9. Rule: a leading or trailing run where drums, bass and guitar are each under 8 percent of their own song median (ignoring stems whose median is negligible). Fires on Wet Leg 109-112 and PSSOM bar 0 only. It does not catch PSSOM's 25.2 s video pre-roll (bars 0 to 8): Demucs puts it into the guitar stem at 0.56 to 0.91 of the mix, so the only cue is the mix level (-28 to -37 dB against -22 to -24 dB after), which is the v1.2 "Video" title hint's territory.

**Effort** small. **Impact** low-medium. **Confidence** 70. Build on the per-bar stem table of rank 14.

### 3.13 One-beat fragments and position re-snap, after rank 2 (rank 19)

Merged from arrange 7 and beats 8. Both target small populations that rank 2 reduces further; re-measure after it lands.

**Touches.** `music/snap.py:24-56` (a pass after run merging, before `fill_silent_bars` in worktree `stages/harmony.py:69`); `schemas.ChordEvent` (`merged_from: int = 0`, `snapped_from: int | None`); `tests/test_snap.py`.

**Evidence.** One-beat non-`N` events: PSSOM 6, Wet Leg 1 (bar 63's C#, already a v1.2 passing chord), Chelsea 0, S69 0. PSSOM bar 58 (E one beat, A one beat, B two beats) is the only three-name cell; Hooktheory and Ultimate Guitar write that bar E A on beats 1 and 3. Chelsea's 13 two-beat events in bars 110-122 alternate C and D every half bar on beats 1 and 3: harmonic rhythm, not flicker; do not merge. Runs starting on beat 1 or 3 and lasting 3 or more beats: PSSOM `B:maj` at bars 28, 56, 86 (3.1 beats, confidence 0.84 to 0.89, a full bar on the chart), Wet Leg bar 18 `C:maj`, S69 bar 113 `D:maj`: about 5 of roughly 290 changes.

**Design.** (a) An event of exactly one beat starting on beat 2 or 4 is absorbed into the longer neighbour within the same bar; one-beat events on beats 1 or 3 are kept; nothing merges across a bar line; no seconds threshold (it would merge Chelsea's half-bar changes at 158 bpm). (b) A run starting on beat 1 or 3 lasting at least 3 beats moves back one beat when the previous run's share on the preceding even beat is under 0.75 (`_beat_label` returns the share, `snap.py:21`); never move `N` starts or runs shorter than 3 beats. No fixed lag shift (refuted: boundaries are early by 27 to 44 ms).

**Effort** small. **Impact** low. **Confidence** 65 for (a) (bar 58's A might be a real anticipation), 50 for (b) (untested share condition).

### 3.14 Small render and diagnostic items (ranks 20 to 24, 27)

| Rank | Item | Touches | Evidence | Design | Confidence |
|---:|---|---|---|---|---:|
| 20 | `nearest_named` hint | `music/as_played.py` (new), `schemas.py:135-142`, `render/html.py:48-65`, template line 83 | Hamming distance 0 for S69 verse 1 "eighths", S69 chorus 2 "D-DU-UD-", S69 sec 0 and Wet Leg sec 10 "island", Chelsea choruses "all downs" | Table of 18 UkuTabs plus 5 Roadie patterns as strike/rest strings (8 slots 4/4, 6 slots 3/4); print "close to the island strum" only at distance 0 or 1 and not uncertain; never alter `slots` | 80 |
| 21 | Grid phase offset | `music/onsets.py:79-88, 102-106, 118-140`; `stages/strums.py:65-68`; `Strums.grid_offset_ms` | Wet Leg onsets 16 ms late (median +0.068 slots); shifting raises grid fit 0.73 to 0.81; Chelsea -0.033 (0.55 to 0.58); per-section medians consistent within a song | `grid_offset(onsets, bars, slots)` = median signed deviation, clipped to a quarter slot, applied inside `quantise_bar` and `grid_fit`; Beat This! untouched | 70 |
| 22 | Tempo diagnostics and "about" | `music/tempo.py` (`tempo_fit` beside worktree `mean_bpm` line 53); worktree `stages/grid.py:83`; `Grid.tempo_jitter_ms`, `tempo_range`; `render/html.py:74` | Regression equals the mean within 0.02 bpm on all four (header already handled by v1.2); residual std 33 ms Chelsea (intro 156.3 vs body 154.5) against 11 to 16 ms elsewhere; Riptide spans 98.5 to 107 bpm per 32 beats | Per-section regression tempo (at least 8 beats); header "about N bpm" when `(max - min) / mean > 0.03`. Do not add `Bar.free_time` (no rubato example) | 60 |
| 23 | Meter suggestion | `stages/grid.py` after `downbeat_indices` (line 69); `options.py:16`; `cli.py:46`; `Grid.meter_shares`, `meter_suggested`; `Meter.parse` (`schemas.py:23-28`) maps "auto" to 4/4 | 4-beat spacing share 0.75 to 1.00 on seven real songs; synthetic 3/4 at 96 gives `{3: 25}` but 3/4 at 120 is tracked at 81 bpm with 2 "beats" per bar; two-beat spacings 13 to 19 percent on PSSOM and Over the Rainbow | `shares["3"] >= 0.6 and shares["4"] < 0.2` logs "run with --meter 3/4 if the song is a waltz"; `shares["2"] >= 0.5` under 100 bpm logs the dotted-crotchet warning; "2" never triggers a switch. Promote to automatic only after a real 3/4 and 6/8 song are in the set | 50 |
| 24 | Section confidence from cue agreement | `music/sections.py:24` (`LOW_MARGIN_DB`), `:222-226`; `stages/grid.py:95-96, 110`; `schemas.py:69-70`; README.md:50 | 1.5 dB flag fired on 4 of 4 (margins 1.43, 0.70, 0.93, 0.75 dB) while the chorus was right on 6 of 6 verifiable; nothing on the sheet reads `confidence` | `bridge` = novelty fraction; `intro`/`instrumental`/`outro` = 1 minus vocal share; `chorus` = 0.5 + 0.25 if loudest cluster is also the most vocal recurring cluster + 0.25 if margin exceeds the pooled within-cluster loudness IQR; `verse` = 0.5. Keep `chorus_margin_db` | 60 |
| 27 | `medium` tier; slash provenance | `options.py:13`; `schemas.Arrangement.tier:189`; `music/arrange.py:96-112` (`simplify_for_tier`), `:29-32` (`_best_cost`); `music/shapes.py:79-85` (`_split_label` returns bass); `tests/test_arrange.py:153-176` | 0 of 293 events carry a seventh, sus or inversion, even with the `full` dictionary; chords-db costs: G7 0212 1.70 = G 0232 1.70, A7 0100 0.40 < A 2100 1.30, D7 2223 3.60 > D 1.20 | `medium`: keep the seventh when `min shape_cost(seventh) <= min shape_cost(triad)`, with a reason string. Slash: record `"bass dropped (not a chord tone)"` via `mir_eval.chord.quality_to_bitmap`; show `C/B` in the full tier only when the bass is outside the triad | 70 to 80 |

---

## 4. Medium changes

### 4.1 Key from the chord stream, mode from harmonic-stem chroma, shared chroma, hedged header (rank 3)

Merged from chords 3.2, arrange 1 (steps 1 to 5), arrange 3 and arrange 4. Both strands independently arrived at the same architecture (tonic from the chords, mode from the summed harmonic stems at that tonic, never a 24-way profile search) and both get 4 of 4 songs right. They differ in the tonic rule; see the conflict note.

**Touches.** `music/key.py:17-35` (`estimate_key`, `chroma_mean_for`; new `estimate_key_from_chords(...)` or `key_from_chords(...)`); new `music/chroma.py` (`harmonic_chroma(stems) -> HarmonicChroma` with `.frames`, `.times`, `.bar_means(bars)`, `.energy(bars)`, `.mean(mask)`); worktree `stages/harmony.py:22-38` (`harmonic_mix` moves to the helper), `:53` (constructor `chroma` argument becomes injectable `harmonic_chroma`), `:69-77` (call after `fill_silent_bars`; `bar_chroma` already exists at `:70-75`); worktree `music/fill.py:54-78` (`bar_chroma`, `bar_energy` become thin wrappers); `schemas.py:99-103` (`Key` gains `method`, `runner_up`, `margin`, `mix: Key | None`); `music/score_builder.py:159, 181`; `render/html.py:31-39, 72-73`; `templates/sheet.html.j2:56, 64`; `tests/test_key.py` (two chroma tests today), `tests/test_stage_harmony.py` fakes.

**Evidence.**
- Krumhansl on the mix: Chelsea D 0.768 vs G 0.762; PSSOM C# major 0.550 vs C# minor 0.546. On the summed bass, guitar, piano and other stems PSSOM becomes C# minor 0.716 (right) but S69 flips to A major 0.883 over D 0.807 (wrong), the dominant-key tendency music21 documents for Krumhansl-Schmuckler. So the 24-way search is unreliable on any source and harmonic-stem Krumhansl is a tie-breaker only.
- Mode at a fixed tonic on the harmonic stems is right on 4 of 4 with every profile: PSSOM minor at C# by 0.379 (Krumhansl), 0.336 (Kostka-Payne), 0.342 (Albrecht-Shanahan); S69 major at D by 0.299 / 0.148 / 0.105; Chelsea major at G by 0.313 / 0.201 / 0.153; Wet Leg major at C by 0.220 / 0.175 / 0.118. Profile disagreement carries no signal (the 24-way winners disagree on all four songs).
- Tonic cues: root time share PSSOM C# 0.415 (B 0.257), S69 D 0.402 vs A 0.396, Chelsea G 0.382 vs D 0.317, Wet Leg C 0.527 (F 0.333); final chord D, G, C# (passing), B (PSSOM fades on V); section-end chords S69 D 6 of 11 vs A 4, Chelsea G 4 of 8. Section-start chords are not a cue (S69 choruses start on Bm).
- Diatonic-pair share with half credit for a diatonic root of the wrong quality: Chelsea G/Em 0.974 over D/Bm 0.929 (margin 0.045); S69 D/Bm 0.930 over A/F#m 0.877 (0.052); PSSOM E/C#m 0.781 over F#/D#m 0.697 (0.084); Wet Leg C/Am = F/Dm 0.988, broken by stem chroma C 0.710 over F 0.604. Without the half credit PSSOM goes to F# major (0.696).
- The worktree computes `chroma_cqt` twice per run (fill on the harmonic sum at `fill.py:62`, key on the mix at `key.py:34`), and the mix is the worse witness.

**Design.**
1. `harmonic_chroma` computed once on the harmonic sum (`chroma_cqt`, hop 512); fill reads bar means; key reads the energy-masked mean (bars above `FILL_MIN_ENERGY`, so silence and pre-roll do not vote). Keep `sections.py:beat_chroma` on the mix.
2. Tonic from the chord stream. Two measured rules, both 4 of 4; pick one and record the other's result in the harmony note for the Fame blind test:
   - (chords strand) candidates = roots with at least 0.2 of chord time; score = root share + 0.10 if the final chord lasting at least a bar + 0.15 times the share of sections ending on it. PSSOM C# 0.458 over B 0.421; S69 D 0.584 over A 0.451; Chelsea G 0.557 over D 0.336; Wet Leg C 0.593 over F 0.393.
   - (arrange strand) relative-major pair by time-weighted diatonic share with `ROOT_ONLY_CREDIT = 0.5`; pairs within `PAIR_TIE = 0.02` broken by harmonic-stem Krumhansl; tonic within the pair by root time plus 0.1 each for opening and closing the song.
3. Mode = sign of Krumhansl major minus minor correlation at the chosen tonic on the harmonic chroma mean; fall back to `estimate_key(chroma_mean_for(wav))` with fewer than four chord events.
4. `Key` gains `method: Literal["mix_krumhansl", "chords_stems"]`, `margin` (the tonic or pair margin), `runner_up` (the other candidate, or the chroma's dissenting key), and `mix: Key | None` holding today's estimate for the validation table. Schema version stays 1.
5. Header hedge: `Key: G major (or D major)` when `margin < KEY_HEDGE_MARGIN` (0.05; Chelsea 0.045 hedged, S69 0.052 not) or when the chroma's best key disagrees with the chord key. With a capo, hedge `_shape_key` the same way.
6. Compute the key after the fill and after rank 12's stems pass so recovered chords count.

**Measure.** PSSOM "C# minor", S69 "D major", Wet Leg "C major", Chelsea "G major (or D major)" (unverified truth; G fits the detected C and Am better, 94.7 against 91.0 percent diatonic). Capo stays 4 on PSSOM (1.80 against 2.60 for capo 2). Add the four songs as fixtures to `tests/test_key.py` from `chords.json` plus the dumped `chroma_means.json`.

**Effort** medium. **Impact** high (fixes the one wrong header, removes two coin tosses, prerequisite for ranks 10 and 16). **Confidence** 85.

**Conflict flag.** The two strands define `Key.confidence` differently: the chords strand as the mode margin at the tonic (about 0.38 PSSOM, 0.30 S69, 0.31 Chelsea, 0.22 Wet Leg), the arrange strand as the pair margin (0.084, 0.052, 0.045, tie). Store both (`mode_margin`, `margin`) and hedge on the tonic/pair margin, since that is where Chelsea is actually doubtful.

### 4.2 Vocal-run boundaries and vocal-aware labels (rank 5)

From structure 3.1. The largest measured gain on the structure strand.

**Touches.** `stages/grid.py:42` (`GridStage.requires` adds `separate/stems/vocals.wav`), `:64-68` (read it as the drums stem is read), `:84-87` (worktree `:87-90`: call `insert_vocal_boundaries` after `boundaries_from_clusters(..., min_bars=MIN_SECTION_BARS)` and before `label_sections`); `music/sections.py` (new `bar_stem_db`, `vocal_flags`, `insert_vocal_boundaries`, and a `vocal` parameter on `label_sections` at `:182-186`); `schemas.py:58-72` (`Grid.bar_vocal_db: list[float] = []`); `tests/test_stage_grid.py:26-43` (`_ctx` writes a vocals stem), `tests/test_sections.py:142-181`.

**Evidence.** Vocal threshold = median per-bar vocal dB (over bars above -60 dB) minus 12; flags median-filtered over 3 bars; runs of at least 4 non-vocal bars. Runs found: Chelsea (0, 20) and (93, 108); S69 (0, 3), (67, 75), (114, 118); PSSOM (12, 15), (67, 77); Wet Leg none of 4 bars inside the song. These coincide with the known arrangement (lessons: Chelsea vocals silent 0-19 and 93-108; hand lists: S69 solo 67-74, PSSOM solo 67-76). Prototype result on the v1.2 segmentation:

| Song | today | with vocal runs | F0.58 at one bar | hits@1 |
|---|---|---|---|---|
| Chelsea | verse 0-9, chorus 9-38, ..., chorus 93-99, bridge 99-105, chorus 105-142 | intro 0-9, instrumental 9-20, chorus 20-38, verse 38-61, chorus 61-71, verse 71-93, instrumental 93-108, chorus 108-142 | no reference | |
| S69 | verse 2 0-4, ..., verse 69-83, ... | intro 0-4, ..., bridge 58-68 (with rank 7), instrumental 68-75, verse 75-83, ... | 0.609 to 0.735 | 8 to 10 of 13 |
| PSSOM | ..., verse 67-84, chorus | ..., instrumental 67-77, verse 77-84, chorus | 0.484 to 0.555 | 4 to 5 of 12 |
| Wet Leg | unchanged | unchanged | | |

Adding stem levels to the embedding instead was measured and rejected (path graph: no change; recurrence graph: S69 0.588, PSSOM 0.363). The Van Balen chorusness score flips Chelsea's correct chorus to the verse cluster; loudness alone is right on 3 of 3 verifiable songs.

**Design.** `VOCAL_BELOW_MEDIAN_DB = 12`, `VOCAL_RUN_MIN_BARS = MIN_SECTION_BARS`. For each non-vocal run of at least 4 bars strictly inside the song, insert its edges as boundaries when both resulting pieces are at least 4 bars; otherwise move the nearest existing boundary onto the edge when the move is at most 3 bars and keeps both neighbours at 4 bars or more. Do not touch the trailing run (the prototype wrongly moved S69's 111 to 114 inside the fade) or the first boundary. In `label_sections`: a segment with vocal share under 0.25, or the first or last with under 0.5, is `intro`, `outro` or `instrumental` regardless of cluster; chorus candidates are recurring clusters with bar-weighted vocal share at least 0.5 (every recurring cluster passes today, 0.70 to 0.98; the gate guards the Riptide-type case from spike round 3); adjacent `intro`/`instrumental`/`outro` merge, so Chelsea prints `intro 0-20`. No `solo` label: guitar/mix in the two solos (0.23; 0.44 to 0.63) is too close to the song medians (0.27; 0.40).

**Measure.** The rank 4 harness: floors 0.609 and 0.484, targets 0.735 and 0.555; assertions for Chelsea (intro ends at bar 20, no `chorus` before 20, bars 93-108 instrumental) and Wet Leg (boundaries unchanged).

**Effort** medium. **Impact** high. **Confidence** 85.

### 4.3 Per-section strum source between `guitar` and `other` (rank 9)

From strums 2.2. The finding the research missed and the biggest single strums gain: S69's chorus recall collapse is separation routing, not a threshold.

**Touches.** `music/onsets.py:63-72` (`choose_source`, whole-song), `:75-76` (`section_has_instrument`); `stages/strums.py:62-68` (one detector call on one stem), `:72-80` (no-instrument branch), `:108-116`; `schemas.py:145-152` (`SectionPattern.source`); `sheet.html.j2:65` (mix note); `tests/test_stage_strums.py:106-150`.

**Evidence.** S69 per section, baseline detector on each stem:

| Section | guitar/mix RMS | other/mix RMS | guitar strikes per bar, Jaccard | other strikes per bar, Jaccard |
|---|---:|---:|---|---|
| sec 1 verse (4-19) | 0.40 | 0.00 | 6.1, 0.76 | 0.0 |
| sec 4 chorus (41-53) | 0.29 | 0.06 | 2.9, 0.39 | 6.8, 0.85 |
| sec 6 bridge (58-69) | 0.40 | 0.17 | 3.5, 0.38 | 6.1, 0.76 |
| sec 8 chorus (83-95) | 0.30 | 0.11 | 1.8, 0.53 | 7.0, 0.88 |
| sec 9 verse (95-111) | 0.47 | 0.21 | 3.3, 0.43 | 7.9, 0.98 |
| sec 10 outro (111-121) | 0.33 | 0.32 | 2.6, 0.18 | 7.5, 0.94 |

From bar 41 on, Demucs files the eighth-note rhythm part into `other`. RMS cannot see this (guitar is louder in every section), so a song-level choice is wrong either way: `other` by default would give the verses 0.0 strikes per bar. Wet Leg sec 24 outro (108-113): guitar/mix 0.01, other/mix 0.82, `other` gives 6.8 strikes per bar at Jaccard 0.85, yet the sheet prints "No strummed instrument detected" because `section_has_instrument` is only asked about the chosen stem. PSSOM sec 0 and sec 6: `other` has 9.8 and 12.0 strikes per bar (all sixteenths) against 7.7 and 3.4 on guitar; whether that is rhythm guitar or keyboards is not knowable from the numbers. Chelsea: `other` below 1.8 strikes per bar everywhere; never switches. Summing `guitar + other` behaves like the louder stem (S69 sec 8 stays at 1.5).

**Design.** Detect onsets on both stems once (1 to 3 s per stem). Per section compute the `> 1/3` pattern, `explained`, strikes per bar and Jaccard for each stem. Choose `other` when the song-level stem's section is sparse (`explained < 0.6` or strikes per bar under 2) and `other` has Jaccard at least 0.7 and at least 4 strikes per bar, or when `section_has_instrument` fails on the song-level stem but passes on `other`. Measured, this switches S69 sec 8 and 10, Wet Leg sec 24, PSSOM sec 6, nothing on Chelsea; a stricter density test (`guitar < 0.6 x other`) would also switch S69 sec 4, 6, 9 and should be tried after an ear check. Record `SectionPattern.source: Literal["guitar_stem", "other_stem", "mix"]`; keep the whole-song mix fallback (ratio under 0.05).

**Measure.** Listen to S69 `other.wav` from 70 to 100 s and 165 s onward and confirm it is the strummed guitar; compare strikes per bar and `explained` per section before and after on all four runs; PSSOM sec 6 is the control that may be wrong.

**Effort** medium. **Impact** high. **Confidence** 65 (the `other` content has not been heard; thresholds fitted to four songs). **Conflict with rank 18 on Wet Leg bars 108-113; see section 6.**

### 4.4 Power chords: relabel the tonic major to the key's quality (rank 10)

Merged from chords 3.4 and arrange 1 (steps 6 and 7). Both strands discard the chroma third test and agree the fix is key-driven and tonic-only.

**Touches.** Worktree `stages/harmony.py` (new step after the key); `music/triads.py:17-34` (`to_triad` must not turn `X:5` into `maj`; `triads.py:33` is the max-overlap fallback that does); `music/shapes.py:11-33` (`HARTE_TO_SUFFIX` has no `5`); `music/arrange.py:123-139` (`simplify_for_tier`); `schemas.py:106-114` (`ChordEvent.power: bool` or `quality_from_key: bool`); `stages/arrange.py:35` (substitutions); `tests/test_triads.py`, `tests/test_arrange.py`.

**Evidence.** PSSOM's riff is `C#:maj` for 41.1 percent of chord time (`C#:min` 0.3 percent), printed `A` at capo 4; the published chart prints C#m. The chroma third test fails: per event on the summed harmonic stems, median third-over-fifth is 0.63 for the riff against 0.38 for PSSOM's real `A:maj`, 0.32 for `F#:maj`, 0.46 for S69's `A:maj`, 1.01 for Wet Leg's `C:maj` (the fifth harmonic of a distorted root lands on the major third); any threshold flagging C# also flags real triads. The model cannot emit `5` with any dictionary: `complex_chord.Chord("C:5").to_numpy()` gives triad id 73, above `triad_limit*12+1 = 37`, so the decoder drops it; the `full` dictionary run returns the shipped shares exactly. `harte_to_db("C#:5")` returns `None` and chords-db has no `5` suffix for any root.

**Design.**
1. After the key: when `key.mode == "minor"`, the tonic root's chord time in the opposite quality exceeds its time in the key's quality, the harmonic chroma prefers the key's mode at that tonic (chords strand: mode margin at least 0.2; arrange strand: PSSOM C# minor 0.716 against C# major 0.338), and the share is at least 0.2 of chord time (stops a one-bar Picardy or borrowed major tonic), relabel those events' `triad` to the key's quality, set `label = "C#:5"` and `power = True` (or `quality_from_key = True`). Touch no other `maj` label: a wider rule would relabel S69's and Chelsea's genuine majors and PSSOM's real `B` and `E`.
2. The stage writes `triad` explicitly so `to_triad` stays for model labels.
3. Arrange: `easy` prints the key's quality (C#m; Am at capo 4). `full`: the chords strand prefers printing the minor shape with a "5" badge and a legend note "(power chord on the record)" because chords-db has no `5` shapes and a two-string root-fifth is not a true power chord on re-entrant tuning; the arrange strand prefers printing `C#5` with a `Substitution` reason `"no-third chord: quality from key"`. Product decision; both agree on `easy`.

**Measure.** PSSOM: header "C# minor", riff cells `Am` at capo 4, legend `Am D G C F`; capo stays 4 (validation margin 0.47 holds with C#m). S69, Chelsea, Wet Leg: no change.

**Effort** medium. **Impact** medium (one song's most-used chord prints as the chart has it). **Confidence** 65 (chords strand, one song exercises the gates) to 85 (arrange strand, as part of the key item).

### 4.5 Second recogniser pass on guitar+other for all-`N` bars (rank 12)

From chords 3.5.

**Touches.** Worktree `stages/harmony.py:64-73` (between the mix pass and the fill); `models/chords.py:30` (takes any wav); `music/snap.py:24` (reuse on the second span list); `schemas.ChordEvent.source: Literal["mix", "stems", "template"]`; `tests/test_stage_harmony.py`.

**Evidence.** Over 189.5 to 237.5 s PSSOM `N` falls from 0.683 (mix) to 0.515 (four harmonic stems) to 0.388 (guitar+other), and `D:maj` appears at 0.213 of the window (`D:maj` 195.1 to 200.6 s and 205.8 to 210.5 s, `E:maj` 200.6 to 205.8 s and 211.9 to 217.3 s). But the whole-song `N` share on guitar+other is worse (0.326 against 0.277) and the stems add spurious inversions (`F#:maj/5`, Chelsea `D:maj/5`), matching Mitoma and Furuya: stems help locally and hurt globally. Chelsea's intro gains nothing (`N` 1.0 on guitar+other). Cost: one more model run, 9.5 to 12.6 s per song.

**Design.** Write `work_dir/guitar_other.wav` (mono sum), run the same recogniser with beats (after rank 2), snap, and for each bar all-`N` on the mix pass that has a chord with confidence at least 0.75 on the stems pass, take the stems events, mark `filled = True`, `source = "stems"`. Run the template fill afterwards for what remains. Compute the key after both passes.

**Measure.** PSSOM bars 67-74: `D`, `E`, `D`, `E` where the stems lab has them, `N` share below 0.22; the other three songs unchanged (their all-`N` bars are silent, fade or non-song audio). Note "stems pass filled k bars".

**Effort** medium. **Impact** medium (6 of PSSOM's 11 solo `N` bars with the chords the record plays). **Confidence** 70 (one passage; the 0.75 gate is a guess to set on Fame).

### 4.6 Per-bar stem levels computed once in the grid stage (rank 14)

Plumbing merged from structure 3.1 and 3.5 (vocals, drums, bass, guitar per bar), chords 3.3 ("the per-bar stem RMS table is the better evidence" for whether a bar is a riff or silence), strums 2.2 (per-section guitar and other RMS) and the worktree's `fill.py:71-78` `bar_energy`.

**Touches.** `stages/grid.py:42` (`requires` lists all six stems), `:64-68`; a new `music/stem_levels.py` (`bar_stem_levels(stems, bars) -> dict[str, list[float]]`, RMS per bar divided by the mix RMS, plus dB); `schemas.Grid.bar_stem_levels` (or the `bar_vocal_db` of rank 5 generalised); worktree `music/fill.py:71-78` reads it instead of recomputing; `stages/strums.py` reads it for the per-section RMS it already computes.

**Evidence.** Four strands each propose computing the same per-bar stem RMS in a different stage. The stems exist before the grid stage runs. Cost today is negligible (the structure experiments computed all six stems per bar for four songs in seconds), and storing the table in `grid.json` makes the rank 5, 12, 13 and 18 gates inspectable and hand-editable without a rerun.

**Design.** Compute once in the grid stage, store in `grid.json`, and have harmony, strums and the labeller read it. Keep the shapes small (six lists of floats per song).

**Effort** small to medium. **Impact** medium as an enabler. **Confidence** 85.

### 4.7 Metrical-level regularisation before the global octave decision (rank 25)

From beats 5.

**Touches.** `music/tempo.py`: new `regularise_beats(beats, downbeat_idx) -> tuple[list[float], list[int], list[Repair]]` between `fill_gaps` (`:23-43`) and `bpm_from_beats`; `stages/grid.py:61`; `normalise_octave` (`:102-132`) unchanged; `Grid.repairs`; a test beside `test_normalise_octave_repairs_half_doubled_list` (`tests/test_tempo.py:56`).

**Evidence.** The prototype (dominant interval from the middle 80 percent; runs of at least 8 intervals within 10 percent of 0.5x or 2.0x) repairs Over the Rainbow's two 2x stretches (59.7 to 89.3 s, 42 intervals; 178.5 to 209.4 s, 44 intervals; bars max/median 2.01 to 1.01) and is a no-op on the six other songs. Today the repair happens only inside `normalise_octave`, that is only when the global decision is "half".

**Design.** Classify each interval as 0.5x (within 5 percent of half the dominant), 2.0x (within 20 percent of double) or normal; runs of at least 8 consecutive 0.5x intervals drop every other beat (reusing the parity logic of `normalise_octave` lines 123-126); runs of 2.0x insert midpoints. Shorter runs stay with `fill_gaps`. Log the repairs.

**Measure.** Over the Rainbow's beat list comes out with one bar length even with `--beat-octave none`; the four runs, I'm Yours and Riptide byte-identical before and after; synthetic 150 bpm click with 40 middle beats at 75 bpm.

**Effort** small to medium. **Impact** medium, latent. **Confidence** 55 (no positive example where the global decision is "none").

### 4.8 Keep every k level in `grid.json` (rank 26)

From structure 3.7.

**Touches.** `music/sections.py:125-142` (`segment_bars` returns the labelling for every k from 3 to the chosen k, which the loop at `:137-142` already computes and discards); `schemas.Grid.section_levels`; `stages/grid.py:84-87`; `--sections-k` (`options.py:15`, `cli.py:45`) already exists.

**Evidence.** S69 at k 3: F 0.428; k 4 (chosen): 0.609; k 5, 6: 0.571. PSSOM k 3 (chosen): 0.484, hits@1 4/12; k 5: 0.476, hits@1 5/12. Wet Leg k 4 gives a 12-bar periodic middle (5 17 12 12 12 7 36 7 5) against the chosen k 5. No level is best on every song (Salamon 2021, MSAF). The design spec already says sections live in an editable file because shared progressions cannot be separated from audio.

**Design.** Store the levels; print each level's bar lengths in the log so a hand fix is a one-number `--sections-k` edit. Enables structure 3.10 (fusion by lower-level vote) if ever wanted.

**Effort** medium. **Impact** medium for hand editing, none automatic. **Confidence** 65.

### 4.9 Ordinal shape difficulty (rank 28)

From arrange 10.

**Touches.** `music/shapes.py:109-117` (`shape_cost`); `music/arrange.py:32, 43, 72, 80`; `tests/test_shapes.py:47-66`, `tests/test_arrange.py:56-116` (the published-chart capo tests must stay green).

**Evidence.** E `1402` beats `4442` by 2.70 to 3.00, a 0.3 margin a weight change flips; chords-db marks `4442` as no barre though players treat it as one. The five major and minor chords with no open, barre-free shape are B, Bm, Bb, Bbm, Db; the capo search is in effect trying to remove them. No published ukulele difficulty model exists.

**Design.** Tier each shape `open` (base fret 1, no barre, at most three fingers, span at most two frets), `stretch`, `barre`, `high` (base fret above 3); score capo and voicings on `(tier, cost)` lexicographically with the current weights as the within-tier cost.

**Measure.** The seven capo cases in `tests/test_arrange.py:60-116` unchanged; E still `1402`; PSSOM still capo 4; Chelsea's margin over capo 2 reported.

**Effort** medium. **Impact** low-medium. **Confidence** 60 (the current rule is right on every validation song).

---

## 5. Larger directions

### 5.1 Multi-cue boundary candidates with a duration prior (rank 29)

From structure 3.8. The only route to the shared-progression boundaries other than hand editing.

**Touches.** New `music/boundaries.py`: bar-level Foote novelty on the chroma+MFCC self-similarity that `_embedding` already builds (`sections.py:93-99`), a stem-level novelty (vocals, drums, bass, guitar dB over 4-bar windows), and a dynamic programme over bars choosing boundaries from the union of peaks with a modulo-4 length penalty (Marmoret 2023: 0 at 8, 1/4 for multiples of 4, 1/2 even, 1 odd) and the cluster boundaries as strong candidates; called from `stages/grid.py:84-87` between `segment_bars` and `label_sections`.

**Evidence for the ceiling.** Within one bar of a reference boundary there is a chroma-novelty peak for 9 of 13 (S69) and 7 of 12 (PSSOM), a stem-novelty peak for 5 of 13 and 6 of 12, and the union covers 9 of 12 on PSSOM against 4 of 12 today. Evidence against a naive version: both snap variants lowered PSSOM's precision (0.484 to 0.121 or 0.363) because the peaks nearest the current boundaries are pre-chorus centres. Build only behind the rank 4 harness, scored on one-bar precision first.

**Effort** large. **Impact** medium-high. **Confidence** 55 (candidate recall is not boundary precision; two songs are too few to tune a prior).

### 5.2 Trained CRNN strum detector on synthetic stems (rank 30)

From strums 2.10.

**Touches.** New `models/strums.py` beside `models/beats.py`; `detect_onsets` becomes one of two detectors behind the `onset_detector` hook `StrumsStage.__init__` already has (`stages/strums.py:49-50`); training scripts outside the package.

**Evidence.** Classical detectors reach 79 to 83 percent onset F1 on isolated guitar and less on stems; both 2025 papers (Yousician; Murgul) trained a small frame model on synthetic strummed audio mixed into real backing and gained 15 to 20 F1 points over spectral flux. Symptoms here: S69 chorus recall of 1.8 strikes per bar on a part that plays eighths (though rank 9 shows routing explains much of that), PSSOM grid fit 0.59. torch is already a dependency; Beat This! already runs a CPU transformer in the grid stage.

**Design.** Render strums from generated chord grids with ukulele and nylon-guitar soundfonts (FluidSynth), random pattern, tempo, transposition, EQ, reverb and noise; mix at random levels into the project's own drums, bass and vocals stems; separate with htdemucs_6s and train on the resulting `guitar` and `other` stems so the model sees Demucs artefacts; Beat This!'s shift-tolerant BCE. Validate on the rank 4 strum truth. Ship opt-in until it beats librosa on the truth set.

**Effort** large. **Impact** high. **Confidence** 55 (soundfont-to-record gap; the baseline F1 has not been measured yet, so rank 4 first).

### 5.3 Chord-level decoding over the beat grid with a duration prior (rank 31)

From chords 4.2. Needs the raw posteriors in-process (`beat_decode_experiment.py:85-90` shows how) and a Viterbi over beat tokens favouring two- and four-beat chords. Korzeniowski and Widmer measured about one WCSR point; after rank 2 the remaining sub-beat events are one in PSSOM and none elsewhere, so the marginal gain on these songs is small. **Effort** large. **Impact** low-medium. **Confidence** 55.

### 5.4 Beat This! checkpoint ensemble on logits (rank 32)

From beats 9. `models/beats.py:19-29` (`detect_beats`) would use `beat_this.inference.Audio2Frames` for `final0`, `final1`, `final2`, average logits, then `Postprocessor("minimal")`; three passes stay under 20 s. Beat This! issue #13 reports Accuracy1 89.3 to 90.9 percent with an ensemble; the defect it could reduce here is mid-bar extra downbeats (PSSOM 22, Over the Rainbow 18). Not measured locally (`final1`, `final2` not cached). **Effort** medium. **Impact** low-medium. **Confidence** 35.

### 5.5 Accents from the detrended envelope (rank 33)

From strums 2.8. Envelope minus its 200 ms running mean, two strongest slots per section: Chelsea slots 2 and 6 (beats 2 and 4) in seven of eight sections, which is either the real guitar accent or snare bleed; no onset-level test separates them (the drum veto was measured and rejected). Mark accents only when both strongest slots are pattern strikes and stable in at least 70 percent of bars, never on the mix source. `onsets.py:38-52`, `render/strum_box.py:22-45`, `SectionPattern.accents`. **Effort** small. **Impact** low. **Confidence** 45; needs the rank 4 truth or an ear check first.

### 5.6 Swing grid (rank 34)

From strums 2.9. None of the four songs is swung (onset phase inside the beat: S69 0.42 on the beat and 0.34 at the half; Chelsea 0.23 and 0.43 just before; PSSOM flat). Add a 12-slot candidate in `choose_slots_per_bar` (`onsets.py:91-99`) when phase mass at 2/3 exceeds 1/2, relax `check_strums_match_grid` (`score_builder.py:41-46`) to `(2, 3, 4) x numerator`, 12-column box (`strum_box.py:12` already has a 3-per-beat entry). Do it when a swung validation song exists. **Effort** large. **Impact** low today. **Confidence** 60.

### 5.7 Local key and the last-chorus lift (rank 35)

From arrange 11. Per-section scoring over `grid.sections` using the shared chroma (rank 3) and the chord stream; capo per key segment with "same shapes, capo +1" for a one or two fret lift. None of the five validation songs modulates (Fame does not either), so there is nothing to set the self-transition penalty against. Add a modulating song first. **Effort** large. **Confidence** not assessable.

### 5.8 Deferred without rank

- **Vote labels across repeated sections (Mauch 2009)**, chords 4.1: `Section` has no cluster id (`schemas.py:52-56`) and same-label sections have unequal lengths (Chelsea choruses 29, 10, 6, 37 bars); rank 2 already lifts Chelsea's on-bar changes 54 to 58 of 68. Confidence 45.
- **ChordMini as a second opinion**, chords 4.3: option plumbing exists (`options.py:18`, `cli.py:48`, `preflight.py:93`); MIT code, unstated checkpoint licence, CC BY-NC-SA teacher weights, Majmin 80.24 below the vendored model. Confidence 40.
- **Kostka-Payne and Albrecht-Shanahan as a three-way mode vote** inside rank 3, chords 4.4: they agree with Krumhansl on the mode at every candidate tonic; flag `confidence = 0` if they ever split. Confidence 60 that it ever fires.
- **Pre-chorus rule**, structure 3.9: neither pre-chorus is its own cluster at any k from 3 to 6. Confidence 40.
- **Section fusion by lower-level vote**, structure 3.10: equals merge-forward on both scored songs. Confidence 40.

---

## 6. Conflicts and dependencies between strands

| # | Between | What conflicts | Suggested resolution |
|---|---|---|---|
| C1 | structure 3.5 (rank 18) and strums 2.2 (rank 9) | Wet Leg bars 108/109 to 112/113: structure measures drums, bass and guitar at 0.00 to 0.01 of the mix and `other` at 0.82 and calls it non-song audio to omit; strums measures 6.8 regular strikes per bar on `other` (Jaccard 0.85) and proposes rescuing the outro's "No strummed instrument detected" with a strum box from `other`. One strand drops the bars, the other prints a pattern for them. | Listen to `other.wav` over the last four bars. If it is non-song audio, the not-music class wins and the strums rescue must be gated to bars inside the song (use the rank 14 stem table). If it is the record's outro riff, the not-music rule's 8 percent test is wrong on this song and needs a vocals or `other` term. |
| C2 | chords 3.2 and arrange 1 (both in rank 3) | Two tonic rules (root share + final chord + section-end bonus; diatonic-pair share with half credit + pair tie-break + root time + opening/closing bonus) and two `Key.confidence` definitions (mode margin, about 0.2 to 0.38; pair margin, 0.045 to 0.084). Both rules are 4 of 4 on the set. | Implement one, log the other's answer in the harmony note until the Fame blind test, and store both margins on `Key`. Hedge on the tonic/pair margin, which is where Chelsea is doubtful. |
| C3 | chords 3.4 and arrange 1 step 6 (rank 10) | Gates differ (mode margin at least 0.2 and share at least 0.2; versus opposite quality exceeding the key quality and chroma preferring the key mode at the tonic) and the `full` tier presentation differs (minor shape with a "5" badge and legend note; versus `C#5` with a substitution reason). | Both fire only on PSSOM's six `C#:maj` events. Use the conjunction of both gates for now; the `full` tier presentation is a product decision. `easy` prints the minor either way. |
| C4 | chords 3.1 rationale and beats 1.3 | The chords report explains today's per-beat vote by a model lag of 0.1 to 0.4 s (spike B). The beats strand measured the real songs: boundaries are early by 27 to 44 ms median, none beyond half a beat; the lag was a synthetic-clip artefact. | No change to rank 2 (beat-aware decoding), but the research's fixed lag shift (`CHORD_LAG_S`) is refuted and must not be added; rank 19(b) is the only remaining position rule, and it is small. |
| C5 | structure 3.3 (rank 7) and strums 2.3 (rank 11) | Rank 7 removes the cluster id from the label string (`verse 2` becomes `verse`) and moves bridge relabelling to the score stage. Rank 11 pools strum bars by label in the strums stage, which runs before the score stage; after rank 7 it would pool S69's bridge (bars 58-69, `other` stem, `SSSSSSSS`) with the verses. | Pool by cluster id, not label: either store the cluster id on `Section` (`schemas.py:52-56`, also wanted by chords 4.1) or run the pooling at the score stage after `refine_labels`. |
| C6 | beats 4 (rank 15) and v1.2 narrow pickup cell | v1.2 draws the pickup as a narrow leading cell; rank 15 omits a one-beat all-`N` pickup from the score and shifts `ScoreSection` starts by one. Both operate at the score stage. | Apply the drop before the narrow-cell rendering; a pickup with a chord keeps the narrow cell. |
| C7 | arrange 1 (rank 3) and structure 3.2 (rank 7) and rank 12 | Rank 7's bridge rule uses the chord set; rank 3 counts filled events in the key; rank 12 adds stems-recovered events. Order matters. | Harmony stage order: mix pass, stems pass, template fill, key, power-chord relabel. Score stage: phrase alignment, `refine_labels`, pickup drop. |
| C8 | arrange (htdemucs_ft discarded) and strums 3.7 (roformer or MDXC guitar checkpoints) | Both strands decline a separator change for now; strums leaves the door open "only after 2.2 and 2.5 show that routing between the two existing stems is not enough". | Consistent: no separator change until rank 9 and rank 4 are measured. |
| C9 | Chelsea bars 110-122 | arrange 1(e) calls the two-beat C/D alternation harmonic rhythm (keep); chords 4.1 says six two-beat `D` events could be genuine and defers; beats 1.3 finds no beat 1/3 starts on Chelsea. | Agreement by three strands: do not merge; rank 19 explicitly never merges across a bar line or two-beat events. |

Dependencies in one line each: rank 10 needs rank 3; rank 16 needs rank 3; rank 7's vocal condition and rank 24 need rank 5; ranks 5, 12, 13, 18 share rank 14's stem table; rank 11 and rank 1 share `explained`; ranks 13 and 19 should be re-measured after ranks 2 and 12; every threshold change should be scored through rank 4.

---

## 7. What the research says, per strand

### 7.1 Chord recognition, no-chord handling and key

- Major/minor WCSR on Isophonics-style pop sits at 82 to 85 percent for every modern architecture (CNN+CRF 82.9, BTC 82.7, Jiang 82.6, ChordFormer 84.1, Würzburg 84.7); humans agree about 73 percent on the same labels (Koops 2019). The vendored Chord-CNN-LSTM is within about two points of the best. Swapping the recogniser is not where quality will come from; context (beats, sections, key, stems) and presentation rules are (Pauwels et al. 2019; Humphrey and Bello 2015).
- Remaining errors are related chords, passages without chords, mistuning and granularity disagreements; 2025 to 2026 papers attack class imbalance and over-segmentation, not these (ChordFormer; Micchi 2021).
- Beat-synchronous decoding and long-range structure give more readable output (Mauch, Noland, Dixon 2009; Korzeniowski and Widmer 2018 duration and harmonic language models, about one WCSR point; Papadopoulos and Peeters 2011 metric-position change probability).
- Stems: one peer-reviewed study (Mitoma and Furuya, APSIPA 2025) finds a small global gain, bigger local gains, and a known failure on single-note riffs; this session's measurement agrees exactly.
- Key: template methods on clean harmonic chroma remain competitive; gains come from removing percussion before chroma, better minor profiles (Albrecht-Shanahan 2013), and deciding tonic and mode from different evidence (rock tonic from chord roots, Temperley and de Clercq 2013; mode from pitch-class content). Supervised key CNNs (madmom, Korzeniowski and Widmer 2018) add 1 to 10 points but are CC BY-NC-SA.
- Libraries that fail the CPU-only Windows Python 3.12 permissive-licence test: Essentia (AGPL, no Windows wheels), madmom (Python below 3.10, CC BY-NC-SA models), Chordino (GPL), BTC original weights (CC BY-NC-SA), crema (TensorFlow), ChordMini (unstated checkpoint licence).

### 7.2 Beat tracking, tempo octave, downbeats and the bar grid

- Beat tracking on pop and rock is at about 95 percent F1 and downbeats at 88 to 94 percent (Beat This!: Harmonix 90.7, RWC Pop 93.7, Beatles 88.8; Foscarin, Schlüter, Widmer 2024). Residual errors are structural (octave, phase, meter, continuity), not jitter.
- Tempo Accuracy2 is 95 to 96 percent while Accuracy1 is high 80s to low 90s, so almost all residual tempo error is octave error (Schreiber and Müller 2017; Beat This! issue #13 heuristic 89.3 to 90.9 on GiantSteps). Octave identification by metrical profile (Smith, Beat Critic, 2010) and perceptual tempo studies (McKinney and Moelants 2004) underlie the backbeat test.
- The DBN trade-off: it improves CMLt coherence but reduces F1 (Beat This! Table 2; the SMC blind-spot analysis 2026). For a chord grid, coherence is worth more than per-beat placement, so a light coherence pass (rank 25) is the right investment, not madmom.
- Meter from downbeat spacing is reliable when downbeats are; 6/8 is ambiguous with 3/4 and 2/4 by construction (Abimbola et al. 2021; Morais, McFee, Fuentes 2025 on underrepresented meters).
- Joint chord and downbeat models exist (Papadopoulos and Peeters 2011; US patent 9,653,056) but a position-dependent change penalty on a beat lattice, which the vendored decoder already supports, captures most of the benefit.
- Downstream projects correct octaves post hoc with heuristics (Drumscore PR #116, Beat This! issue #13, stagehand PR #22); the ratio-based test here is of the same family.

### 7.3 Song structure segmentation and labelling

- Unsupervised spectral clustering (McFee and Ellis 2014, the method the project uses) reaches HR0.5 0.26 to 0.41 and HR3 about 0.56 on Harmonix; with section fusion and deep embeddings HR0.5 0.46, HR3 0.69 (Salamon, Nieto, Bryan 2021). Supervised 2023 to 2025: allin1 HR.5F 0.596, LinkSeg 0.630, SongFormer 0.696, label accuracy 0.74 to 0.81. Human agreement is about 90 percent (TISMIR 2020), 66 percent within 0.5 s per annotator pair, 78 percent for chorus starts (Wang 2021).
- For a printed sheet the relevant tolerance is one bar (1.5 to 2.8 s at 85 to 160 bpm), between the 0.5 s and 3 s windows; a good bar-level unsupervised system with a length prior should sit at 0.6 to 0.7, which is where the project is on S69 and above where it is on PSSOM.
- Consensus: process at bar level (Harmonix 81.1 percent of boundaries on downbeats; Marmoret 2023); duration prior around 8 bars favouring multiples of 4 (Shibata 2019, Sargent 2011, McFee 2025); fuse short sections by lower-level clusterings (Salamon 2021); value precision over recall (Nieto 2014 F-measure perception study; MSAF); label with arrangement and timbre cues, not loudness alone (Van Balen 2013; Wang 2021, 2022); keep a non-music class (Wang 2022; allin1); pre-chorus is hard everywhere; offer more than one granularity.
- Apps: boundaries are more reliable than labels; Moises and Chordify number sections by occurrence and let the user edit (Chordonomicon's eight names include `instrumental`).
- Measured locally: the Van Balen chorusness score flips Chelsea, smaller smoothing filters lose on S69, and novelty snapping halves PSSOM's recall, so the heuristics the literature recommends must be gated by a harness on this pipeline's own data.

### 7.4 Strumming pattern and rhythm extraction

- Strum onset detection on a stem or mix is at about 95 to 97 percent F1 with a trained frame model (Yousician's fine-tuned MERT, Lukoianov and Klapuri 2025; Murgul, Schimper and Heizmann 2025 CRNN 97.6 percent on pickup audio). Spectral-flux detectors reach 79 to 83 percent on isolated guitar and less on stems. The gap is recall on quiet or smeared passages and false positives from bleed.
- Direction from audio alone is 79 to 86 percent per class even with sensor-labelled training (Murgul 2022, 2025); the positional convention is what humans write, so positional direction plus honest wording is good enough.
- Mutes and accents have no published audio model for strumming; the 2025 Yousician paper excludes muted strokes. Decay-based palm-mute cues from technique detection (Reboursière 2012) were measured here and do not separate in Demucs stems.
- Pattern decoding: Viterbi over a vocabulary with a Gaussian two-way mismatch emission and a change penalty (Yousician, 15 percent bar-to-bar discontinuity on real songs); Dixon, Gouyon and Widmer 2004 show the cheaper route of averaging bar profiles within the dominant cluster, which is what pooling by section does.
- Yousician found `other` beats `guitar` as the strum source; here that holds per section, not per song, which is the basis of rank 9.
- Good enough for a chord sheet: one box per section with the right density, positional directions, and a sentence saying how much of what was heard it covers; Ultimate Guitar prints one pattern per song with no score, Chordify prints none.
- Not usable: MERT-v1-95M (CC-BY-NC-4.0, 95M parameters on CPU), madmom onsets (CC BY-NC-SA, broken on NumPy 2.5.3), the proprietary 924-pattern vocabulary.

### 7.5 Ukulele arrangement, chord simplification and key

- Large-vocabulary accuracy drops steeply beyond major/minor (McFee and Bello 2017: triads 0.812, sevenths 0.729, tetrads 0.671; Jiang et al. 2019: rare classes rarely detected); annotators agree at 0.73 for major/minor and 0.60 for sevenths (Koops 2019); inversion WCSR is near 20 percent for implicit-bass models (Deng and Kwok 2016). Good enough for a ukulele sheet: major/minor plus N snapped to beats, with sevenths as an optional layer, which is what the `easy` tier already does.
- Key: profile choice matters more than algorithm (Essentia's `tonictriad`, `edma`, `shaath`, `temperley` profiles exist because Krumhansl underperforms on popular repertoire); key-aware chord relabelling can hurt on borrowed chords (Mauch and Dixon; Pauwels), but key from chords is safe (Temperley; ISMIR 2006 HMM). Local key needs whole-piece coherence (Korzeniowski and Widmer) and no pop local-key dataset exists.
- Harmonic rhythm: beat-synchronous features and Viterbi are the standard remedy (Cho and Bello 2014; Papadopoulos and Peeters 2011); a metric minimum (one beat with a bar-position prior) is better founded than a seconds one (ChordZart's 0.5 s).
- Voicing: guitarists favour minimal movement, open voicings and barre avoidance (DadaGP diagram study 2024); no quantitative ukulele difficulty model exists.
- Separation: stems do not improve chord recognition on the mix (APSIPA 2025 +0.20; Ko worse); `htdemucs_ft` improves stems by 0.5 to 1.3 dB at four times the time; the 6s guitar and piano stems are poor in absolute terms (3.07 dB, 1.60 dB on MoisesDB) and `other` is near zero SDR; better guitar models (9 dB) are unlicensed or MVSEP-hosted.
- Products: Chordify and Moises present simplification and capo as toggles and let the user pick the capo; Ultimate Guitar and iReal Pro conventions (capo line, legend order, numbered sections) are what the sheet hygiene items copy.

---

## 8. Discarded across strands, with the measurement

| Idea | Strand | Why |
|---|---|---|
| Chroma third test for power chords | chords, arrange | Riff third/fifth 0.63 to 0.69, above real majors (0.28 to 0.63); any threshold flags A, F#, Bm too |
| Switching the model dictionary to `full` for `:5` | arrange | Triad id 73 above the network's limit 37; output identical to `submission` |
| Harmonic-stem Krumhansl as primary key | chords, arrange | Flips S69 to A major 0.883 vs D 0.807 |
| Profile disagreement as a confidence flag | chords | 24-way winners disagree on all four songs including the two certain ones |
| Raising `FILL_MIN_MATCH` to 0.5 / `FILL_MIN_MARGIN` to 0.15 | chords | Would remove true positives (PSSOM 70, 74 at 0.38, 0.33); doubtful fills pass up to 0.46 anyway |
| Fixed chord lag shift (`CHORD_LAG_S`) | beats | Boundaries are early by 27 to 44 ms, not late |
| Tempogram or onset-autocorrelation ambiguity flag | beats | Half lag stronger than beat lag on 3 of 4 correct songs |
| Max backbeat ratio over half/detected/double | beats | Doubled hypothesis scores 2 to 15 on every song |
| Harmonic-rhythm octave vote | beats | PSSOM's median chord is 0.51 bars at the correct level |
| Regression instead of mean for the header | beats | Identical within 0.02 bpm; mean already in v1.2 |
| Automatic 2/4 or 6/8 detection | beats | 13 to 19 percent two-beat spacings on correct 4/4 songs; synthetic 3/4 at 120 tracked at the dotted crotchet |
| Van Balen chorusness score | structure | Flips Chelsea's correct chorus to the verse cluster |
| Smaller smoothing filters at bar rate | structure | S69 0.609 to 0.522 (0.465 with none); Wet Leg fragments 25 to 49 |
| Stem levels as embedding features | structure | Path graph: no change; recurrence graph: S69 0.588, PSSOM 0.363 |
| Novelty or regularity snapping of boundaries | structure | PSSOM 0.484 to 0.121 (chroma, shift 2) or 0.363 |
| A `solo` label | structure | Guitar/mix in solos not separable from song medians |
| Median or SuperFlux `onset_strength` | strums | Onsets fall 537 to 307, 491 to 112, 626 to 212, 815 to 237; S69 choruses to 0.2 strikes per bar |
| Section-relative peak picking | strums | Either falls back everywhere or gives `SSSSSSSS` with explained 1.00 and lower grid fit |
| Drum veto from `drums.wav` | strums | Removes 27 to 54 percent of onsets, lowers grid fit on every song, empties Wet Leg chorus 23 |
| Decay feature for the mute rule | strums | Medians 0.88 to 1.56 with no separation (AUC 0.64 in the spike) |
| Slot-strength profile as the pattern | strums | Dense stems never return to zero; sparse S69 sections become `SSSSSSSS` |
| Rate-vector correlation merge (0.8) | strums | Links Chelsea chorus to verse (0.95), S69 muted verse to open chorus (0.91) |
| Seconds-based minimum chord duration (0.5 s) | arrange | Would merge Chelsea's half-bar changes at 158 bpm |
| `htdemucs_ft`, BS Roformer SW, four-stem models | arrange, strums | Doubles separation time (already 76 to 84 percent of a run); strums stage built on 6s stems; roformer SW unlicensed |
| Essentia, madmom, Chordino, BTC weights, crema, ChordFormer, DECIBEL, MERT, BeatNet, allin1, LinkSeg, SongFormer, OpenL3, VGGish | all | Licence (AGPL, CC BY-NC), no Windows wheels or Python 3.12 support, GPU or TensorFlow dependency, or no public code |

---

## 9. Suggested order of work

1. Rank 4 (harness) and rank 14 (stem table), so every later change is measured and the stems are read once. Commit the owner's two hand lists as section truth; export strums onsets for annotation.
2. Rank 1 (strum threshold and `explained`) and rank 2 (beat-aware chord decoding): both small, both change what later items operate on.
3. Rank 3 (key) with rank 6 (no-capo line, alongside v1.2 Task 6's fret formatter) as one harmony-and-render change set; then rank 10 (power chords) once the key has been checked on the Fame blind test.
4. Rank 5 (vocal runs) then rank 7 (section names), resolving C5 by storing the cluster id on `Section`.
5. Rank 8 (octave test) with the cues persisted; re-check the seven-song table; add Fame before merging.
6. Rank 12 (stems pass) then rank 13 (fill refinement), in that order so the template rule sees fewer cases.
7. Rank 9 (per-section strum source) after an ear check of S69's `other` stem, resolving C1 on Wet Leg at the same time; then rank 11 (pooling).
8. Ranks 15 to 24 and 27 as small follow-ups in render and diagnostics.
9. Ranks 25, 26, 28 when a song exercises them (a locally doubled song, hand editing pain, a hard-key song).
10. Ranks 29 to 35 only behind the harness, and only after the above has moved the floors.

---

## 10. Sources

Project evidence (read-only): `docs/superpowers/specs/2026-10-03-real-run-lessons.md`, `2026-10-03-v1-1-validation.md`, `2026-10-03-ukulele-tab-chain-design.md`, `...-v1-1-design.md`, `...-v1-2-design.md`, `2026-10-03-v1-2-fill-measurements.md`, `2026-10-03-spike-models.md`, `2026-10-03-spike-grid-round3.md`, `2026-10-03-spike-audio.md`, `2026-10-03-spike-audio-round2.md`, `2026-10-03-assumption-checks-tools.md`; `src/youkelele/**`; `runs/{sexhetcxqy4,9f06qzcvuhg,0uib9y4ofps,lbc6ccztp5e}/**`; vendored model at `~/.youkelele/models/chord_cnn_lstm/`; `research_notes/` (`verification_papers_and_libraries.md`, `bass_anchor_and_local_key.md`, `tablature_theory_and_strumming.md`, `techniques_and_ukulele_arrangement.md`, `gap_analysis/verification_web_pages.md`). Measurement scripts: `scratchpad/research/apply/*.py`, `scratchpad/research/beats_apply/*.py`, `scratchpad/research/structure_experiments*.py`, `chroma_means.json`, `beat_decode_out/`, `stems_out/`.

Chords and key:
- Pauwels, O'Hanlon, Gómez, Sandler, "20 Years of Automatic Chord Recognition from Audio", ISMIR 2019. http://archives.ismir.net/ismir2019/paper/000004.pdf
- Humphrey, Bello, "Four Timely Insights on Automatic Chord Estimation", ISMIR 2015. http://ismir2015.uma.es/articles/294_Paper.pdf
- Jiang, Chen, Li, Xia, "Large-Vocabulary Chord Transcription via Chord Structure Decomposition", ISMIR 2019. http://archives.ismir.net/ismir2019/paper/000078.pdf ; https://github.com/music-x-lab/ISMIR2019-Large-Vocabulary-Chord-Recognition
- Park et al., "A Bi-Directional Transformer for Musical Chord Recognition", ISMIR 2019. https://arxiv.org/abs/1907.02698 ; https://github.com/jayg996/BTC-ISMIR19
- McFee, Bello, "Structured training for large-vocabulary chord recognition", ISMIR 2017. https://archives.ismir.net/ismir2017/paper/000077.pdf
- Deng, Kwok, ISMIR 2016. https://archives.ismir.net/ismir2016/paper/000058.pdf ; 2017. https://arxiv.org/abs/1709.07153
- Koops et al., "Annotator subjectivity in harmony annotations of popular music", JNMR 2019. https://pure.uva.nl/ws/files/62264010/Annotator_subjectivity_in_harmony_annotations_of_popular_music.pdf
- Phan et al., ChordMini, DAFx 2026. https://arxiv.org/abs/2602.19778 ; https://github.com/ptnghia-j/ChordMini
- ChordFormer, 2025. https://arxiv.org/abs/2502.11840
- Ding, Weiß, MIREX 2025 ACE system description. https://futuremirex.com/portal/wp-content/uploads/2025/audio-chord-estimation/wu-ensemble.pdf
- Micchi et al., "A deep learning method for enforcing coherence in automatic chord recognition", ISMIR 2021. https://archives.ismir.net/ismir2021/paper/000055.pdf
- Mitoma, Furuya, "Accuracy Improvement of Automatic Chord Recognition with Source Separation Preprocessing", APSIPA 2025. http://www.apsipa.org/proceedings/2025/papers/APSIPA2025_P307.pdf
- Ko, "Automatic chord recognition by music source separation". https://ko28.github.io/chord-transcription/
- Mauch, Noland, Dixon, "Using Musical Structure to Enhance Automatic Chord Transcription", ISMIR 2009. https://zenodo.org/records/1414844
- Mauch, Dixon, "Simultaneous Estimation of Chords and Musical Context from Audio", IEEE TASLP 2010. https://webspace.eecs.qmul.ac.uk/s.e.dixon/pub/2010/Mauch-Dixon-TASLP-2010-real.pdf
- Korzeniowski, Widmer, "Improved Chord Recognition by Combining Duration and Harmonic Language Models", ISMIR 2018. https://arxiv.org/abs/1808.05335 ; "Genre-Agnostic Key Classification with CNNs", ISMIR 2018. https://arxiv.org/abs/1808.05340
- Papadopoulos, Peeters, "Joint Estimation of Chords and Downbeats from an Audio Signal", IEEE TASLP 2011. https://hal.archives-ouvertes.fr/hal-00525172
- Cho, Bello, "On the relative importance of individual components of chord recognition systems", 2014. https://doi.org/10.1109/taslp.2013.2295926
- Temperley, de Clercq, "Statistical Analysis of Harmony and Melody in Rock Music", JNMR 2013. https://www.midside.com/publications/temperley_declercq_2013.pdf ; https://rockcorpus.midside.com/
- Albrecht, Shanahan 2013, via Nápoles López et al. 2019. https://napulen.github.io/media/justkeydding/napoles19key.pdf ; https://github.com/napulen/justkeydding
- Temperley, Bayesian key finding. https://music.informatics.indiana.edu/courses/I546/pdf/temperley.pdf ; HMM key from chords, ISMIR 2006. https://archives.ismir.net/ismir2006/paper/000091.pdf
- Key profile vectors: partitura `utils/globals.py`. https://raw.githubusercontent.com/CPJKU/partitura/main/partitura/utils/globals.py ; music21 analysis notes. https://www.music21.org/music21docs/moduleReference/moduleAnalysisDiscrete.html
- Odekerken, Koops, Volk, "DECIBEL", TISMIR 2021. https://arxiv.org/abs/2002.09748
- Magalhães, "Chordify: three years after the launch", ISMIR LBD 2015. https://www.ismir2015.uma.es/LBD/LBD42.pdf ; de Haas et al., ISMIR 2012. https://www.cs.ox.ac.uk/publications/publication6253-abstract.html
- Essentia Key. https://essentia.upf.edu/reference/std_Key.html ; licensing. https://essentia.upf.edu/licensing_information.html
- madmom chords and key docs. https://madmom.readthedocs.io/en/v0.16/modules/features/chords.html ; https://madmom.readthedocs.io/en/v0.16/modules/features/key.html
- mir_eval chord metrics. https://mir-eval.readthedocs.io/stable/api/chord.html

Beats and grid:
- Foscarin, Schlüter, Widmer, "Beat this! Accurate beat tracking without DBN postprocessing", ISMIR 2024. https://arxiv.org/abs/2407.21658 ; https://github.com/CPJKU/beat_this ; post-processor source https://raw.githubusercontent.com/CPJKU/beat_this/main/beat_this/model/postprocessor.py ; issue #13 (octave correction) https://github.com/CPJKU/beat_this/issues/13
- Smith, "Beat Critic: Beat Tracking Octave Error Identification by Metrical Profile Analysis", ISMIR 2010. https://archives.ismir.net/ismir2010/paper/000019.pdf
- Schreiber, Müller, "A Post-Processing Procedure for Improving Music Tempo Estimates Using Supervised Learning", ISMIR 2017. https://archives.ismir.net/ismir2017/paper/000137.pdf
- McKinney, Moelants, "Extracting the Perceptual Tempo from Music", ISMIR 2004. https://archives.ismir.net/ismir2004/paper/000197.pdf
- "The SMC Blind Spot: A Failure Mode Analysis of State-of-the-Art Beat Tracking", 2026. https://arxiv.org/abs/2605.12287
- BeatFM, 2025. https://arxiv.org/html/2508.09790v1
- Morais, McFee, Fuentes, "Skip That Beat", 2025. https://arxiv.org/abs/2502.12972
- Abimbola, Kostrzewa, Kasprowski, "Time Signature Detection: A Survey", Sensors 2021. https://pmc.ncbi.nlm.nih.gov/articles/PMC8512143/
- Krebs, Böck, Widmer, "Rhythmic Pattern Modeling for Beat and Downbeat Tracking", ISMIR 2013. https://archives.ismir.net/ismir2013/paper/000051.pdf
- Böck, Davies, Knees, "Multi-Task Learning of Tempo and Beat", ISMIR 2019. http://archives.ismir.net/ismir2019/paper/000058.pdf
- de Clercq, harmonic rhythm statistics for the Rolling Stone 200. https://www.midside.com/presentations/declercq_2018_smt_miig_slides.pdf
- US patent 9,653,056, "Evaluation of beats, chords and downbeats from a musical audio signal". https://patents.google.com/patent/US9653056
- Drumscore PR #116. https://github.com/simbasang/Drumscore/pull/116 ; stagehand PR #22. https://github.com/dsoto1998/stagehand/pull/22 ; Moises "The BPM is wrong". https://help.moises.ai/hc/en-us/articles/16697903875484-The-BPM-is-wrong-what-should-I-do
- madmom DBNDownBeatTrackingProcessor. https://madmom.readthedocs.io/en/v0.16/modules/features/downbeats.html ; LICENSE. https://github.com/CPJKU/madmom/blob/main/LICENSE ; Beat This! issue #9 (madmom requires Python 3.9). https://github.com/CPJKU/beat_this/issues/9
- BeatNet. https://github.com/mjhydri/BeatNet ; allin1. https://github.com/mir-aidj/all-in-one

Structure:
- McFee, Ellis, "Analyzing Song Structure with Spectral Clustering", ISMIR 2014. https://archives.ismir.net/ismir2014/paper/000319.pdf ; https://github.com/bmcfee/laplacian_segmentation
- Salamon, Nieto, Bryan, "Deep Embeddings and Section Fusion Improve Music Segmentation", ISMIR 2021. https://archives.ismir.net/ismir2021/paper/000074.pdf
- Nieto, Bello, "Systematic Exploration of Computational Music Structure Research", ISMIR 2016. https://archives.ismir.net/ismir2016/paper/000043.pdf ; MSAF https://github.com/urinieto/msaf
- Nieto et al., "Audio-Based Music Structure Analysis: Current Trends, Open Challenges, and Applications", TISMIR 2020. https://transactions.ismir.net/articles/10.5334/tismir.54
- Nieto, Farbood, Jehan, Bello, "Perceptual Analysis of the F-Measure to Evaluate Section Boundaries in Music", ISMIR 2014. https://archives.ismir.net/ismir2014/paper/000124.pdf
- Shibata et al., ISMIR 2019. https://archives.ismir.net/ismir2019/paper/000031.pdf
- Sargent, Bimbot, Vincent, "A Regularity-Constrained Viterbi Algorithm", ISMIR 2011. https://archives.ismir.net/ismir2011/paper/000105.pdf
- Marmoret, Cohen, Bimbot, "Barwise Music Structure Analysis with the Correlation Block-Matching Segmentation Algorithm", TISMIR 2023. https://arxiv.org/abs/2311.18604
- Nieto et al., "The Harmonix Set", ISMIR 2019. https://archives.ismir.net/ismir2019/paper/000068.pdf
- Wang, Smith, Chen, Song, Wang, "Supervised Chorus Detection for Popular Music", ICASSP 2021. https://arxiv.org/abs/2103.14253 ; Wang, Hung, Smith, "To Catch a Chorus, Verse, Intro, or Anything Else", ICASSP 2022. https://arxiv.org/pdf/2205.14700
- Kim, Nam, "All-In-One Metrical and Functional Structure Analysis", WASPAA 2023. https://arxiv.org/abs/2307.16425
- Buisson, McFee, Essid, LinkSeg, ISMIR 2024. https://ismir2024program.ismir.net/poster_405.html ; SongFormer, 2025. https://arxiv.org/html/2510.02797v2
- McFee, "Quantifying Regularity in Music Structure Analysis", ISMIR 2025. https://ismir2025program.ismir.net/poster_50.html
- Van Balen, Burgoyne, Wiering, Veltkamp, "An Analysis of Chorus Features in Popular Song", ISMIR 2013. https://webspace.science.uu.nl/~veltk101/publications/art/ismir2013-chorus.pdf
- Chordonomicon dataset paper. https://arxiv.org/html/2410.22046v1
- Moises Sections. https://moises.ai/newsroom/product-announcements/new-song-sections-feature/ ; Chordify Song Lessons. https://support.chordify.net/hc/en-us/articles/33951891429917-What-are-Song-Lessons
- mir_eval 0.8.2. https://mir-evaluation.github.io/mir_eval/

Strums:
- Lukoianov, Klapuri, "Transcribing Rhythmic Patterns of the Guitar Track in Polyphonic Music", 2025. https://arxiv.org/html/2510.05756v1 ; https://github.com/YousicianGit/rhythmic-pattern-transcription
- Murgul, Schimper, Heizmann, "Joint Transcription of Acoustic Guitar Strumming Directions and Chords", ISMIR 2025. https://arxiv.org/html/2508.07973 ; Murgul, Heizmann, ISMIR 2022 LBD. https://ismir2022program.ismir.net/lbd_393.html
- Dixon, Gouyon, Widmer, "Towards Characterisation of Music via Rhythmic Patterns", ISMIR 2004. https://archives.ismir.net/ismir2004/paper/000165.pdf
- McFee, Ellis, "Better Beat Tracking Through Robust Onset Aggregation", ICASSP 2014. https://brianmcfee.net/papers/icassp2014_beats.pdf
- Böck, Widmer, SuperFlux, DAFx 2013. https://dafx.de/paper-archive/details/0oee-99Z88WL7pSo749gcA
- Reboursière et al., "Left and right-hand guitar playing techniques detection", NIME 2012. https://nime.org/proceedings/2012/nime2012_213.pdf
- librosa `onset_detect`. https://librosa.org/doc/0.10.2/generated/librosa.onset.onset_detect.html
- MERT-v1-95M model card. https://portrait.gitee.com/modelee/MERT-v1-95M ; madmom NumPy breakage issue #527. https://github.com/CPJKU/madmom/issues/527
- UkuTabs strumming patterns. https://ukutabs.com/ukulele-guides/ukulele-strumming-patterns-beginners/ ; Roadie Music. https://www.roadiemusic.com/blog/5-ukulele-strumming-patterns-for-beginners/
- Chordify, "Does Chordify show the strumming patterns?". https://support.chordify.net/hc/en-us/articles/360019489618-Does-Chordify-show-the-strumming-patterns- ; Ultimate Guitar, "Strumming patterns". https://help.ultimate-guitar.com/en/articles/6744662-strumming-patterns-how-to-read-play
- IDMT-SMT-Guitar. https://www.idmt.fraunhofer.de/en/publications/datasets/guitar.html ; GuitarSet, ISMIR 2018. https://archives.ismir.net/ismir2018/paper/000188.pdf

Arrangement and separation:
- DadaGP chord diagram study. https://arxiv.org/pdf/2407.14260 ; Fretting-Transformer. https://arxiv.org/pdf/2506.14223
- MoisesDB (six-stem SDR). https://ar5iv.labs.arxiv.org/html/2307.15913 ; Demucs README. https://github.com/facebookresearch/demucs ; MVSEP guitar leaderboard. https://mvsep.com/quality_checker/leaderboard/guitar ; python-audio-separator. https://github.com/nomadkaraoke/python-audio-separator
- Amadeus ChordZart minimum duration. https://amadeus-chordzart.readthedocs.io/en/stable/pipeline/chord_detection.html
- Moises Guitar Capo Mode. https://moises.ai/features/guitar-capo-mode/ ; Hooktheory review of Chordify alternatives. https://www.hooktheory.com/blog/chordify-alternatives/ ; Ultimate Guitar Pro features. https://help.ultimate-guitar.com/en/articles/6741560-what-do-i-get-if-i-subscribe-to-pro ; iReal Pro chart layout. https://www.irealpro.com/learn/chart-layout
- Live Ukulele: capos https://liveukulele.com/lessons/theory/transposing/capos/ ; hard chords https://liveukulele.com/chords/hard-chords/ ; slash chords https://liveukulele.com/chords/ukulele-slash-chords/
- UkuTabs: E chord https://ukutabs.com/ukulele-guides/ukulele-e-chord/ ; simplify tips https://ukutabs.com/ukulele-guides/simplify-difficult-ukulele-chords-5-quick-tips/ ; keys https://ukutabs.com/ukulele-keys/
- capo-calc (MIT). https://github.com/nobodywasishere/capo-calc ; ukechords. https://github.com/nickurak/ukechords
