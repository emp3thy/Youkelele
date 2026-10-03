# Strumming pattern and rhythm extraction: research applied to the codebase

Date: 2026-10-03. Input: `research/strums-research.md` (this scratchpad). Code read: `src/youkelele/music/onsets.py`, `music/as_played.py`, `stages/strums.py`, `render/strum_box.py`, `render/html.py`, `render/templates/sheet.html.j2`, `music/score_builder.py`, `schemas.py`, `music/backbeat.py`, `evaluate.py`, and the tests `tests/test_onsets.py`, `test_as_played.py`, `test_stage_strums.py`. Runs read: `runs/{sexhetcxqy4,9f06qzcvuhg,0uib9y4ofps,lbc6ccztp5e}/{00_ingest,01_separate,02_grid,04_strums}`. All file:line pointers are into the main checkout at `C:\Users\gethi\sources\Youkelele` (identical to the v1.2 worktree for these files; the v1.2 branch does not touch the strums stage).

Every research claim was tested against the real stems with read-only scripts in `research/apply/` (`stats.py`, `experiments.py`, `experiments2.py`, `experiments3.py`, run with the project venv). The scripts replicate `detect_onsets` exactly (librosa 1.0.0 `onset_detect`, hop 512, `normalize=True`, `delta` 0.07) and then vary one thing at a time. Where I say "measured" below it means the number came out of those scripts today; "from strums.json" means it was recomputed from the shipped artefact.

## 0. Summary

Of the ten research easy wins, **four regress or do nothing when run on the actual stems** (median/SuperFlux onset strength, section-relative peak picking, the drum veto, the decay-based mute feature) and are discarded with numbers in section 3. **One finding the research missed turned out to be the largest**: Summer of '69's chorus recall collapse is not a threshold problem, it is separation routing. In the choruses and outro the `other` stem carries 6.1 to 7.9 regular strikes per bar (Jaccard 0.76 to 0.98) while the `guitar` stem that `choose_source` picks for the whole song carries 1.8 to 3.5. The same thing makes the Wet Leg outro print "No strummed instrument detected" although `other` has RMS 0.82 of the mix there.

The ordered list (impact per effort):

| # | Improvement | Effort | Impact | Confidence |
|---|---|---|---|---|
| 1 | Strike threshold > 1/3 with a density floor, plus `explained_onsets` as the uncertainty flag | small | high | 85 |
| 2 | Per-section source choice between `guitar` and `other`, including the no-instrument rescue | medium | high | 65 |
| 3 | One pattern per section label (pooled bars), per-section box only when it disagrees | small | medium | 75 |
| 4 | Sheet wording: "covers N% of detected strokes", drop the repeatability percentage | small | medium | 90 |
| 5 | Strum onset ground truth for 30 s of each validation song and `evaluate` support | medium | high (enabling) | 85 |
| 6 | `nearest_named` label from the UkuTabs/Roadie list, printed as a hint | small | low | 80 |
| 7 | Grid phase offset: shift bars by the median onset deviation before quantising | small | low | 70 |
| 8 | Accents from the detrended envelope | small | low | 45 |
| 9 | Swing grid (12 slots per bar) | large | low today | 60 |
| 10 | Trained CRNN strum detector on synthetic ukulele/guitar stems | large | high | 55 |

Already in progress (version 1.2) and skipped here: four-bar minimum sections (which already removes 17 of Wet Leg's 25 sections from the inheritance path), mean tempo, title cleaning, chroma filling, passing chords, phrase alignment, repeated row blocks.

## 1. What the runs show today (from strums.json and grid.json)

| Song | bpm | source (ratio) | slots | grid fit | stage uncertain | sections | uncertain | boxes 75%+ rests | mean rest share | strikes/bar | mute share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Chelsea Dagger `sexhetcxqy4` | 157.9 | guitar 0.39 | 8 | 0.55 | yes | 8 | 1 | 4 | 0.66 | 3.17 | 0.10 |
| Summer of '69 `9f06qzcvuhg` | 136.4 | guitar 0.39 | 8 | 0.91 | no | 11 | 4 | 4 | 0.56 | 3.94 | 0.23 |
| Pour Some Sugar On Me `0uib9y4ofps` | 85.7 | guitar 0.29 | 16 | 0.59 | yes | 7 | 7 | 4 | 0.80 | 5.47 | 0.09 |
| Wet Leg `lbc6ccztp5e` | 130.4 | guitar 0.20 | 8 | 0.73 | no | 25 | 19 (17 for being under 4 bars) | 1 | 0.23 | 5.96 | 0.18 |

The four boxes the validation called wrong, with per-slot strike rates (share of bars with an onset in the slot), from `bar_onsets`:

| Section | bars | pattern printed | confidence | rates |
|---|---|---|---|---|
| Chelsea sec 1 chorus (9 to 38) | 29 | `--D---D-` | 0.46, printed as certain | 0.41 0.00 0.86 0.10 0.45 0.17 0.62 0.14 |
| Chelsea sec 6 bridge (99 to 105) | 6 | `--D---D-` | 0.47 | 0.33 0.00 1.00 0.50 0.50 0.17 0.83 0.50 |
| Chelsea sec 7 chorus (105 to 142) | 37 | `--D-D---` | 0.45 | 0.46 0.03 0.81 0.05 0.54 0.05 0.46 0.19 |
| S69 sec 8 chorus (83 to 95) | 12 | `D-------` | 0.53 | 0.83 0.08 0.25 0.25 0.08 0.00 0.25 0.08 |

Slots struck in 41 to 54% of bars (Chelsea beats 1 and 3) are erased by the strict `> n/2` test in `majority_vector` (`as_played.py:49`). S69 sec 8 is different: only 1.8 strikes per bar are detected at all, so no threshold on these onsets can recover it (section 2.2 explains why).

## 2. Improvements

### 2.1 Strike threshold > 1/3 with a density floor, and `explained_onsets` as the uncertainty flag

**Touches.** `src/youkelele/music/as_played.py:40-53` (`majority_vector`), `:63-71` (`section_summary`), `:17` (`UNCERTAIN_BELOW`); `src/youkelele/stages/strums.py:81-87` (pattern construction, `uncertain=`); `src/youkelele/schemas.py:135-142` (`SectionPattern`, new field), `:220-227` (`ScoreSection`, new field); `src/youkelele/music/score_builder.py:144-149` (copy the field); tests `tests/test_as_played.py:39-57` (`test_majority_vector_needs_more_than_half_the_bars` asserts the old rule and must change).

**Evidence (measured, baseline onsets, > 1/3 vote plus a floor of `round(0.6 x median strikes per bar)` filled from the highest-rate slots).**

| Section | > 1/2 today | explained | > 1/3 + floor | explained | Jaccard of new vector |
|---|---|---|---|---|---|
| Chelsea sec 1 chorus | `--S---S-` | 0.54 | `S-S-S-S-` | 0.85 | 0.55 |
| Chelsea sec 6 bridge | `--S---S-` | 0.48 | `--SSS-SS` | 0.87 | 0.62 |
| Chelsea sec 7 chorus | `--S-S---` | 0.52 | `S-S-S-S-` | 0.88 | 0.54 |
| S69 sec 4 chorus | `S-------` | 0.31 | `S-S--SS-` | 0.77 | 0.47 |
| S69 sec 6 verse 2 | `S--S----` | 0.41 | `S-SSS-SS` | 0.87 | 0.47 |
| S69 sec 8 chorus | `S-------` | 0.45 | `S-------` | 0.45 | 0.53 |
| S69 sec 1 verse | `SSSS-SSS` | 0.92 | `SSSSSSSS` | 1.00 | 0.77 |
| Wet Leg sec 9 verse | `SSSSSSSS` | 1.00 | `SSSSSSSS` | 1.00 | 0.83 |
| Wet Leg sec 22 verse 2 | `SSSS--S-` | 0.73 | `SSSSSSSS` | 1.00 | 0.69 |

"explained" is the share of the section's detected strikes that fall on a pattern strike. It is the one number that separates the boxes the validation called wrong from the rest: under today's vote it is 0.31 to 0.57 for every one of them (Chelsea 0.54, 0.48, 0.52; S69 0.31, 0.41, 0.45, 0.57, 0.23) and 0.69 to 1.00 for every box judged usable. Mean Jaccard (today's `confidence`) does not separate them (0.45 to 0.53 against 0.46 to 0.83) and neither does a per-bar F1 (measured 0.58 to 0.62 against 0.66 to 0.90; same ordering as Jaccard, higher numbers). The lessons' proposal "mark uncertain any pattern whose strike count is under half the section's mean strikes per bar" is subsumed: a pattern with that few strikes necessarily has low explained share.

Dense songs are left alone: every Wet Leg section at or above 4 bars keeps or gains strikes only where the rate is above 1/3 (sec 22's slots 4 and 5 are at 0.42 and 0.50).

**Design.**
- `majority_vector(bars, threshold=STRIKE_SHARE)` with `STRIKE_SHARE = 1/3` (strictly greater), then `_fill_to_floor(out, rates, floor)` where `floor = round(DENSITY_FLOOR x median strikes per bar)` and `DENSITY_FLOOR = 0.6`; the mute decision per slot stays `x if mutes > strikes / 2`.
- New `explained_onsets(bars, vector) -> float` in `as_played.py`; `section_summary` returns it as a fourth value.
- `SectionPattern.explained: float` (new, default 0.0 so old `strums.json` still loads) and `ScoreSection.explained: float`.
- In `strums.py:85`: `uncertain = confidence < UNCERTAIN_BELOW or explained < EXPLAINED_BELOW or not long_enough`, `EXPLAINED_BELOW = 0.6`. Keep `UNCERTAIN_BELOW` at 0.45: the Jaccard of the new vectors on the four fixed boxes is 0.47 to 0.62, so none would be re-flagged by it, while S69 sec 9 (0.44) and the outro (0.37) stay uncertain as they should.
- Measurement: re-run `youkelele run --from strums` on the four slugs; expected outcomes are the table above; count boxes at 75%+ rests (today 4, 4, 4, 1; expected 0, 1, 2, 0) and sections flagged uncertain by `explained` (expected Chelsea sec 0; S69 sec 8, 9, 10; all PSSOM; Wet Leg none at or above 4 bars).

**Effort small. Impact high. Confidence 85.** The 15 is PSSOM, where the > 1/3 vectors are denser but still noisy (explained 0.48 to 0.94, Jaccard 0.33 to 0.50) and the stage rightly stays uncertain; this item does not give PSSOM a box.

### 2.2 Per-section source choice between `guitar` and `other`, with a no-instrument rescue

**Touches.** `src/youkelele/music/onsets.py:63-72` (`choose_source`, whole-song), `:75-76` (`section_has_instrument`); `src/youkelele/stages/strums.py:62-68` (one detector call on one stem), `:72-80` (no-instrument branch), `:108-116` (`Strums(source=...)`); `src/youkelele/schemas.py:145-152` (`Strums.source` is one value per song; add `SectionPattern.source`); `render/templates/sheet.html.j2:65` (the mix note keys off the song-level source); tests `tests/test_stage_strums.py:106-150`.

**Evidence (measured, per section, baseline detector on each stem).**

Summer of '69, where the validation says the record strums through the choruses:

| Section | guitar/mix RMS | other/mix RMS | guitar strikes/bar, pattern, Jaccard | other strikes/bar, pattern, Jaccard |
|---|---|---|---|---|
| sec 1 verse (4 to 19) | 0.40 | 0.00 | 6.1 `SSSS-SSS` 0.76 | 0.0 |
| sec 2 chorus (19 to 31) | 0.42 | 0.00 | 3.9 `S-SS--S-` 0.61 | 0.6 |
| sec 4 chorus (41 to 53) | 0.29 | 0.06 | 2.9 `S-------` 0.39 | 6.8 `SSSSSSSS` 0.85 |
| sec 6 verse 2 (bridge, 58 to 69) | 0.40 | 0.17 | 3.5 `S--S----` 0.38 | 6.1 `SSSSSSSS` 0.76 |
| sec 8 chorus (83 to 95) | 0.30 | 0.11 | 1.8 `S-------` 0.53 | 7.0 `SSSSSSSS` 0.88 |
| sec 9 verse (95 to 111) | 0.47 | 0.21 | 3.3 `S--SS---` 0.43 | 7.9 `SSSSSSSS` 0.98 |
| sec 10 outro (111 to 121) | 0.33 | 0.32 | 2.6 `S-------` 0.18 | 7.5 `SSSSSSSS` 0.94 |

From bar 41 on, Demucs files the eighth-note rhythm part into `other`; the guitar stem keeps the muted verse chug and a thinner part elsewhere. RMS cannot see this (guitar is louder in every section), which is why `choose_source` picks guitar for the song and the research's "use `other` by default" would be wrong for the verses (0.0 strikes per bar). Yousician's result (`other` beats `guitar`) holds here per section, not per song.

Wet Leg sec 24 outro (108 to 113): guitar/mix RMS 0.01, other/mix 0.82; `other` gives 6.8 strikes per bar, `SSSSSSSS`, Jaccard 0.85. Today it prints "No strummed instrument detected" because `section_has_instrument` (`onsets.py:75`) is only asked about the chosen stem.

Pour Some Sugar On Me sec 0 intro and sec 6 chorus: `other` has 9.8 and 12.0 strikes per bar (all sixteenths, Jaccard 0.59 and 0.75) against 7.7 and 3.4 on guitar. Whether that is the rhythm guitar or keyboards and claps I cannot tell from the numbers; the rule below would switch sec 6 only.

Chelsea: `other` is below 1.8 strikes per bar in every section; the rule never switches. Summing `guitar + other` (the round 2 spike's idea) was measured too and behaves like the louder stem (S69 sec 8 stays at 1.5 strikes per bar).

**Design.**
- Detect onsets on both stems once (`detect_onsets` is 1 to 3 s per stem on these songs; the stage takes 1.7 to 2.8 s today). Keep `mute_mask` per stem.
- Per section, compute the > 1/3 pattern, `explained`, strikes per bar and Jaccard for each stem. Choose `other` when the song-level stem's section is sparse (`explained < 0.6` or strikes per bar < 2) **and** `other` has Jaccard >= 0.7 and at least 4 strikes per bar, or when `section_has_instrument` fails on the song-level stem but passes on `other`. Otherwise keep the song-level stem. Measured on the four runs this switches S69 sec 8 and sec 10, Wet Leg sec 24, PSSOM sec 6, and nothing on Chelsea. S69 sec 4 (explained 0.77 after item 2.1) is not switched by this rule; a stricter density test (`guitar strikes per bar < 0.6 x other strikes per bar`) would switch sec 4, 6 and 9 too and should be tried after an ear check.
- Record `SectionPattern.source: Literal["guitar_stem", "other_stem", "mix"]` and keep `Strums.source` as the song-level default; the sheet's mix note (`sheet.html.j2:65`) should trigger when any section used the mix.
- Keep the mix fallback whole-song as today (ratio under 0.05).
- Measurement: listen to `01_separate/stems/other.wav` from 70 s to 100 s and 165 s onward on S69 (bars 41 to 53 and 95 to 121) and confirm it is the strummed guitar; then compare strikes per bar and `explained` per section before and after on all four runs; PSSOM sec 6 is the control that may be wrong.

**Effort medium. Impact high. Confidence 65.** Below 80 because the `other` content has not been heard; a dense `SSSSSSSS` from `other` could be a keyboard or percussion part on PSSOM, and the rule's thresholds (0.7, 4) are fitted to four songs.

### 2.3 One pattern per section label, per-section box only when it disagrees

**Touches.** `src/youkelele/stages/strums.py:70-89` (the per-section loop; needs `sec.label`, available from `grid.sections`), `:91-106` (inheritance, which this generalises); `src/youkelele/schemas.py:135-142` (`SectionPattern.shared_with: list[int]` or `pooled: bool`); `render/html.py:48-65` (the label line can say "same as other choruses").

**Evidence (measured, bars pooled across all sections at or above 4 bars with the same label, > 1/3 plus floor).**

| Song, label | sections | bars | pooled pattern | Jaccard | explained | per-section patterns today's data gives |
|---|---|---|---|---|---|---|
| S69 chorus | 2, 4, 8 | 36 | `S-SS--S-` | 0.47 | 0.77 | `S-SS-SS-`, `S-S--SS-`, `S-------` |
| S69 verse | 1, 3, 5, 7, 9 | 60 | `SSSSSSS-` | 0.61 | 0.93 | `SSSSSSSS`, `SSSSS-S-`, `SS-SSSSS`, `SSSSSSSS`, `S--SS-S-` |
| Chelsea chorus | 1, 3, 5, 7 | 82 | `S-S-S-S-` | 0.54 | 0.83 | `S-S-S-S-`, `S-S-S-S-`, `S-SSS-SS`, `S-S-S-S-` |
| Chelsea verse | 0, 2, 4 | 54 | `S-S-S-S-` | 0.50 | 0.70 | `S-------`, `S-SSSSSS`, `S-S-S-S-` |
| Wet Leg verse | 7, 9 | 31 | `SSSSSSSS` | 0.64 | 1.00 | `S-S-S-SS`, `SSSSSSSS` |
| PSSOM chorus | 2, 4, 6 | 42 | `S---S---S---S--S` | 0.37 | 0.58 | three different vectors |

This is the validation's "boxes vary from verse to verse where the record has one pattern" fixed at the source, and it rescues S69 sec 8 (1.8 strikes per bar) with the other choruses' bars instead of a neighbour's pattern. The research's correlation-of-rate-vectors merge rule (0.8) was measured and rejected: on Chelsea it links chorus to verse at 0.95 and on S69 the muted verse to the open chorus at 0.91, because correlation ignores density and the mute class; labels are the safer grouping key.

**Design.**
- After computing per-section vectors, for each label with two or more sections at or above 4 bars compute the pooled vector and its `explained` over the pooled bars. A section takes the pooled vector when its own `explained` is below 0.6, or when Jaccard(own, pooled) >= 0.5 (so near-identical variants collapse to one box); it keeps its own vector when it clearly differs (Jaccard < 0.5 and own `explained` >= 0.6), which preserves genuine differences such as S69's muted verse 1 (`xxxU-xxx`) against the open later verses. Record `shared_with`.
- Short sections (under 4 bars) take the pooled vector of their label before falling back to a neighbour, which fixes the validation's "verse inherited from verse 3" complaint on Wet Leg (mostly moot after the 1.2 four-bar minimum).
- Measurement: count distinct patterns per label per song (S69 choruses today 3, expected 1).

**Effort small. Impact medium. Confidence 75.** The Jaccard 0.5 grouping threshold is a guess from the table; the mute class must be handled in the pooled vote (S69 verse 1 is 72% `x`, later verses 0 to 14%), otherwise pooling would print a half-muted verse pattern.

### 2.4 Sheet wording and the printed number

**Touches.** `src/youkelele/render/templates/sheet.html.j2:83` ("Strum as played, {{ section.repeat }} repeatable"); `src/youkelele/render/html.py:60` (`"repeat": f"{section.bar_repeat:.0%}"`); `tests/test_html.py`.

**Evidence.** `bar_repeat` is 0.29 to 0.53 on S69's confident sections and 0.37 to 0.58 on Chelsea's (from strums.json); printed as "43% repeatable" it reads as a failure for a pattern that explains 87% of what was heard. Ultimate Guitar prints one pattern per song with no score; Chordify prints none. The honest, actionable number is `explained`.

**Design.** "Strum heard in this section, covers {{ explained }} of detected strokes; up and down follow the beat." Append "(uncertain)" and "same as {{ label }}" as today. Keep `bar_repeat` in `score.json` for diagnostics. Depends on 2.1 for the field.

**Effort small. Impact medium. Confidence 90.**

### 2.5 Strum onset ground truth and `evaluate` support

**Touches.** `src/youkelele/evaluate.py:101-130` (`evaluate_run` reads `beats.txt` and `chords.lab` from `--truth`), `:23-29` (`Report`); `src/youkelele/commands.py` (`evaluate_command`); `tests/fixtures/ground_truth/README.md` (formats); new `runs/<slug>/eval/strums.txt` is not possible (runs are read-only outputs), so truth lives in the `--truth` directory as `strums.txt`.

**Evidence.** Every strums decision so far has been tuned against published beginner patterns the records do not play (round 2 spike: 0 of 14 sections) or against my own reading of `bar_onsets`. The research's deeper options (2.10 below) and the thresholds in 2.1 to 2.3 cannot be tuned without onset truth. Both 2025 papers score onset F1 at 50 ms; `mir_eval.onset.f_measure` does this and `mir_eval` is already a dependency (`evaluate.py:8`).

**Design.**
- `strums.txt`: one onset time per line in seconds, optional second column `x` for a muted stroke, covering a stated window (first line `# window 30.0 60.0`). Make it by exporting `detect_onsets` times for the window as an Audacity label track, fixing by ear, and saving.
- `evaluate_run` adds `strum_f`, `strum_precision`, `strum_recall` (50 ms window, within the stated window only) and, per section overlapping the window, `explained` of the shipped pattern against the truth onsets.
- Also export the detected onsets: a `--debug` flag on the strums stage writing `strums/onsets.txt` so a human can load stem and labels in Audacity. This is the cheapest listening tool and needs no new dependency.
- Target: 30 s of each of the four songs plus the two blind songs; every change in 2.1 to 2.3 and 2.7 reported as onset F1 and explained before adoption.

**Effort medium (mostly listening). Impact high as an enabler. Confidence 85.**

### 2.6 `nearest_named` label from the UkuTabs and Roadie list

**Touches.** `src/youkelele/music/as_played.py` (new `nearest_named(vector) -> tuple[str, int] | None`); `src/youkelele/schemas.py:135-142`; `render/html.py:48-65` and the template line 83.

**Evidence (measured, Hamming distance on strike/rest over the 8-slot > 1/3 vectors).** S69 verse 1 "eighths", S69 chorus 2 "D-DU-UD-" at distance 0, S69 sec 0 "island" at 0, Chelsea choruses "all downs (quarters)" at 0, Wet Leg sec 10 "island" at 0; nothing sensible at 16 slots (PSSOM) without a 16-slot table. The round 2 spike recommended this field and the stage shipped without it.

**Design.** A module-level table of the 18 UkuTabs plus 5 Roadie patterns as strike/rest strings (8 slots for 4/4, 6 for 3/4; the two-bar and 6/8 ones omitted until the stage has two-bar patterns). Print "close to the island strum" only when the distance is 0 or 1 and the section is not uncertain; never alter `slots`.

**Effort small. Impact low. Confidence 80.**

### 2.7 Grid phase offset before quantising

**Touches.** `src/youkelele/music/onsets.py:79-88` (`_bar_positions`), `:102-106` (`grid_fit`), `:118-140` (`quantise_bar`); `src/youkelele/stages/strums.py:65-68`.

**Evidence (measured, signed deviation of each onset from its nearest slot, in slot widths).** Wet Leg median +0.068 (onsets 16 ms late against the Beat This! grid); shifting the bars by that raises grid fit 0.73 to 0.81, best 0.84 at +0.10 slots, and changes sec 22 from `SSSS--S-` to `SSSS-SSS` under the old vote. Chelsea median -0.033, fit 0.55 to 0.58 (best 0.59 at -0.08); S69 +0.038, 0.91 to 0.92; PSSOM +0.020, no change. Dixon et al. refine bar boundaries the same way. Per-section medians are consistent within a song (Wet Leg +0.02 to +0.17, S69 +0.02 to +0.06), so one song-level offset is enough.

**Design.** `grid_offset(onsets, bars, slots) -> float` = median signed deviation in seconds, clipped to a quarter slot; apply it inside `quantise_bar` and `grid_fit` (shift `bar.start` and `bar.end`); record `Strums.grid_offset_ms`. Beat This! and the grid stage are untouched.

**Effort small. Impact low (one song by 0.08 to 0.11 of fit). Confidence 70.** Below 80 because on Chelsea the deviation spread is wide (p25 -0.13, p75 +0.10 slots), which no constant shift fixes; the Chelsea fit of 0.55 is loose timing or smeared attacks, not an offset.

### 2.8 Accents from the detrended envelope

**Touches.** `src/youkelele/music/onsets.py:38-52` (`detect_onsets` would return the envelope, hop and sr on `Onsets`); `src/youkelele/render/strum_box.py:22-45` (a `>` glyph above the arrow); `schemas.py` (`SectionPattern.accents: list[int]`).

**Evidence (measured, envelope minus its 200 ms running mean, sampled within 23 ms of each slot centre, averaged over the section's bars, two strongest slots).** Chelsea: slots 2 and 6 (beats 2 and 4) in seven of eight sections. S69 verse 1: 2 and 6; chorus 2: 0 and 2; sec 5: 0 and 6. Wet Leg: mostly 0 and 6. The Chelsea result is either the real guitar accent or the snare bleed the lessons describe; the numbers cannot tell them apart and no drum-based veto survived testing (section 3.3). The research's profile-as-pattern idea (threshold 0.4 of the max) was also measured and rejected: it gives `SSSSSSSS` for S69 sections with 2.9 to 3.5 strikes per bar and drops beat 1 in Chelsea's verses, because the envelope in a dense stem never returns to zero between strokes.

**Design (if pursued).** Mark accents only when the two strongest slots are both pattern strikes and the section's accent profile is stable (the same two slots in at least 70% of bars), and never on the mix source. Ultimate Guitar's `>` convention.

**Effort small. Impact low. Confidence 45.** Needs the ground truth of 2.5 or an ear check before anyone ships it.

### 2.9 Swing grid (12 slots per bar)

**Touches.** `src/youkelele/music/onsets.py:91-99` (`choose_slots_per_bar`), `src/youkelele/music/score_builder.py:41-46` (`check_strums_match_grid` accepts only `2 x` and `4 x` the numerator), `src/youkelele/schemas.py:154-161`, `render/strum_box.py:12` (`_SUBDIVISIONS` already has a 3-per-beat entry), `render/grid.py`.

**Evidence (measured, onset phase inside the beat, 8 bins).** S69 0.42 on the beat and 0.34 at the half; Wet Leg 0.41 and 0.31; Chelsea 0.23 on the beat, 0.43 just before it, 0.12 at 5/8; PSSOM flat. None of the four is swung; a shuffle would show mass at bins 5 to 6 (two thirds). Latent gap, as the research says.

**Design.** Add a 12-slot candidate when the phase histogram's mass at 2/3 exceeds its mass at 1/2 by a margin; relax `check_strums_match_grid` to `(2, 3, 4) x numerator`; 12-column box. Do it when a swung validation song exists, not before.

**Effort large. Impact low today. Confidence 60.**

### 2.10 Trained CRNN strum detector on synthetic stems

**Touches.** New `src/youkelele/models/strums.py` beside `models/beats.py`; `onsets.detect_onsets` becomes one of two detectors behind the `onset_detector` hook that `StrumsStage.__init__` already has (`stages/strums.py:49-50`); training scripts outside the package.

**Evidence.** Classical detectors reach 79 to 83% onset F1 on isolated guitar and less on stems (Yousician paper); the measured baseline here cannot be scored without 2.5, but S69 chorus recall of 1.8 strikes per bar on a part that plays eighths, and PSSOM's 0.59 grid fit, are the symptom. Both 2025 papers trained a small frame model on synthetic strummed audio mixed into real backing tracks and gained 15 to 20 F1 points over spectral flux. torch is already a dependency (`pyproject.toml`), Beat This! already runs a CPU transformer in the grid stage, and a Murgul-size CRNN (conv stack plus BiGRU 256) runs faster than real time on CPU.

**Design.** Render strums from GuitarPro or generated chord grids with a ukulele and nylon-guitar soundfont (FluidSynth), random pattern, tempo, transposition, EQ, reverb and noise; mix at random levels into the project's own `drums`, `bass`, `vocals` stems from runs; separate the mix with htdemucs_6s and train on the resulting `guitar` and `other` stems so the model sees Demucs artefacts; labels exact; Beat This!'s shift-tolerant BCE. Validate on the 2.5 truth. Ship as an opt-in detector until it beats librosa on the truth set.

**Effort large. Impact high. Confidence 55.** Below 80 because of the soundfont-to-record gap (Murgul saw 40% upstroke F1 gain from adding real recordings) and because nobody has measured the baseline F1 yet (2.5 first).

## 3. Research discarded or downgraded, with the measurements

### 3.1 Median aggregation and SuperFlux settings in `onset_strength` (research 4.3)

Measured as the one-line change proposed (`aggregate=np.median, max_size=3, lag=2, fmin=150, fmax=5000`) with the default peak picker: onsets fall from 537 to 307 (Chelsea), 491 to 112 (S69), 626 to 212 (PSSOM), 815 to 237 (Wet Leg). S69 choruses drop to 0.2 strikes per bar, Wet Leg's dense verses to 1.4. Median-only (`aggregate=np.median`) is less severe (491 to 264 on S69) but still halves recall everywhere. The median across mel bands suppresses a strum, which excites a few bands strongly, as readily as it suppresses bleed, and `normalize=True` then scales the few surviving spikes to 1. McFee and Ellis designed it for beat tracking, where fewer, surer onsets help; here recall is the problem. Discarded. (A re-tuned `delta` on the median envelope was not explored because the spike already showed what tuning `delta` does.)

### 3.2 Section-relative peak picking (research 4.2)

Measured two ways. Normalising each section's envelope by its own 95th percentile with `delta` 0.07 produced more than 1.2 x slots x bars onsets in every section of every song (the guard fell back on 8 of 8, 10 of 11, 7 of 7, 25 of 25). Normalising by the section maximum: S69 onsets 491 to 1221, choruses 1.8 to 7.6 strikes per bar, every S69 section `SSSSSSSS` with explained 1.00, grid fit 0.91 to 0.61; Chelsea 537 to 639, fit 0.55 to 0.50; PSSOM 626 to 1082, fit 0.59 to 0.48. This is the round 1 spike's `delta` 0.03 result by another route: the peak picker's `delta` is an absolute step on a normalised envelope, so any per-section rescaling lowers the threshold wherever the section is quiet, and the quiet sections are quiet because the strummed part is not in this stem (2.2). Discarded; the recall problem it targets is solved by 2.2 instead.

### 3.3 Drum veto using `drums.wav` (research 4.4)

Measured: 41% (Chelsea), 38% (S69), 27% (PSSOM) and 54% (Wet Leg) of guitar-stem onsets fall within 20 ms of a drum-stem onset. Dropping those unless the guitar envelope exceeds 1.25 x the section median removes 149 of 537, 139 of 491, 129 of 626 and 337 of 815 onsets, lowers grid fit on every song (Chelsea 0.55 to 0.46, S69 0.91 to 0.88, PSSOM 0.59 to 0.49, Wet Leg 0.73 to 0.55), turns Wet Leg's `SSSSSSSS` chorus 23 into an empty vector, and still leaves Chelsea's choruses at `--S-----`. A rhythm guitar plays with the drummer; coincidence is music, not bleed. Discarded. Beat-position arguments (Chelsea's slot 2 at 0.81 to 1.00) remain suggestive of snare bleed but no onset-level test separates the two, which is also why 2.8 is low confidence.

### 3.4 Decay feature for the mute rule (research 4.6)

Measured RMS in 60 to 120 ms after each onset over RMS in the first 20 ms, per section. Medians: S69 verse 1 (72% `x` today, the real chug) 1.05; S69 chorus 2 (0% `x`) 1.05; S69 outro (42% `x`, the false mutes) 0.99; Chelsea 0.98 to 1.18; PSSOM 0.88 to 1.22; Wet Leg 1.12 to 1.56. No separation at all, matching the round 1 spike's 150 ms decay ratio (AUC 0.64). In a separated stem of a dense mix the energy after a stroke is other instruments' residue, not the string's decay. Discarded. The false mutes in S69's outro already vanish in the printed box because the slot-wise mute vote (`as_played.py:50`) needs mutes to be the majority of strikes; nothing further is needed there.

### 3.5 Slot-strength profile as the pattern (research 4.1 first variant)

Measured with the detrended envelope (3.3 above) at thresholds 0.4 and 0.5 of the section maximum: S69 sections with 2.9 to 3.5 strikes per bar come out `SSSSSSSS`; Chelsea verses lose beat 1 (`--S-S-S-`) because slot 2 dominates the normalisation; Wet Leg sec 0 becomes `S---S---` against a binary `S-SSSSS-`. The binary vote with the lower threshold (2.1) is better behaved on every song. Keep the envelope only for 2.8.

### 3.6 Section merge by rate-vector correlation (research 4.8)

Measured: correlation >= 0.8 links Chelsea's chorus with its verse (0.95) and S69's muted verse 1 with open chorus 2 (0.91). Replaced by label pooling (2.3).

### 3.7 Not applicable to this pipeline

- **MERT-v1-95M fine-tuning**: CC-BY-NC-4.0 weights, a 95M transformer at 75 Hz on CPU for a four-minute song; out.
- **madmom CNN/RNN onsets**: CC BY-NC-SA models and PyPI 0.16.1 broken on NumPy 2.5.3 (this venv); out.
- **Direction from audio**: 79 to 86% per class with wrist-sensor labels; the positional rule (`onsets.py:143-145`) stays, with the wording of 2.4.
- **Viterbi over a 924-pattern vocabulary**: the vocabulary is proprietary and the round 1 spike showed the small-vocabulary version is pulled to the densest row; the label pooling in 2.3 is the cheap substitute for its transition cost.
- **Roformer or MDXC guitar checkpoints through audio-separator**: possible (MIT package already installed) but each checkpoint's licence and CPU runtime are unknown and separation is already 76 to 84% of the run; try only after 2.2 and 2.5 show that routing between the two existing stems is not enough.
- **IDMT-SMT-Guitar** (CC BY-NC-ND) and **GuitarSet** are isolated-guitar sets; useful to sanity-check a detector, not to tune this stage, whose problem is stems of mixes.

## 4. Side observations for whoever implements

- `detect_onsets` (`onsets.py:42`) uses librosa's default hop of 512 (11.6 ms at 44.1 kHz); the spikes that fixed the thresholds ran at hop 256. Not a defect, but any constant carried over from the spike reports was measured at a different frame rate.
- `Onsets` (`onsets.py:31-35`) carries only times, centroid and zcr. Items 2.2, 2.7 and 2.8 all want the envelope, hop and sample rate on it; add them once.
- `StrumsStage.__init__` already takes an `onset_detector` callable (`strums.py:49`), so 2.10 slots in without touching tests that use the fake detector in `tests/test_stage_strums.py:70-86`.
- `check_strums_match_grid` (`score_builder.py:28-46`) only checks counts and slot arithmetic; the new fields in 2.1 to 2.3 need defaults so `score` keeps loading the existing `runs/*/04_strums/strums.json`.
- The research's claim that Chelsea's first chorus prints at confidence 0.51 is from the version 1 run; the shipped version 1.1 artefact has 0.46 for sec 1 and 0.45 for sec 7, both still above `UNCERTAIN_BELOW`.
