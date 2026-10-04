# Riff thresholds: spike for assumption A17

Measured on 2026-10-04 with throwaway scripts (`C:\Users\gethi\AppData\Local\Temp\youkelele-v15-research\riff\`); no source file, test or run folder was changed. Spec reference: section 4.3 of `docs/superpowers/specs/2026-10-04-ukulele-tab-chain-v1-5-design.md`.

## Summary

1. The rule as the spec words it (entropy of the section's mean onset chroma) does not work: it marks none of the 14 riff rows (all of Fame and the five Need You Tonight sections) as riff. The spec's own constants table was measured with the **median of the per-onset chroma entropies**, and the rule works on that: with it every truth row is classified as the ear did except one.
2. The one miss is All Fired Up 33-49, which the ear called strum and both features call riff, in all three windows, by a wide margin (it sits inside the riff cluster on both features and on both candidate third features). No threshold fixes it without breaking riff rows.
3. The margins are thin on the riff side: entropy 0.80 has +0.012 (Need You Tonight 24-31 at 0.788), single share 0.45 has +0.016 (Fame 0-17 at 0.466). At the 50 to 150 ms window Need You Tonight 24-31 moves to 0.811 and fails the entropy threshold. Moving the entropy ceiling to 0.82 makes all three windows classify the truth rows identically (still with the All Fired Up miss).
4. The Pour Some Sugar On Me margin on single share is 0.152 on the three truth rows (0.314 against 0.466) and 0.040 only if every section of that song is treated as two-guitar (the unlabelled 67-77 sits at 0.426). Entropy keeps the three truth rows 0.115 or more above the 0.80 ceiling.
5. Neither third feature widens the Pour Some Sugar On Me margin once its unlabelled sections count (pYIN voiced probability of 67-77 is 0.120, above Fame's lowest 0.092). On truth rows alone, voiced probability separates all non-riff rows except All Fired Up 33-49 more cleanly than single share does, but it needs a pYIN pass the stage does not make today.

## Method

- **Signal and onsets.** Each song's `01_separate/stems/guitar.wav` (stereo mean, native sample rate), through `youkelele.music.onsets.detect_onsets(y, sr)` with no `fmin`: the call `StrumsStage.run` makes on the guitar stem. All seven songs' `strums.json` record `source: guitar_stem`, so this is the stage's own signal. The recall gate's extra onsets are not added; the gate runs on the same detector but its spliced onsets are not part of what the spike measured.
- **Chroma.** Per `s4_audio.py`: stem resampled to 22 050 Hz, constant-Q power from C2, 72 bins at 12 per octave, folded over the six octaves, hop 256. Per onset, the mean over the frames from onset + 40 ms to onset + 130 ms (and the two other windows).
- **Per-onset features.** `entropy` is the normalised Shannon entropy of the onset's chroma (log of 12). `npc` is the number of pitch classes at 0.5 x the maximum or more; the single share is the share of a section's onsets with `npc <= 1`.
- **Section features.** Onsets with `section start <= t < section end`, bars from the grid (`start_bar` to `end_bar`), with the last section's trailing silent bars dropped as the strums stage drops them (Summer of '69 111-121 is measured over 111-120, Fame 85-101 over 85-100, Need You Tonight 79-86 over 79-84; the tables show the grid bars). Two entropy readings are reported:
  - **median per onset** (the middle value of the section's per-onset entropies): what `s4_audio.py` called `chroma_ent`, and what reproduces the spec's constants table;
  - **mean chroma, literal**: the entropy of the section's mean of the per-onset (unnormalised) chroma, as the spec's sentence reads. The mean of per-onset L1-normalised chroma behaves the same (Fame 0.86 to 0.94, Need You Tonight 0.80 to 0.92) and is not tabulated separately.
- **Sections.** The 65 sections of the 1.4 grid, not the merged v1.5 plan sections. "Certain or uncertain" is the 1.4 `strums.json` `uncertain` flag. Mangetout 108-113 has no onsets (the last bar is trimmed; its row is blank).
- **Truth mapping.** A section carries truth when its grid range lies inside a truth range: Need You Tonight 13-24, 24-31, 31-48, 48-56, 56-79 and every Fame section (riff); Summer of '69 41-53 and 83-95, Chelsea Dagger 20-38 and 108-142 (inside 9-38 and 105-142; the intro 0-20 and the instrumental 93-108 only overlap, so they carry no truth), All Fired Up 33-49 (strum); Pour Some Sugar On Me 28-39, 55-67, 84-103 (two-guitar). That is 22 truth rows.
- **Third features.** From `s4_audio.py`: harmonic dominance (largest share of a note's first eight harmonics in the onset's constant-Q spectrum, as a section median and as the share of onsets at 0.6 or more) and the mean pYIN voiced probability over the onset windows (pYIN, 80 to 1000 Hz, whole stem).

## 1. Both features for every section (window 40 to 130 ms)

Verdict is `riff = entropy <= 0.80 and single >= 0.45` using the median-per-onset entropy. "WRONG" marks a truth row the rule misclassifies.

| Song | Sec | Bars (grid) | Label | Cert. | Onsets | Entropy (median per onset) | Entropy (mean chroma, literal) | Single share | Verdict | Truth | Check |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Summer of '69 | 0 | 0-4 | intro | certain | 21 | 0.611 | 0.733 | 0.667 | riff |  |  |
| Summer of '69 | 1 | 4-19 | verse | certain | 95 | 0.693 | 0.821 | 0.547 | riff |  |  |
| Summer of '69 | 2 | 19-31 | chorus | certain | 49 | 0.893 | 0.978 | 0.265 | no |  |  |
| Summer of '69 | 3 | 31-41 | verse | certain | 46 | 0.850 | 0.937 | 0.391 | no |  |  |
| Summer of '69 | 4 | 41-53 | chorus | certain | 36 | 0.877 | 0.977 | 0.306 | no | strum | ok |
| Summer of '69 | 5 | 53-58 | verse | certain | 25 | 0.886 | 0.964 | 0.320 | no |  |  |
| Summer of '69 | 6 | 58-68 | verse | certain | 33 | 0.877 | 0.969 | 0.212 | no |  |  |
| Summer of '69 | 7 | 68-75 | instrumental | certain | 48 | 0.850 | 0.930 | 0.417 | no |  |  |
| Summer of '69 | 8 | 75-83 | verse | certain | 35 | 0.899 | 0.944 | 0.343 | no |  |  |
| Summer of '69 | 9 | 83-95 | chorus | certain | 23 | 0.876 | 0.980 | 0.478 | no | strum | ok |
| Summer of '69 | 10 | 95-111 | verse | uncertain | 53 | 0.820 | 0.927 | 0.642 | no |  |  |
| Summer of '69 | 11 | 111-121 | outro | uncertain | 24 | 0.904 | 0.954 | 0.042 | no |  |  |
| Chelsea Dagger | 0 | 0-20 | intro | uncertain | 69 | 0.809 | 0.907 | 0.246 | no |  |  |
| Chelsea Dagger | 1 | 20-38 | chorus | certain | 53 | 0.922 | 0.955 | 0.264 | no | strum | ok |
| Chelsea Dagger | 2 | 38-61 | verse | certain | 107 | 0.859 | 0.985 | 0.327 | no |  |  |
| Chelsea Dagger | 3 | 61-71 | chorus | certain | 34 | 0.926 | 0.954 | 0.147 | no |  |  |
| Chelsea Dagger | 4 | 71-93 | verse | certain | 101 | 0.858 | 0.986 | 0.376 | no |  |  |
| Chelsea Dagger | 5 | 93-108 | instrumental | certain | 85 | 0.873 | 0.923 | 0.341 | no |  |  |
| Chelsea Dagger | 6 | 108-142 | chorus | certain | 89 | 0.872 | 0.956 | 0.270 | no | strum | ok |
| Pour Some Sugar On Me | 0 | 0-11 | intro | uncertain | 91 | 0.780 | 0.839 | 0.385 | no |  |  |
| Pour Some Sugar On Me | 1 | 11-28 | verse | uncertain | 104 | 0.892 | 0.952 | 0.288 | no |  |  |
| Pour Some Sugar On Me | 2 | 28-39 | chorus | uncertain | 72 | 0.927 | 0.989 | 0.153 | no | two-guitar | ok |
| Pour Some Sugar On Me | 3 | 39-55 | verse | uncertain | 126 | 0.863 | 0.921 | 0.349 | no |  |  |
| Pour Some Sugar On Me | 4 | 55-67 | chorus | uncertain | 51 | 0.918 | 0.974 | 0.314 | no | two-guitar | ok |
| Pour Some Sugar On Me | 5 | 67-77 | instrumental | uncertain | 94 | 0.786 | 0.873 | 0.426 | no |  |  |
| Pour Some Sugar On Me | 6 | 77-84 | verse | uncertain | 20 | 0.914 | 0.799 | 0.300 | no |  |  |
| Pour Some Sugar On Me | 7 | 84-103 | chorus | uncertain | 68 | 0.915 | 0.972 | 0.250 | no | two-guitar | ok |
| Mangetout | 0 | 0-5 | verse | certain | 30 | 0.795 | 0.901 | 0.600 | riff |  |  |
| Mangetout | 1 | 5-18 | chorus | certain | 105 | 0.815 | 0.914 | 0.390 | no |  |  |
| Mangetout | 2 | 18-33 | verse | certain | 60 | 0.824 | 0.962 | 0.383 | no |  |  |
| Mangetout | 3 | 33-42 | chorus | certain | 71 | 0.793 | 0.892 | 0.338 | no |  |  |
| Mangetout | 4 | 42-58 | verse | certain | 124 | 0.822 | 0.911 | 0.331 | no |  |  |
| Mangetout | 5 | 58-65 | verse | certain | 38 | 0.805 | 0.895 | 0.500 | no |  |  |
| Mangetout | 6 | 65-100 | verse | certain | 292 | 0.783 | 0.946 | 0.428 | no |  |  |
| Mangetout | 7 | 100-108 | chorus | certain | 57 | 0.798 | 0.913 | 0.561 | riff |  |  |
| Mangetout | 8 | 108-113 | outro | uncertain | 0 | - | - | - | n/a | | |
| Fame | 0 | 0-17 | intro | certain | 146 | 0.760 | 0.951 | 0.466 | riff | riff | ok |
| Fame | 1 | 17-29 | verse | certain | 126 | 0.753 | 0.935 | 0.524 | riff | riff | ok |
| Fame | 2 | 29-35 | instrumental | certain | 62 | 0.724 | 0.920 | 0.629 | riff | riff | ok |
| Fame | 3 | 35-47 | verse | certain | 113 | 0.737 | 0.950 | 0.549 | riff | riff | ok |
| Fame | 4 | 47-61 | instrumental | certain | 123 | 0.706 | 0.906 | 0.585 | riff | riff | ok |
| Fame | 5 | 61-71 | chorus | certain | 114 | 0.739 | 0.882 | 0.491 | riff | riff | ok |
| Fame | 6 | 71-81 | verse | certain | 120 | 0.704 | 0.855 | 0.583 | riff | riff | ok |
| Fame | 7 | 81-85 | instrumental | certain | 33 | 0.735 | 0.872 | 0.576 | riff | riff | ok |
| Fame | 8 | 85-101 | verse | certain | 164 | 0.695 | 0.821 | 0.622 | riff | riff | ok |
| All Fired Up | 0 | 0-28 | intro | uncertain | 110 | 0.783 | 0.921 | 0.373 | no |  |  |
| All Fired Up | 1 | 28-33 | verse | certain | 30 | 0.604 | 0.727 | 0.833 | riff |  |  |
| All Fired Up | 2 | 33-49 | verse | certain | 57 | 0.660 | 0.896 | 0.614 | riff | strum | WRONG |
| All Fired Up | 3 | 49-55 | chorus | certain | 8 | 0.788 | 0.919 | 0.625 | riff |  |  |
| All Fired Up | 4 | 55-61 | verse | certain | 31 | 0.642 | 0.756 | 0.613 | riff |  |  |
| All Fired Up | 5 | 61-90 | verse | certain | 43 | 0.729 | 0.907 | 0.721 | riff |  |  |
| All Fired Up | 6 | 90-97 | verse | uncertain | 40 | 0.689 | 0.889 | 0.400 | no |  |  |
| All Fired Up | 7 | 97-104 | verse | certain | 64 | 0.646 | 0.881 | 0.562 | riff |  |  |
| All Fired Up | 8 | 104-110 | verse | certain | 42 | 0.567 | 0.597 | 0.738 | riff |  |  |
| All Fired Up | 9 | 110-124 | chorus | uncertain | 30 | 0.701 | 0.890 | 0.500 | riff |  |  |
| All Fired Up | 10 | 124-128 | verse | uncertain | 3 | 0.850 | 0.853 | 0.333 | no |  |  |
| All Fired Up | 11 | 128-132 | chorus | certain | 2 | 0.830 | 0.965 | 0.500 | no |  |  |
| All Fired Up | 12 | 132-156 | outro | certain | 18 | 0.892 | 0.948 | 0.389 | no |  |  |
| Need You Tonight | 0 | 0-13 | intro | uncertain | 36 | 0.862 | 0.963 | 0.444 | no |  |  |
| Need You Tonight | 1 | 13-24 | verse | certain | 138 | 0.540 | 0.837 | 0.783 | riff | riff | ok |
| Need You Tonight | 2 | 24-31 | chorus | certain | 75 | 0.788 | 0.958 | 0.480 | riff | riff | ok |
| Need You Tonight | 3 | 31-48 | verse | certain | 180 | 0.599 | 0.897 | 0.683 | riff | riff | ok |
| Need You Tonight | 4 | 48-56 | chorus | certain | 82 | 0.756 | 0.933 | 0.524 | riff | riff | ok |
| Need You Tonight | 5 | 56-79 | verse | certain | 228 | 0.660 | 0.921 | 0.675 | riff | riff | ok |
| Need You Tonight | 6 | 79-86 | outro | uncertain | 46 | 0.646 | 0.895 | 0.630 | riff |  |  |

Rows marked riff with no truth at 40 to 130 ms (12): Summer of '69 0-4 and 4-19; Mangetout 0-5 and 100-108; All Fired Up 28-33, 49-55 (8 onsets only), 55-61, 61-90, 97-104, 104-110, 110-124; Need You Tonight 79-86. The spec's validation row "riff marker on Fame's and Need You Tonight's own-pattern sections and nowhere else" cannot pass as an exact criterion on the 1.4 sections; the merged v1.5 sections will change some of these rows (A5 below).

## 2. Classification and margins

**Every truth row?** No. 21 of 22 at 40 to 130 ms and at 30 to 110 ms; 20 of 22 at 50 to 150 ms. All Fired Up 33-49 (strum) is marked riff in every window. At 50 to 150 ms Need You Tonight 24-31 (riff) also misses, on entropy (0.811).

With the literal "entropy of the mean chroma" 14 of 22 truth rows are wrong in every window (all 14 riff rows), so that wording must not be implemented.

### Margins (window 40 to 130 ms, median-per-onset entropy)

| Threshold | Riff side: nearest riff row, margin | Non-riff side: nearest non-riff truth row, margin |
|---|---|---|
| Entropy <= 0.80 | Need You Tonight 24-31 at 0.788: **+0.012** | Chelsea Dagger 108-142 at 0.872: **+0.072** (All Fired Up 33-49 at 0.660 is on the wrong side: -0.140) |
| Single >= 0.45 | Fame 0-17 at 0.466: **+0.016** | Pour Some Sugar On Me 55-67 at 0.314 among rows below the threshold: **+0.136**; Summer of '69 83-95 at 0.478 is above it (-0.028) and is rejected by entropy (0.876, +0.076) |

Notes on reading the margins.

- Among the strum and two-guitar truth rows other than All Fired Up 33-49, **none** passes the entropy test (lowest 0.872). The single-share test therefore decides no truth row on its own except by backing up entropy. It does the work on unlabelled rows: Pour Some Sugar On Me 0-11 (0.780, share 0.385) and 67-77 (0.786, share 0.426) both pass entropy and are held back only by the share.
- Over all eight Pour Some Sugar On Me sections (which the spec's table treats as two-guitar), the lowest entropy is 0.780 (-0.020 against 0.80) and the highest share is 0.426 (gap 0.040 to Fame's 0.466, the spec's figure). Over the three truth rows alone, the entropy gap is 0.115 (0.915 against 0.80) and the share gap is 0.152.
- Across the three windows the riff-side margins are: entropy +0.029, +0.012, -0.011 (30-110, 40-130, 50-150); single share +0.023, +0.016, +0.009. The non-riff-side margins (excluding All Fired Up 33-49) are: entropy +0.073, +0.072, +0.061; single share, nearest truth row below the threshold, +0.089, +0.136, +0.117.

### The misclassified row

All Fired Up 33-49 (strum by ear) has median entropy 0.660, 0.668, 0.644 and single share 0.614, 0.579, 0.667 across the windows: inside the riff cluster on both features (Need You Tonight 31-48 is 0.599 and 0.683; Need You Tonight 56-79 is 0.660 and 0.675). To mark it non-riff, entropy would need a ceiling below 0.66, which loses all of Fame (0.695 to 0.760) and Need You Tonight 24-31 and 48-56 (56-79 is level at 0.660); or a single-share floor above 0.62, which loses seven of nine Fame sections and Need You Tonight 24-31 and 48-56. No pair of thresholds on these two features separates it from the riff rows. The third features do not either (section 4).

## 3. Sensitivity to the window

Each cell is median entropy / single share / verdict.

| Song | Sec | Bars | Truth | 30-110: ent / single / verdict | 40-130: ent / single / verdict | 50-150: ent / single / verdict |
|---|---|---|---|---|---|---|
| Summer of '69 | 0 | 0-4 |  | 0.663 / 0.619 / riff | 0.611 / 0.667 / riff | 0.578 / 0.714 / riff |
| Summer of '69 | 1 | 4-19 |  | 0.733 / 0.516 / riff | 0.693 / 0.547 / riff | 0.674 / 0.558 / riff |
| Summer of '69 | 2 | 19-31 |  | 0.898 / 0.265 / no | 0.893 / 0.265 / no | 0.892 / 0.306 / no |
| Summer of '69 | 3 | 31-41 |  | 0.859 / 0.370 / no | 0.850 / 0.391 / no | 0.850 / 0.413 / no |
| Summer of '69 | 4 | 41-53 | strum | 0.888 / 0.361 / no | 0.877 / 0.306 / no | 0.872 / 0.333 / no |
| Summer of '69 | 5 | 53-58 |  | 0.887 / 0.240 / no | 0.886 / 0.320 / no | 0.885 / 0.320 / no |
| Summer of '69 | 6 | 58-68 |  | 0.886 / 0.273 / no | 0.877 / 0.212 / no | 0.885 / 0.242 / no |
| Summer of '69 | 7 | 68-75 |  | 0.852 / 0.396 / no | 0.850 / 0.417 / no | 0.850 / 0.458 / no |
| Summer of '69 | 8 | 75-83 |  | 0.915 / 0.371 / no | 0.899 / 0.343 / no | 0.889 / 0.343 / no |
| Summer of '69 | 9 | 83-95 | strum | 0.890 / 0.522 / no | 0.876 / 0.478 / no | 0.878 / 0.478 / no |
| Summer of '69 | 10 | 95-111 |  | 0.814 / 0.509 / no | 0.820 / 0.642 / no | 0.823 / 0.642 / no |
| Summer of '69 | 11 | 111-121 |  | 0.902 / 0.042 / no | 0.904 / 0.042 / no | 0.902 / 0.042 / no |
| Chelsea Dagger | 0 | 0-20 |  | 0.853 / 0.261 / no | 0.809 / 0.246 / no | 0.807 / 0.290 / no |
| Chelsea Dagger | 1 | 20-38 | strum | 0.934 / 0.132 / no | 0.922 / 0.264 / no | 0.910 / 0.283 / no |
| Chelsea Dagger | 2 | 38-61 |  | 0.868 / 0.336 / no | 0.859 / 0.327 / no | 0.843 / 0.355 / no |
| Chelsea Dagger | 3 | 61-71 |  | 0.936 / 0.147 / no | 0.926 / 0.147 / no | 0.915 / 0.147 / no |
| Chelsea Dagger | 4 | 71-93 |  | 0.866 / 0.317 / no | 0.858 / 0.376 / no | 0.835 / 0.386 / no |
| Chelsea Dagger | 5 | 93-108 |  | 0.881 / 0.259 / no | 0.873 / 0.341 / no | 0.869 / 0.353 / no |
| Chelsea Dagger | 6 | 108-142 | strum | 0.873 / 0.270 / no | 0.872 / 0.270 / no | 0.861 / 0.326 / no |
| Pour Some Sugar On Me | 0 | 0-11 |  | 0.777 / 0.330 / no | 0.780 / 0.385 / no | 0.764 / 0.407 / no |
| Pour Some Sugar On Me | 1 | 11-28 |  | 0.895 / 0.221 / no | 0.892 / 0.288 / no | 0.888 / 0.317 / no |
| Pour Some Sugar On Me | 2 | 28-39 | two-guitar | 0.932 / 0.139 / no | 0.927 / 0.153 / no | 0.927 / 0.167 / no |
| Pour Some Sugar On Me | 3 | 39-55 |  | 0.869 / 0.294 / no | 0.863 / 0.349 / no | 0.864 / 0.365 / no |
| Pour Some Sugar On Me | 4 | 55-67 | two-guitar | 0.911 / 0.353 / no | 0.918 / 0.314 / no | 0.920 / 0.314 / no |
| Pour Some Sugar On Me | 5 | 67-77 |  | 0.794 / 0.447 / no | 0.786 / 0.426 / no | 0.777 / 0.426 / no |
| Pour Some Sugar On Me | 6 | 77-84 |  | 0.919 / 0.300 / no | 0.914 / 0.300 / no | 0.922 / 0.300 / no |
| Pour Some Sugar On Me | 7 | 84-103 | two-guitar | 0.917 / 0.265 / no | 0.915 / 0.250 / no | 0.913 / 0.265 / no |
| Mangetout | 0 | 0-5 |  | 0.796 / 0.533 / riff | 0.795 / 0.600 / riff | 0.791 / 0.600 / riff |
| Mangetout | 1 | 5-18 |  | 0.828 / 0.362 / no | 0.815 / 0.390 / no | 0.811 / 0.410 / no |
| Mangetout | 2 | 18-33 |  | 0.835 / 0.417 / no | 0.824 / 0.383 / no | 0.810 / 0.433 / no |
| Mangetout | 3 | 33-42 |  | 0.809 / 0.366 / no | 0.793 / 0.338 / no | 0.788 / 0.352 / no |
| Mangetout | 4 | 42-58 |  | 0.835 / 0.306 / no | 0.822 / 0.331 / no | 0.818 / 0.371 / no |
| Mangetout | 5 | 58-65 |  | 0.805 / 0.500 / no | 0.805 / 0.500 / no | 0.798 / 0.500 / riff |
| Mangetout | 6 | 65-100 |  | 0.793 / 0.401 / no | 0.783 / 0.428 / no | 0.777 / 0.421 / no |
| Mangetout | 7 | 100-108 |  | 0.811 / 0.526 / no | 0.798 / 0.561 / riff | 0.801 / 0.544 / no |
| Mangetout | 8 | 108-113 |  | - | - | - |
| Fame | 0 | 0-17 | riff | 0.771 / 0.473 / riff | 0.760 / 0.466 / riff | 0.751 / 0.459 / riff |
| Fame | 1 | 17-29 | riff | 0.761 / 0.540 / riff | 0.753 / 0.524 / riff | 0.748 / 0.484 / riff |
| Fame | 2 | 29-35 | riff | 0.702 / 0.645 / riff | 0.724 / 0.629 / riff | 0.730 / 0.613 / riff |
| Fame | 3 | 35-47 | riff | 0.755 / 0.611 / riff | 0.737 / 0.549 / riff | 0.734 / 0.558 / riff |
| Fame | 4 | 47-61 | riff | 0.712 / 0.642 / riff | 0.706 / 0.585 / riff | 0.733 / 0.577 / riff |
| Fame | 5 | 61-71 | riff | 0.751 / 0.474 / riff | 0.739 / 0.491 / riff | 0.745 / 0.474 / riff |
| Fame | 6 | 71-81 | riff | 0.707 / 0.583 / riff | 0.704 / 0.583 / riff | 0.699 / 0.583 / riff |
| Fame | 7 | 81-85 | riff | 0.735 / 0.636 / riff | 0.735 / 0.576 / riff | 0.753 / 0.515 / riff |
| Fame | 8 | 85-101 | riff | 0.694 / 0.671 / riff | 0.695 / 0.622 / riff | 0.638 / 0.610 / riff |
| All Fired Up | 0 | 0-28 |  | 0.798 / 0.336 / no | 0.783 / 0.373 / no | 0.774 / 0.409 / no |
| All Fired Up | 1 | 28-33 |  | 0.615 / 0.767 / riff | 0.604 / 0.833 / riff | 0.584 / 0.800 / riff |
| All Fired Up | 2 | 33-49 | strum | 0.668 / 0.579 / riff | 0.660 / 0.614 / riff | 0.644 / 0.667 / riff |
| All Fired Up | 3 | 49-55 |  | 0.789 / 0.750 / riff | 0.788 / 0.625 / riff | 0.781 / 0.750 / riff |
| All Fired Up | 4 | 55-61 |  | 0.638 / 0.613 / riff | 0.642 / 0.613 / riff | 0.651 / 0.613 / riff |
| All Fired Up | 5 | 61-90 |  | 0.747 / 0.721 / riff | 0.729 / 0.721 / riff | 0.728 / 0.651 / riff |
| All Fired Up | 6 | 90-97 |  | 0.706 / 0.425 / no | 0.689 / 0.400 / no | 0.692 / 0.400 / no |
| All Fired Up | 7 | 97-104 |  | 0.662 / 0.594 / riff | 0.646 / 0.562 / riff | 0.645 / 0.547 / riff |
| All Fired Up | 8 | 104-110 |  | 0.605 / 0.714 / riff | 0.567 / 0.738 / riff | 0.560 / 0.762 / riff |
| All Fired Up | 9 | 110-124 |  | 0.693 / 0.633 / riff | 0.701 / 0.500 / riff | 0.694 / 0.467 / riff |
| All Fired Up | 10 | 124-128 |  | 0.843 / 0.667 / no | 0.850 / 0.333 / no | 0.862 / 0.333 / no |
| All Fired Up | 11 | 128-132 |  | 0.834 / 0.500 / no | 0.830 / 0.500 / no | 0.836 / 0.500 / no |
| All Fired Up | 12 | 132-156 |  | 0.904 / 0.278 / no | 0.892 / 0.389 / no | 0.893 / 0.444 / no |
| Need You Tonight | 0 | 0-13 |  | 0.856 / 0.500 / no | 0.862 / 0.444 / no | 0.847 / 0.444 / no |
| Need You Tonight | 1 | 13-24 | riff | 0.545 / 0.819 / riff | 0.540 / 0.783 / riff | 0.558 / 0.746 / riff |
| Need You Tonight | 2 | 24-31 | riff | 0.705 / 0.547 / riff | 0.788 / 0.480 / riff | 0.811 / 0.467 / no |
| Need You Tonight | 3 | 31-48 | riff | 0.616 / 0.722 / riff | 0.599 / 0.683 / riff | 0.614 / 0.678 / riff |
| Need You Tonight | 4 | 48-56 | riff | 0.663 / 0.573 / riff | 0.756 / 0.524 / riff | 0.769 / 0.524 / riff |
| Need You Tonight | 5 | 56-79 | riff | 0.657 / 0.671 / riff | 0.660 / 0.675 / riff | 0.669 / 0.636 / riff |
| Need You Tonight | 6 | 79-86 |  | 0.656 / 0.696 / riff | 0.646 / 0.630 / riff | 0.683 / 0.630 / riff |

Threshold grid: truth rows wrong, and unlabelled rows marked riff, for entropy ceiling x single-share floor x window. The All Fired Up miss is in every row.

| Entropy max | Single min | Window | Truth rows wrong | No-truth rows marked riff |
|---|---|---|---|---|
| 0.80 | 0.40 | 40-130 | 1 (AFU 33-49) | 15 |
| 0.80 | 0.40 | 30-110 | 1 (AFU 33-49) | 14 |
| 0.80 | 0.40 | 50-150 | 2 (AFU 33-49, NYT 24-31) | 17 |
| 0.80 | 0.45 | 40-130 | 1 (AFU 33-49) | 12 |
| 0.80 | 0.45 | 30-110 | 1 (AFU 33-49) | 11 |
| 0.80 | 0.45 | 50-150 | 2 (AFU 33-49, NYT 24-31) | 12 |
| 0.80 | 0.50 | 40-130 | 4 (Fame 0-17, Fame 61-71, AFU 33-49, NYT 24-31) | 12 |
| 0.80 | 0.50 | 30-110 | 3 (Fame 0-17, Fame 61-71, AFU 33-49) | 11 |
| 0.80 | 0.50 | 50-150 | 5 (Fame 0-17, Fame 17-29, Fame 61-71, AFU 33-49, NYT 24-31) | 11 |
| 0.82 | 0.40 | 40-130 | 1 (AFU 33-49) | 16 |
| 0.82 | 0.40 | 30-110 | 1 (AFU 33-49) | 17 |
| 0.82 | 0.40 | 50-150 | 1 (AFU 33-49) | 20 |
| 0.82 | 0.45 | 40-130 | 1 (AFU 33-49) | 13 |
| 0.82 | 0.45 | 30-110 | 1 (AFU 33-49) | 14 |
| 0.82 | 0.45 | 50-150 | 1 (AFU 33-49) | 13 |
| 0.82 | 0.50 | 40-130 | 4 (Fame 0-17, Fame 61-71, AFU 33-49, NYT 24-31) | 13 |
| 0.82 | 0.50 | 30-110 | 3 (Fame 0-17, Fame 61-71, AFU 33-49) | 14 |
| 0.82 | 0.50 | 50-150 | 5 (Fame 0-17, Fame 17-29, Fame 61-71, AFU 33-49, NYT 24-31) | 12 |
| 0.84 | 0.40 | 40-130 | 1 (AFU 33-49) | 18 |
| 0.84 | 0.40 | 30-110 | 1 (AFU 33-49) | 19 |
| 0.84 | 0.40 | 50-150 | 1 (AFU 33-49) | 22 |
| 0.84 | 0.45 | 40-130 | 1 (AFU 33-49) | 15 |
| 0.84 | 0.45 | 30-110 | 1 (AFU 33-49) | 15 |
| 0.84 | 0.45 | 50-150 | 1 (AFU 33-49) | 15 |
| 0.84 | 0.50 | 40-130 | 4 (Fame 0-17, Fame 61-71, AFU 33-49, NYT 24-31) | 15 |
| 0.84 | 0.50 | 30-110 | 3 (Fame 0-17, Fame 61-71, AFU 33-49) | 15 |
| 0.84 | 0.50 | 50-150 | 5 (Fame 0-17, Fame 17-29, Fame 61-71, AFU 33-49, NYT 24-31) | 14 |

Reading the grid:

- Raising the single-share floor to 0.50 loses two to four truth riff rows (Fame 0-17, 61-71, and in some windows Fame 17-29 and Need You Tonight 24-31): 0.45 is already at the edge of the riff side. Lowering it to 0.40 changes no truth row but marks three to five more unlabelled rows riff (Pour Some Sugar On Me 67-77 enters at 0.426).
- Raising the entropy ceiling to 0.82 makes the truth classification identical in all three windows (only All Fired Up 33-49 wrong), at a cost of one to three more unlabelled rows marked riff. At 0.84 the non-riff side margin (nearest 0.861) is 0.021 and the unlabelled marks rise to 15.

## 4. A third feature for the Pour Some Sugar On Me margin

Window 40 to 130 ms, for the truth rows and every Pour Some Sugar On Me section.

| Song | Bars | Truth | Single share | Voiced prob. | Harmonic dominance (median) | Dominance share >= 0.6 |
|---|---|---|---|---|---|---|
| Summer of '69 | 41-53 | strum | 0.306 | 0.013 | 0.383 | 0.000 |
| Summer of '69 | 83-95 | strum | 0.478 | 0.013 | 0.348 | 0.000 |
| Chelsea Dagger | 20-38 | strum | 0.264 | 0.010 | 0.304 | 0.000 |
| Chelsea Dagger | 108-142 | strum | 0.270 | 0.010 | 0.353 | 0.000 |
| Pour Some Sugar On Me | 0-11 | (no truth) | 0.385 | 0.083 | 0.432 | 0.088 |
| Pour Some Sugar On Me | 11-28 | (no truth) | 0.288 | 0.051 | 0.350 | 0.000 |
| Pour Some Sugar On Me | 28-39 | two-guitar | 0.153 | 0.024 | 0.302 | 0.000 |
| Pour Some Sugar On Me | 39-55 | (no truth) | 0.349 | 0.050 | 0.403 | 0.032 |
| Pour Some Sugar On Me | 55-67 | two-guitar | 0.314 | 0.018 | 0.326 | 0.000 |
| Pour Some Sugar On Me | 67-77 | (no truth) | 0.426 | 0.120 | 0.409 | 0.106 |
| Pour Some Sugar On Me | 77-84 | (no truth) | 0.300 | 0.052 | 0.273 | 0.000 |
| Pour Some Sugar On Me | 84-103 | two-guitar | 0.250 | 0.016 | 0.324 | 0.000 |
| Fame | 0-17 | riff | 0.466 | 0.092 | 0.409 | 0.021 |
| Fame | 17-29 | riff | 0.524 | 0.196 | 0.436 | 0.095 |
| Fame | 29-35 | riff | 0.629 | 0.172 | 0.449 | 0.129 |
| Fame | 35-47 | riff | 0.549 | 0.139 | 0.447 | 0.053 |
| Fame | 47-61 | riff | 0.585 | 0.197 | 0.448 | 0.138 |
| Fame | 61-71 | riff | 0.491 | 0.138 | 0.435 | 0.070 |
| Fame | 71-81 | riff | 0.583 | 0.284 | 0.486 | 0.158 |
| Fame | 81-85 | riff | 0.576 | 0.200 | 0.451 | 0.212 |
| Fame | 85-101 | riff | 0.622 | 0.299 | 0.506 | 0.207 |
| All Fired Up | 33-49 | strum | 0.614 | 0.223 | 0.545 | 0.175 |
| Need You Tonight | 13-24 | riff | 0.783 | 0.396 | 0.577 | 0.370 |
| Need You Tonight | 24-31 | riff | 0.480 | 0.209 | 0.384 | 0.253 |
| Need You Tonight | 31-48 | riff | 0.683 | 0.300 | 0.542 | 0.311 |
| Need You Tonight | 48-56 | riff | 0.524 | 0.251 | 0.424 | 0.232 |
| Need You Tonight | 56-79 | riff | 0.675 | 0.255 | 0.480 | 0.228 |

- **Harmonic dominance (median).** Riff minimum 0.384 (Need You Tonight 24-31); Pour Some Sugar On Me truth maximum 0.326, but its unlabelled 0-11 is 0.432 and Summer of '69 41-53 is 0.383. No gap on the strum side and the Pour Some Sugar On Me gap goes negative with all sections counted. All Fired Up 33-49 is 0.545. Not useful.
- **Dominance share >= 0.6.** Riff minimum 0.021 (Fame 0-17), strum and two-guitar truth rows 0.000, but Pour Some Sugar On Me 0-11 (0.088) and 67-77 (0.106) are above Fame's lowest. Fame 0-17 is the only riff row below 0.05. All Fired Up 33-49 is 0.175. Not useful.
- **Voiced probability.** Riff minimum 0.092 (Fame 0-17). Every strum and two-guitar truth row is 0.024 or lower (a gap of 0.068 with no overlap, against single share's overlap at Summer of '69 83-95); it would also repair the strum side. With the unlabelled Pour Some Sugar On Me sections included the gap closes: 67-77 is 0.120, 0-11 is 0.083. All Fired Up 33-49 is 0.223, inside the riff range (Fame up to 0.299, Need You Tonight up to 0.396). The other two windows give the same pattern (riff minimum 0.084 and 0.095; truth non-riff maximum, excluding All Fired Up, 0.022 and 0.025).

None of the three separates All Fired Up 33-49. Voiced probability would widen the margin on the truth rows (a gap of 0.068, so a threshold near 0.06 would leave about 0.03 each side; single share has no gap on the truth rows, since Summer of '69 83-95 at 0.478 is above Fame 0-17 at 0.466) and does not break the strum side, but it is not computed by the stage today, and it narrows to a negative margin if the two unlabelled Pour Some Sugar On Me sections are in fact two-guitar. The pYIN run was not timed here.

## Recommendation

1. **Fix the definition before anything else.** Compute `riff_entropy` as the **median over the section's onsets of the per-onset chroma entropy**, not the entropy of the mean chroma. Correct the sentence in spec 4.3 (and the `evaluate` column heading). With the literal wording the rule marks no riff section.
2. **Keep 0.45 for `RIFF_SINGLE_PC_MIN`.** Moving it up loses truth riff rows; moving it down only admits unlabelled rows.
3. **Move `RIFF_ENTROPY_MAX` from 0.80 to 0.82.** It removes the one window-sensitive truth failure (Need You Tonight 24-31 at 50 to 150 ms, 0.811) and keeps the nearest non-riff truth row 0.04 away (0.861). Riff-side margin becomes +0.009 at worst and +0.032 at 40 to 130 ms; non-riff side +0.041 at worst. Both margins stay small, so keep the window at 40 to 130 ms and do not tune the number further.
4. **Treat All Fired Up 33-49 as a known miss, not a tuning target.** Record it in the validation record as a section the features call riff and the ear called strum. If the owner's ear is right, a feature other than these two is needed (not found among the three tested); if the section is single-note or power-chord playing the ear grouped with strumming, the truth label is what is wrong. The spec's "marker nowhere else" expectation should be restated as a recorded list (the 12 unlabelled rows above are the baseline on 1.4 sections), since no threshold removes them without removing riff rows.
5. **Do not add a third feature now.** Voiced probability is the only candidate with value (it does better than single share on the truth rows) but costs a pYIN pass and fails on unlabelled Pour Some Sugar On Me 67-77.
6. Sections with few onsets (All Fired Up 49-55 has 8, 124-128 has 3, 128-132 has 2) get noisy features; a minimum onset count before the marker is allowed was not measured here.

## Assumptions

| # | Assumption | Status | Cost if wrong |
|---|---|---|---|
| A1 | The spec's constants table was measured with the median per-onset entropy, not the entropy of the mean chroma | Verified: the median reproduces the table (Need You Tonight and Fame 0.540 to 0.788 at 40 to 130 ms; strum side 0.872 to 0.922; single share 0.466 to 0.783 and 0.264 to 0.478) and the literal reading does not | If the literal reading was intended, the rule marks no riff section and the feature and thresholds must be re-measured |
| A2 | The strums stage runs `detect_onsets` on the guitar stem for these songs | Verified: all seven `strums.json` have `source: guitar_stem`; the stage's other source options (other stem, mix) are not exercised | A different source on a new song changes the onsets and the features; the thresholds would be re-measured per source |
| A3 | The spike's onsets equal the stage's | Partly verified: same function, no `fmin`; the recall gate's spliced extra onsets are excluded | Boosted sections gain extra (weaker) onsets; some per-section values would move, in a direction not measured |
| A4 | The truth labels (Fame all riff, five Need You Tonight sections, the strum and two-guitar rows) are right as given | Assumed; owner's ear, not re-checked | If All Fired Up 33-49 is really riff-like, the rule is correct on 22 of 22; if any Fame row is not riff the rule marks it wrongly |
| A5 | Features measured on the 1.4 sections carry over to the merged v1.5 plan sections | Not tested | Merged sections pool onsets; medians move toward the pooled mix, so a merged riff plus strum section may flip; re-measure on the merged plan before fixing the thresholds |
| A6 | Pour Some Sugar On Me's unlabelled sections (0-11, 11-28, 39-55, 67-77, 77-84) are not riff | Unknown; the spec's table counts all eight as two-guitar | If they are riff, the 0.040 margin is not a margin and the share threshold could move; if two-guitar, the 0.426 at 67-77 is the real constraint on the share floor |
| A7 | A window of 40 to 130 ms is stable enough | Partly verified: 30 to 110 and 50 to 150 ms give the same truth classification except Need You Tonight 24-31 at 50 to 150 ms (0.811) | If the stage's onset timing drifts by 10 to 20 ms against the detector, that row flips at 0.80; 0.82 absorbs it |
| A8 | One song's sections per truth class are enough to set thresholds | Weak: five strum and three two-guitar truth rows against 14 riff rows, from seven songs | Thresholds are fitted to these rows; a new song's riff sections with entropy 0.82 to 0.88 would be missed and its single-note-heavy strummed sections (as All Fired Up) marked riff |
| A9 | Voiced probability and harmonic dominance values from `s4_audio.py` are what a stage implementation would compute | Assumed; computed once over the whole stem with the script's pYIN settings, not timed | If the stage cannot afford pYIN, the third-feature option is closed (the recommendation already does not rely on it) |
