# Youkelele tab chain, version 1.3: design

Date: 2026-10-04. Status: approved in conversation, awaiting written review. Amends `2026-10-03-ukulele-tab-chain-v1-2-design.md`. Evidence: `2026-10-03-v1-2-validation.md` ("What to improve next", items 1 and 2), `../research/2026-10-03-quality/README.md` (ranks 1, 2, 4 and 18), and two spikes run on this machine on 2026-10-04 (section 8).

## 1. Purpose

Version 1.2 made the sheet compact and filled its gaps. Its validation named the strum box as the largest visible fault for the second version running: three of five songs print "certain" boxes that are three quarters rests, one prints a single down stroke as a whole chorus, and one gets no box at all. Version 1.3 makes the strum box trustworthy and puts chord changes on the bar lines, and it adds the measurement harness that every later version needs, so that each change ships with a before-and-after table rather than a reading of the pages.

## 2. Scope

In: a truth-free measurement harness with a run-to-run compare; the strike vote and the `explained` figure; recovery of strums in loud sustained sections; dropping trailing non-song bars; beat-aware chord decoding; a worked example on the sheet tying each section's pattern to its chords. Out: the key mode (validation item 3), earlier phrase shifts (item 4), fill refinement (item 5), section naming (item 6), the strum stem switch (refuted by ear, section 8), separating two guitars in one stem (Pour Some Sugar On Me stays uncertain).

## 3. What the ear check established

The owner listened to nine separated-stem clips on 2026-10-04. On every section where the research proposed switching the strum source to the `other` stem, that stem was a keyboard (Summer of '69, both choruses; Pour Some Sugar On Me, last chorus, with vocal bleed), or noise that is not music (Wet Leg, outro bars 108 to 112). The strummed guitar was in the `guitar` stem every time, and in Summer of '69's choruses it is sustained, distorted power chords that today's detector hears at 1.8 to 2.9 strikes per bar against about 6 in the verse. Pour Some Sugar On Me's `guitar` stem holds two guitars at once, one strumming and one playing a single-note riff. The Chelsea Dagger control (`other`, near silence) was bleed, as the numbers said.

Consequences: the fault is detector recall on the right stem, not stem routing; a "no strummed instrument" rescue to `other` would print traffic noise as a pattern; the trailing Wet Leg bars should be dropped, not analysed.

A second listening session judged click tracks (a click at every detected strike) for today's detector and the recall spike's winner (section 8): Summer of '69 chorus 1, today's clicks correct but sparse, the winner's "pretty much perfect", the verse unharmed; Chelsea Dagger chorus, the winner's clicks match the strums once the guitar enters but two or three clicks fall in the silent bars before it; Pour Some Sugar On Me last chorus, today's clicks cannot follow the two parts and the winner over-clicks: with one guitar on power chords and another soloing over it there is no strumming pattern to extract. Those two verdicts are the guards in 4.3.

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

Known deviation: a slot added by the density floor is always `S`; the per-slot mute rule is not applied to it, so a floor slot whose strikes are mostly muted prints as a stroke rather than `x`. It is left for the next version because applying the rule could change patterns on all five validation songs and invalidate the 1.3 validation.

`explained_onsets(bars, vector) -> float` is the share of the section's detected strikes that fall on a slot the pattern strikes. It is the one measure that separates the boxes the validation called wrong (0.31 to 0.57) from the usable ones (0.69 to 1.00); mean Jaccard, today's `confidence`, does not.

`uncertain = confidence < UNCERTAIN_BELOW or explained < EXPLAINED_BELOW (0.6) or the section is shorter than four bars`, where `UNCERTAIN_BELOW` is 0.45 on the eighth-note grid and `UNCERTAIN_BELOW_SIXTEENTH = 0.55` on the sixteenth grid; the strums stage chooses with `eighth_grid(slots_per_bar, meter)`, the same test the recall gate uses. The second value was measured at validation and set by the owner after the whole-branch review: with the third-share vote, Pour Some Sugar On Me's two-guitar sections (16 slots) reached confidence 0.453 to 0.472 and printed as certain, while every certain section of the other sixteenth-grid song (Fame) sits at 0.625 or above, and 0.55 is the midpoint. 0.50 was rejected: a random 16-slot spray striking half the slots has a median confidence of 0.527, so 0.50 would pass noise. On the eighth grid the nearest good sections (Wet Leg verse 0.458, Summer of '69 verse 2 0.470) must stay certain, so one threshold for both grids does not exist. At 16 slots a dense two-part spray strikes many slots and inflates the mean Jaccard. Measured on two sixteenth-grid songs; recorded as such. `bar_repeat` stays in `strums.json` for diagnostics and leaves the sheet.

Known limitation: neither threshold is a test for noise. A dense two-part or noisy section can pass the certainty test on either grid, because the third-share vote keeps most of a dense spray's slots, so `explained` is high and the mean Jaccard is inflated. The whole-branch review measured random sprays striking each slot with probability one half: 85 percent print certain at 8 slots with 0.45, and 69 percent at 16 slots with 0.50. Fewer pass at 0.55, but not none (re-measured for this note on 2000 random eight-bar sections: 30 percent at 16 slots). The next version should replace the bare mean Jaccard with a chance-corrected confidence: the mean Jaccard against the section's own vote, less the same figure for a slot-shuffled baseline at the same density.

Both changes can only add strikes, so the dense songs (Wet Leg at 8 slots, Fame at 16) cannot get sparser; the harness confirms it.

### 4.3 Strums: recall in loud sustained sections

Measured by the recall spike (section 8) and confirmed by ear: today's single global threshold on a full-band onset-strength envelope is set by the sharpest attacks in the song (a palm-muted chug), and the re-attacks of a ringing distorted chord fall under it. Nothing applied to the whole song fixes this without changing the dense songs, so the fix is gated per section.

After today's detection, the stage computes a second onset list from a high-band envelope: `librosa.onset.onset_strength(y, sr, hop_length=512, fmin=HIGH_BAND_FMIN, aggregate=np.mean)` with librosa's default peak picker, `HIGH_BAND_FMIN = 3000` (stable from 2500 to 4000; 2000 fails). For each section where today's strikes per bar are below `SPARSE_SHARE x slots_per_bar`, `SPARSE_SHARE = 0.4`, the high-band onsets not within `MERGE_MS = 60` ms of an existing onset are added, except in bars whose stem RMS is below `SILENT_BAR_SHARE` of the section's median bar RMS (so nothing is added where the instrument has not entered; `SILENT_BAR_SHARE` is measured in implementation on Chelsea Dagger's chorus, whose first three bars are silent). The gate applies only on the eighth-note grid (`slots_per_bar == meter.numerator * 2`). The union is kept only when all four hold: strikes per bar rise by at least `MIN_GAIN = 1.0`; the section's mean Jaccard to its own vote does not fall; raw onsets per bar stay at or under `slots_per_bar`; the section's grid fit stays at or above the song's fit minus `FIT_TOLERANCE = 0.05`. Otherwise the section keeps today's onsets. `SILENT_BAR_SHARE = 0.25` (Chelsea Dagger's silent bars 9 to 11 sit at 0.135 and below; the quietest struck bar in any accepted section is at 0.446; any value from 0.15 to 0.40 gives the same patterns).

Why the eighth-note restriction rather than a regularity guard: a second spike (section 8) measured every onset-level quantity that might tell a recovered strum from two guitars in one stem, on the union the gate produces. None separates the ear-accepted sections (Summer of '69 bars 41-53 and 83-95, Chelsea Dagger 9-38 and 105-142) from the ear-rejected ones (Pour Some Sugar On Me 28-39, 55-67, 84-103) with a usable margin: the union's own `explained` overlaps (accepted 0.88 to 0.98, rejected 0.87 to 0.94), mean Jaccard separates by 0.008, the bar-to-bar variability of onset counts by 0.012, and the gain ratio overlaps exactly (1.59 on both sides). What does separate them is the grid: the rejected song runs sixteenths. The restriction is a stated limitation (a sixteenth-grid song with sustained strums is not recovered in this version) rather than a guess dressed as a threshold. `SectionPattern.recall_boost: bool = False` records a kept union. The mute rule's medians are computed on the final onset list.

Measured effect on the 1.2 runs before the two new guards: Summer of '69 choruses 2.9 to 5.2 and 1.8 to 4.6 strikes per bar, patterns `S-SSSSS-` with `explained` 0.95 and 0.96; verse 1 unchanged; Wet Leg and Fame onsets identical; Chelsea Dagger choruses 2.8 to 4.4 and 2.6 to 5.0 (right by ear, apart from the pre-entry clicks the silent-bar guard removes); Pour Some Sugar On Me choruses 3.4 to 5.8 up to 8.8 to 9.5 per 16-slot bar, which the ear check rejected and the regularity guard must reject; song grid fit moves by at most 0.011.

### 4.4 Score: trailing bars that are not music

After the last chord event that is not `N` (filled events count), any remaining bars that are entirely `N` are dropped from the score: the last section's `end_bar` shrinks, and the strum analysis of that section ignores them. `Score.trailing_bars_dropped: int = 0` records the count; `grid.json` and `chords.json` are unchanged. Evidence: Wet Leg bars 109 to 112 are traffic-like noise (ear check) and fill its third page on their own; Summer of '69 bar 120 and Fame bar 100 are ring-outs no player needs. Leading bars are untouched.

### 4.5 Harmony: beat-aware chord decoding

The vendored Chord-CNN-LSTM's decoder accepts beat and downbeat positions; our entry point passes `False` for both. 1.3 adds `models/chord_driver.py`, run in the child process in place of `chord_recognition.py`, which builds the model's data entry as that script does, attaches a beat file, and decodes with `use_beats=True, use_downbeats=True` at the model's default penalties. No patch to the vendored code.

`recognise_chords(wav, work_dir, log, beats=None)` takes an optional list of `(time, position_in_bar)` pairs; the harmony stage derives it from the gap-filled `grid.beats` and each beat's 1-based position in its bar. The driver writes the model's headerless tab format (time, running index, position) to `work_dir/beats.lab`; the model reads only the time and position columns. A pickup bar's single beat is numbered as the last position of the bar (4 in 4/4), not 1, so it is not taken as a downbeat. Beats outside the audio are dropped by the model. With `beats=None` the driver decodes as today, so the fake-recogniser tests are unchanged. `ctx.note("decoding", "beats+downbeats")`.

Measured by the decoding spike (section 8) on Summer of '69: changes on bar starts 63 of 75 to 75 of 75, the same 76-event label sequence, N share unchanged, 0.6 s more. `snap_to_beats` still runs afterwards as the safety net; the research refuted the "model lag" the snap was built on (boundaries are early by 27 to 44 ms, not late), so no fixed shift is added.

## 5. The sheet

- The strum box line becomes "Strum heard in this section; covers NN% of detected strokes. Up and down follow the beat", with "(uncertain)" kept as today. "NN% repeatable" goes. NN is truncated, not rounded, so a figure under the 60 percent threshold never prints as 60. A section whose pattern is inherited prints "Strum as in <label> (uncertain)" instead, without the covers clause: an inherited pattern's `explained` is the donor's, not a figure for the section's own strokes.
- Nothing marks a section whose recall gate fired; the pattern is what the sheet owes the reader.
- Dropped trailing bars do not print.
- **The worked example.** The box and the grid were unrelated: the box gave a pattern and the grid gave chords, and nothing said on which stroke a chord change falls. Each section's strum box becomes a two-bar strip, drawn in the box's SVG style, that shows the stroke row with its beat labels (D, U, -, x per slot, as the one-bar box drew them) over a chord row in which each chord name sits at the slot it starts on (`ScoreChord.start_slot`) with dots for the slots it holds, and a bar line between the bars. The strip replaces the one-bar box rather than sitting under it: measured during implementation, keeping both pushed Chelsea Dagger and Fame to an extra page, while the strip alone keeps every validation song within its page budget, and the strip's first bar carries everything the box did. The bars shown are the section's first two full bars (a pickup bar is skipped); if neither has a change inside the bar and a later bar in the section does, that bar replaces the second, so a section with half-bar changes always shows one. The strip has the box's visibility: sections with no strummed instrument, and sections whose pattern is uncertain (which includes every inherited pattern), keep their label line and show no strip, exactly as they showed no box; a pattern the stage does not trust is not drawn over the chords. The slot width is one per song, 28 px per slot up to 8 slots and 20 px above, so a 16-slot two-bar strip fits the text width (measured: 908 px at 28 px overflows the 688 px text width; 652 px at 20 px fits). Render-only: no new data.

## 6. Data format changes

`SectionPattern.explained: float = 0.0`, `SectionPattern.recall_boost: bool = False`, `ScoreSection.explained: float = 0.0`, `Score.trailing_bars_dropped: int = 0`; new artefacts `02_grid/beats_raw.json` and `03_harmony/spans.lab` (written on every run) and `04_strums/onsets.txt` (only with `--debug`). Schema version stays 1; version 1.2 files load.

## 7. Validation

Keep the five 1.2 run folders as the baseline (copy before re-running). Re-run the five songs from their URLs and compare each with `evaluate --compare`.

| Song | Expectation |
|---|---|
| Summer of '69 | both chorus boxes dense (`S-SSSSS-` or denser) and certain; verse 1 unchanged; chord changes on bar starts 75 of 75; tempo header still 139 |
| Chelsea Dagger | chorus boxes no longer mostly rests; no added onsets in the silent bars before the guitar enters; on-bar changes rise from 54 of 68 |
| Pour Some Sugar On Me | sub-beat events gone; the recall gate does not fire on its choruses (two guitars in one stem, judged by ear) and every section stays uncertain as today; capo 4 kept |
| Wet Leg "mangetout" | onsets and patterns identical to 1.2; trailing bars dropped; two pages |
| David Bowie "Fame" | onsets and patterns identical to 1.2; bar 100 dropped; the chain completes |
| All | `boxes_mostly_rests` 4, 4, 4, 1, 0 falls to at most 0, 1, 2, 0, 0; `evaluate <run>` works with no truth; `evaluate --compare` of a run with itself gives identity; chord label sets unchanged except removed slivers; no section gets sparser; every section with a certain pattern shows the strip and no uncertain section does; on Fame's verses (half-bar Dm to Am and Am to G changes) the strip shows the second chord at its stroke |

## 8. Spikes run for this design

- **Beat-aware decoding** (`scratchpad/spike_beats`): the vendored decoder accepts our beat file through `entry.append_file(beats, BeatLabIO, "beat")`; Summer of '69 63 of 75 to 75 of 75 on-bar changes, identical labels, +0.6 s. Gotchas carried into 4.5.
- **Strum recall** (`scratchpad/spike_recall`, config `G_f3000_g0.4_union`): the gated high-band union of 4.3 is the only candidate that recovered the choruses while leaving Wet Leg and Fame identical. Failed: bar-local contrast on the full-band envelope (re-attacks only 1.1 to 1.4 times the inter-beat level); a lowered threshold per section (adds off-beat noise before strums); `aggregate=np.max` (triples onsets, fit about 0.45); any whole-song change (alters all eight Fame sections). Click tracks of Summer of '69's first chorus and first verse were judged by ear: today's clicks correct but sparse, the winner's "pretty much perfect", the verse unharmed. Click tracks of Chelsea Dagger's and Pour Some Sugar On Me's choruses were judged afterwards (section 3); the spike's gate had accepted both sections.
- **Gate constants** (`scratchpad/spike_recall2`): measured `SILENT_BAR_SHARE` (0.25, margins in 4.3) and tested five candidate regularity guards against the ear verdicts (union `explained`, mean Jaccard, count variability as coefficient of variation and as share of bars off the median by 25 percent, gain ratio). None separates with a usable margin; the eighth-note grid does. The tables are copied into `2026-10-04-v1-3-recall-measurements.md` during implementation.

## 9. Decisions

- Harness first, so every later change is a table.
- Recall is recovered per section with a gate, never by a whole-song detector change, because the dense songs are already right.
- The strum source stays song-level; density in `other` is not evidence of a strum.
- Trailing non-music bars are dropped in the score stage, leaving the grid and harmony artefacts intact for hand editing.
- Constants are measured, not guessed, and their spike evidence is recorded beside them.
