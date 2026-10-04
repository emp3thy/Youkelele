# Research strand: splitting the guitar stem's onsets by pitch register

Date: 2026-10-04. Code read and run from worktree `v1-4`, then `v1-5` (the session moved; `music/onsets.py`, `music/as_played.py`, `music/recall.py` and `stages/strums.py` are byte-identical in both). Data: the seven run folders under `C:\Users\gethi\sources\Youkelele\runs` as written by version 1.4. No source file, test or run folder was changed. Throwaway scripts and data: `%TEMP%\youkelele-v15-research\register\` (`r1_features.py` to `r8_md.py`; per-onset features in `feat_<song>.json` and `feat_union_<song>.json`; section results in `split.json`, `band_400.json`, `band_1000.json`).

Bar and section numbers are 0-based grid bars, end exclusive, as in `grid.json`. Short names as in `strum-confidence.md`: S69, Chelsea, PSSOM, WetLeg, Fame, AFU, NYT. Ear labels: REJ (two guitars, pattern judged wrong: PSSOM 28-39, 55-67, 84-103), ACC (S69 41-53 and 83-95, Chelsea 20-38 and 108-142, the 1.4 cuts of the accepted 9-38 and 105-142), ACC exact (AFU 33-49, `DUDUDUDU`), RIFF ok (NYT 13-24, single-note riff, clicks "perfect"), RIFF+note (Fame 61-71, riff plus a repeated higher note).

## 1. Summary

1. **The register distribution of the stage's onsets is not bimodal where the owner hears two parts and unimodal where he hears one.** On the register of the energy each onset adds (the measure closest to "which part attacked"), the rejected PSSOM choruses have a k-means gap of 13.3 to 19.1 semitones and the accepted strums 10.9 to 15.4; a two-Gaussian fit is *rejected* by BIC on all three rejected choruses (dBIC -10.8 to -2.0). Six register estimates were tried; on none is every rejected section more bimodal than every accepted one on the generic measures (gap, cluster share, between-cluster variance share, BIC, Sarle's coefficient).
2. **The low stream never gives a pattern the stage could print on the rejected choruses.** Best low-stream confidence on any rejected section, over all six register estimates: **0.382** (PSSOM 28-39, lowest-strong-pitch split, `D-----D-D-D-DU-U`), against the sixteenth-grid floor of 0.55; the best on 55-67 is 0.267 and on 84-103 0.309. The low streams hold 0.7 to 4.5 strikes per bar on 16 slots: sparse, not a strum. Adding the high-band onsets first (the recall gate's union, which the stage does not use on this grid) lifts the best to 0.489, still under the floor.
3. **Forcing a split damages the accepted strums.** Splitting by onset flux register drops every accepted section's confidence (S69 41-53 0.778 to 0.544, Chelsea 108-142 0.711 to 0.456, AFU 33-49 `DUDUDUDU` 0.555 to `DUD-xUx-` 0.378), so a split can only be applied behind a rule that does not fire on them.
4. **One post-hoc rule separates the judged sections, with no margin.** On the lowest strong pitch, "k-means gap at least 17.5 semitones and smaller cluster at least 0.25 of the onsets" fires on the three rejected choruses and on no accepted section. It also fires on every other PSSOM section but the intro and on NYT's intro, all already uncertain, so it changes nothing printed; the nearest certain section it does not fire on sits 0.4 semitones under it (AFU 49-55, gap 17.2 against PSSOM 55-67 at 17.6). The PSSOM gap is about an octave and a fifth (17.6 to 21.6 semitones between cluster centres), where a distorted power chord's third harmonic lies, and pYIN puts 15 of the 18 "high" onsets of 28-39 on a low fundamental (D#2 to B2). It reads as a property of the song's distorted chord sound, not a second part.
5. **Verdict: null.** The owner's description is right for Need You Tonight (135 of 138 onsets in one register cluster) but the measurement cannot find the second part in Pour Some Sugar On Me or Fame, and the low register alone does not recover a strum. A band-limited low-register onset detector (variant B) saturates into a pulse (`DUDUDUDU` on nine of twelve Summer of '69 sections) and is worse.

## 2. Method

**Onsets.** The stage's own: `stages/strums.py` was replayed step for step (`choose_source`, `detect_onsets`, `choose_slots_per_bar`, `grid_fit`, `section_has_instrument`, the recall gate per section with `gate_section`, `_splice`, `mute_mask`, `quantise_bar`). The rebuilt bar vectors equal the stored `bar_onsets` on all 822 bars of the seven songs, and the recomputed section confidences equal the stored ones (including the five recall-boosted eighth-grid sections). All seven songs use the guitar stem.

**Register per onset**, window 40 to 130 ms after the onset (as in `s4_audio.py`: past the attack, inside the shortest sixteenth here), on the stem resampled to 22050 Hz, constant-Q power from C2 over 72 semitone bins (hop 256):

| name | definition |
|---|---|
| flux register | log-frequency centroid (MIDI) of the CQT power that is new at the onset: window mean less the mean of the 80 to 10 ms before the onset, negatives set to zero |
| CQT register | log-frequency centroid of the window's CQT power |
| peak | MIDI of the strongest CQT bin in the window |
| lowest strong | MIDI of the lowest CQT bin with at least a quarter of the window's maximum power |
| pYIN | median pYIN f0 over the window (80 to 1200 Hz, unvoiced frames keep their best guess), as MIDI |
| centroid | median spectral centroid over the window, as MIDI |

Energy per onset: the window's RMS in dB.

**Bimodality per section** (sections with at least 12 onsets; the window shifted back half a slot, as `quantise_bar` does): an exact one-dimensional 2-means (the split of the sorted values with the least within-cluster sum of squares), reported as the gap between the two centres in semitones, the smaller cluster's share of onsets and eta (between-cluster share of the variance; about 0.64 for a single Gaussian). Also a two-Gaussian fit by EM against one Gaussian, as dBIC (BIC of one less BIC of two; positive favours two), and Sarle's bimodality coefficient (above 0.555 suggests two modes).

**Streams.** Low stream: the section's onsets at or below the 2-means threshold; high stream: the rest. Each stream keeps every onset's mute flag from the full list, is quantised with `quantise_bar` on the song's grid and summarised with `section_summary`, exactly as the stage does; "certain" uses the grid's floor (0.45 on 8 slots, 0.55 on 16) and `explained` at least 0.6.

**Supplementary runs.** (a) On the three sixteenth-grid songs, the same split on the union of the stage's onsets and the high-band onsets (`detect_onsets(fmin=3000)`, merged beyond 60 ms as `recall.merge_onsets` does, no gate checks), to test whether the low stream is sparse only because distorted re-attacks are missed. (b) Variant B: a low-register onset list from librosa's default picker on an onset envelope averaged over mel bands up to 400 Hz or 1000 Hz only, mute rule over that list, then the stage's quantisation and summary.

## 3. Bimodality per section (question 1)

The two register estimates with the most physical meaning: flux register (what the onset added) and lowest strong pitch (the bass of the attack window). "rule fires" is the candidate rule of section 6 on lowest strong. AFU 124-128 (11 onsets) and Wet Leg's outro (no instrument) are left out.

| song | # | bars | label | slots | printed | ear | onsets | flux: gap | flux: smaller share | flux: eta | flux: dBIC | lowest-strong: gap | lowest-strong: smaller share | lowest-strong: dBIC | rule fires |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PSSOM | 0 | 0-11 | intro | 16 | uncertain |  | 91 | 19.7 | 0.44 | 0.69 | -8.5 | 19.5 | 0.21 | +153.0 |  |
| PSSOM | 1 | 11-28 | verse | 16 | uncertain |  | 104 | 20.6 | 0.46 | 0.71 | -4.1 | 21.1 | 0.34 | +21.4 | yes |
| PSSOM | 2 | 28-39 | chorus | 16 | uncertain | REJ | 71 | 19.1 | 0.45 | 0.72 | -8.0 | 19.9 | 0.25 | +21.5 | yes |
| PSSOM | 3 | 39-55 | verse | 16 | uncertain |  | 127 | 18.4 | 0.40 | 0.72 | -2.9 | 19.5 | 0.46 | +25.0 | yes |
| PSSOM | 4 | 55-67 | chorus | 16 | uncertain | REJ | 51 | 16.8 | 0.35 | 0.76 | -2.0 | 17.6 | 0.41 | +5.3 | yes |
| PSSOM | 5 | 67-77 | instrumental | 16 | uncertain |  | 93 | 19.7 | 0.32 | 0.58 | +2.1 | 23.6 | 0.27 | +21.2 | yes |
| PSSOM | 6 | 77-84 | verse | 16 | uncertain |  | 21 | 26.7 | 0.43 | 0.82 | -0.9 | 18.1 | 0.48 | +10.4 | yes |
| PSSOM | 7 | 84-103 | chorus | 16 | uncertain | REJ | 68 | 13.3 | 0.42 | 0.58 | -10.8 | 21.6 | 0.46 | +6.8 | yes |
| Fame | 0 | 0-17 | intro | 16 | certain |  | 146 | 24.1 | 0.25 | 0.69 | +17.6 | 16.5 | 0.44 | +18.8 |  |
| Fame | 1 | 17-29 | verse | 16 | certain |  | 126 | 14.7 | 0.26 | 0.66 | +26.2 | 10.1 | 0.43 | +47.7 |  |
| Fame | 2 | 29-35 | instrumental | 16 | certain |  | 62 | 17.7 | 0.10 | 0.54 | -2.1 | 8.6 | 0.42 | +24.1 |  |
| Fame | 3 | 35-47 | verse | 16 | certain |  | 113 | 15.1 | 0.34 | 0.59 | -5.6 | 9.9 | 0.44 | -2.2 |  |
| Fame | 4 | 47-61 | instrumental | 16 | certain |  | 122 | 13.7 | 0.32 | 0.59 | -7.1 | 12.7 | 0.32 | +10.4 |  |
| Fame | 5 | 61-71 | chorus | 16 | certain | RIFF+note | 114 | 23.0 | 0.29 | 0.70 | +4.8 | 33.5 | 0.06 | +32.1 |  |
| Fame | 6 | 71-81 | verse | 16 | certain |  | 120 | 14.4 | 0.33 | 0.63 | -1.2 | 10.7 | 0.29 | +139.6 |  |
| Fame | 7 | 81-85 | instrumental | 16 | certain |  | 33 | 12.6 | 0.30 | 0.72 | +3.3 | 8.6 | 0.48 | +16.7 |  |
| Fame | 8 | 85-100 | verse | 16 | certain |  | 164 | 17.9 | 0.30 | 0.78 | +49.6 | 11.9 | 0.13 | +221.7 |  |
| NYT | 0 | 0-13 | intro | 16 | uncertain |  | 36 | 23.4 | 0.43 | 0.82 | +3.7 | 35.5 | 0.25 | +15.9 | yes |
| NYT | 1 | 13-24 | verse | 16 | certain | RIFF ok | 138 | 17.5 | 0.16 | 0.76 | +141.2 | 9.4 | 0.02 | +45.5 |  |
| NYT | 2 | 24-31 | chorus | 16 | certain |  | 74 | 21.9 | 0.47 | 0.81 | +21.9 | 33.8 | 0.05 | +48.7 |  |
| NYT | 3 | 31-48 | verse | 16 | certain |  | 181 | 17.2 | 0.19 | 0.63 | +30.7 | 13.8 | 0.20 | +5.4 |  |
| NYT | 4 | 48-56 | chorus | 16 | certain |  | 82 | 19.2 | 0.34 | 0.78 | +45.0 | 12.9 | 0.09 | +2.0 |  |
| NYT | 5 | 56-79 | verse | 16 | certain |  | 228 | 19.0 | 0.21 | 0.61 | +26.2 | 13.3 | 0.35 | +18.2 |  |
| NYT | 6 | 79-84 | outro | 16 | uncertain |  | 46 | 16.3 | 0.33 | 0.82 | +11.5 | 11.3 | 0.24 | -10.9 |  |
| S69 | 0 | 0-4 | intro | 8 | certain |  | 21 | 19.9 | 0.38 | 0.83 | +1.2 | 25.0 | 0.24 | +45.8 |  |
| S69 | 1 | 4-19 | verse | 8 | certain |  | 95 | 18.4 | 0.22 | 0.71 | +11.3 | 13.9 | 0.14 | +55.5 |  |
| S69 | 2 | 19-31 | chorus | 8 | certain |  | 49 | 15.9 | 0.35 | 0.67 | -7.7 | 13.8 | 0.37 | -4.4 |  |
| S69 | 3 | 31-41 | verse | 8 | certain |  | 45 | 16.7 | 0.42 | 0.75 | -4.7 | 15.9 | 0.40 | -7.0 |  |
| S69 | 4 | 41-53 | chorus | 8 | certain | ACC | 65 | 13.1 | 0.34 | 0.66 | -3.4 | 16.7 | 0.17 | +9.4 |  |
| S69 | 5 | 53-58 | verse | 8 | certain |  | 26 | 9.2 | 0.38 | 0.68 | -7.3 | 10.2 | 0.27 | -6.1 |  |
| S69 | 6 | 58-68 | verse | 8 | certain |  | 33 | 10.7 | 0.39 | 0.68 | -10.6 | 15.1 | 0.42 | +1.8 |  |
| S69 | 7 | 68-75 | instrumental | 8 | certain |  | 47 | 11.7 | 0.49 | 0.77 | -4.0 | 12.3 | 0.45 | -8.4 |  |
| S69 | 8 | 75-83 | verse | 8 | certain |  | 36 | 14.9 | 0.47 | 0.78 | -2.1 | 12.2 | 0.19 | -5.7 |  |
| S69 | 9 | 83-95 | chorus | 8 | certain | ACC | 56 | 12.2 | 0.39 | 0.62 | -10.5 | 26.8 | 0.04 | +17.2 |  |
| S69 | 10 | 95-111 | verse | 8 | uncertain |  | 54 | 11.5 | 0.41 | 0.61 | -11.9 | 13.2 | 0.26 | +16.6 |  |
| S69 | 11 | 111-120 | outro | 8 | uncertain |  | 22 | 11.3 | 0.36 | 0.69 | -8.9 | 9.5 | 0.14 | +21.8 |  |
| Chelsea | 0 | 0-20 | intro | 8 | uncertain |  | 69 | 32.7 | 0.11 | 0.74 | +29.3 | 29.3 | 0.12 | +17.4 |  |
| Chelsea | 1 | 20-38 | chorus | 8 | certain | ACC | 95 | 15.4 | 0.46 | 0.72 | -7.4 | 11.8 | 0.46 | +14.7 |  |
| Chelsea | 2 | 38-61 | verse | 8 | certain |  | 108 | 13.0 | 0.27 | 0.57 | +9.0 | 11.0 | 0.44 | -14.3 |  |
| Chelsea | 3 | 61-71 | chorus | 8 | certain |  | 34 | 12.1 | 0.50 | 0.75 | -5.4 | 10.6 | 0.44 | +5.4 |  |
| Chelsea | 4 | 71-93 | verse | 8 | certain |  | 101 | 13.5 | 0.24 | 0.48 | +16.9 | 13.2 | 0.30 | +21.4 |  |
| Chelsea | 5 | 93-108 | instrumental | 8 | certain |  | 83 | 11.5 | 0.28 | 0.58 | -2.6 | 10.4 | 0.48 | -13.5 |  |
| Chelsea | 6 | 108-142 | chorus | 8 | certain | ACC | 187 | 13.0 | 0.35 | 0.68 | -8.3 | 11.1 | 0.29 | -16.2 |  |
| WetLeg | 0 | 0-5 | verse | 8 | certain |  | 31 | 15.0 | 0.35 | 0.64 | -5.3 | 7.2 | 0.45 | +20.7 |  |
| WetLeg | 1 | 5-18 | chorus | 8 | certain |  | 105 | 17.7 | 0.21 | 0.69 | +40.8 | 5.8 | 0.29 | +25.6 |  |
| WetLeg | 2 | 18-33 | verse | 8 | certain |  | 60 | 16.0 | 0.22 | 0.64 | +5.3 | 7.7 | 0.22 | -2.5 |  |
| WetLeg | 3 | 33-42 | chorus | 8 | certain |  | 71 | 8.7 | 0.39 | 0.68 | -12.3 | 6.4 | 0.25 | -1.3 |  |
| WetLeg | 4 | 42-58 | verse | 8 | certain |  | 124 | 17.1 | 0.19 | 0.70 | +22.8 | 5.7 | 0.29 | +17.7 |  |
| WetLeg | 5 | 58-65 | verse | 8 | certain |  | 38 | 11.2 | 0.50 | 0.70 | -11.0 | 8.3 | 0.47 | +21.1 |  |
| WetLeg | 6 | 65-100 | verse | 8 | certain |  | 291 | 13.2 | 0.27 | 0.65 | +36.9 | 7.2 | 0.28 | +18.2 |  |
| WetLeg | 7 | 100-108 | chorus | 8 | certain |  | 58 | 7.9 | 0.47 | 0.64 | -9.3 | 7.3 | 0.41 | -6.1 |  |
| AFU | 0 | 0-28 | intro | 8 | uncertain |  | 110 | 15.1 | 0.21 | 0.57 | +3.1 | 12.7 | 0.30 | +89.2 |  |
| AFU | 1 | 28-33 | verse | 8 | certain |  | 30 | 9.1 | 0.43 | 0.57 | +1.7 | 7.3 | 0.07 | +28.6 |  |
| AFU | 2 | 33-49 | verse | 8 | certain | ACC exact | 95 | 10.9 | 0.39 | 0.66 | -13.9 | 11.6 | 0.41 | +35.6 |  |
| AFU | 3 | 49-55 | chorus | 8 | certain |  | 30 | 16.1 | 0.30 | 0.63 | -4.5 | 17.2 | 0.47 | +20.7 |  |
| AFU | 4 | 55-61 | verse | 8 | certain |  | 31 | 19.8 | 0.10 | 0.62 | +6.2 | 12.5 | 0.29 | +35.0 |  |
| AFU | 5 | 61-90 | verse | 8 | certain |  | 122 | 15.2 | 0.32 | 0.62 | -8.4 | 13.6 | 0.40 | +48.4 |  |
| AFU | 6 | 90-97 | verse | 8 | uncertain |  | 39 | 21.7 | 0.13 | 0.65 | +11.4 | 14.2 | 0.23 | +46.1 |  |
| AFU | 7 | 97-104 | verse | 8 | certain |  | 65 | 11.7 | 0.40 | 0.75 | -1.6 | 13.5 | 0.45 | +49.0 |  |
| AFU | 8 | 104-110 | verse | 8 | certain |  | 41 | 19.2 | 0.10 | 0.63 | +4.8 | 13.4 | 0.46 | +30.0 |  |
| AFU | 9 | 110-124 | chorus | 8 | uncertain |  | 31 | 14.0 | 0.26 | 0.71 | -1.2 | 11.9 | 0.35 | +13.3 |  |
| AFU | 11 | 128-132 | chorus | 8 | certain |  | 14 | 16.9 | 0.21 | 0.76 | -0.1 | 9.7 | 0.43 | +4.3 |  |
| AFU | 12 | 132-156 | outro | 8 | certain |  | 99 | 16.5 | 0.38 | 0.69 | -6.9 | 14.0 | 0.37 | +67.7 |  |

Group ranges for all six estimates. "Two-part" = REJ plus Fame 61-71; "one-part" = ACC, ACC exact and NYT 13-24. Margin = lowest two-part value less highest one-part value (positive would separate).

| estimate | statistic | REJ (3) | ACC (5) | margin REJ over ACC | margin two-part over one-part |
|---|---|---|---|---|---|
| flux register | gap (semitones) | 13.3 to 19.1 | 10.9 to 15.4 | -2.1 | -4.2 |
| flux register | smaller share | 0.35 to 0.45 | 0.34 to 0.46 | -0.11 | -0.17 |
| flux register | eta | 0.58 to 0.76 | 0.62 to 0.72 | -0.14 | -0.18 |
| flux register | dBIC | -10.8 to -2.0 | -13.9 to -3.4 | -7.4 | -152.0 |
| flux register | Sarle | 0.25 to 0.48 | 0.25 to 0.48 | -0.23 | -0.35 |
| CQT register | gap | 9.7 to 12.5 | 7.0 to 9.9 | -0.2 | -7.7 |
| CQT register | dBIC | -12.9 to -5.2 | -16.7 to +1.1 | -14.0 | -177.2 |
| peak | gap | 21.5 to 23.0 | 11.8 to 18.6 | +3.0 | -16.1 |
| peak | smaller share | 0.16 to 0.32 | 0.27 to 0.49 | -0.34 | -0.34 |
| lowest strong | gap | 17.6 to 21.6 | 11.1 to 26.8 | -9.2 | -9.2 |
| lowest strong | smaller share | 0.25 to 0.46 | 0.04 to 0.46 | -0.21 | -0.40 |
| lowest strong | eta | 0.77 to 0.80 | 0.48 to 0.80 | -0.03 | -0.23 |
| lowest strong | dBIC | +5.3 to +21.5 | -16.2 to +35.6 | -30.3 | -40.2 |
| lowest strong | Sarle | 0.52 to 0.63 | 0.34 to 0.51 | +0.01 | -0.02 |
| pYIN | gap | 7.4 to 22.5 | 5.8 to 9.5 | -2.0 | -7.4 |
| pYIN | dBIC | +44.3 to +77.1 | -13.2 to +102.8 | -58.5 | -217.8 |
| centroid | gap | 3.7 to 6.1 | 3.0 to 16.5 | -12.8 | -12.8 |

Reading:

- **Every section is "two-cluster" by gap.** On flux register and lowest strong the 2-means gap is 5.7 to 35.5 semitones, and above 7 in all but three, because each estimate is broad: a strummed chord's window holds six strings and their harmonics, so a few semitones of noise in each onset's estimate spread a single part over an octave or more. The gap alone carries no information; it has to be read with the share, eta and BIC.
- **The flux register, which isolates what the onset added, calls the rejected choruses unimodal.** dBIC is negative on all three (-10.8 to -2.0) and eta (0.58 to 0.76) brackets the single-Gaussian 0.64. If a riff were attacking in a higher register than the chords, this is where it should show.
- **The two positive margins are on unusable statistics.** Peak gap separates REJ from ACC by 3.0 semitones, but NYT 13-24 (one part, by ear) has 37.7 and Fame's sections up to 37.8: the strongest CQT bin jumps between harmonics. Sarle's coefficient on lowest strong separates by 0.01.
- **Need You Tonight agrees with the owner.** On lowest strong, 135 of 138 onsets of 13-24 fall in one cluster (C#4 centre; the other three are in the last bar). On flux register the smaller cluster is 16 percent. A single-note riff is one register stream here.
- **Fame's "repeated higher note" is not found.** Lowest strong puts 7 of 114 onsets of 61-71 in a high cluster (A5 to C7, spectral centroid D7 to F7), at slots 5, 6, 6, 8, 8, 13 and 15 of bars 62 to 68: no repeated slot, and the register is that of cymbal bleed or pick noise rather than a guitar note. On flux register the smaller cluster (29 percent) gives a high stream of `-U----D---------` at 0.412: no repeated note either.
- **Energy does not separate the parts.** Median window energy of the low and high lowest-strong clusters: PSSOM 28-39 -33.6 and -37.0 dB, 55-67 -32.8 and -32.0 dB, 84-103 -32.5 and -31.5 dB; the five accepted sections differ by 0.1 to 0.8 dB.

## 4. The low stream's pattern (question 2)

Patterns before and after the split, for every PSSOM section and every judged section. "stage" = the stage's onsets; "stage + high band" = the union of section 2(a). Confidence floor: 0.55 on 16 slots, 0.45 on 8.

| onsets | split on | song | bars | ear | full pattern | full conf | low pattern | low conf | low strikes/bar | high pattern | high conf | high strikes/bar |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| stage | flux | PSSOM | 0-11 |  | `DUDUDUDUDUD-D-DU` | 0.447 | `---UD---D-------` | 0.258 | 3.3 | `-----U-U-UD-D---` | 0.226 | 4.3 |
| stage | flux | PSSOM | 11-28 |  | `D-D--UDU----DU--` | 0.378 | `-----U-------U--` | 0.162 | 2.5 | `-------U--------` | 0.281 | 2.4 |
| stage | flux | PSSOM | 28-39 | REJ | `D--UD-D-D-D-DU-U` | 0.453 | `----D-------D---` | 0.308 | 2.8 | `D--U----D------U` | 0.342 | 3.1 |
| stage | flux | PSSOM | 39-55 |  | `DU--DxDU-UDUDU-U` | 0.467 | `D---Dx----------` | 0.201 | 3.1 | `-------U--DU-U-U` | 0.364 | 4.5 |
| stage | flux | PSSOM | 55-67 | REJ | `----D---D-D-D---` | 0.312 | `------------D---` | 0.212 | 1.5 | `------D-D-------` | 0.222 | 2.7 |
| stage | flux | PSSOM | 67-77 |  | `DU-UxUDU-UDUDUDU` | 0.504 | `----D-------D---` | 0.163 | 2.6 | `DU-UDUDU-U---UDU` | 0.387 | 5.6 |
| stage | flux | PSSOM | 77-84 |  | `D----------U----` | 0.208 | `D---------------` | 0.214 | 1.4 | `------D---------` | 0.214 | 1.3 |
| stage | flux | PSSOM | 84-103 | REJ | `D---D---D---D--U` | 0.361 | `------------D---` | 0.167 | 1.4 | `--------D-------` | 0.177 | 1.9 |
| stage | flux | Fame | 61-71 | RIFF+note | `DUDUDUD---D-DUD-` | 0.719 | `D-DUD-----D-D-D-` | 0.734 | 7.2 | `-U----D---------` | 0.412 | 3.0 |
| stage | flux | NYT | 13-24 | RIFF ok | `DUD-D-D-DUxUxU-U` | 0.815 | `DUD-D-D-DUxU-U-U` | 0.751 | 9.1 | `D---------------` | 0.399 | 2.0 |
| stage | flux | S69 | 41-53 | ACC | `D-DUDUD-` | 0.778 | `D-D-DUD-` | 0.544 | 3.4 | `D--U----` | 0.314 | 1.8 |
| stage | flux | S69 | 83-95 | ACC | `D-DUDUD-` | 0.704 | `----D-D-` | 0.353 | 1.8 | `D-D---D-` | 0.458 | 2.8 |
| stage | flux | Chelsea | 20-38 | ACC | `D-D-D-DU` | 0.775 | `D---D-DU` | 0.414 | 2.4 | `D-D---D-` | 0.474 | 2.3 |
| stage | flux | Chelsea | 108-142 | ACC | `D-DUDUDU` | 0.711 | `D-DUD-DU` | 0.456 | 3.4 | `--D-D-D-` | 0.323 | 1.9 |
| stage | flux | AFU | 33-49 | ACC exact | `DUDUDUDU` | 0.555 | `DUD-xUx-` | 0.378 | 3.4 | `D---D--U` | 0.334 | 2.1 |
| stage | lowest strong | PSSOM | 0-11 |  | `DUDUDUDUDUD-D-DU` | 0.467 | `D--UDUDUDUD-D-D-` | 0.401 | 6.2 | `-------U--------` | 0.125 | 1.6 |
| stage | lowest strong | PSSOM | 11-28 |  | `D-D--UDU----DU--` | 0.369 | `D------U----DU--` | 0.232 | 3.2 | `-------U--------` | 0.068 | 1.7 |
| stage | lowest strong | PSSOM | 28-39 | REJ | `D--UD-D-D-D-DU-U` | 0.453 | `D-----D-D-D-DU-U` | 0.382 | 4.5 | `----D-----------` | 0.167 | 1.5 |
| stage | lowest strong | PSSOM | 39-55 |  | `DU--DxDU-UDUDU-U` | 0.472 | `D-----DU-U---U--` | 0.225 | 4.0 | `----D------UD---` | 0.218 | 3.5 |
| stage | lowest strong | PSSOM | 55-67 | REJ | `----D---D-D-D---` | 0.312 | `----------D-D---` | 0.251 | 2.5 | `-------U--------` | 0.181 | 1.7 |
| stage | lowest strong | PSSOM | 67-77 |  | `DU-UxUDU-UDUDUDU` | 0.504 | `------------D---` | 0.225 | 2.2 | `DU-UxUDU-U-----U` | 0.357 | 5.8 |
| stage | lowest strong | PSSOM | 77-84 |  | `D----------U----` | 0.208 | `------D---------` | 0.214 | 1.3 | `----------------` | 0.571 | 1.3 |
| stage | lowest strong | PSSOM | 84-103 | REJ | `D---D---D---D--U` | 0.359 | `------------D---` | 0.175 | 1.9 | `--------D-------` | 0.164 | 1.6 |
| stage | lowest strong | Fame | 61-71 | RIFF+note | `DUDUDUD---D-DUD-` | 0.724 | `DUDUDUD---D-D-D-` | 0.737 | 9.6 | `----------------` | 0.600 | 0.7 |
| stage | lowest strong | NYT | 13-24 | RIFF ok | `DUD-D-D-DUxUxU-U` | 0.815 | `DUD-D-D-DUxUxU-U` | 0.808 | 10.7 | `----------------` | 0.909 | 0.3 |
| stage | lowest strong | S69 | 41-53 | ACC | `D-DUDUD-` | 0.778 | `--------` | 0.500 | 0.9 | `D-DUDUD-` | 0.625 | 4.2 |
| stage | lowest strong | S69 | 83-95 | ACC | `D-DUDUD-` | 0.704 | `D-DUDUD-` | 0.679 | 4.4 | `--------` | 0.833 | 0.2 |
| stage | lowest strong | Chelsea | 20-38 | ACC | `D-D-D-DU` | 0.775 | `--D-D-DU` | 0.455 | 2.6 | `D-D-D-D-` | 0.440 | 2.3 |
| stage | lowest strong | Chelsea | 108-142 | ACC | `D-DUDUDU` | 0.711 | `D-DUDUDU` | 0.503 | 3.6 | `--D-----` | 0.186 | 1.6 |
| stage | lowest strong | AFU | 33-49 | ACC exact | `DUDUDUDU` | 0.555 | `D-D-----` | 0.223 | 2.3 | `D-D-D-D-` | 0.324 | 3.1 |
| stage + high band | flux | PSSOM | 28-39 | REJ | `DUDUDUD-D-D-DUDU` | 0.616 | `D-D-D-----D-D-D-` | 0.425 | 4.3 | `D-DU-U--D-D--U-U` | 0.456 | 5.4 |
| stage + high band | flux | PSSOM | 55-67 | REJ | `D-DUD-DUD-D-D-DU` | 0.606 | `--D-D-----D-D---` | 0.402 | 3.7 | `D--U--DUD------U` | 0.398 | 5.6 |
| stage + high band | flux | PSSOM | 84-103 | REJ | `D-DUD-DUD-DUD-DU` | 0.616 | `D-D-D-------D---` | 0.370 | 4.8 | `D-D-D-DUD-D----U` | 0.413 | 5.2 |
| stage + high band | lowest strong | PSSOM | 28-39 | REJ | `DUDUDUD-D-D-DUDU` | 0.616 | `DUD-D-D-D-D-DUDU` | 0.481 | 6.9 | `----D---D---D--U` | 0.270 | 2.8 |
| stage + high band | lowest strong | PSSOM | 55-67 | REJ | `D-DUD-DUD-D-D-DU` | 0.606 | `D-DUD---D-D-D---` | 0.448 | 5.4 | `------DU-------U` | 0.236 | 3.5 |
| stage + high band | lowest strong | PSSOM | 84-103 | REJ | `D-DUD-DUD-DUDUDU` | 0.613 | `D-DUD---D-D-D--U` | 0.489 | 6.6 | `----D--UD------U` | 0.270 | 3.1 |
| stage + high band | lowest strong | Fame | 61-71 | RIFF+note | `DUDUDUD---D-DUDU` | 0.718 | `DUDUDUD---D-D-D-` | 0.746 | 9.7 | `----------------` | 0.600 | 0.8 |
| stage + high band | lowest strong | NYT | 13-24 | RIFF ok | `DUD-D-D-DUxUxU-U` | 0.817 | `DUD-D-D-DUxUxU-U` | 0.812 | 11.5 | `----------------` | 0.909 | 0.3 |

The other four estimates give lower low-stream confidences on the rejected choruses (CQT register 0.158 to 0.358, peak 0.149 to 0.250, pYIN 0.235 to 0.309, centroid 0.189 to 0.282).

Reading:

- **On the stage's onsets the rejected choruses do not hold enough strikes to split.** The full stem gives 3.4 to 5.8 strikes per bar on 16 slots; splitting that leaves 0.7 to 4.5 in the low stream across the six estimates. No low stream reaches the floor (best 0.382); none is regular or dense; the high streams are no better (0.164 to 0.342 on flux register and lowest strong).
- **With the high-band onsets added, the full-stem pattern itself turns certain on all three rejected choruses** (0.606 to 0.616, `explained` 0.87 to 0.94), which confirms why the recall gate is off on the sixteenth grid. The low stream of that union is denser (5.4 to 6.9 strikes per bar) and reads more like a strum (`D-DUD---D-D-D--U` on 84-103) but stays under the floor (0.448 to 0.489). Whether that low-stream pattern is what the rhythm guitar plays has not been heard.
- **Where the full pattern was already good (Fame 61-71, NYT 13-24), the low stream is the full pattern**, because the high cluster is 2 to 6 percent of onsets.

## 5. Harm on the accepted strums (question 3)

- **A forced split harms every accepted section.** On flux register every accepted section loses confidence, by 0.177 to 0.361, and three of the five fall under the eighth-grid floor (S69 83-95 0.353, Chelsea 20-38 0.414, AFU 33-49 0.378). On lowest strong, S69 41-53's low stream is empty (11 onsets, 17 semitones below the rest; `--------`, 0.9 strikes per bar), and AFU's exact `DUDUDUDU` becomes `D-D-----` at 0.223. The accepted strums split at about an octave (F2 against F3 on AFU 33-49, F#2 against F3 on Chelsea 20-38): one chord read at its root or at its octave.
- **Behind the candidate rule (section 6) nothing accepted is touched**: the rule fires on no accepted section and on no certain section of the seven songs, so AFU's exact verse and all four accepted choruses print unchanged.
- **Variant B (low-band onset envelope) fails this check.** At 400 Hz it fires on nearly every slot: nine of twelve Summer of '69 sections become `DUDUDUDU` (confidence 0.856 to 0.984, 6.9 to 7.9 strikes per bar on 8 slots, including the ear-accepted `D-DUDUD-` choruses), and PSSOM's rejected choruses become `DUDUDUDUDUDUDUDU` at 0.72 to 0.85 (12 to 14 strikes per bar), certain. At 1000 Hz Chelsea 108-142 drops to `D-D-D-DU` at 0.419 and AFU 33-49 to `DUDxDU-U` at 0.447, both uncertain. A low-band envelope tracks the pulse (bass and kick bleed in the stem, the same bleed `strum-confidence.md` section 7.3 found), not the strum.

## 6. Candidate rule and bands (question 4)

**Rule (lowest strong pitch, stage onsets): a section holds two register streams when the exact 2-means gap of its onsets' lowest strong CQT pitch is at least 17.5 semitones and the smaller cluster holds at least 0.25 of the onsets.**

Bands across the sections:

| quantity | fires (REJ) | fires (unjudged) | nearest that does not fire | margin |
|---|---|---|---|---|
| gap | 17.6 to 21.6 | 18.1 to 35.5 (PSSOM 1, 3, 5, 6; NYT 0) | AFU 49-55 at 17.2 (share 0.47, certain); Fame 0-17 at 16.5 (0.44, certain); S69 41-53 at 16.7 (0.17, ACC) | 0.4 semitones |
| smaller share | 0.25 to 0.46 | 0.25 to 0.48 | S69 0-4 at 0.24 (gap 25.0, certain); PSSOM 0-11 at 0.21 (gap 19.5); S69 83-95 at 0.04 (gap 26.8, ACC) | 0.01 |

The rule fires on 8 of 63 analysed sections: the three rejected choruses, four other PSSOM sections and NYT's intro (exactly 0.25). All 8 are already uncertain, so it changes nothing printed on these seven songs. It was chosen after the fact from six estimates and a grid of thresholds against eight labelled sections; the other estimates' best rules catch two of three rejected sections, or catch all three only together with 13 unjudged sections (peak).

What the rule most likely measures: the cluster centres of the rejected choruses are 17.6 to 21.6 semitones apart (A#2 to B2 against E4 to G4), near the 19 semitones of a power chord's third harmonic, and pYIN on the "high" onsets of 28-39 finds a low fundamental in 15 of 18. Distorted power chords whose fundamental drops below a quarter of the strongest partial put their lowest strong bin an octave and a fifth up. That is a property of PSSOM's guitar sound, which the rule cannot tell from a second part; it is also why the rule fires on PSSOM's verses and instrumental.

How it would slot into `stages/strums.py`, if pursued:

1. `music/onsets.py`: a second librosa call, `onset_register(y, sr, times) -> np.ndarray`, returning each onset's lowest strong CQT pitch (72-bin CQT from C2 on the stem, window 40 to 130 ms after the onset, threshold a quarter of the window's maximum). The stage's onset detector is injectable for tests, so this would need the same seam.
2. `music/as_played.py`: `two_streams(registers) -> bool` with the exact 2-means and the two constants `TWO_STREAM_GAP = 17.5` and `TWO_STREAM_SHARE = 0.25`.
3. `stages/strums.py`, in the per-section loop beside the `uncertain = confidence < floor or ...` line: compute the section's onsets' registers (with the half-slot shift of `quantise_bar`) and add `or two_streams(...)` to `uncertain`, with a new `SectionPattern` field naming the reason. The pattern is not replaced by the low stream's, because section 4 shows the low stream is not a printable pattern.

As a guard it would only matter if something else lifted a two-part section over the floor, for example enabling the recall gate on the sixteenth grid (section 4: the union prints the rejected choruses certain at 0.61). On these songs its margin to a certain section it must not touch (AFU 49-55) is 0.4 semitones.

## 7. Verdict

**Null.** The register of the stage's onsets does not split into two streams where the owner hears two guitars and stay whole where he hears one: the generic bimodality measures overlap between rejected and accepted sections on all six register estimates, and the estimate best suited to the question (flux register) calls the rejected choruses unimodal. The low-register stream never reaches the sixteenth-grid floor on a rejected chorus (best **0.382** against 0.55; 0.489 with the high-band union) and forcing the split degrades every accepted strum. The only separating rule is post hoc, has a 0.4-semitone margin, fires on whole songs rather than on parts and changes nothing printed. The owner's description holds for Need You Tonight (one register stream) and is not visible in the audio features for Pour Some Sugar On Me and Fame.

## 8. Risks

- **Mixtures in the window.** When a riff note sounds over a ringing chord, the 40 to 130 ms window holds both, so every whole-window estimate (CQT register, peak, lowest strong, pYIN, centroid) sees the chord. The flux register removes what was already sounding, but on a distorted, compressed stem the chord's own re-attack and the riff note add energy in overlapping bands. A null here may be a limit of these estimates, not proof that the registers overlap.
- **Detection before register.** On PSSOM's choruses the stage detects only 3.4 to 5.8 onsets per bar. If the strummed part's re-attacks are missing, no split of the detected onsets can recover them; the high-band union suggests they are partly there to be found, at the cost of making the full pattern print certain.
- **The candidate rule is a selected result** (six estimates, a 2-D threshold grid, eight labelled sections, three of them from one song), and it may be a fingerprint of PSSOM's distortion. A new song with heavily distorted power chords could fire it on a single strummed part.
- **Ground truth is thin.** Three rejected sections from one song, of which only the last chorus was ear-checked by click track (A3 of `strum-confidence.md`); Fame 61-71's second part is described, not located; no low-stream pattern has been heard.
- **Variant B's thresholds were not tuned** (two cut-offs, librosa's default picker). A tuned low-band picker may stop saturating, but it would still be counting bass and kick bleed.

## 9. Assumptions

| # | assumption | status | cost if wrong |
|---|---|---|---|
| A1 | The rebuilt onsets are the stage's onsets | **Verified**: rebuilt bar vectors equal stored `bar_onsets` on all 822 bars; section confidences equal stored ones | none found |
| A2 | A 40 to 130 ms window after the onset is the right place to read the attacking part's register | Assumed from `s4_audio.py`; not varied | a shorter window nearer the attack might separate a riff note from a ringing chord; the null could be the window's |
| A3 | Lowest strong at a quarter of the window maximum, and flux register as the positive CQT change over the 80 to 10 ms before, are fair register estimates | Judgement; four further estimates gave the same answer | another estimate (a multi-pitch transcriber, a trained guitar-part separator) could find two streams these miss |
| A4 | An exact 1-D 2-means with gap and smaller share is a fair test of "two streams" | Measured alongside eta, two-Gaussian BIC and Sarle's coefficient, which agree | a mixture of more than two registers (bass bleed, chord, riff) could hide two parts inside three clusters |
| A5 | PSSOM 28-39 and 55-67 are two-guitar sections like 84-103 | Unverified (as A3 in `strum-confidence.md`) | the rejected set is one section; the low-stream result (best 0.309 on 84-103) does not change |
| A6 | The owner's "riff consistently higher than the chords" means higher fundamentals at the riff's onsets | Interpretation of a listening note | if the riff is higher only in timbre or octave doubling, register is the wrong axis and so is this test |
| A7 | The union run (stage onsets plus every high-band onset beyond 60 ms) approximates what a sixteenth-grid recall gate would admit | Assumed; no gate checks were applied | a gated union would add fewer onsets, so its low stream would be sparser still |
| A8 | The mute flags of the full onset list are right for each stream | Assumed; `mute_mask` uses the song median over all onsets | small: the rejected choruses' low streams contain no mutes |
| A9 | The 0.55 and 0.45 floors and `explained` at least 0.6 are the bar a stream must meet | Taken from `as_played.py` unchanged | a lower floor for a split stream would be a new, unsupported threshold |
