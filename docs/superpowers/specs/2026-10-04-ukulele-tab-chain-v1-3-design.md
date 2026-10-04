# Youkelele tab chain, version 1.3: design

Date: 2026-10-04. Status: approved in conversation, awaiting written review. Amends `2026-10-03-ukulele-tab-chain-v1-2-design.md`. Evidence: `2026-10-03-v1-2-validation.md` ("What to improve next", items 1 and 2), `../research/2026-10-03-quality/README.md` (ranks 1, 2, 4 and 18), and two spikes run on this machine on 2026-10-04 (section 8).

## 1. Purpose

Version 1.2 made the sheet compact and filled its gaps. Its validation named the strum box as the largest visible fault for the second version running: three of five songs print "certain" boxes that are three quarters rests, one prints a single down stroke as a whole chorus, and one gets no box at all. Version 1.3 makes the strum box trustworthy and puts chord changes on the bar lines, and it adds the measurement harness that every later version needs, so that each change ships with a before-and-after table rather than a reading of the pages.

## 2. Scope

In: a truth-free measurement harness with a run-to-run compare; the strike vote and the `explained` figure; recovery of strums in loud sustained sections; dropping trailing non-song bars; beat-aware chord decoding. Out: the key mode (validation item 3), earlier phrase shifts (item 4), fill refinement (item 5), section naming (item 6), the strum stem switch (refuted by ear, section 8), separating two guitars in one stem (Pour Some Sugar On Me stays uncertain).

## 3. What the ear check established

The owner listened to nine separated-stem clips on 2026-10-04. On every section where the research proposed switching the strum source to the `other` stem, that stem was a keyboard (Summer of '69, both choruses; Pour Some Sugar On Me, last chorus, with vocal bleed), or noise that is not music (Wet Leg, outro bars 108 to 112). The strummed guitar was in the `guitar` stem every time, and in Summer of '69's choruses it is sustained, distorted power chords that today's detector hears at 1.8 to 2.9 strikes per bar against about 6 in the verse. Pour Some Sugar On Me's `guitar` stem holds two guitars at once, one strumming and one playing a single-note riff. The Chelsea Dagger control (`other`, near silence) was bleed, as the numbers said.

Consequences: the fault is detector recall on the right stem, not stem routing; a "no strummed instrument" rescue to `other` would print traffic noise as a pattern; the trailing Wet Leg bars should be dropped, not analysed.

## 4. Stage changes

### 4.1 Evaluate: the measurement harness

`youkelele evaluate <run>` works on any run folder with no `--truth`. `Report` gains truth-free fields computed from the run's artefacts:

- Chords, from `03_harmony/chords.json` and `02_grid/grid.json`: `n_share` (N time over total time), `all_n_bars`, `filled_bars`, `changes_on_bar_share` (changes whose start is within 60 ms of a bar start, over all changes), `sub_beat_events` (events shorter than one beat), `key_confidence`.
- Strums, from `04_strums/strums.json`: per section `strikes_per_bar`, `explained`, `rest_share` of the printed pattern, `uncertain`, `recall_boost`; song totals `boxes_mostly_rests` (sections printed as certain with 75 percent or more rests).
- Existing truth-based fields are filled only when `--truth` is given.

`evaluate <run> --compare <other run>` scores two runs against each other: `mir_eval.chord` over-segmentation, under-segmentation and majmin agreement between the two `chords.json`, and the strum fields side by side per section with their differences. This is the regression guard for every change in this version: the kept 1.2 run folders against the new ones.

`youkelele run ... --debug` (a stage option merged through the manifest like the others) makes the strums stage also write `04_strums/onsets.txt`, one detected onset per line in Audacity label-track format (`start<TAB>end<TAB>label`, label `S` or `x`, with `+` appended for an onset added by the recall gate). The grid stage writes `02_grid/beats_raw.json` (the detected beats and downbeats before gap filling and octave normalisation, and the lists of inserted and dropped beats). The harmony stage keeps the model's raw output as `03_harmony/spans.lab` beside `chords.json`.

Out: section truth and strum onset truth files. The harness accepts them in a later version; nothing in 1.3 writes them.

### 4.2 Strums: the strike vote and `explained`

`majority_vector(bars, threshold)` marks a slot struck when strictly more than `STRIKE_SHARE = 1/3` of the section's bars strike it (was more than half). A density floor follows: `floor = round(DENSITY_FLOOR x median strikes per bar)` with `DENSITY_FLOOR = 0.6`; while the voted pattern has fewer strikes than the floor, the unstruck slot with the highest strike rate is added. The mute decision per slot is unchanged (`x` when more than half of that slot's strikes are muted). Directions follow the beat as today.

`explained_onsets(bars, vector) -> float` is the share of the section's detected strikes that fall on a slot the pattern strikes. It is the one measure that separates the boxes the validation called wrong (0.31 to 0.57) from the usable ones (0.69 to 1.00); mean Jaccard, today's `confidence`, does not.

`uncertain = confidence < UNCERTAIN_BELOW (0.45) or explained < EXPLAINED_BELOW (0.6) or the section is shorter than four bars`. `bar_repeat` stays in `strums.json` for diagnostics and leaves the sheet.

Both changes can only add strikes, so the dense songs (Wet Leg at 8 slots, Fame at 16) cannot get sparser; the harness confirms it.

### 4.3 Strums: recall in loud sustained sections

Measured by the recall spike (section 8) and confirmed by ear: today's single global threshold on a full-band onset-strength envelope is set by the sharpest attacks in the song (a palm-muted chug), and the re-attacks of a ringing distorted chord fall under it. Nothing applied to the whole song fixes this without changing the dense songs, so the fix is gated per section.

After today's detection, the stage computes a second onset list from a high-band envelope: `librosa.onset.onset_strength(y, sr, hop_length=512, fmin=HIGH_BAND_FMIN, aggregate=np.mean)` with librosa's default peak picker, `HIGH_BAND_FMIN = 3000` (stable from 2500 to 4000; 2000 fails). For each section where today's strikes per bar are below `SPARSE_SHARE x slots_per_bar`, `SPARSE_SHARE = 0.4`, the high-band onsets not within `MERGE_MS = 60` ms of an existing onset are added, and the union is kept only when all four hold: strikes per bar rise by at least `MIN_GAIN = 1.0`; the section's mean Jaccard to its own vote does not fall; raw onsets per bar stay at or under `slots_per_bar`; the section's grid fit stays at or above the song's fit minus `FIT_TOLERANCE = 0.05`. Otherwise the section keeps today's onsets. `SectionPattern.recall_boost: bool = False` records a kept union. The mute rule's medians are computed on the final onset list.

Measured effect on the 1.2 runs: Summer of '69 choruses 2.9 to 5.2 and 1.8 to 4.6 strikes per bar, patterns `S-SSSSS-` with `explained` 0.95 and 0.96; verse 1 unchanged; Wet Leg and Fame onsets identical; Chelsea Dagger choruses 2.8 to 4.4 and 2.6 to 5.0; Pour Some Sugar On Me choruses 3.4 to 5.8 up to 8.8 to 9.5 per 16-slot bar (possibly the riff guitar; checked by ear before merging, section 7); song grid fit moves by at most 0.011.

### 4.4 Score: trailing bars that are not music

After the last chord event that is not `N` (filled events count), any remaining bars that are entirely `N` are dropped from the score: the last section's `end_bar` shrinks, and the strum analysis of that section ignores them. `Score.trailing_bars_dropped: int = 0` records the count; `grid.json` and `chords.json` are unchanged. Evidence: Wet Leg bars 109 to 112 are traffic-like noise (ear check) and fill its third page on their own; Summer of '69 bar 120 and Fame bar 100 are ring-outs no player needs. Leading bars are untouched.

### 4.5 Harmony: beat-aware chord decoding

The vendored Chord-CNN-LSTM's decoder accepts beat and downbeat positions; our entry point passes `False` for both. 1.3 adds `models/chord_driver.py`, run in the child process in place of `chord_recognition.py`, which builds the model's data entry as that script does, attaches a beat file, and decodes with `use_beats=True, use_downbeats=True` at the model's default penalties. No patch to the vendored code.

`recognise_chords(wav, work_dir, log, beats=None)` takes an optional list of `(time, position_in_bar)` pairs; the harmony stage derives it from the gap-filled `grid.beats` and each beat's 1-based position in its bar. The driver writes the model's headerless tab format (time, running index, position) to `work_dir/beats.lab`; the model reads only the time and position columns. A pickup bar's single beat is numbered as the last position of the bar (4 in 4/4), not 1, so it is not taken as a downbeat. Beats outside the audio are dropped by the model. With `beats=None` the driver decodes as today, so the fake-recogniser tests are unchanged. `ctx.note("decoding", "beats+downbeats")`.

Measured by the decoding spike (section 8) on Summer of '69: changes on bar starts 63 of 75 to 75 of 75, the same 76-event label sequence, N share unchanged, 0.6 s more. `snap_to_beats` still runs afterwards as the safety net; the research refuted the "model lag" the snap was built on (boundaries are early by 27 to 44 ms, not late), so no fixed shift is added.

## 5. The sheet

- The strum box line becomes "Strum heard in this section; covers NN% of detected strokes. Up and down follow the beat", with "(uncertain)" and "same as <label>" kept as today. "NN% repeatable" goes.
- Nothing marks a section whose recall gate fired; the pattern is what the sheet owes the reader.
- Dropped trailing bars do not print.

## 6. Data format changes

`SectionPattern.explained: float = 0.0`, `SectionPattern.recall_boost: bool = False`, `ScoreSection.explained: float = 0.0`, `Score.trailing_bars_dropped: int = 0`; new optional artefacts `02_grid/beats_raw.json`, `03_harmony/spans.lab`, `04_strums/onsets.txt` (with `--debug`). Schema version stays 1; version 1.2 files load.

## 7. Validation

Keep the five 1.2 run folders as the baseline (copy before re-running). Re-run the five songs from their URLs and compare each with `evaluate --compare`.

| Song | Expectation |
|---|---|
| Summer of '69 | both chorus boxes dense (`S-SSSSS-` or denser) and certain; verse 1 unchanged; chord changes on bar starts 75 of 75; tempo header still 139 |
| Chelsea Dagger | chorus boxes no longer mostly rests; the chorus click clip confirmed by ear before merging; on-bar changes rise from 54 of 68 |
| Pour Some Sugar On Me | sub-beat events gone; the chorus click clip judged by ear (riff or strum) and the outcome recorded, whichever way it falls; capo 4 kept |
| Wet Leg "mangetout" | onsets and patterns identical to 1.2; trailing bars dropped; two pages |
| David Bowie "Fame" | onsets and patterns identical to 1.2; bar 100 dropped; the chain completes |
| All | `boxes_mostly_rests` 4, 4, 4, 1, 0 falls to at most 0, 1, 2, 0, 0; `evaluate <run>` works with no truth; `evaluate --compare` of a run with itself gives identity; chord label sets unchanged except removed slivers; no section gets sparser |

## 8. Spikes run for this design

- **Beat-aware decoding** (`scratchpad/spike_beats`): the vendored decoder accepts our beat file through `entry.append_file(beats, BeatLabIO, "beat")`; Summer of '69 63 of 75 to 75 of 75 on-bar changes, identical labels, +0.6 s. Gotchas carried into 4.5.
- **Strum recall** (`scratchpad/spike_recall`, config `G_f3000_g0.4_union`): the gated high-band union of 4.3 is the only candidate that recovered the choruses while leaving Wet Leg and Fame identical. Failed: bar-local contrast on the full-band envelope (re-attacks only 1.1 to 1.4 times the inter-beat level); a lowered threshold per section (adds off-beat noise before strums); `aggregate=np.max` (triples onsets, fit about 0.45); any whole-song change (alters all eight Fame sections). Click tracks of Summer of '69's first chorus and first verse were judged by ear: today's clicks correct but sparse, the winner's "pretty much perfect", the verse unharmed.

## 9. Decisions

- Harness first, so every later change is a table.
- Recall is recovered per section with a gate, never by a whole-song detector change, because the dense songs are already right.
- The strum source stays song-level; density in `other` is not evidence of a strum.
- Trailing non-music bars are dropped in the score stage, leaving the grid and harmony artefacts intact for hand editing.
- Constants are measured, not guessed, and their spike evidence is recorded beside them.
