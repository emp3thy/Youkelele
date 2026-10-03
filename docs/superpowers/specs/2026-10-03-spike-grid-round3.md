# Spike, round 3: tempo octave, bar phase, k selection and labelling on five songs (plan Task 8)

Date: 2026-10-03. Same machine and venv as rounds 1 and 2; no package installed, no download, no separation. Work dir `SP\spike_grid3\` (SP is the session scratchpad named in round 1). Inputs: the five `audio.wav` + `beats.json` (Beat This! final0, dbn=False) pairs from `SP\spike_audio\{s69,pssom}\` and `SP\spike_audio2\{riptide,imyours,sotr}\`, the round-1 hand lists `sections_hand_list.json` for Summer of '69 and Pour Some Sugar, and the chord-model `.lab` files (`SP\spike_models\out\{s69,pssom}.lab` from round 1; `riptide.lab`, `imyours.lab`, `sotr.lab` produced this round with `SP\spike_models\run_chords.py`, 12.5 to 14.9 s each, written to the work dir). Nothing in the data folders was modified.

Everything below is derived from audio features, the beat lists and the chord model. Section names are the labeller's heuristic names.

| Task | Before | After | One-line reason |
|---|---|---|---|
| 8 Grid | 80% | 85% | The fixed octave rule is right on all five songs and the chroma phase rule on both halved songs; two unreported grid defects (Beat This! switching octave mid-song, a dropped beat flipping the bar phase) were found and fixed with measured rules; the iterative-split k rule weakly dominates the plan rule on five songs and the labeller names the chorus on five of five; not higher because the octave rule is a threshold with a fragile band (real tempos 141 to 190 bpm) and chroma cannot separate sections that share a progression. |

---

## Question

Do the Task 8 fixes specified in round 2 (`2026-10-03-spike-audio-round2.md`, Spike 3 and key findings 2 and 5) hold when measured: (A) which tempo-octave rule picks the nominal tempo on all five songs without halving Summer of '69, and how to resolve the bar phase after halving; (B) which k rule, minimum segment length and labeller order recover the section structure on the Fix A grid?

## What was run

Scripts, all in `SP\spike_grid3\`:

- `common.py`: song table, cached frame features (`chroma_cqt` bins_per_octave 36, 20 MFCCs, RMS, onset strength, hop 512; `feat_<song>.npz`), the round-2 modal-phase bar builder (`grid2.py` logic), bar features as `segment2.py`, and the new Fix A builder `fixa_grid` (gap fill, octave rule, local octave normalisation, modal phase, chroma phase tie-break).
- `fixa.py`: per-song tempo cues (Beat This! bpm, `librosa.feature.tempo` with and without prior, onset-autocorrelation peak, autocorrelation at the beat, half and double lags, modal phase share and adjacent-bar chroma similarity at both octaves, chroma-change alternation, percussive backbeat shares), the candidate octave rules, and the phase rule judged against chord-change times from the `.lab` and the hand lists. Output `fixa.json`.
- `grid_fixa.py`: writes `bars_<song>_fixa.json` and `grid_fixa.json` (phase, chord changes on bar starts per candidate phase, bar-length regularity).
- `dbn_check.py`: Beat This! with `dbn=True` as an octave cue. Not runnable: it imports `madmom`, which is not installed (no install allowed).
- `refs3.py`: reference cues for the three songs without a hand list on the Fix A grid: recurrence-profile novelty, MFCC+dB novelty, chord-loop breaks from the `.lab`, 4-bar loudness steps; `rec_<song>.png` recurrence images.
- `fixb.py`: the Laplacian embedding from `segment2.py`, then k rule in {plan, split60, silhouette} x minimum segment in {2 bars, 5 s, 7 s, 10 s}; boundaries scored against `ref_<song>.json`; the labeller in the order given below. Output `fixb.json`.

`librosa.beat.tempo` no longer exists in librosa 1.0.0; `librosa.feature.tempo` was used.

References: `ref_s69.json` and `ref_pssom.json` are the owner hand lists (12 and 11 boundaries, all hard, including 1- and 2-bar riff sections). For Riptide, I'm Yours and Over the Rainbow no hand list exists; `ref_<song>.json` was assembled from the `refs3.py` cues with this rule: hard = a sustained 4-bar loudness step of at least 3 dB with a novelty peak within 1 bar, or two independent cue families (timbre+loudness novelty, recurrence-profile novelty, chord-model off-loop chord) within 1 bar; one cue = soft (not scored). Riptide 14 hard (10.9, 20.6, 39.4, 55.6, 74.6, 86.7, 103.0, 110.2, 116.9, 125.9, 130.5, 137.7, 147.0, 156.2 s); I'm Yours 8 hard (13.4, 64.3, 89.8, 127.9, 140.6, 178.7, 207.4, 223.2 s; its recurrence novelty is flat because the song is one four-chord loop, so only the off-loop chords `C#/3`, `F:dim`, `F:hdim7`, `N` count as the chord cue); Over the Rainbow 8 hard (14.3, 42.6, 59.7, 85.1, 118.9, 169.4, 183.6, 200.4 s; recurrence novelty saturates and chord loop breaks are everywhere, so hard = loudness step + novelty only). These three are marked "judged by recurrence/novelty only" in every table below.

---

## Fix A: tempo octave and bar phase

### A1. Tempo cues

| Song | nominal | Beat This! | `feature.tempo` prior / none | onset autocorr peak (50 to 220, no prior) | autocorr at BT / half / double lag | fixed rule halves? | right |
|---|---|---|---|---|---|---|---|
| Summer of '69 | 139 | 136.4 | 139.7 / 139.7 | 68.9 | 0.430 / 0.435 / 0.208 | no | yes |
| Pour Some Sugar | 85 | 85.7 | 84.7 / 84.7 | 84.7 | 0.502 / 0.539 / 0.295 | no | yes |
| Riptide | ~100 | 103.4 | 103.4 / 103.4 | 206.7 | 0.289 / 0.194 / 0.346 | no | yes |
| I'm Yours | ~75 | 150.0 | 152.0 / 152.0 | 152.0 | 0.420 / 0.387 / -0.016 | yes -> 75.0 | yes |
| Over the Rainbow | ~85 | 166.7 | 172.3 / 172.3 | 84.7 | 0.421 / 0.450 / 0.235 | yes -> 85.7 | yes |

`librosa.feature.tempo` returns the same octave as Beat This! on all five, including both doubled songs, so it cannot correct the octave. The onset-autocorrelation peak is at the wrong octave on three of five (Summer of '69 halved, Riptide doubled, I'm Yours doubled). The autocorrelation ratio half/BT is above 1 on Summer of '69, Pour Some Sugar and Over the Rainbow and below 1 on I'm Yours: no threshold separates the doubled songs. Beat This! `dbn=True` was not testable (needs `madmom`).

### A2. Octave rules: which picks the nominal tempo

Structure cues at both octaves (bars from the round-2 modal-phase builder; "alt" = lag-1 autocorrelation of the adjacent-bar chroma-change sequence, negative = alternation):

| Song | detected: bars, len, phase share, adj. chroma sim mean / std, alt | halved: bars, len, phase share, sim mean / std, alt |
|---|---|---|
| Summer of '69 | 118, 1.74 s, **0.98**, 0.923 / 0.062, **-0.377** | 59, 3.46 s, 0.50, 0.917 / 0.049, 0.669 |
| Pour Some Sugar | 93, 2.82 s, 0.64, 0.985 / 0.015, 0.683 | 46, 5.64 s, 0.36, 0.993 / 0.009, 0.214 |
| Riptide | 82, 2.36 s, 0.57, 0.942 / 0.048, 0.578 | 41, 4.74 s, 0.49, 0.982 / 0.018, 0.560 |
| I'm Yours | 151, 1.58 s, **0.99**, 0.886 / 0.093, -0.237 | 75, 3.18 s, 0.50, 0.849 / 0.071, 0.351 |
| Over the Rainbow | 124, 1.42 s, 0.52, 0.858 / 0.104, -0.162 | 61, 2.82 s, 0.30, 0.834 / 0.103, 0.387 |

| Rule | halves | nominal tempo picked | note |
|---|---|---|---|
| **fixed: bpm > 140 and 60 <= bpm/2 <= 95** | I'm Yours, Rainbow | **5 / 5** | Summer of '69 at 136.4 not halved; a real 141 to 190 bpm song would be halved wrongly, so `--beat-octave` stays as the override |
| data-driven: higher modal phase share | none | 3 / 5 | Beat This! downbeats are self-consistent at its own octave (0.99 on the doubled I'm Yours), so this cue always says "keep" |
| data-driven: lower adjacent-bar chroma similarity std | all five | 2 / 5 | longer bars always average more; always says "halve" |
| chroma-change alternation < -0.2 at the detected octave | Summer of '69, I'm Yours | 3 / 5 | Summer of '69 changes chord every two bars, which looks exactly like a doubled grid; Rainbow at -0.162 missed |
| `feature.tempo` nearer bpm/2 than bpm | none | 3 / 5 | same octave as Beat This! on every song |
| autocorr(half lag) > autocorr(beat lag), bpm > 140 | Rainbow | 4 / 5 | misses I'm Yours (0.387 < 0.420) |
| percussive backbeat asymmetry over the four beat positions | n/a | uninformative | shares 0.22 to 0.28 everywhere on the HPSS percussive onset envelope; hi-hats fill every beat |

The data-driven alternatives named in round 2 do not work: the phase-share cue is circular and the chroma cues cannot tell a half-bar grid from a two-bar harmonic rhythm. The fixed rule is the only one right on all five.

### A3. Two grid defects found while building the halved grids

1. **Beat This! switches octave mid-song.** Over the Rainbow: 167 bpm for 0 to 59 s and 90 to 178 s, 86 bpm for 60 to 90 s and 178 s to the end (86 beat intervals of 0.70 s against a 0.36 s median). The round-2 global "drop every other beat" therefore produced 5.6 s double bars in the 86 bpm stretches (bars 20 to 24 of `bars_half.json`). Fix: normalise locally. With the target period 2 x median interval, walk the beat list and drop any beat closer than 0.75 x target to the last kept beat. Result: 73 bars of 2.82 s, max/median bar length 1.02, no bar over 1.5x (before: 61 bars with five at 2x).
2. **A dropped beat flips the bar phase for the rest of the song.** Riptide has a 2.04x interval at 37.4 s (and 1.36x at 85.3 s). Because bars are built from beat indices modulo 4, every bar after 37 s was one beat off, which is why the modal share was 0.57 (counts 1/15/48/20). Fix: where an interval exceeds 1.6x the local median (window of 17 intervals), insert round(gap / median) - 1 beats evenly. Result: 4 beats inserted, share 0.81 (1/15/68/0), chord changes on bar starts 0.38 -> 0.59, 83 regular bars (max/median 1.09). Summer of '69 gets one inserted beat at 205.7 s (end of the fade), share 0.98 -> 0.99.
3. **Halving parity.** The plan's "half keeps every other beat starting from the first downbeat" picks the wrong parity on Summer of '69: its first two downbeats are one beat apart (0.02 and 0.44 s) while the modal phase is 1, so a halved grid built from the first downbeat puts 0 of 73 chord changes and 0 of 12 hand-list starts on bar starts for both candidate phases. Use the modal downbeat parity.

### A4. Phase after halving (chroma-change rule) and validation

Candidates are the two phases carrying downbeats (half a bar apart). For each, bars are built and the mean (1 - cosine) between adjacent bar mean-chroma vectors is computed; the larger wins.

| Song (halved, Fix A grid) | downbeat counts per phase | chroma change per candidate | chroma pick | chord changes on bar starts per candidate (tol 0.25 s) | chord-model pick | agree |
|---|---|---|---|---|---|---|
| I'm Yours | 76 / 0 / 76 / 0 | 0: 0.151, 2: 0.067 | 0 | 0: **0.908**, 2: 0.053 (of 76) | 0 | yes |
| Over the Rainbow | 74 / 0 / 61 / 0 | 0: 0.208, 2: 0.129 | 0 | 0: **0.644**, 2: 0.055 (of 73) | 0 | yes |

Validation on the un-halved grids with four candidates (truth = modal downbeat phase, which puts 12/12 and 11/11 hand-list starts on bar starts for Summer of '69 and Pour Some Sugar):

| Song | modal phase (share) | chroma pick | chord-model pick | chord changes on bar starts at the modal phase |
|---|---|---|---|---|
| Summer of '69 | 1 (0.99) | 1 | 1 | 0.986 |
| Pour Some Sugar | 0 (0.64) | 0 | 0 | 0.551 (riff chords change mid-bar) |
| Riptide | 2 (0.81 after gap fill) | 2 | 2 | 0.587 |
| I'm Yours (150 bpm grid) | 1 (0.99) | 1 | 1 | 0.961 |
| Over the Rainbow (167 bpm grid) | 2 (0.52) | 0 | 0 | 0.342 vs 0.411 at phase 0 |

The chroma rule picks the right phase on 2 of 2 halved songs and agrees with the modal downbeat phase on 4 of 4 correct-octave grids; the one disagreement is on the wrong-octave Rainbow grid, where the chroma rule agrees with the chord model instead. Summary for the question asked: nominal tempo 5/5 (fixed rule), right phase 5/5 (modal phase where un-halved, chroma rule where halved).

Final Fix A grids: Summer of '69 136.4 bpm, 119 bars of 1.74 s; Pour Some Sugar 85.7, 93 of 2.82 s; Riptide 103.4, 83 of 2.36 s; I'm Yours 75.0, 75 of 3.18 s; Over the Rainbow 85.7, 73 of 2.82 s.

---

## Fix B: k selection, minimum segment length, labelling (on the Fix A grids)

Scores are hits against the hard reference boundaries within 1 bar and within 2 bars (tolerance n x median bar length + 0.05 s), precision at 1 and 2 bars, segment count. Silhouette rows are shown once per song: the silhouette on the Laplacian embedding decreases monotonically with k on every song (Summer of '69 0.86 / 0.75 / 0.63 / 0.58 for k 3..6, Rainbow 0.59 / 0.55 / 0.53 / 0.49) and always picks k = 3.

**Summer of '69** (119 bars, 1.74 s; hand list, 12 boundaries incl. a 2-bar riff and a 1-bar riff):

| variant | k | segs | hits @1 | hits @2 | P@1 | P@2 | labels (start s) |
|---|---|---|---|---|---|---|---|
| plan, any minimum | 4 | 10 | 6/12 | 8/12 | 0.56 | 0.67 | verse 0.4, chorus 33.4, verse 52.4, chorus 69.8, verse 90.6, bridge 100.9, verse 118.3, chorus 142.5, verse 163.3, outro 192.7 |
| split60, any minimum | 4 (share 0.55) | 10 | 6/12 | 8/12 | 0.56 | 0.67 | identical |
| silhouette | 3 | 4 | 2/12 | 3/12 | 0.33 | 0.67 | verse, chorus 100.9 (the bridge), verse, outro |

Misses are the intro/verse split at 3.9 s (same progression), the 2-bar riff at 49.0 (merged into the next verse boundary at 52.4, within 2 bars), the chorus/riff boundaries that the chord-derived round-1 reference also merged, and solo 114.8 / breakdown 128.6 (same progression as the verse). The chorus cluster is right (c2 at -12.1 dB vs verse c1 -13.3; the once-only bridge c0 is the loudest at -11.0 and is excluded by the recurrence requirement).

**Pour Some Sugar** (93 bars, 2.82 s; hand list, 11 boundaries):

| variant | k | segs | hits @1 | hits @2 | P@1 | P@2 | labels |
|---|---|---|---|---|---|---|---|
| plan or split60, 2 bars or 5 s | 3 (share 0.54) | 7 | 3/11 | 4/11 | 0.50 | 0.67 | intro 0.4, verse 51.3 (2-bar pre-chorus), chorus 56.9, verse 82.3, chorus 138.8, verse 161.4, chorus 215.1 |
| plan or split60, 7 s | 3 | 4 | 1/11 | 3/11 | 0.33 | 0.67 | chorus 0.4, verse 51.3, bridge 138.8, verse 161.4 |
| plan or split60, 10 s | 3 | 2 | 0/11 | 2/11 | 0.00 | 1.00 | chorus 0.4, verse 51.3 |

The 7 s minimum deletes the real 2-bar pre-chorus (5.6 s at 85 bpm): the merge drops the boundary at its end, so the chorus start moves to 51.3 and the chorus inherits the pre-chorus cluster; the chorus label is then lost entirely. The hand list's intro / riff / verse / verse_b boundaries (6.1, 17.4, 34.3, 45.6) all sit on the C#m riff progression and are not separable by chroma, which caps the recall at about 5/11 for any k; the three choruses are found exactly at 56.9 and 215.1 and within 1.4 bars at 138.8 vs the hand list's 124.7 (the hand list starts chorus 2 at the pre-chorus; round 1's chord-derived reference put it at 136.0).

**Riptide** (83 bars, 2.36 s; judged by recurrence/novelty only, 14 hard):

| variant | k | segs | hits @1 | hits @2 | P@1 | P@2 | labels |
|---|---|---|---|---|---|---|---|
| plan, 2 bars / 5 s / 7 s | 3 | 5 | 3/14 | 5/14 | 0.75 | 1.00 | chorus 1.0 (intro, wrong), verse 23.1 (one 107 s block), bridge 130.5, chorus 137.7, verse 149.3 |
| **split60, 2 bars** | **5** (share 0.43) | 13 | **9/14** | 9/14 | 0.83 | 0.83 | verse 3 1.0, verse 2 20.6, verse 32.6, **chorus 39.4**, verse 62.7, **chorus 86.7**, verse 2 110.2, verse 125.9, bridge 130.5, verse 3 137.7, verse 2 147.0, verse 154.0, **chorus 158.6** |
| split60, 5 s | 5 | 11 | 8/14 | 9/14 | 0.80 | 0.80 | chorus and verse swapped (c3 -20.1 vs c0 -20.8 after the 2-bar segments merge) |
| split60, 7 s | 5 | 9 | 7/14 | 8/14 | 0.88 | 0.88 | as 2 bars minus the 2-bar segments |
| split60, 10 s | 5 | 8 | 6/14 | 7/14 | 0.86 | 0.86 | chorus moves to c3 |
| silhouette | 3 | 5 | 3/14 | 5/14 | 0.75 | 1.00 | as plan |

At k = 5 the quiet intro (1.0 s) and the quiet breakdown (137.7 s) share a cluster, the loud blocks 39.4 to 62.7, 86.7 to 110.2 and 158.6 to the end are the chorus cluster (c0, 36 bars, -19.8 dB) and the bridge (130.5, once) is found. The chorus margin is only 1.2 dB over c3 (-21.0), which is why the label flips once short segments are merged away; the stage should write the margin into `grid.json`. With k = 3 the 107 s body is one cluster of 66 of 83 bars (0.80), so the ">60% = verse" rule fires and makes it the verse; the only other recurring cluster is the quiet intro/breakdown pair (-28.7 dB), which the chorus rule then has to name chorus. The precondition alone cannot rescue a k that is too small; the iterative split fixes it by never leaving an 80% cluster in place.

**I'm Yours** (75 bars, 3.18 s; judged by recurrence/novelty only, 8 hard):

| variant | k | segs | hits @1 | hits @2 | P@1 | P@2 | labels |
|---|---|---|---|---|---|---|---|
| plan, any minimum | 3 | 4 (3 at 10 s) | 1/8 | 1/8 | 0.33 | 0.33 | intro 0.7, verse 23.0 (one 181 s block, 60 of 75 bars), chorus 204.2 (the scat outro, wrong), verse 229.6 |
| **split60, any minimum** | **5** (share 0.39) | 8 | **4/8** | **5/8** | 0.57 | 0.71 | intro 0.7, verse 13.4, **chorus 64.3**, bridge 121.5, verse 150.1, **chorus 181.9**, bridge 2 204.2, chorus 226.4 (fade tail) |
| silhouette | 3 | 4 | 1/8 | 1/8 | 0.33 | 0.33 | as plan |

With the segment-mean loudness used in `segment2.py` the fade tail (3 bars at -25 to -36 dB) pulled the loud cluster c1 to -17.0 dB and the quiet verse cluster c0 (-16.5) was called chorus; with the bar-weighted mean c1 is -14.0 dB and the labels are right (louder blocks at 64 and 182 s are the choruses). Misses: 89.8 (verse 2, same loop and loudness), 127.9 (the `F:dim` pre-chorus; found at 121.5, two bars early), 140.6 (found at 150.1).

**Over the Rainbow** (73 bars, 2.82 s; judged by recurrence/novelty only, 8 hard):

| variant | k | segs | hits @1 | hits @2 | P@1 | P@2 | labels |
|---|---|---|---|---|---|---|---|
| plan = split60 = silhouette, any minimum | 3 (share 0.48) | 6 | 2/8 | 4/8 | 0.40 | 0.80 | intro 3.0, verse 17.2, chorus 90.7, verse 124.6, chorus 138.5, verse 169.4 |

A clean A/B alternation with the louder type (-17.9 vs -19.9 dB) called chorus, as in round 2 but now on a regular grid; the 17.2 s boundary misses the reference 14.3 by 2.9 s (tolerance 2.87 s) and counts at 2 bars. The segmenter does not split the 73 s A block (17.2 to 90.7), which the loudness cues at 42.6, 59.7 and 85.1 say contains three sections.

### Summary across the five songs (hard boundaries)

| Song | plan rule @1 / @2 | split60 @1 / @2 | split60 k | chorus right |
|---|---|---|---|---|
| Summer of '69 | 6/12, 8/12 | 6/12, 8/12 | 4 | yes |
| Pour Some Sugar | 3/11, 4/11 | 3/11, 4/11 | 3 | yes (3 of 3) |
| Riptide | 3/14, 5/14 | **9/14, 9/14** | 5 | yes (margin 1.2 dB) |
| I'm Yours | 1/8, 1/8 | **4/8, 5/8** | 5 | yes (with bar-weighted loudness) |
| Over the Rainbow | 2/8, 4/8 | 2/8, 4/8 | 3 | plausible (A/B form) |
| total | 15/53, 22/53 | **24/53, 30/53** | | 5/5 |

The combination that works on all five is: split60 k rule, 2-bar minimum, bar-weighted loudness labeller with the >60% precondition. Its named failures: boundaries inside a shared progression are not found on any song (Pour Some Sugar intro/riff/verse, Summer of '69 solo/breakdown, I'm Yours verse 2, the Rainbow A block); the chorus margin on Riptide is 1.2 dB; the >60% rule never fired on the final grids (max share 0.55) because the iterative split removes the big cluster first, so it remains a safety net for `--sections-k` overrides only.

---

## Recommended exact rules for the plan (Task 8)

**Tempo and octave (`music/tempo.py`).**

1. `fill_gaps(beats, factor=1.6)`: for each interval greater than `factor` x the median of the surrounding 17 intervals, insert `round(gap / median) - 1` beats evenly spaced. Measured: Riptide 4 inserted (phase share 0.57 -> 0.81), Summer of '69 1, others 0.
2. `bpm_from_beats` = 60 / median interval after gap filling, rounded to an integer in the sheet header.
3. Octave rule (`options.beat_octave == "auto"`, the default): halve if and only if `bpm > 140 and 60 <= bpm / 2 <= 95`. Measured 5/5; `none`, `half` and `double` remain as explicit overrides because any real tempo in 141 to 190 bpm would be halved by this rule. Do not use `librosa.feature.tempo`, the onset autocorrelation peak, the modal phase share or chroma self-similarity for this decision (measured 2/5 to 4/5).
4. Halving is a local normalisation, not a global decimation: `normalise_octave(beats, downbeats, target_period = 2 x median interval, tol = 0.75)` drops every beat closer than `tol x target_period` to the last kept beat; the leading fast run starts at the beat whose index parity equals the modal downbeat parity. Measured: Over the Rainbow 207 beats dropped, 73 bars with max/median length 1.02 (global halving gave five 2x bars); I'm Yours 304 dropped, 75 bars.
5. Print the median bar length and the octave decision in the stage output (unchanged from round 2).

**Bar phase (`build_bars`).**

6. Modal downbeat phase: beat index mod `meter.numerator` over downbeats within 70 ms of a beat; measured shares 0.64 to 0.99 on the five final grids.
7. When the grid was halved (the two downbeat-carrying candidates are half a bar apart and the counts tie or nearly tie), resolve by chroma change: for each candidate build bars, take the mean chroma per bar (L2-normalised), compute the mean of `1 - cosine` between adjacent bars, and keep the phase with the larger value. Measured: right on 2/2 halved songs (0.151 vs 0.067; 0.208 vs 0.129), agrees with the modal phase on 4/4 un-halved grids. Untested extension: apply the same tie-break whenever the modal share is under 0.6.

**Segmentation (`music/sections.py`).**

8. `k` by iterative split: `k = 3`; while the largest cluster covers more than 60% of bars and `k < 6`, `k += 1`. Measured: 4, 3, 5, 5, 3 on the five songs; never worse than the plan rule, better on two. Keep `--sections-k` and write `k` and the largest cluster share into `grid.json`. Do not use silhouette (picks 3 on every song).
9. Minimum segment length: 2 bars, in bars, not seconds. 5 s is neutral on four songs and costs one hit on Riptide; 7 s and 10 s destroy the 2-bar pre-chorus on Pour Some Sugar. When a segment is too short, the boundary at its end is dropped (merge into the following segment); then merge adjacent segments with equal cluster ids.
10. Labeller order, with `bar_loudness_db` per bar and cluster loudness = the **bar-weighted** mean over all bars of the cluster (not the mean of segment means; measured swap on I'm Yours):
    1. a cluster covering more than 60% of all bars is `verse`;
    2. `chorus` = the loudest cluster among clusters occurring at least twice and not already `verse` (fallback: most bars);
    3. `verse`, if not set by rule 1, = the remaining recurring cluster with the most bars;
    4. a cluster occurring once: first segment `intro`, last segment `outro`, otherwise `bridge` (`bridge 2`, ... for further ones);
    5. other recurring clusters `verse 2`, `verse 3`, ...;
    6. write the chorus margin in dB (chorus loudness minus the next recurring cluster) to `grid.json`; flag the labels as low confidence when it is under 1.5 dB (Riptide 1.2 dB; the others 1.2 to 2.5 dB: Summer of '69 1.2, Pour Some Sugar 0.9 against the pre-chorus cluster but 3.4 against the verse cluster, I'm Yours 2.5, Rainbow 2.0).
11. Tests to add: a `fill_gaps` test with one dropped beat; a `normalise_octave` test with a beat list that is doubled for its first half only (the Rainbow case) asserting regular bar lengths; a phase tie-break test where two candidate phases tie on downbeats and only one coincides with chroma changes; a k test where one cluster holds 80% of the bars at k = 3 and splits at k = 4; a labeller test where the loud recurring cluster has a quiet fade tail (bar-weighted mean must still choose it).

---

## New confidence for Task 8: 85%

Up five points: the octave rule, phase rule, k rule and labeller are now measured on five songs and hold on all five, and two previously unseen grid defects (mid-song octave switches and dropped beats) have measured fixes; not higher because the octave rule is a bare threshold with a known fragile band, and chroma-based segmentation cannot find boundaries inside a shared progression (recall 4/11 on Pour Some Sugar's hand list, 5/8 on I'm Yours), so the stage still depends on `--beat-octave` and `--sections-k` for some songs.

## Side findings

- `librosa.beat.tempo` is gone in librosa 1.0.0; use `librosa.feature.tempo`.
- Beat This! `dbn=True` imports `madmom`, which is not in the venv; if the DBN is wanted as an octave cue it is a new dependency.
- The chord model `.lab` files for the three round-2 songs now exist in `SP\spike_grid3\` (12.5 to 14.9 s each on CPU). On the single-loop songs they are useless as section references but decisive for the bar phase (0.908 and 0.644 of chord changes on bar starts at the chosen phase).
- The recurrence images `rec_<song>.png` show the Riptide intro and breakdown as one cluster and I'm Yours as diagonals every 4 bars with no block structure; the segmenter's behaviour on both follows directly from that.
