# Research strand: a chance-corrected strum confidence, and one guitar or two on a sixteenth grid

Date: 2026-10-04. Worktree `v1-4` (matches main). Data: the seven run folders under `C:\Users\gethi\sources\Youkelele\runs` as written by version 1.4 (Summer of '69, Chelsea Dagger, Pour Some Sugar On Me, Wet Leg "mangetout", Fame, All Fired Up, Need You Tonight). No source file, test or run folder was changed. Throwaway scripts: `%TEMP%\youkelele-v15-research\strums\` (`s1_check.py` to `s9_tables.py`, data in `stats.json`, `spray.json`, `audio.json`).

Bar and section numbers are 0-based grid bars, end exclusive, as in `grid.json`. Short names: S69, Chelsea, PSSOM, WetLeg, Fame, AFU (All Fired Up), NYT (Need You Tonight).

## 1. Summary

1. The chance correction the 1.3 spec asked for (mean Jaccard to the vote less the same figure for slot-shuffled bars) is exactly zero, by construction, for every section whose vote strikes every slot: the shuffled bars vote "every slot" too, and their Jaccard to it is the bar density. Eleven sections that print certain today, including Wet Leg's `DUDUDUDU` choruses (confidence 0.79 to 0.84), score 0.000 and would go uncertain. As a replacement for the confidence it is wrong; this is the kappa prevalence paradox (section 9).
2. Used as a test rather than a score, it works for what it can see. The permutation p-value (share of shuffles whose confidence reaches the section's own) passes about 5 percent of random sprays at any density, grid and section length, which the bare confidence cannot do: half-density sprays print certain 92 percent of the time at 8 slots and 30 percent at 16 slots today, and 8 and 5 percent under the proposed rule (section 6).
3. No chance-corrected figure separates the ear-rejected Pour Some Sugar On Me choruses from the ear-accepted sections. The two-guitar choruses are not noise: their p-values are 0.000 to 0.026, as structured as Fame's. What holds them uncertain is still the bare sixteenth-grid floor (0.55 against 0.312 to 0.453), and the nearest certain sixteenth-grid section now sits at 0.552 (Fame 47-61, re-cut by 1.4), 0.002 above it.
4. The proposed rule adds the test without replacing the floors. It flips three sections from certain to uncertain on the seven songs (S69 53-58, AFU 55-61, AFU 128-132, all four to six bars long) and nothing else.
5. One guitar against two on a sixteenth grid: a null result. Of seventeen audio features not tried in 1.3, none separates the rejected choruses from both the sixteenth-grid certain sections and the ear-accepted choruses with a usable margin. The pitch features that do split PSSOM from Fame and NYT point the wrong way: Fame's and Need You Tonight's certain sections are the most single-note-like guitar audio in the set.

## 2. State of the code

- `src/youkelele/music/as_played.py:17` `UNCERTAIN_BELOW = 0.45` (eighth grid); `:22` `UNCERTAIN_BELOW_SIXTEENTH = 0.55`; `:25` `STRIKE_SHARE = 1/3`; `:26` `DENSITY_FLOOR = 0.6`; `:27` `EXPLAINED_BELOW = 0.6`.
- `as_played.py:35-50` `jaccard`: agreement over slots struck in either vector, strike against mute earns half, two all-rest vectors agree fully. Rests agreed by both are not counted, which is why a dense vote against dense bars scores high whatever the arrangement.
- `as_played.py:53-68` `majority_vector`: a slot is struck when more than a third of the bars strike it. With 8 bars, a slot struck with probability 0.5 in each bar passes 86 percent of the time, so a half-density spray votes nearly every slot.
- `as_played.py:71-85` `fill_to_floor`, `:95-115` `section_summary`: the confidence (`:109`) is the mean Jaccard of each bar to the topped-up vote.
- `as_played.py:118-133` `explained_onsets`.
- `src/youkelele/stages/strums.py:137` chooses the grid (`eighth_grid`); `:163` quantises each bar (`onsets.quantise_bar`, `onsets.py:130-152`); `:166` picks the floor by grid; `:184` calls `section_summary`; `:188` `uncertain = confidence < floor or explained < EXPLAINED_BELOW or not long_enough`; `:219` stores every bar's vector as `Strums.bar_onsets`.
- `src/youkelele/music/recall.py:91-101` `_strikes_and_agreement` uses the same confidence for the recall gate; `:126` skips the gate on the sixteenth grid; `:141` rejects a union whose agreement falls.
- `src/youkelele/schemas.py:160-169` `SectionPattern` (`confidence`, `explained`, `uncertain`, `recall_boost`).

The per-bar strike vectors are stored in `strums.json` (`bar_onsets`), so no stem had to be re-analysed for sections 3 to 7. No run folder has the `--debug` export `04_strums/onsets.txt`. Mapping `D` and `U` back to a strike and keeping `x`, and trimming the last section as `strums.py` does (`trailing_silent_bars`), reproduces every stored confidence and `explained` exactly (checked on all 64 analysed sections by `s1_check.py` and by an assertion in `s2_stats.py`).

Section edges moved in 1.4. Chelsea's first chorus is now 20-38 (the ear-accepted range was 9-38) and the last chorus 108-142 (was 105-142); both lie inside the accepted ranges and are counted as accepted. S69 41-53 and 83-95 and PSSOM 28-39, 55-67 and 84-103 are unchanged.

## 3. Method

For each section's bars, coded rest, strike and mute:

- **conf**: today's confidence (mean Jaccard of each bar to the topped-up vote).
- **E**: the mean of the same confidence over 1000 slot-shuffled copies of the section. Each bar's cells are permuted independently, so every bar keeps its own number of strikes and mutes; the vote and floor are recomputed on each copy.
- **conf minus E**, the correction the 1.3 spec proposed; **ARI-like** = (conf minus E) / (1 minus E), the Hubert and Arabie form.
- **p**: the share of the 1000 shuffled copies whose confidence is at least the section's own (a one-sided permutation test of "the slot positions carry no information beyond each bar's density").
- **Bootstrap stability** of the vote: 500 resamples of the bars with replacement; the vote is recomputed on each; reported as the mean Jaccard of the resampled vote to the section's vote and as the share of resamples whose struck slots match it exactly.

The section statistics use a vectorised copy of `majority_vector`, `fill_to_floor`, `jaccard` and `explained_onsets` (`vec.py`), asserted equal to the project's functions on every real section. A z-score was also computed and dropped: on dense sections every shuffle gives the same confidence, so its spread is zero (Chelsea 108-142).

Random sprays follow the 1.3 review: each slot of each bar struck with probability p, no mutes, 2000 sections per setting, p-values from 200 shuffles. "Certain" means today's rule without the length test (confidence at or above the grid floor and `explained` at least 0.6), plus whatever the candidate adds.

## 4. Per-section measurements (question 1)

"full vote" means the topped-up vote strikes every slot. "ear" marks the owner's verdicts: ACC accepted, REJ rejected.

| song | # | label | bars | slots | density | conf | E (shuffle) | conf minus E | ARI-like | p (shuffle) | bootstrap J | bootstrap exact | explained | full vote | printed | ear |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S69 | 0 | intro | 0-4 | 8 | 0.625 | 0.651 | 0.591 | +0.060 | +0.146 | 0.013 | 0.836 | 0.634 | 0.900 | no | certain `D-xx-xxx` |  |
| S69 | 1 | verse | 4-19 | 8 | 0.767 | 0.654 | 0.656 | -0.002 | -0.005 | 1.000 | 0.862 | 0.674 | 1.000 | yes | certain `xxxUxxxx` |  |
| S69 | 2 | chorus | 19-31 | 8 | 0.490 | 0.619 | 0.503 | +0.117 | +0.234 | 0.000 | 0.889 | 0.444 | 0.872 | no | certain `D-DU-UD-` |  |
| S69 | 3 | verse | 31-41 | 8 | 0.550 | 0.617 | 0.532 | +0.085 | +0.181 | 0.000 | 0.876 | 0.452 | 0.932 | no | certain `DUDUD-D-` |  |
| S69 | 4 | chorus | 41-53 | 8 | 0.646 | 0.778 | 0.639 | +0.139 | +0.385 | 0.000 | 0.991 | 0.944 | 0.952 | no | certain `D-DUDUD-` | ACC |
| S69 | 5 | verse | 53-58 | 8 | 0.650 | 0.693 | 0.667 | +0.026 | +0.077 | 0.332 | 0.848 | 0.202 | 0.962 | no | certain `DU-UDUDU` |  |
| S69 | 6 | verse | 58-68 | 8 | 0.400 | 0.479 | 0.420 | +0.059 | +0.101 | 0.019 | 0.710 | 0.196 | 0.719 | no | certain `D-DU--D-` |  |
| S69 | 7 | instrumental | 68-75 | 8 | 0.786 | 0.786 | 0.786 | -0.000 | -0.001 | 1.000 | 0.978 | 0.840 | 1.000 | yes | certain `DUDUDUDU` |  |
| S69 | 8 | verse | 75-83 | 8 | 0.562 | 0.643 | 0.581 | +0.062 | +0.149 | 0.021 | 0.867 | 0.270 | 1.000 | no | certain `DUDUDUD-` |  |
| S69 | 9 | chorus | 83-95 | 8 | 0.573 | 0.704 | 0.572 | +0.133 | +0.310 | 0.000 | 0.870 | 0.372 | 0.964 | no | certain `D-DUDUD-` | ACC |
| S69 | 10 | verse | 95-111 | 8 | 0.414 | 0.428 | 0.396 | +0.032 | +0.053 | 0.040 | 0.718 | 0.146 | 0.679 | no | uncertain `D--UD-D-` |  |
| S69 | 11 | outro | 111-120 | 8 | 0.306 | 0.219 | 0.259 | -0.040 | -0.054 | 0.733 | 0.397 | 0.106 | 0.409 | no | uncertain `x---D---` |  |
| Chelsea | 0 | intro | 0-20 | 8 | 0.331 | 0.325 | 0.248 | +0.077 | +0.102 | 0.000 | 0.717 | 0.334 | 0.698 | no | uncertain `D-x-x-x-` |  |
| Chelsea | 1 | chorus | 20-38 | 8 | 0.590 | 0.775 | 0.590 | +0.185 | +0.451 | 0.000 | 0.944 | 0.676 | 0.894 | no | certain `D-D-D-DU` | ACC |
| Chelsea | 2 | verse | 38-61 | 8 | 0.489 | 0.496 | 0.452 | +0.044 | +0.080 | 0.000 | 0.861 | 0.334 | 0.978 | no | certain `D-DUDUDU` |  |
| Chelsea | 3 | chorus | 61-71 | 8 | 0.400 | 0.605 | 0.433 | +0.172 | +0.303 | 0.000 | 0.846 | 0.446 | 0.844 | no | certain `D-D-D-D-` |  |
| Chelsea | 4 | verse | 71-93 | 8 | 0.460 | 0.539 | 0.441 | +0.098 | +0.175 | 0.000 | 0.873 | 0.472 | 0.753 | no | certain `D-D-D-D-` |  |
| Chelsea | 5 | instrumental | 93-108 | 8 | 0.508 | 0.594 | 0.504 | +0.089 | +0.180 | 0.000 | 0.917 | 0.574 | 0.934 | no | certain `D-DUD-DU` |  |
| Chelsea | 6 | chorus | 108-142 | 8 | 0.640 | 0.711 | 0.640 | +0.071 | +0.198 | 0.000 | 0.983 | 0.882 | 0.983 | no | certain `D-DUDUDU` | ACC |
| PSSOM | 0 | intro | 0-11 | 16 | 0.483 | 0.467 | 0.457 | +0.009 | +0.017 | 0.093 | 0.764 | 0.046 | 0.941 | no | uncertain `DUDUDUDUDUD-D-DU` |  |
| PSSOM | 1 | verse | 11-28 | 16 | 0.301 | 0.369 | 0.288 | +0.081 | +0.114 | 0.000 | 0.674 | 0.042 | 0.671 | no | uncertain `D-D--UDU----DU--` |  |
| PSSOM | 2 | chorus | 28-39 | 16 | 0.364 | 0.453 | 0.380 | +0.073 | +0.117 | 0.000 | 0.755 | 0.024 | 0.812 | no | uncertain `D--UD-D-D-D-DU-U` | REJ |
| PSSOM | 3 | verse | 39-55 | 16 | 0.465 | 0.472 | 0.445 | +0.026 | +0.047 | 0.008 | 0.827 | 0.066 | 0.874 | no | uncertain `DU--DxDU-UDUDU-U` |  |
| PSSOM | 4 | chorus | 55-67 | 16 | 0.260 | 0.312 | 0.223 | +0.089 | +0.115 | 0.026 | 0.558 | 0.058 | 0.480 | no | uncertain `----D---D-D-D---` | REJ |
| PSSOM | 5 | instrumental | 67-77 | 16 | 0.500 | 0.504 | 0.484 | +0.020 | +0.038 | 0.036 | 0.822 | 0.074 | 0.950 | no | uncertain `DU-UxUDU-UDUDUDU` |  |
| PSSOM | 6 | verse | 77-84 | 16 | 0.161 | 0.208 | 0.189 | +0.019 | +0.024 | 0.302 | 0.347 | 0.094 | 0.278 | no | uncertain `D----------U----` |  |
| PSSOM | 7 | chorus | 84-103 | 16 | 0.214 | 0.359 | 0.177 | +0.182 | +0.221 | 0.000 | 0.704 | 0.186 | 0.646 | no | uncertain `D---D---D---D--U` | REJ |
| WetLeg | 0 | verse | 0-5 | 8 | 0.700 | 0.683 | 0.597 | +0.086 | +0.214 | 0.003 | 0.819 | 0.500 | 0.929 | no | certain `D-xUDxD-` |  |
| WetLeg | 1 | chorus | 5-18 | 8 | 0.865 | 0.837 | 0.837 | +0.000 | +0.000 | 1.000 | 0.999 | 0.998 | 1.000 | yes | certain `DUDUDUDU` |  |
| WetLeg | 2 | verse | 18-33 | 8 | 0.433 | 0.458 | 0.407 | +0.052 | +0.087 | 0.001 | 0.843 | 0.438 | 0.788 | no | certain `D-D-D-DU` |  |
| WetLeg | 3 | chorus | 33-42 | 8 | 0.819 | 0.688 | 0.690 | -0.002 | -0.007 | 0.639 | 0.901 | 0.912 | 1.000 | yes | certain `DUDUDxDU` |  |
| WetLeg | 4 | verse | 42-58 | 8 | 0.828 | 0.805 | 0.805 | +0.000 | +0.000 | 1.000 | 0.997 | 0.984 | 1.000 | yes | certain `DUDUDUDU` |  |
| WetLeg | 5 | verse | 58-65 | 8 | 0.589 | 0.645 | 0.585 | +0.060 | +0.143 | 0.018 | 0.854 | 0.322 | 0.909 | no | certain `D-DU-UDU` |  |
| WetLeg | 6 | verse | 65-100 | 8 | 0.836 | 0.732 | 0.718 | +0.014 | +0.050 | 0.000 | 0.965 | 1.000 | 1.000 | yes | certain `DUDUxxDU` |  |
| WetLeg | 7 | chorus | 100-108 | 8 | 0.812 | 0.789 | 0.789 | -0.000 | -0.000 | 1.000 | 0.976 | 0.862 | 1.000 | yes | certain `DUDUDUDU` |  |
| Fame | 0 | intro | 0-17 | 16 | 0.474 | 0.563 | 0.461 | +0.102 | +0.189 | 0.000 | 0.876 | 0.170 | 0.907 | no | certain `D-D-D-D-DUDUDUD-` |  |
| Fame | 1 | verse | 17-29 | 16 | 0.583 | 0.643 | 0.529 | +0.114 | +0.241 | 0.000 | 0.869 | 0.260 | 0.938 | no | certain `DUD-DUx-D-DUDUD-` |  |
| Fame | 2 | instrumental | 29-35 | 16 | 0.604 | 0.668 | 0.559 | +0.109 | +0.246 | 0.000 | 0.829 | 0.288 | 0.897 | no | certain `DU--DUx-D-DUDUD-` |  |
| Fame | 3 | verse | 35-47 | 16 | 0.516 | 0.605 | 0.484 | +0.121 | +0.234 | 0.000 | 0.851 | 0.126 | 0.919 | no | certain `DU--DUx-D-DUDUD-` |  |
| Fame | 4 | instrumental | 47-61 | 16 | 0.500 | 0.552 | 0.472 | +0.081 | +0.153 | 0.000 | 0.816 | 0.110 | 0.786 | no | certain `D-D-DUD-D-D-D-D-` |  |
| Fame | 5 | chorus | 61-71 | 16 | 0.637 | 0.724 | 0.613 | +0.111 | +0.287 | 0.000 | 0.830 | 0.076 | 0.892 | no | certain `DUDUDUD---D-DUD-` |  |
| Fame | 6 | verse | 71-81 | 16 | 0.688 | 0.679 | 0.609 | +0.070 | +0.178 | 0.000 | 0.843 | 0.094 | 0.936 | no | certain `D-DUDUD-DUD-DUxx` |  |
| Fame | 7 | instrumental | 81-85 | 16 | 0.500 | 0.713 | 0.546 | +0.167 | +0.368 | 0.000 | 0.823 | 0.362 | 0.906 | no | certain `D-DUDUD--U--xU--` |  |
| Fame | 8 | verse | 85-100 | 16 | 0.613 | 0.777 | 0.552 | +0.225 | +0.502 | 0.000 | 0.935 | 0.736 | 0.918 | no | certain `D-DUD-D--UD-DUx-` |  |
| AFU | 0 | intro | 0-28 | 8 | 0.446 | 0.357 | 0.357 | -0.000 | -0.000 | 0.518 | 0.713 | 0.190 | 0.910 | no | uncertain `DxxUDUD-` |  |
| AFU | 1 | verse | 28-33 | 8 | 0.625 | 0.562 | 0.544 | +0.018 | +0.040 | 0.256 | 0.801 | 0.410 | 1.000 | yes | certain `DUxxxUxU` |  |
| AFU | 2 | verse | 33-49 | 8 | 0.672 | 0.555 | 0.559 | -0.004 | -0.010 | 1.000 | 0.825 | 0.556 | 1.000 | yes | certain `DUDUDUDU` |  |
| AFU | 3 | chorus | 49-55 | 8 | 0.604 | 0.695 | 0.633 | +0.062 | +0.169 | 0.017 | 0.824 | 0.336 | 0.828 | no | certain `DUD-D-D-` |  |
| AFU | 4 | verse | 55-61 | 8 | 0.542 | 0.533 | 0.487 | +0.047 | +0.091 | 0.064 | 0.778 | 0.416 | 0.846 | no | certain `D-Dx-U-U` |  |
| AFU | 5 | verse | 61-90 | 8 | 0.500 | 0.547 | 0.497 | +0.049 | +0.098 | 0.000 | 0.799 | 0.160 | 0.793 | no | certain `D-D-D-DU` |  |
| AFU | 6 | verse | 90-97 | 8 | 0.536 | 0.432 | 0.449 | -0.017 | -0.030 | 0.964 | 0.643 | 0.214 | 0.933 | no | uncertain `xUDxxxx-` |  |
| AFU | 7 | verse | 97-104 | 8 | 0.786 | 0.714 | 0.688 | +0.026 | +0.083 | 0.051 | 0.878 | 0.520 | 1.000 | yes | certain `xxDxDxDx` |  |
| AFU | 8 | verse | 104-110 | 8 | 0.792 | 0.740 | 0.722 | +0.017 | +0.062 | 0.073 | 0.900 | 0.588 | 1.000 | yes | certain `Dxxxxxxx` |  |
| AFU | 9 | chorus | 110-124 | 8 | 0.250 | 0.212 | 0.163 | +0.049 | +0.058 | 0.188 | 0.420 | 0.060 | 0.571 | no | uncertain `DU----x-` |  |
| AFU | 10 | verse | 124-128 | 8 | 0.094 | 0.375 | 0.467 | -0.092 | -0.173 | 1.000 | 0.537 | 0.382 | 0.667 | no | uncertain `-------U` |  |
| AFU | 11 | chorus | 128-132 | 8 | 0.438 | 0.562 | 0.526 | +0.036 | +0.077 | 0.208 | 0.741 | 0.104 | 0.786 | no | certain `D---DUD-` |  |
| AFU | 12 | outro | 132-156 | 8 | 0.500 | 0.559 | 0.498 | +0.060 | +0.120 | 0.000 | 0.799 | 0.268 | 0.708 | no | certain `D-D-D-D-` |  |
| NYT | 0 | intro | 0-13 | 16 | 0.135 | 0.084 | 0.596 | -0.512 | -1.266 | 0.994 | 0.348 | 0.246 | 0.179 | no | uncertain `D---------------` |  |
| NYT | 1 | verse | 13-24 | 16 | 0.688 | 0.815 | 0.633 | +0.182 | +0.497 | 0.000 | 0.933 | 0.370 | 0.950 | no | certain `DUD-D-D-DUxUxU-U` |  |
| NYT | 2 | chorus | 24-31 | 16 | 0.607 | 0.660 | 0.586 | +0.073 | +0.177 | 0.000 | 0.844 | 0.144 | 0.941 | no | certain `D-DUD-DUDUDUxU-U` |  |
| NYT | 3 | verse | 31-48 | 16 | 0.603 | 0.688 | 0.555 | +0.134 | +0.300 | 0.000 | 0.907 | 0.404 | 0.890 | no | certain `DUD-D-D-DUxU-U-U` |  |
| NYT | 4 | chorus | 48-56 | 16 | 0.578 | 0.617 | 0.555 | +0.062 | +0.139 | 0.000 | 0.840 | 0.188 | 0.946 | no | certain `DUD-D-DUDUDUxU-U` |  |
| NYT | 5 | verse | 56-79 | 16 | 0.562 | 0.615 | 0.506 | +0.109 | +0.220 | 0.000 | 0.889 | 0.292 | 0.889 | no | certain `DUD-D-D-DUxU-U-U` |  |
| NYT | 6 | outro | 79-84 | 16 | 0.525 | 0.532 | 0.520 | +0.012 | +0.025 | 0.287 | 0.727 | 0.038 | 0.929 | no | uncertain `DU-UDUDUD-xU-UDU` |  |

Wet Leg's one-bar outro (108-109) is `no_instrument` and has no statistics.

What the table shows:

- **The baseline is the density once the vote saturates.** With eight or more bars at a density well above a third, the shuffled copies vote every slot, and a bar's Jaccard to an all-struck vote is its share of struck slots. E then equals the density (Chelsea 108-142: 0.640 and 0.640; Wet Leg 42-58: 0.805 and 0.828 less the mutes' half credit). This is the expectation Chung et al. derive for the Jaccard of two independent binary vectors, p1 p2 / (p1 + p2 minus p1 p2), with the vote's p2 at 1.
- **Every full vote scores zero.** The eleven certain sections with a full vote (S69 4-19 and 68-75; Wet Leg 5-18, 33-42, 42-58, 65-100, 100-108; AFU 28-33, 33-49, 97-104, 104-110) have conf minus E between -0.004 and +0.026 and p from 0.000 to 1.000 (0.000 only for Wet Leg 65-100, whose mutes are placed consistently). The figure says "no structure beyond density", which is true and irrelevant: "strum every slot" is a claim about density.
- **The ear-rejected choruses are structured.** PSSOM 28-39, 55-67 and 84-103 have p of 0.000, 0.026 and 0.000 and ARI-like values of 0.117, 0.115 and 0.221, in the range of the accepted Chelsea 108-142 (0.198). Two guitars in one stem are two patterns superimposed, and each is regular, so the mixture is far from random.

## 5. Which statistic separates accepted from rejected (question 2)

Margin = worst kept value minus best rejected value, in the direction where higher means more trustworthy (for p, lower). The ear sets are 4 accepted (all 8 slots) and 3 rejected (all 16 slots). "16-grid certain" is the 14 sections Fame and NYT print certain, which no ear check covers (section 11).

| statistic | accepted (ear) | rejected (ear) | margin vs ear-accepted | 16-grid certain range | margin vs 16-grid certain | margin vs all 47 certain sections outside PSSOM |
|---|---|---|---|---|---|---|
| conf (today) | 0.704 to 0.778 | 0.312 to 0.453 | **+0.252** | 0.552 to 0.815 | **+0.100** | +0.006 |
| conf minus E | 0.071 to 0.185 | 0.073 to 0.182 | -0.110 | 0.062 to 0.225 | -0.120 | -0.186 |
| ARI-like | 0.198 to 0.451 | 0.115 to 0.221 | -0.023 | 0.139 to 0.502 | -0.082 | -0.230 |
| p (shuffle) | 0.000 | 0.000 to 0.026 | 0.000 (none) | 0.000 | 0.000 (none) | -1.000 |
| bootstrap J | 0.870 to 0.991 | 0.558 to 0.755 | +0.116 | 0.816 to 0.935 | +0.061 | -0.045 |
| bootstrap exact | 0.372 to 0.944 | 0.024 to 0.186 | +0.186 | 0.076 to 0.736 | -0.110 | -0.110 |
| explained | 0.894 to 0.983 | 0.480 to 0.812 | +0.082 | 0.786 to 0.950 | -0.027 | -0.104 |

- The widest margin on the ear sets belongs to today's bare confidence (+0.252), and it is confounded twice: every accepted section is on the eighth grid and was recovered by the recall gate, every rejected one is on the sixteenth grid. Within the sixteenth grid its margin is +0.100, between PSSOM 28-39 (0.453) and Fame 47-61 (0.552). The empty band is therefore (0.453, 0.552); its midpoint is 0.503. Today's 0.55 sits 0.002 below its upper edge. PSSOM's instrumental (67-77, 0.504, not ear-checked) lies inside the band.
- Bootstrap stability separates the ear sets (+0.116) and the sixteenth grid (+0.061), but it is not a noise test: half-density sprays have a median bootstrap J of 0.82 at 8 bars (p5 0.70 to 0.74), above the rejected choruses, because a saturated vote is stable under resampling.
- The chance-corrected figures do not separate the ear sets at all, for the reason in section 4.

So the answer to "which statistic separates with the widest margin" is the bare confidence within a grid, as today, and the answer to "what does a chance correction add" is a noise test, not a two-guitar test. The proposal in section 6 keeps both.

### 5.1 Random sprays (each slot struck with probability p)

False-certain rate: share of 2000 random sections printing certain.

| slots | p | bars | conf median (p95) | full vote share | today | proposed rule | p-test alone, no full-vote exemption |
|---|---|---|---|---|---|---|---|
| 8 | 0.3 | 8 | 0.375 (0.475) | 0.002 | 0.095 | 0.037 | 0.037 |
| 8 | 0.5 | 8 | 0.527 (0.616) | 0.273 | **0.920** | **0.082** | 0.046 |
| 8 | 0.5 | 16 | 0.510 (0.578) | 0.418 | 0.919 | 0.069 | 0.056 |
| 8 | 0.7 | 8 | 0.703 (0.797) | 0.916 | 1.000 | 0.919 | 0.034 |
| 16 | 0.3 | 8 | 0.370 (0.439) | 0.000 | 0.000 | 0.000 | 0.000 |
| 16 | 0.5 | 8 | 0.529 (0.593) | 0.080 | **0.298** | **0.051** | 0.041 |
| 16 | 0.5 | 16 | 0.509 (0.559) | 0.173 | 0.080 | 0.017 | 0.016 |
| 16 | 0.7 | 8 | 0.703 (0.773) | 0.827 | 1.000 | 0.879 | 0.055 |

"Today" is confidence at or above 0.45 (8 slots) or 0.55 (16 slots) and `explained` at least 0.6. The proposed rule is section 6.

- The 1.3 figure of 30 percent at 16 slots with 0.55 is reproduced (0.298). The review's 85 percent at 8 slots with 0.45 and 69 percent at 16 slots with 0.50 are not: this simulation gives 92 and 78.5 percent (a second run 77.6). Its method is not recorded; sprays striking exactly half of every bar give 100, 100 and 15.2 percent, so it was neither.
- The p-test alone holds every density at about 5 percent (1.4 to 6.2 percent over all twelve settings), as a permutation test should: a Bernoulli spray is exchangeable under the shuffle.
- The full-vote exemption (section 6) is what lets dense sprays through: at p = 0.7 the vote is "every slot" and the bars strike 70 percent of the slots, which the rule accepts as busy strumming. At p = 0.5 it adds 3.6 points at 8 slots and 1 point at 16.
- Sprays with a metrical bias are not noise to the test, correctly: on 16 slots with eighths struck at 0.7 and odd sixteenths at 0.3, 78 percent have p at or below 0.05 and 71 percent print certain under the proposed rule (83 percent today). The vote finds a real slot preference. A two-part section is this case.

## 6. Proposal

### 6.1 The rule

Keep today's confidence, `explained` and length tests, and add a structure test:

```
full      = every slot of the topped-up vote is struck
structured = (strike density >= FULL_VOTE_DENSITY) if full else (chance_p <= CHANCE_ALPHA)
uncertain = confidence < floor(grid) or explained < EXPLAINED_BELOW or not long_enough or not structured
```

- `chance_p`: (b + 1) / (m + 1), where b is the number of the m slot-shuffled copies whose confidence is at least the section's (Phipson and Smyth's correction, so it is never zero). Each bar's cells are permuted, so its strikes and mutes are kept; the vote, floor and confidence are recomputed per copy exactly as `section_summary` does.
- `CHANCE_ALPHA = 0.05`. Band on the seven songs: the certain sections that keep their status have p up to 0.021 (S69 75-83); the lowest p among those it flips is 0.064 (AFU 55-61). 0.05 sits in (0.021, 0.064) and gives the calibrated 5 percent on sprays. 0.10 would also sit in the band for six of the seven songs but keeps AFU 55-61 (0.064).
- `FULL_VOTE_DENSITY = 0.6` (strike share, mutes counted as strikes). Band: the certain full-vote sections run from 0.625 (AFU 28-33) to 0.865; half-density sprays with a full vote have a median of 0.547 at 8 slots and 8 bars (p95 0.625, max 0.672; at 16 bars p95 0.594). This is the weakest threshold in the proposal: AFU 28-33 (0.625) and AFU 33-49 (0.672) sit inside the spray range.
- `CHANCE_SHUFFLES = 1000`, from a generator seeded per section (for example by its start bar), so a re-run writes identical files, as the validation compares. With 1000 shuffles the Monte Carlo error of p near 0.05 is about 0.007; with 200 it is about 0.015, which could move AFU 55-61 (0.064) across the line between seeds.
- The floors stay: 0.45 on the eighth grid and 0.55 on the sixteenth. The sixteenth floor is the only thing holding PSSOM 28-39 (section 5), and no structure test replaces it. With the p-test guarding against noise, the sixteenth floor no longer has to sit high to reject sprays (the 1.3 reason for rejecting 0.50), so it could move to **0.53**: centred between PSSOM's instrumental (0.504, not ear-checked) and Fame 47-61 (0.552), margins 0.026 and 0.022 instead of 0.046 and 0.002. It flips nothing on the seven songs; half-density 16-slot sprays then print certain 5.3 percent of the time against 4.3 percent at 0.55 (second run, 8 bars). The midpoint of the ear band, 0.503, is not recommended: it would make PSSOM 67-77 certain.

### 6.2 Code

- `src/youkelele/music/as_played.py`: add `CHANCE_ALPHA`, `CHANCE_SHUFFLES`, `FULL_VOTE_DENSITY` beside `:17-27`, with this document as their evidence; add `chance_p(bars, seed) -> float` and `full_vote(vector) -> bool`; give `section_summary` (`:95-115`) the vote it already builds (`:108`) to the new test rather than recomputing it. `jaccard`, `majority_vector` and `fill_to_floor` are unchanged, so every printed pattern is unchanged.
- `src/youkelele/stages/strums.py:188`: add `or not structured` to `uncertain`. An inherited pattern (`:205-210`) is already uncertain.
- `src/youkelele/schemas.py:160-169`: `SectionPattern.chance_p: float | None = None` and `strike_density: float | None = None`, defaulted so version 1.4 files load; schema version stays 1.
- `src/youkelele/evaluate.py`: print `chance_p` per section beside `explained`, so the compare harness shows the new reason for an uncertain box.
- Not changed: the recall gate's agreement check (`recall.py:141`). It compares the bare confidence before and after adding onsets, and adding strikes raises the bare confidence of a saturated section by itself (section 4), so the check is weaker than it reads. It is recorded as a risk, not changed here, because the gate's ear-checked decisions rest on it.

### 6.3 Expected flips (question 3)

Only certain-to-uncertain flips are possible. On the seven songs:

| song | flips | section | bars | printed | conf | p | judgement |
|---|---|---|---|---|---|---|---|
| Summer of '69 | 1 | 5 verse | 53-58 (5 bars) | `DU-UDUDU` | 0.693 | 0.332 | Defensible, not clearly right. The five bars (`D--U-UD-`, `DU-UD-D-`, `DU-U-UDU`, `DUDUDUD-`, `D--U--DU`) share the `DU-U` opening, the groove the certain verse 75-83 also shows (`DU-UD-D-` three times), but the second half varies bar to bar and five bars cannot show the printed rests are better than chance. The sheet loses a strip that was roughly right. |
| Chelsea Dagger | 0 | | | | | | Every section has p 0.000; the ear-accepted choruses stay certain. |
| Pour Some Sugar On Me | 0 | | | | | | Already uncertain throughout. |
| Wet Leg | 0 | | | | | | Five full votes exempt (density 0.812 to 0.865), the rest p at or below 0.018. |
| Fame | 0 | | | | | | Every section p 0.000. |
| All Fired Up | 2 | 4 verse | 55-61 (6 bars) | `D-Dx-U-U` | 0.533 | 0.064 | Right. No bar matches the pattern (`D-D-----`, `---U-U--`, `--DxxU-x`, `xxxU-x-x`, `D-DxDU-U`, `D--x-UDU`); the other verses print `D-D-D-DU` or `DUDUDUDU`. |
| All Fired Up | | 11 chorus | 128-132 (4 bars) | `D---DUD-` | 0.562 | 0.208 | Probably wrong. Two of the four bars (`DU--DUD-`, `D---DUDU`) are close to the pattern; at four bars the test has little power (section 6.4). Low stakes: a recall-boosted four-bar section. |
| Need You Tonight | 0 | | | | | | Every certain section p 0.000. |

The ear-accepted sections and every sixteenth-grid certain section keep their status. Of the three flips, one is right, one defensible and one probably wrong; all three are sections of four to six bars.

### 6.4 Power on short sections

A true pattern with each cell flipped with probability q, 500 sections per cell, share printing certain (today's rule passes all of them):

| pattern | q | 4 bars | 5 bars | 6 bars | 8 bars | 12 bars |
|---|---|---|---|---|---|---|
| `S-SS-SSS` (8) | 0.1 | 0.89 | 0.96 | 0.99 | 1.00 | 1.00 |
| `S-SS-SSS` (8) | 0.2 | 0.55 | 0.71 | 0.82 | 0.93 | 0.99 |
| `S-S-S-SS` (8) | 0.2 | 0.64 | 0.77 | 0.89 | 0.95 | 1.00 |
| `S-SS-SSSS-S-SSS-` (16) | 0.2 | 0.86 | 0.93 | 0.99 | 1.00 | 1.00 |

At four bars a noisy but real eighth-grid pattern goes uncertain a third to a half of the time. The cost of the test falls on short sections, which is where the three real flips are.

## 7. One guitar or two on a sixteenth grid (question 4)

### 7.1 What was measured

The 1.3 spike tried onset-level quantities on the union (`explained`, mean Jaccard, onset-count variability, gain ratio). This strand measured the guitar stem's audio around the stage's own onsets (`onsets.detect_onsets` on the mono guitar stem; all seven songs use the guitar stem), and the bass stem, per section (`s4_audio.py`):

- **Pitch content of each onset** (window 40 to 130 ms after it, past the attack and inside the shortest sixteenth here, 138 ms): constant-Q power from C2 over six octaves. *Chroma entropy* (normalised; low means one or two pitch classes); *one-pitch-class share* (onsets with only one pitch class at half the maximum or more); *harmonic dominance* (the largest share of the window's energy on one harmonic series whose fundamental is present; high for a single note); *single share* (onsets with dominance at least 0.6).
- **pYIN** voiced probability (80 to 1000 Hz) over the section's non-silent frames: a single-note line is voiced, a chord is not.
- **Inter-onset spectral flatness**: median over frames more than 60 ms after an onset and more than 30 ms before the next.
- **Onset spread**: the entropy of the positive spectral flux across 96 mel bands at the onset, and the share of that flux in the lower 48 bands.
- **Onset strength**: Sarle's bimodality coefficient of the log onset strengths; their coefficient of variation.
- **Guitar against bass**: share of guitar onsets within 50 ms of a bass onset, less the chance share for the section's bass onset rate; the correlation of the two onset-strength envelopes over the section.
- **Chord continuity**: the median cosine between the chroma of consecutive onsets (a riff changes pitch from onset to onset; a strum on one chord repeats).

### 7.2 Results

Ranges per group. "Margin" is in the better of the two directions; negative means overlap. KEEP16 = the 14 sixteenth-grid certain sections (Fame, NYT); ACC8 = the 4 ear-accepted choruses.

| feature | REJ (3) | KEEP16 (14) | ACC8 (4) | other PSSOM (5) | margin REJ vs KEEP16 | margin REJ vs KEEP16 and ACC8 |
|---|---|---|---|---|---|---|
| chroma entropy | 0.915 to 0.927 | 0.540 to 0.788 | 0.872 to 0.922 | 0.780 to 0.914 | +0.127 (KEEP16 lower) | -0.007 |
| one-pitch-class share | 0.153 to 0.314 | 0.466 to 0.783 | 0.264 to 0.478 | 0.288 to 0.426 | +0.152 (KEEP16 higher) | -0.050 |
| harmonic dominance | 0.302 to 0.326 | 0.384 to 0.577 | 0.304 to 0.383 | 0.273 to 0.432 | +0.058 (KEEP16 higher) | -0.022 |
| single share (dominance at least 0.6) | 0.000 | 0.021 to 0.370 | 0.000 | 0.000 to 0.106 | +0.021 | 0.000 |
| pYIN voiced probability | 0.012 to 0.021 | 0.067 to 0.346 | 0.010 to 0.020 | 0.017 to 0.078 | +0.046 (KEEP16 higher) | -0.010 |
| low-band share of onset flux | 0.576 to 0.588 | 0.448 to 0.526 | 0.433 to 0.481 | 0.514 to 0.566 | +0.050 (REJ higher) | +0.050 |
| onset flux spread | 0.889 to 0.903 | 0.901 to 0.968 | 0.892 to 0.971 | 0.889 to 0.946 | -0.002 | -0.011 |
| strength bimodality | 0.299 to 0.421 | 0.237 to 0.606 | 0.203 to 0.332 | 0.220 to 0.568 | -0.184 | -0.218 |
| strength CV | 0.226 to 0.371 | 0.317 to 0.571 | 0.206 to 0.431 | 0.321 to 0.463 | -0.054 | -0.165 |
| bass-coincidence excess | 0.221 to 0.262 | -0.043 to 0.186 | 0.138 to 0.525 | -0.040 to 0.172 | +0.035 (REJ higher) | -0.304 |
| guitar-bass envelope correlation | 0.113 to 0.292 | 0.004 to 0.340 | 0.239 to 0.432 | 0.041 to 0.315 | -0.226 | -0.288 |
| consecutive chroma cosine | 0.835 to 0.889 | 0.547 to 0.806 | 0.675 to 0.905 | 0.813 to 0.925 | +0.030 (KEEP16 lower) | -0.070 |
| inter-onset flatness | 0.0017 to 0.0027 | 0.0003 to 0.0014 | 0.0011 to 0.0014 | 0.0010 to 0.0845 | +0.0003 | +0.0003 |

Per section:

| song | # | bars | state | ear | chroma entropy | one-pitch-class share | harmonic dominance | pYIN voiced prob | low-band onset flux share | strength bimodality | bass-coincidence excess | guitar-bass envelope corr | consecutive chroma cosine | inter-onset flatness |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S69 | 4 | 41-53 | certain | ACC | 0.877 | 0.306 | 0.383 | 0.020 | 0.452 | 0.272 | +0.299 | 0.248 | 0.778 | 0.0011 |
| S69 | 9 | 83-95 | certain | ACC | 0.876 | 0.478 | 0.348 | 0.019 | 0.433 | 0.332 | +0.138 | 0.239 | 0.675 | 0.0014 |
| Chelsea | 1 | 20-38 | certain | ACC | 0.922 | 0.264 | 0.304 | 0.011 | 0.473 | 0.279 | +0.525 | 0.432 | 0.905 | 0.0013 |
| Chelsea | 6 | 108-142 | certain | ACC | 0.872 | 0.270 | 0.353 | 0.010 | 0.481 | 0.203 | +0.174 | 0.304 | 0.802 | 0.0011 |
| PSSOM | 0 | 0-11 | uncertain |  | 0.780 | 0.385 | 0.432 | 0.051 | 0.527 | 0.220 | +0.005 | 0.143 | 0.925 | 0.0010 |
| PSSOM | 1 | 11-28 | uncertain |  | 0.892 | 0.288 | 0.350 | 0.034 | 0.533 | 0.360 | +0.020 | 0.084 | 0.813 | 0.0015 |
| PSSOM | 2 | 28-39 | uncertain | REJ | 0.927 | 0.153 | 0.302 | 0.012 | 0.577 | 0.299 | +0.252 | 0.235 | 0.835 | 0.0017 |
| PSSOM | 3 | 39-55 | uncertain |  | 0.863 | 0.349 | 0.403 | 0.039 | 0.517 | 0.282 | +0.026 | 0.041 | 0.847 | 0.0011 |
| PSSOM | 4 | 55-67 | uncertain | REJ | 0.918 | 0.314 | 0.326 | 0.021 | 0.576 | 0.421 | +0.262 | 0.292 | 0.889 | 0.0021 |
| PSSOM | 5 | 67-77 | uncertain |  | 0.786 | 0.426 | 0.409 | 0.078 | 0.514 | 0.226 | -0.040 | 0.072 | 0.835 | 0.0011 |
| PSSOM | 6 | 77-84 | uncertain |  | 0.914 | 0.300 | 0.273 | 0.017 | 0.566 | 0.568 | +0.172 | 0.315 | 0.860 | 0.0845 |
| PSSOM | 7 | 84-103 | uncertain | REJ | 0.915 | 0.250 | 0.324 | 0.014 | 0.588 | 0.312 | +0.221 | 0.113 | 0.849 | 0.0027 |
| Fame | 0 | 0-17 | certain |  | 0.760 | 0.466 | 0.409 | 0.067 | 0.487 | 0.298 | +0.175 | 0.080 | 0.627 | 0.0014 |
| Fame | 1 | 17-29 | certain |  | 0.753 | 0.524 | 0.436 | 0.154 | 0.452 | 0.314 | +0.028 | 0.031 | 0.601 | 0.0005 |
| Fame | 2 | 29-35 | certain |  | 0.724 | 0.629 | 0.449 | 0.156 | 0.471 | 0.277 | +0.051 | 0.082 | 0.547 | 0.0014 |
| Fame | 3 | 35-47 | certain |  | 0.737 | 0.549 | 0.447 | 0.125 | 0.448 | 0.368 | +0.027 | 0.083 | 0.590 | 0.0008 |
| Fame | 4 | 47-61 | certain |  | 0.706 | 0.585 | 0.448 | 0.147 | 0.484 | 0.237 | +0.047 | 0.018 | 0.560 | 0.0014 |
| Fame | 5 | 61-71 | certain |  | 0.739 | 0.491 | 0.435 | 0.115 | 0.501 | 0.345 | +0.186 | 0.102 | 0.648 | 0.0005 |
| Fame | 6 | 71-81 | certain |  | 0.704 | 0.583 | 0.486 | 0.247 | 0.496 | 0.408 | +0.026 | 0.050 | 0.597 | 0.0003 |
| Fame | 7 | 81-85 | certain |  | 0.735 | 0.576 | 0.451 | 0.160 | 0.515 | 0.400 | -0.043 | 0.004 | 0.632 | 0.0008 |
| Fame | 8 | 85-100 | certain |  | 0.695 | 0.622 | 0.506 | 0.248 | 0.526 | 0.432 | +0.002 | 0.011 | 0.589 | 0.0004 |
| NYT | 0 | 0-13 | uncertain |  | 0.862 | 0.444 | 0.372 | 0.044 | 0.474 | 0.582 | +0.146 | 0.328 | 0.853 | 0.0823 |
| NYT | 1 | 13-24 | certain |  | 0.540 | 0.783 | 0.577 | 0.346 | 0.496 | 0.316 | +0.095 | 0.283 | 0.620 | 0.0004 |
| NYT | 2 | 24-31 | certain |  | 0.788 | 0.480 | 0.384 | 0.174 | 0.487 | 0.606 | +0.030 | 0.174 | 0.806 | 0.0009 |
| NYT | 3 | 31-48 | certain |  | 0.599 | 0.683 | 0.542 | 0.238 | 0.490 | 0.352 | +0.143 | 0.301 | 0.554 | 0.0005 |
| NYT | 4 | 48-56 | certain |  | 0.756 | 0.524 | 0.424 | 0.202 | 0.507 | 0.529 | +0.051 | 0.156 | 0.806 | 0.0007 |
| NYT | 5 | 56-79 | certain |  | 0.660 | 0.675 | 0.480 | 0.200 | 0.504 | 0.258 | +0.146 | 0.340 | 0.661 | 0.0006 |
| NYT | 6 | 79-84 | uncertain |  | 0.646 | 0.630 | 0.519 | 0.220 | 0.521 | 0.404 | +0.210 | 0.288 | 0.713 | 0.0008 |

### 7.3 Reading

- **The pitch features split PSSOM from Fame and NYT the wrong way round.** Chroma entropy, one-pitch-class share, harmonic dominance, pYIN voicing and chord continuity all say the certain sixteenth-grid sections are *more* single-note-like than the rejected choruses (NYT 13-24: one pitch class at 78 percent of onsets, voiced probability 0.35; PSSOM 28-39: 15 percent, 0.012). On these features the rejected choruses look like the ear-accepted strummed choruses (chroma entropy 0.915 to 0.927 against 0.872 to 0.922). A guard built on "single notes present" would make Fame and Need You Tonight uncertain and leave PSSOM where it is; inverted, it would reject the accepted choruses. Neither is a two-guitar test. The likely reason: the rejected choruses are dominated by the strummed, distorted part, which masks the riff in a 90 ms window, while Fame's and Need You Tonight's guitars are riffs and short chord stabs.
- **The only feature with a positive margin on both comparisons, the low-band share of onset flux (+0.050), is not usable.** It is the best of seventeen tried on three rejected sections from one song, so it is a selected result; the other PSSOM sections (not ear-checked) run 0.514 to 0.566, between the groups; and on the eighth grid All Fired Up's certain, palm-muted `Dxxxxxxx` verse (104-110) reaches 0.584, inside the rejected range. It measures low-frequency attack (palm-muted chugs, bass and kick bleed in the guitar stem, which the bass-coincidence excess of the PSSOM choruses also suggests), not a second guitar.
- **Inter-onset flatness** separates by 0.0003 on values of 0.001 to 0.003: noise.
- **Onset strength bimodality, strength CV, guitar-bass correlation and onset spread** overlap outright.

**Null result.** Nothing measured here separates Pour Some Sugar On Me's rejected sections from the accepted sixteenth-grid sections with a usable margin, and the features that come closest do so by calling the accepted sixteenth-grid sections single-note riffs. The sixteenth-grid recall gate and a two-guitar guard are not achievable with section-level onset or spectral statistics on these seven songs.

### 7.4 What the stated limitation should say

Proposed wording for the spec and the README's limitations:

> The strums stage cannot tell one strummed guitar from two parts in one stem. Pour Some Sugar On Me's two-guitar choruses are held uncertain only by the sixteenth-grid confidence floor (they score 0.31 to 0.45; the floor is 0.55 and the nearest certain sixteenth-grid section scores 0.552); the chance test does not catch them, because two regular parts together are a regular, non-random pattern. A two-part section whose combined strikes repeat more consistently will print a certain box. On the sixteenth grid a certain box means a repeatable rhythm in the guitar stem, which may be a riff (Fame, Need You Tonight) rather than strummed chords. The recall gate stays off on the sixteenth grid for the same reason.

What would be needed instead, from the literature (section 9): separating the parts first (lead and rhythm guitar separation is an open problem for timbrally similar sources), or a trained strum detector of the Yousician kind, which reports that other guitars in the backing are amplified in the guitar stem and still decodes against a pattern vocabulary rather than trusting a confidence.

## 8. Risks

- **Three short sections lose their strips**, and one of them (AFU 128-132) is probably right as printed. At four to six bars the test's power is 55 to 89 percent on noisy real patterns (section 6.4). If short sections matter more than spray rejection, a softer alpha for sections under eight bars is the lever, at the cost of the calibrated rate.
- **The full-vote exemption is the weak joint.** At 8 slots and 8 bars, 27 percent of half-density sprays vote every slot, and their densities (to 0.672) overlap the two lowest real full-vote sections (AFU 0.625 and 0.672). Raising `FULL_VOTE_DENSITY` to 0.68 would make AFU 28-33 and 33-49 uncertain; whether their `DUxxxUxU` and `DUDUDUDU` are right is not known (blind song).
- **The sixteenth floor's upper margin is 0.002** (Fame 47-61 at 0.552 against 0.55), created by 1.4's re-cut sections. Any change to onsets, sections or the vote can tip Fame's instrumental. Moving the floor to 0.53 trades that for a 0.026 margin to PSSOM's instrumental, which no one has listened to.
- **Determinism.** An unseeded shuffle would make `uncertain` flicker between runs for sections near alpha. Seed per section.
- **The recall gate's agreement check** (`recall.py:141`) uses the bare confidence, which rises with density on saturated sections; it is weaker than it reads. Not changed here.
- **The audio features used today's full-band onsets**, not the recall gate's union, for the four eighth-grid choruses. Their pitch content is unaffected by which strikes are counted, but their onset-level features (bimodality, bass coincidence) would shift with the union.

## 9. Literature

- Chung, Miasojedow, Startek and Gambin, "Jaccard/Tanimoto similarity test and estimation methods for biological presence-absence data", BMC Bioinformatics 20 (2019), https://pmc.ncbi.nlm.nih.gov/articles/PMC6929325/. The centred Jaccard is the observed coefficient less its expectation under independence, p_i p_j / (p_i + p_j minus p_i p_j); they test it exactly, asymptotically and by bootstrap, and show the raw coefficient correlates with occurrence rates. Used for: the 1.3 proposal is their centring; with the vote fully struck the expectation is the bar density (section 4).
- Hubert and Arabie, "Comparing partitions", Journal of Classification 2 (1985) 193-218, https://doi.org/10.1007/BF01908075. Used for the (index minus expected) / (maximum minus expected) form of the ARI-like figure.
- Feinstein and Cicchetti, "High agreement but low kappa: I. The problems of two paradoxes", Journal of Clinical Epidemiology 43 (1990) 543-549, https://doi.org/10.1016/0895-4356(90)90158-L. With one category's prevalence near 0 or 1, chance agreement is large and a chance-corrected index is low despite high agreement. Used for: why every full-vote section scores zero, and why the correction cannot replace the confidence.
- Phipson and Smyth, "Permutation p-values should never be zero: calculating exact p-values when permutations are randomly drawn", Statistical Applications in Genetics and Molecular Biology 9 (2010) article 39, https://arxiv.org/abs/1603.05766. Used for (b + 1) / (m + 1) in `chance_p`.
- Lukoianov and Klapuri (Yousician), "Transcribing Rhythmic Patterns of the Guitar Track in Polyphonic Music", arXiv 2510.05756 (2025), https://arxiv.org/abs/2510.05756. Backing tracks often contain other guitars, and extra parts are sometimes amplified in the separated guitar stem; their system decodes strums against a 924-pattern vocabulary with a Viterbi pass rather than thresholding a confidence. Used for the limitation wording and the "what would be needed".
- Chen, Su and Yang, "Electric guitar playing technique detection in real-world recordings based on F0 sequence pattern recognition", ISMIR 2015, https://ismir2015.uma.es/articles/119_Paper.pdf; and Su, Yu and Yang, "Sparse cepstral and phase codes for guitar playing technique classification", ISMIR 2014, https://archives.ismir.net/ismir2014/paper/000213.pdf. Technique detection is trained on isolated notes or on solo tracks without accompaniment (F-score 74 percent and 71.7 percent). Used for: there is no off-the-shelf detector of a single-note part inside a strummed stem.
- GuitarDuets, arXiv 2507.01172 (2025), https://arxiv.org/abs/2507.01172: per its abstract, separating instruments of similar timbre (monotimbral separation) has been overlooked by source separation research. Used for: separating two guitars first is a research problem, not a configuration.

## 10. Assumptions

| # | assumption | status | cost if wrong |
|---|---|---|---|
| A1 | `bar_onsets` in the run folders are the strike vectors the stored patterns were voted from | **Verified**: every stored confidence and `explained` reproduced exactly on 64 sections | none found |
| A2 | Chelsea's 1.4 sections 20-38 and 108-142 inherit the ear verdict of 9-38 and 105-142 | Unverified (they are subsets of the accepted bars; the ear check heard clicks from the recall spike, not these runs) | the accepted set shrinks to two sections; no conclusion changes, since all four have p 0.000 |
| A3 | PSSOM 28-39 and 55-67 are two-guitar sections like 84-103 | Unverified: the click-track ear check covered the last chorus only (1.3 validation, "What cannot be verified") | the rejected set is one section; the null result in section 7 stands with even less evidence |
| A4 | Fame's and Need You Tonight's certain sixteenth-grid sections are good patterns | Unverified, and section 7 suggests they are riffs (the 1.4 validation also says so for Need You Tonight) | the "keep" side of every sixteenth-grid margin is unknown; the 0.55 floor's evidence is weaker than it looks |
| A5 | Random Bernoulli sprays are the right noise model | Measured (1.3's 30 percent reproduced; its 85 and 69 percent not) | a different spray changes the "today" column, not the proposed rule's 5 percent, which holds for any exchangeable noise |
| A6 | Shuffling all slots of a bar uniformly is the right null | Measured as calibrated on sprays; it ignores metre, so a metrically biased random section is (correctly) called structured | a metre-aware null would flip more short sections and would also call PSSOM's choruses structured |
| A7 | "Every slot struck" is a claim about density, not structure | Judgement, supported by the kappa paradox literature | if a full vote should also be tested, every DUDUDUDU section on Wet Leg and Summer of '69 goes uncertain |
| A8 | `FULL_VOTE_DENSITY = 0.6` | Measured band (spray median 0.547, lowest real 0.625), narrow and overlapping the spray tail | dense sprays print certain about 8 percent at 8 slots instead of about 5 percent |
| A9 | The audio features are computed correctly | Measured on all 64 sections; pYIN's per-frame voiced probability is low on distorted guitar (median 0.01 on PSSOM), so the mean was used | a feature mis-specified here could hide a real separator; the null result is for these features, not for all features |
| A10 | Today's full-band onsets are a fair sample of each section's strikes for the audio features | Unverified for the four recall-boosted choruses | onset-level features of those four may move; pitch features should not |
| A11 | Seven songs, of which two are sixteenth-grid songs with certain sections, are enough to set alpha | Unverified; alpha is set by calibration on sprays, not by these songs | a song with many short, noisy but real sections pays more in lost strips |
