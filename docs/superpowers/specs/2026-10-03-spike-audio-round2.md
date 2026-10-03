# Spike, round 2: strums, end-to-end clip and grid on five real songs (plan Tasks 8, 10, 14)

Date: 2026-10-03. Same machine and venv as the round-1 reports (`2026-10-03-spike-audio.md`, `2026-10-03-spike-models.md`); no package installed. Scripts in `SP\spike_audio2\scripts\` (`grid2.py`, `segment2.py`, `strums2.py`, `stem_ratios.py`, `phase_check.py`, `hand_sections.py`, `sum_stems.py`, `make_clip_nokick3.py`), outputs under `SP\spike_audio2\{riptide,imyours,sotr,clip,clip_nokick3}\` plus new files in `SP\spike_audio\{s69,pssom}\` (`bars*.json`, `sections*.json`, `strums_*.json`, `stem_ratios.json`). SP is the session scratchpad named in round 1.

Everything below is derived from audio features and the existing scripts only. No lyric sources were consulted; section labels are the segmenter's own heuristic names.

| Task | Before | After | One-line reason |
|---|---|---|---|
| 10 Strums | 75% | 85% | The revised algorithm was run on five songs plus the clip; where a usable stem exists it produces regular, repeatable bar vectors, but the published beginner patterns are not what the records play (0 of 14 sections on the three new songs), so the tests must target regularity and an "as played" output, not published patterns; two concrete rule changes (source stem, mix mute rule) are specified below. |
| 14 End to end | 88% | 93% | With the beat-3 kick removed from the synthetic clip the whole chain recovers `D-DU-UDU` at 0.917 from the mix and 0.71 to 0.82 from the `other` stem, with Beat This! still exact; only the render stage remains untried in one run. |
| 8 Grid | 82% | 80% | The modal-phase bar builder and the k rule plus loudness labeller hold on three of five songs, but two new failure modes appeared (Beat This! returns the double tempo on slow strummed songs, and single-progression songs are not separable by chroma); mitigations are specified but untested. |

Songs added this round (chosen by duration from `ytsearch3`, studio versions):

| Song | id | upload length | channel type | bpm from Beat This! | note |
|---|---|---|---|---|---|
| Riptide | `uJ_1HMAGb4k` | 204 s | label channel, official video | 103.4 | ukulele-led, drums and bass |
| I'm Yours | `w5qOYi41WiA` | 243 s | re-upload of the studio audio | 150.0 | acoustic guitar-led; the song reads as 75 bpm, Beat This! returned the double |
| Somewhere Over the Rainbow | `V1bFr2SWP1I` | 227 s | label channel, official audio | 166.7 | ukulele and voice only, no drums or bass; reads as about 85 bpm, Beat This! returned the double |

All three downloads resolved to webm/opus and converted to 44.1 kHz stereo s16 as in round 1. Separation (htdemucs_6s, capitalised `custom_output_names`) took 108 s, 108 s and 123 s (0.45 to 0.55x real time).

---

## Spike 1: the revised strum algorithm on three new songs (Task 10)

### Question

Does the algorithm recommended by the round-1 audio report (librosa default onsets on the guitar stem with mix fallback, 25% odd-sixteenth slot rule, class-only slot vectors with the relative centroid/zcr mute rule, Jaccard emission, Viterbi over 37 + 3 - 1 patterns with switch penalty 0.35, short sections inheriting, direction from metric position) recover the documented pattern `D-DU-UDU` on three songs where that pattern is published, and do the 0.45 floor and the 0.6 grid-fit threshold hold?

### What was run

- `grid2.py <song> none|half [- phase]`: bars from the modal downbeat phase (beat index modulo 4 shared by most downbeats), optionally after halving the beat list from the first downbeat, optionally forcing the phase.
- `segment2.py <song> <bars.json> [k]`: the Spike D Laplacian method on bar features with `k = max(3, min(6, round(n_bars/30)))` and the loudness labeller (chorus = loudest cluster occurring at least twice, verse = next most bars, once-only clusters intro/bridge/outro by position). Sections for Spike 1 come from this, not from any lyric knowledge.
- `strums2.py <song> <bars.json> <sections.json> <refs> [--source stem|mix] [--stem path] [--force-slots 8|16] [--min-strength-pct P]`: the revised algorithm exactly as listed in the question; per section it prints the decoded pattern, confidence (mean emission x share of bars), per-section grid fit, strikes per bar, the reference pattern's emission and rank, the accent profile (summed onset strength per slot), the "as played" majority vector (slot is a strike if present in at least half the section's bars) with its emission, and the bar-to-bar repeat score (mean Jaccard between consecutive bars).
- `stem_ratios.py`: RMS ratio of every stem to the mix, overall and per section.
- `phase_check.py`: onset phase within the beat (8 bins) and autocorrelation of the half-beat onset-strength sequence at lags 1, 2, 4, 8, 16 beats.

### Results

**Which stem carries the strummed instrument.** RMS ratio stem/mix, whole song (per-section range in brackets):

| Song | guitar | other | drums | bass | vocals | piano |
|---|---|---|---|---|---|---|
| Riptide | **0.03** (0.00 to 0.03) | **0.18** (0.03 to 0.37) | 0.56 | 0.40 | 0.61 | 0.07 |
| I'm Yours | **0.22** (intro 0.64, body 0.20, bridge 0.12, tail 0.00) | 0.12 | 0.28 | 0.52 | 0.52 | 0.14 |
| Somewhere Over the Rainbow | 0.12 (0.00 to 0.04 for 170 s, then 0.15 and 0.26) | **0.55** (0.41 to 0.84) | 0.01 | 0.00 | 0.77 | 0.00 |
| Summer of '69 (round 1) | 0.39 | | | | | |
| Pour Some Sugar (round 1) | 0.30 | | | | | |
| synthetic clip | 0.13 (0.07 / 0.16 / 0.06) | **0.48** | 0.83 | 0.06 | 0.06 | 0.06 |

htdemucs_6s puts a ukulele in `other`, not `guitar`: Riptide's guitar stem is 3% of the mix (below the 0.05 threshold, so the plan's rule falls back to the drum-dominated mix), the Hawaiian recording's guitar stem is empty for the first 170 s, and the clip's Karplus-Strong strings go to `other` with only bleed in `guitar`. An acoustic guitar (I'm Yours) does land in `guitar`, but only the exposed intro is strong; in the body the ratio is 0.20 and from 177 s on it is under 0.10 in most Laplacian segments.

**Beat grid and octave.** Modal downbeat phase and bars:

| Song | beats | downbeats | spans of 4 beats | modal phase share | bars (len) | half-octave bars (len) |
|---|---|---|---|---|---|---|
| Riptide | 332 | 84 | 80 of 83 | 0.57 (counts 1/15/48/20) | 82 (2.36 s) | not needed |
| I'm Yours | 607 | 153 | 151 of 152 | 0.99 | 151 (1.58 s) | 75 (3.18 s), phase undetermined (76/76) |
| Over the Rainbow | 501 | 135 | 115 of 134 | 0.52 (counts 51/3/70/11) | 124 (1.42 s) | 61 to 62 (2.82 s), phase undetermined |
| clip | 61 | 16 | 15 of 15 | 1.00 | 15 (2.00 s) | |

For the two slow strummed songs Beat This! returned twice the tempo the songs read as (150 and 166.7 bpm) and marked every fourth fast beat as a downbeat, so the detected bar is half a real bar. On that grid the 25% rule picks 16 slots (odd-sixteenth share 0.34 and 0.12 on the guitar stem, 0.42 on the Rainbow `other` stem) so the slots are real sixteenths, but a one-bar pattern then spans two detected bars and nothing in the vocabulary can represent it. Halving the beat list fixes the bar length but leaves two candidate bar phases two fast beats apart that the downbeats cannot resolve (76/76 and 26+25/34+36); both were run and the decoded patterns were nearly identical because the observed vectors are close to symmetric. The autocorrelation test in `phase_check.py` did not give a reliable octave decision (on the clip, which is at the right octave, lag 8 beats scored 0.64 to 0.77 against 0.34 for lag 4 because chords change every two bars), so the beat octave stays a user option (`--beat-octave half`, already in the plan) and the stage should print the detected bar length in the header so the user can see 1.4 s bars at once.

**Onset phase within the beat** (strength-weighted share per eighth of a beat, bin 0 = on the beat): Riptide `other` 0.11 0.18 0.08 0.09 0.15 0.18 0.12 0.07 (onsets spread through the beat, consistent with sixteenths that sit 1/8 beat late against the Beat This! grid); Rainbow `other` 0.29 0.01 0.01 0.14 0.22 0.02 0.05 0.27 (on the fast beat, half way, and just before the beat); I'm Yours guitar 0.37 0.05 0.01 0.01 0.11 0.22 0.02 0.22; Summer of '69 stem 0.37 0.01 0.01 0.10 0.26 0.01 0.01 0.24; clip mix 0.60 0 0 0 0.40 0 0 0. The real songs have real anticipations and lags; the clip is exact.

**Decoded patterns per section.** Best configuration per song (stem with the most energy; half-octave grid where Beat This! doubled; references `D-DU-UDU`, plus `D-xU-UxU` for I'm Yours). "fit" is the per-section within-15% grid fit, "spb" strikes per bar, "rep" the bar-to-bar Jaccard, "as played" the majority vector rendered with positional direction. `ref rank` is the reference's rank among the 38 to 39 vocabulary rows by mean emission.

Riptide, `other` stem, 103 bpm, 16 slots, song grid fit 0.767, mute share 0.18:

| section (Laplacian) | bars | ratio | spb | fit | decoded | conf | hit | ref em / rank | as played | em | rep |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 verse (1.0 s) | 10 | 0.37 | 10.0 | 0.79 | `DUDUDUDUDUDUDUDU` | 0.616 | no | 0.46 / 8 | `-UDUD-D--UDUD-D-` | **0.967** | **0.952** |
| 1 chorus (25.5 s) | 42 | 0.18 | 8.7 | 0.74 | `DUDUDUDUDUDUDUDU` | 0.489 | no | 0.22 / 12 | `-UDUD-D--UDUD-DU` | 0.512 | 0.567 |
| 2 bridge (125.9 s) | 5 | 0.03 | 0.4 | 0.50 | all rests | 0 | n/a | no-guitar flag | | | |
| 3 verse (137.7 s) | 5 | 0.29 | 7.6 | 0.86 | `DUDUDUDUDUDUDUDU` | 0.419 unc. | no | 0.04 / 31 | `D--U-U-UD--U-U-U` | 0.803 | 0.759 |
| 4 chorus (149.3 s) | 20 | 0.15 | 9.6 | 0.80 | `DUDUDUDUDUDUDUDU` | 0.523 | no | 0.14 / 25 | `D-DU-U-UD-DU-UDU` | 0.684 | 0.660 |

The verse bars are almost identical to one another (`-SSSS-S--SSSS-S-` in nine of ten bars), i.e. a five-strike half-bar figure repeated twice per bar: the detector sees a clean, repeatable pattern that is simply not in the vocabulary, so the Viterbi settles on the densest row at a misleading 0.62. The same run on the guitar stem is impossible (ratio 0.03 triggers the mix fallback) and on the mix gives the drum pattern (`DUDUDUDUDUDUDUDU` 0.66 in the verse, `D-D-x-D-D-D-x-D-` 0.40 in the last chorus, mute share 0.24 from kick drums).

I'm Yours, guitar stem, half-octave grid (75 bpm, phase 0), 16 slots, grid fit 0.516, mute share 0.23:

| section | bars | ratio | spb | fit | decoded | conf | hit | ref em / rank | as played | em | rep |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 intro (0.7 s) | 7 | 0.64 | 14.9 | 0.54 | `DUDUDUDUDUDUDUDU` | 0.821 | no | 0.36 / 11 | all sixteenths | 0.821 | 0.786 |
| 1 body (23.0 s) | 57 | 0.20 | 8.2 | 0.52 | `DUDUDUDUDUDUDUDU` | 0.255 unc. | no | 0.34 / 16 | `D-D-D-D-D-D---D-` | 0.424 | 0.498 |
| 2 bridge (204.2 s) | 8 | 0.12 | 4.8 | 0.40 | `DUDUDUDUDUDUDUDU` | 0.211 unc. | no | 0.16 / 13 | `---U------DUDU--` | 0.339 | 0.264 |
| 3 tail (229.6 s) | 3 | 0.00 | 0 | | all rests | 0 | n/a | no-guitar flag | | | |

On the un-halved 150 bpm grid the 34 Laplacian segments (see Spike 3) give 7 scorable sections, none a hit, grid fit 0.37. Keeping only onsets above the section median strength (`--min-strength-pct 50`) leaves the accent skeleton `--D---D---D---D-` in the body (accent profile `..#...#...#...#.`): the loudest strokes sit on the off-beat eighths, and the `x` marks in the unfiltered vectors cluster on sixteenth slots 0, 4 and 12 (beats 1, 2 and 4). That is a chunked off-beat figure, not `D-DU-UDU`, and `D-xU-UxU` scores 0.33.

Somewhere Over the Rainbow, `other` stem, half-octave grid (85.7 bpm, phase 0), 16 slots, grid fit 0.771, mute share 0.26:

| section | bars | ratio | spb | fit | decoded | conf | hit | ref em / rank | as played | em | rep |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 intro (5.1 s) | 5 | 0.84 | 15.6 | 0.79 | all sixteenths | 0.831 | no | 0.35 / 10 | all sixteenths | 0.831 | 0.883 |
| 1 chorus (19.3 s) | 11 | 0.56 | 13.5 | 0.80 | all sixteenths | 0.727 | no | 0.42 / 9 | `D-DUDUDUD-DUDUDU` | 0.815 | 0.792 |
| 2 verse (50.4 s) | 10 | 0.62 | 13.4 | 0.67 | all sixteenths | 0.662 | no | 0.31 / 8 | `DUDUDUDU-UDUDUDU` | 0.675 | 0.666 |
| 3 chorus (93.6 s) | 11 | 0.55 | 11.4 | 0.81 | all sixteenths | 0.594 | no | 0.36 / 15 | `D-DUD-DUDUDUD-DU` | 0.679 | 0.635 |
| 4 verse (124.6 s) | 5 | 0.55 | 12.2 | 0.86 | all sixteenths | 0.606 | no | 0.35 / 15 | `D-DUD-DUDUDUD-DU` | 0.710 | 0.663 |
| 5 chorus (138.5 s) | 11 | 0.53 | 10.3 | 0.84 | all sixteenths | 0.523 | no | 0.37 / 16 | `D-DUD-DUDUD---DU` | 0.686 | 0.558 |
| 6 verse (169.4 s) | 8 | 0.41 | 13.5 | 0.70 | all sixteenths | 0.758 | no | 0.29 / 18 | all sixteenths | 0.758 | 0.722 |

The record is a continuous sixteenth-note strum (10 to 16 strikes per bar) with a quarter-note accent; forcing 8 slots gives `DUDUDUDU`, `xxxxxxxx` or `DUxUDUxU` at 0.46 to 0.80, and the strength filter gives `--D---D---D---D-` (accents on the off-beat eighths of this grid phase) at 0.28 to 0.72. The guitar stem decodes nothing (ratio under 0.10 in five of seven sections). The mix gives the same vectors as `other` (no drums to confuse it), grid fit 0.72.

**Hit rate and confidence.** Against the published pattern, 0 of 14 scored sections on the three new songs in the best configuration per song, and 0 of 14 in every other configuration tried (guitar stem, `other` stem, summed guitar+other, mix, 8 or 16 slots forced, strength-filtered onsets, both half-octave phases). Including the round-1 songs and the clip: Summer of '69 stem 1 of 9 (verse `xxxxxxxx` 0.58 against the chug reference), original clip 0 of 2 (reference rank 2, one extra strike), clip variant 2 of 2 (0.917, 0.917, see Spike 2). Confidence does not separate hits from misses: hits 0.57 to 0.92, misses 0.08 to 0.86 with 15 of 31 misses above 0.45 and 9 above 0.6. High confidence on a miss always meant "dense regular strumming matched by the all-strikes row". The bar-repeat score and the as-played emission are the honest regularity indicators: 0.95 / 0.97 on the Riptide verse, 0.56 to 0.88 on the Hawaiian recording, 0.26 to 0.50 on the I'm Yours body, 0.03 to 0.62 on Summer of '69.

**Grid fit 0.6 threshold.** Song-level within-15% share on the chosen grid: Summer of '69 stem 0.926, clip 0.96 to 1.0, Riptide `other` 0.767 (mix 0.823), Rainbow `other` 0.771, I'm Yours guitar 0.516 (half grid) and 0.371 (fast grid), Pour Some Sugar stem 0.575. The two songs under 0.6 are exactly the two whose vectors are irregular (bar repeat under 0.5); above it every song gave repeatable vectors. Keep 0.6.

**Mute rule.** Fires on 18 to 26% of onsets on `other` stems and 23% on the I'm Yours guitar stem. On a mix it fires on kick drums: clip mix slot 0 (and 4) read as `x` in every bar, Riptide mix 24%. The rule must be disabled (or the source must not be the mix) when `source == "mix"`.

**Diagnosis and the alternative tested for each.**

| Diagnosis | Evidence | Alternative tested | Outcome |
|---|---|---|---|
| Separation routing, not smear: the ukulele is in `other` | ratios above; Riptide guitar 0.03 vs other 0.18, Rainbow 0.12 vs 0.55, clip 0.13 vs 0.48 | decode the stem with the larger guitar/other ratio; also a summed guitar+other stem | regular vectors (fit 0.77, repeat up to 0.95) where the guitar stem gave nothing; the sum behaves like whichever stem dominates, so pick by ratio |
| Onset detection returns every sixteenth of a dense strum | 8 to 16 strikes per bar on all three records | keep only onsets above the section median strength | accent skeletons (`--D---D---D---D-`, `--D-D-D---D-D-D-`) at lower confidence; still no reference match; useful as an accent overlay, not as the pattern |
| Emission and vocabulary: the Viterbi is forced into the densest row | Riptide verse all-sixteenths 0.62 vs as-played 0.97 | slot-wise majority vector per section ("as played") | wins by 0.1 or more on Riptide verse (0.967 vs 0.616), Rainbow choruses (0.815 vs 0.727), I'm Yours body (0.424 vs 0.255); loses on Summer of '69 verse (0.505 vs 0.655 for `xxxxxxxx`) where the vocabulary row is right |
| Mix instead of stem for a ukulele-led song | Riptide | run onsets on the mix | drum pattern at 0.40 to 0.66; worse than the `other` stem; for a drumless record (Rainbow) the mix equals the `other` stem |

**Summer of '69 re-run with the revised algorithm** (guitar stem from round 1, 8 slots, grid fit 0.926). With the round-1 RMS-derived hand sections: verse `xxxxxxxx` 0.582 (16 bars, confident), prechorus `D-DU-UD-` 0.250 uncertain, chorus (2 bars) inherits the prechorus pattern as uncertain, verse 2 `--DU--D-` 0.260 uncertain, prechorus 2 `D-DU-UD-` 0.433 uncertain, chorus 2 `DUDUDUD-` 0.524 (as played `D-DUDUDU` 0.664, reference `DUDUDUDU` rank 5), bridge `D-DU-UD-` 0.283 uncertain, solo `D-DUDUDU` 0.708, breakdown and outro `D-------` 0.25 and 0.13 uncertain. With the Laplacian sections (k = 4): segment 0 (0.4 to 33.4 s, intro plus verse, 19 bars) `xxxxxxxx` 0.576; segment 1 (33.4 to 52.4 s, which merges prechorus, chorus and riff) `--DU--D-` 0.318 uncertain; segment 3 (69.8 to 90.6 s, prechorus 2 plus chorus 2) `D-DU-UD-` 0.408 uncertain; segment 4 (90.6 to 100.9 s) `DUDUDUD-` 0.774. So a reader would see a confident muted-eighths chug for the verse and an *uncertain* chorus whose spelling depends on where the section boundary falls, because the segmenter glues the arpeggiated pre-chorus to the chorus and the mixed bars pull the confidence under 0.45. On the mix the verse becomes `D-DUD-DU` 0.43 uncertain and chorus 2 `x-x-x-x-` 0.10, so the stem is the right source for this song.

### Recommended plan changes (Task 10)

1. **Source selection.** Replace "guitar stem if ratio >= 0.05 else mix" with: compute the RMS ratio for `guitar` and `other`; take the larger; if it is under 0.05 use the mix. Record `source` as `"guitar"`, `"other"` or `"mix"` in `strums.json` and the sheet header. Measured: this picks `other` for Riptide (0.18), the Hawaiian recording (0.55) and the clip (0.48), `guitar` for I'm Yours (0.22), Summer of '69 (0.39) and Pour Some Sugar (0.30).
2. **Mute rule only on stems.** When `source == "mix"` emit no `x` (kick drums satisfy the relative centroid/zcr rule).
3. **As-played output.** Per section compute the slot-wise majority vector and its mean Jaccard emission. If it beats the Viterbi winner's mean emission by 0.1 or more, write it as the section pattern with `name: "as played"` and keep the Viterbi row as `nearest_named`. Add `bar_repeat` (mean consecutive-bar Jaccard) to the section record; render it beside the confidence.
4. **Confidence semantics.** Keep `UNCERTAIN_BELOW = 0.45`, but document that confidence measures regularity against the vocabulary, not agreement with any published chart; 9 of 31 misses in this spike scored above 0.6.
5. **Grid fit.** Keep the 0.6 whole-stage threshold (measured 0.37 to 0.58 on the two irregular songs, 0.77 to 1.0 on the rest). Also keep per-section fit in the notes.
6. **Beat octave.** Pass `options.beat_octave` through and print the median bar length in the header; Beat This! returned the double tempo on two of three strummed songs. When `half` is used the stage should try both bar phases and keep the one whose decoded confidence is higher (the downbeats cannot decide it; measured 76/76 and 51/59).
7. **Tests.** Drop any assertion that a real recording reproduces a published pattern. Keep the synthetic-clip assertion (Spike 2). Add: a source-selection test with a louder `other` stem; a test that the mix source produces no `x`; an as-played test where a repeated vector absent from the vocabulary is returned with `name == "as played"`.
8. **Vocabulary.** The three rows added in round 1 (`xxxxxxxx`, `x-x-x-x-`, all sixteenths) were used; `-D-D-D-D` was dropped with no effect. No further rows are justified by this data; the as-played output covers the long tail.

### New confidence: 85%

Up from 75% because the whole algorithm has now run on five songs plus the clip and behaves predictably (regular where the grid fit and stem ratio say it should, uncertain elsewhere), and the two remaining rule changes are small and measured. Not higher because what the stage can promise is "the strum as played" with a regularity score; agreement with beginner charts is 0 of 14 on records and that expectation has to be removed from the spec and tests, and the beat octave remains a manual option.

---

## Spike 2: separation and strums on the synthetic clip (Task 14)

### Question

After separation, which stem carries the plucked chords, does the revised strum algorithm recover `D-DU-UDU` from the guitar stem, the energetic stem and the mix, and should the end-to-end test assert the strum pattern?

### What was run

`make_clip.py` (round 1, iteration 2) regenerated to `SP\spike_audio2\clip\audio.wav`; Beat This! (120.00 bpm, 16 downbeats on bar starts, as in round 1); htdemucs_6s with capitalised custom names (17 s); `segment2.py` (k = 3: bars 0 to 4, 4 to 13, 13 to 15); `stem_ratios.py`; `strums2.py` on the guitar stem, `other`, drums, guitar+other and the mix. Then a variant `clip_nokick3` with the kick on beat 1 only (snare on 2 and 4 unchanged) through the same steps (separation 15.5 s).

### Results

Stem ratios (whole clip; per section in brackets): drums 0.83, **other 0.48** (0.51 / 0.46 / 0.53), guitar 0.13 (0.07 / 0.16 / 0.06), bass, piano and vocals 0.06 each. The Karplus-Strong strings go to `other`; `guitar` holds bleed only, but at 0.13 it passes the plan's 0.05 threshold, so the plan's rule would decode the bleed.

| source | slots | grid fit | section 1 (bars 4 to 13) decoded | conf | hit | reference emission / rank | as played | notes |
|---|---|---|---|---|---|---|---|---|
| guitar stem (plan rule) | 8 | 0.96 | `x-x-x-x-` | 0.343 unc. | no | 0.59 / 1 | `D-D--UDU` | intro and outro flagged no-guitar (0.07, 0.06) |
| other stem | 8 | 0.98 | `D-DUDUDU` | 0.770 | no | 0.70 / 2 | `D-DUDUDU` | slot 4 struck in every bar |
| guitar+other | 8 | 0.99 | `D-DUDUDU` | 0.794 | no | 0.72 / 2 | `D-DUDUDU` | |
| mix | 8 | 1.00 | `D-DUDUDU` | 0.857 | no | 0.79 / 2 | `D-DUDUDU` | bars `x-SSxSSS`: slot 0 and 4 marked `x` by the kick |
| drums | 8 | 1.00 | `D-D-D-D-` | 0.750 | no | 0.36 / 21 | | |

The single error is slot 4 (beat 3), which is a rest in `D-DU-UDU` but carries the kick on beat 3 in the clip; the kick leaks into `other` and dominates the mix there. Everything else is exact (grid fit 1.0 on the mix, bar repeat 1.0).

Variant with the kick on beat 1 only (`clip_nokick3`): Beat This! 120.00 bpm, 61 beats, 16 downbeats all on bar starts, spans all 4; stems drums 0.75, other 0.61, guitar 0.10, rest 0.07.

| source | grid fit | section 1 (bars 6 to 13) decoded | conf | hit | section 0 (bars 0 to 6) | bars seen |
|---|---|---|---|---|---|---|
| mix | 1.00 | **`D-DU-UDU`** | **0.917** | yes | `D-DU-UDU` 0.917 | `x-SS-SSS` every bar (slot 0 `x` from the kick) |
| other stem | 0.82 | **`D-DU-UDU`** | 0.821 | yes | `D-DU-UDU` 0.708 | `S-xx-xSS`, snare bleed read as mutes at 0.5 credit |
| guitar stem (0.10, plan rule) | 0.99 | `D-DU-UDU` | 0.571 | yes | no-guitar flag (0.07) | sparse bleed |

The chord model was not re-run on the variant: the strings are unchanged and only the drum part moved, so the round-1 result (C, G, Am, F, one 23 ms `N`) is expected to stand; the implementer should confirm it in Task 14 Step 4.

### Recommended plan changes (Task 14)

- In `tests/fixtures/make_clip.py` play the kick on beat 1 only (keep snare on 2 and 4): the beat-3 kick is the one drum hit that lands on a rest of the island strum. Beat This! stays exact.
- Add to `test_end_to_end_on_synthetic_clip`: load `05_strums/strums.json` and assert that the section covering bars 6 to 13 has `pattern == "D-DU-UDU"` and `confidence >= 0.7`, and that `source in ("mix", "other")`. With the Task 10 source rule the stage will pick `other` (0.61) and score 0.82; with the mix it scores 0.92. Do not assert from the guitar stem (0.10, bleed only, 0.57 and the intro flagged no-guitar).
- The `x` on slot 0 of every mix bar is the kick (mute rule on the mix); it does not change the decoded pattern because strike-versus-mute scores 0.5, but it is one more reason for Task 10 change 2.
- Keep the chord assertion as a superset test.

### New confidence: 93%

The two model-dependent stages plus separation and the strum stage now give the intended answer on the clip with margin (0.92 from the mix, 0.82 from the stem the source rule will choose, beats exact). What remains untried in one run is the alphaTex/PDF render, and the chord model on the drum variant.

---

## Spike 3: modal-phase bars and segmentation on five songs (Task 8)

### Question

Does building bars from the modal downbeat phase work on all five songs, and do the k rule `max(3, min(6, round(n_bars/30)))` and the loudness labeller recovered in round 1 hold on them, judged by the recurrence matrix and chord-model-free cues only?

### What was run

`grid2.py` on Pour Some Sugar (round-1 `beats.json`), the three new songs, Summer of '69 and the clip; `segment2.py` with the k rule, then with k overrides (Riptide 4 and 5, Pour Some Sugar 4, I'm Yours half 4, Rainbow half 4) and with per-bar loudness appended to the MFCC block (`SEG_RMS=1`). For every segment the script reports the other segment with the highest mean recurrence affinity and whether it shares the cluster (the repetition check), plus cluster occurrence, bar count and mean loudness.

### Results

**Modal downbeat phase.**

| Song | downbeats | share on modal phase | downbeat spans (beats: count) | bars built | bar length |
|---|---|---|---|---|---|
| Pour Some Sugar | 134 | **0.64** (86/9/33/6) | 1:24, 2:41, 3:6, 4:62 | 93 | 2.82 s |
| Riptide | 84 | 0.57 (1/15/48/20) | 2:1, 3:1, 4:80, 5:1 | 82 | 2.36 s |
| I'm Yours | 153 | 0.99 | 4:151 | 151 | 1.58 s (half a real bar) |
| Over the Rainbow | 135 | 0.52 (51/3/70/11) | 2:18, 3:1, 4:115 | 124 | 1.42 s (half a real bar) |
| Summer of '69 | 121 | 0.98 | 4:118 | 118 | 1.74 s |
| clip | 16 | 1.00 | 4:15 | 15 | 2.00 s |

The modal-phase rule turns 134 ragged Pour Some Sugar downbeats into 93 regular bars and copes with Riptide's scattered phases. Where Beat This! has doubled the tempo the phase is unanimous but at the wrong level; after halving, the two candidate phases are tied (I'm Yours 76/76; Rainbow 51/59 with 13 single-beat spans) and the downbeats cannot decide the real bar line.

**Segmentation with the k rule and loudness labeller.** Boundaries in seconds (bar index in brackets), cluster, label, mean dB; "rep" is the segment most similar by recurrence affinity and whether it is in the same cluster.

Pour Some Sugar, 93 bars, k = 3, 9 segments: 0.4 (0) c1 intro -15.1; 51.3 (18) c2 verse -12.4 rep seg 7 same; 56.9 (20) c0 **chorus** -11.9 rep seg 5 same; 82.3 (29) c2 verse -12.8; 130.4 (46) c2 verse -12.0; 138.8 (49) c0 **chorus** -11.9 rep seg 2 same; 161.4 (57) c2 verse -12.6; 209.5 (74) c2 verse -12.1 rep seg 1 same; 215.1 (76) c0 **chorus** -11.5 rep seg 5 same. The three chorus segments are mutually most similar (affinity 0.20 to 0.22) and the two 2-bar pre-chorus tails find each other (0.24); chorus = loudest recurring cluster is right; intro and verse 1 merge into one once-only cluster labelled intro. Chorus starts 56.9, 138.8, 215.1 against round 1's chord-derived 56.9, 136.0, 215.0. k = 4 only splits the verse material further (choruses unchanged). Holds.

Summer of '69, 118 bars, k = 4, 10 segments: verse 0.4, **chorus 33.4**, verse 52.4, **chorus 69.8**, verse 90.6, bridge 100.9 (once, middle), verse 118.3, **chorus 142.5**, verse 163.3, outro 191.0 (once, last). Chorus = loudest recurring (c2 -12.1 vs c0 -12.9), each chorus most similar to another chorus (0.16 to 0.24), bridge and outro have near-zero affinity to anything (0.02). Same as round 1 on the new bar grid. Holds.

Over the Rainbow, half-octave grid, 61 bars, k = 3, 7 segments: intro 5.1 (once); c0 19.3 to 50.4, 93.6 to 124.6, 138.5 to 169.4 labelled chorus (-17.7 to -18.0 dB); c1 50.4 to 93.6, 124.6 to 138.5, 169.4 to end labelled verse (-20.2 to -20.4 dB). Every c0 segment is most similar to another c0 segment (0.14 to 0.17) and every c1 segment to another c1 (0.11 to 0.13) except the short one at 124.6 s. A clean A/B alternation of 31 to 43 s sections with the louder type called chorus. Plausible and self-consistent; k = 4 only adds an outro split at 172 s. Holds. On the un-halved 124-bar grid (k = 4) the result is 23 segments of 2 to 9 half-bars alternating between two clusters: the clustering follows the chord changes, not the form.

Riptide, 82 bars, k = 3, 5 segments: verse 1.0 to 25.5 (-27.7 dB), **chorus 25.5 to 125.9** (42 bars, -20.6), bridge 125.9 to 137.7 (once, 0.0 affinity to anything), verse 137.7 to 149.3 (-29.6), chorus 149.3 to end (-19.1). The 100 s block is under-segmented: the song sits on one chord loop throughout, so chroma cannot separate its sections and k = 3 leaves only quiet/loud/bridge. k = 4 peels off two 7 to 12 s build segments (20.6 and 142.3 s). k = 5 gives 11 segments alternating two body clusters at 32.6, 41.2, 62.1, 89.0, 110.2, 130.5, 137.7, 147.0, 158.6 s (8 to 10 bars each, the loudest recurring cluster at -18.5 to -21.9 dB as chorus), which is the alternation one expects from the recurrence matrix, but the rule picks 3. Fails (under-segmentation).

I'm Yours, un-halved 151-bar grid, k = 5: 34 segments of 2 to 12 half-bars whose cluster sequence cycles c4, c0, c1, c4, c0, c1 with the four-chord loop (adjacent segments of the same cluster have affinity 0.2 to 0.5): chord-level segmentation, useless as sections. Half-octave grid, 75 bars, k = 3: intro 0.7 to 23.0 (once), one 57-bar body segment 23.0 to 204.2 labelled chorus (the only recurring cluster, 60 of 75 bars), bridge 204.2 to 229.6 (once), tail. k = 4 splits a loud middle section 118.4 to 150.1 (-12.3 dB, once, so labelled bridge rather than chorus). Fails (under-segmentation at the right octave, over-segmentation at the wrong one).

Adding per-bar loudness to the MFCC block (`SEG_RMS=1`) changed nothing on any song except one extra 3-bar split on Riptide at k = 3; the path-similarity term already carries the loudness contrast through the MFCCs.

**Verdict on the k rule and labeller.** The k rule holds on Pour Some Sugar, Summer of '69 and the Hawaiian recording (once its grid is at the right octave) and under-segments the two songs built on a single repeating progression (Riptide, I'm Yours). The loudness labeller named the chorus correctly wherever a chorus cluster exists (3 of 3 verifiable songs) and is plausible on the Rainbow A/B form; on I'm Yours it names the only recurring cluster, which covers 80% of the song, "chorus". The modal-phase bar builder holds on all six inputs.

### Recommended plan changes (Task 8)

- Keep `build_bars` from the modal downbeat phase (verified on six inputs, 0.52 to 1.00 phase share).
- Keep `k = max(3, min(6, round(n_bars / 30)))` as the default but expose `--sections-k` as an option and write `k` into `grid.json`; document that songs on one repeating progression (Riptide, I'm Yours) need k = 5 and that the user can re-run only the grid stage.
- Labeller: add a precondition to the chorus rule, "a cluster covering more than 60% of all bars is `verse`, not `chorus`" (I'm Yours body 80%, Riptide k = 3 body 76%; Pour Some Sugar 37%, Summer of '69 30%, Rainbow 54% are unaffected). Then the second recurring cluster, if any, becomes the chorus candidate.
- Segment on the beat-octave-corrected grid only: on a doubled grid the clustering follows chord changes (34 and 23 segments). Print the median bar length in the grid stage output and warn when it is under 1.7 s at a detected tempo above 140 bpm; the user then re-runs with `--beat-octave half`. (Untested alternative for a later spike: choose the octave by comparing the segmentation's self-consistency at both octaves.)
- The 2-bar minimum should be expressed in seconds (at least 5 s) so that it means the same thing on fast and slow grids.
- Dropping the loudness feature idea from round 1: measured no effect.

### New confidence: 80%

Down two points: the bar builder and the labeller are now verified on five songs, but the k rule failed on two of them and the beat octave problem means the grid stage can produce chord-level "sections" on slow strummed songs unless the user intervenes; the fixes above are specified but not yet measured.

---

## Side findings

- `segment2.py` writes `sections.json` into the song directory; it overwrote the round-1 hand section lists in `SP\spike_audio\{s69,pssom}\sections.json`. They were restored as `sections_hand_list.json` (and `sections_hand.json` in the segments format). Stage outputs should never share a file name with user-edited inputs.
- The relative mute rule marks kick drums as `x` on any mix (clip, Riptide); the clip's slot-0 kick shows as `x` in every bar.
- Beat This! on a drumless ukulele-and-voice recording (Rainbow) followed the strum at the eighth-note level (166.7 bpm) and split its downbeats between two phases two beats apart; on a 75 bpm acoustic song with drums (I'm Yours) it returned 150 bpm with unanimous downbeats. The plan's `--beat-octave` option is needed in practice, not just in theory.
- Separation times this round: 108 s (204 s song), 108 s (243 s), 123 s (227 s), 17 s and 15.5 s (30 s clips).
