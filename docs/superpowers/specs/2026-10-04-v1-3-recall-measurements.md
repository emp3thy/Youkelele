# Version 1.3 recall gate: measurements

This document holds the evidence for the recall gate of the strums stage (design spec `2026-10-04-ukulele-tab-chain-v1-3-design.md`, section 4.3; code `src/youkelele/music/recall.py`). Sections 3 to 5 are copied from the two spikes run for the design (`spike_recall`, config `G_f3000_g0.4_union`, and `spike_recall2`); section 2 is the confirmation of the implemented gate on the five 1.2 runs.

## 1. The constants and their evidence

| constant | value | evidence |
|---|---|---|
| `HIGH_BAND_FMIN` | 3000 Hz | Section 3: the gated union passes every criterion at 2500, 3000 and 4000 Hz; at 2000 Hz the second Summer of '69 chorus stays at 3.8 strikes per bar with `S-S-S-S-`. 3000 gives the choruses' `S-SSSSS-` that the ear check called "pretty much perfect". |
| `SPARSE_SHARE` | 0.4 | Section 3: sparse shares 0.4 and 0.5 both pass every criterion; 0.4 is the more conservative and is the configuration judged by ear. Section 5.1 lists the sections it tries (no Wet Leg section is). |
| `MERGE_MS` | 60 ms | Section 3 (spike `gated.py`): a high-band onset within 60 ms of one of today's is the same strike, so it is not counted twice. |
| `MIN_GAIN` | 1.0 strike per bar | Section 3: 0.5 gives the same decisions (`G_f3000_g0.4_union_gain0.5`); the Summer of '69 outro (2.6 to 2.9) and Chelsea Dagger's intro (2.0 to 2.1) fall under it. |
| `FIT_TOLERANCE` | 0.05 | Section 5.1: the lowest accepted section grid fit is 0.53 against a song fit of 0.55 (Chelsea Dagger 9-38). |
| `SILENT_BAR_SHARE` | 0.25 | Section 5.2: Chelsea Dagger's entry bars 9 to 12 sit at 0.135 and below, the quietest struck bar in an accepted section at 0.446; any value from 0.15 to 0.40 gives the same patterns. |

The gate applies only on the eighth-note grid (`slots_per_bar == meter.numerator * 2`). Section 5.3 measured five candidate regularity guards against the ear verdicts (union `explained`, mean Jaccard, coefficient of variation of onsets per bar, share of bars off the median by 25 percent, gain ratio); none separates the ear-accepted sections from Pour Some Sugar On Me's rejected choruses with a usable margin, and the grid does.

## 2. Confirmation on the 1.2 runs

The real `StrumsStage` (with the gate) was run on the five runs in `C:\Users\gethi\sources\Youkelele\runs`, reading the 1.2 stems and grids and writing only to the session scratchpad (`task4/confirm.py`, output `task4/confirm/`). Every song's source is its guitar stem.

Per song:

| song | source | slots per bar | today's onsets | high-band onsets | onsets added | final onsets | grid fit (1.2 / now) | bar_onsets identical to 1.2 | decisions |
|---|---|---|---|---|---|---|---|---|---|
| Summer of '69 | guitar_stem | 8 | 491 | 652 | 63 | 554 | 0.9084 / 0.9084 | no | dense 8, accepted 2, gain 1 |
| Chelsea Dagger | guitar_stem | 8 | 538 | 750 | 148 | 686 | 0.5465 / 0.5465 | no | gain 1, accepted 2, dense 5 |
| Pour Some Sugar On Me | guitar_stem | 16 | 626 | 1094 | 0 | 626 | 0.5942 / 0.5942 | yes | sixteenth grid 7 |
| Wet Leg | guitar_stem | 8 | 815 | 802 | 0 | 815 | 0.7269 / 0.7269 | yes | dense 8, no instrument (not gated) 1 |
| Fame | guitar_stem | 16 | 1005 | 818 | 0 | 1005 | 0.6269 / 0.6269 | yes | sixteenth grid 8 |

Per section, for the two songs where the gate fires (patterns as printed, `D` and `U` for a strike; `D-DUDUD-` is `S-SSSSS-`):

| song | section | bars | decision | strikes per bar today | with the union | onsets added | bars with added onsets | pattern now | explained now |
|---|---|---|---|---|---|---|---|---|---|
| Summer of '69 | 0 verse 2 | 0-4 | dense | 5.00 | 5.00 | 0 | none | `D-xx-xxx` | 0.90 |
| Summer of '69 | 1 verse | 4-19 | dense | 6.13 | 6.13 | 0 | none | `xxxUxxxx` | 1.00 |
| Summer of '69 | 2 chorus | 19-31 | dense | 3.92 | 3.92 | 0 | none | `D-DU-UD-` | 0.87 |
| Summer of '69 | 3 verse | 31-41 | dense | 4.40 | 4.40 | 0 | none | `DUDUD-D-` | 0.93 |
| Summer of '69 | 4 chorus | 41-53 | accepted | 2.92 | 5.17 | 29 | 41 to 52 (11 bars) | `D-DUDUD-` | 0.95 |
| Summer of '69 | 5 verse | 53-58 | dense | 5.20 | 5.20 | 0 | none | `DU-UDUDU` | 0.96 |
| Summer of '69 | 6 verse 2 | 58-69 | dense | 3.55 | 3.55 | 0 | none | `D-DUD-DU` | 0.87 |
| Summer of '69 | 7 verse | 69-83 | dense | 5.21 | 5.21 | 0 | none | `DUDUDUDU` | 1.00 |
| Summer of '69 | 8 chorus | 83-95 | accepted | 1.83 | 4.58 | 34 | 83 to 94 (12 bars) | `D-DUDUD-` | 0.96 |
| Summer of '69 | 9 verse | 95-111 | dense | 3.31 | 3.31 | 0 | none | `D--UD-D-` | 0.68 |
| Summer of '69 | 10 outro | 111-121 | gain | 2.60 | 2.90 | 0 | none | `DU--x---` | 0.58 |
| Chelsea Dagger | 0 verse | 0-9 | gain | 2.00 | 2.11 | 0 | none | `D-------` | 0.17 |
| Chelsea Dagger | 1 chorus | 9-38 | accepted | 2.76 | 4.31 | 49 | 14 to 37 (19 bars) | `D-D-D-DU` | 0.88 |
| Chelsea Dagger | 2 verse | 38-61 | dense | 3.91 | 3.91 | 0 | none | `D-DUDUDU` | 0.98 |
| Chelsea Dagger | 3 chorus | 61-71 | dense | 3.20 | 3.20 | 0 | none | `D-D-D-D-` | 0.84 |
| Chelsea Dagger | 4 verse | 71-93 | dense | 3.68 | 3.68 | 0 | none | `D-D-D-D-` | 0.75 |
| Chelsea Dagger | 5 chorus | 93-99 | dense | 5.00 | 5.00 | 0 | none | `D-DUD-DU` | 0.93 |
| Chelsea Dagger | 6 bridge | 99-105 | dense | 3.83 | 3.83 | 0 | none | `--DUD-DU` | 0.87 |
| Chelsea Dagger | 7 chorus | 105-142 | accepted | 2.59 | 5.00 | 99 | 105 to 141 (34 bars) | `D-DUDUDU` | 0.98 |

Against the expected decisions:

- Summer of '69: bars 41-53 and 83-95 accepted, 2.92 to 5.17 and 1.83 to 4.58 strikes per bar, both `S-SSSSS-` (as expected: about 5.2 and 4.6). The verses are untouched (dense); the outro is tried and rejected on gain.
- Chelsea Dagger: bars 9-38 and 105-142 accepted (2.76 to 4.31 and 2.59 to 5.00); no onset is added in bars 9 to 12 (the first added onset is in bar 14). The spike's union reached 4.38 in 9-38 because it also clicked in the silent entry bars. Patterns `S-S-S-SS` and `S-SSSSSS`, as in section 5.1.
- Pour Some Sugar On Me: every section skipped (sixteenth grid); onsets and `bar_onsets` identical to 1.2.
- Wet Leg: every section dense or without an instrument; onsets and `bar_onsets` identical to 1.2.
- Fame: every section skipped (sixteenth grid); onsets and `bar_onsets` identical to 1.2.
- Song grid fit is unchanged on all five, because the stage reports the fit of today's onsets (the fit the gate compares against).

Outside the accepted sections, the strike positions of Summer of '69 and Chelsea Dagger are unchanged, but a few slots flip between strike and mute: Summer of '69 has 4 slots going from `x` to a strike, Chelsea Dagger 6 slots going from a strike to `x`. The cause is the mute rule's medians (centroid and zero-crossing rate), which the spec computes on the final onset list, so the added onsets shift them slightly.

## 3. Candidate comparison (spike_recall/summary.md)

One row per candidate, scored against today's detector. Columns: the two Summer of '69 choruses (strikes per bar, pattern, mean Jaccard to the section vote); the first verse (`ok` when its strikes per bar move by 0.5 or less and its strike pattern is unchanged); the Wet Leg and Fame sections whose pattern or strikes per bar changed (`ok` for none); Chelsea Dagger's and Pour Some Sugar On Me's mean change in `explained` and Jaccard; the change in song grid fit for the five songs; `PASS` when the choruses reach 4 strikes per bar with Jaccard 0.6, the verse is unharmed and no Wet Leg or Fame section changes. Candidates: `C1` bar-local contrast on the envelope, `C2` the whole-song high-band envelope (`f` its lower edge, `mean` or `max` over bands), `C3` a lowered per-section threshold with a floor, combinations of those, `U_today+C2` today's onsets merged with the whole-song high band, and `G` the gated union or replacement (`f` the lower edge, `g` the sparse share).

| cand | S69 ch 41-53 | S69 ch 83-95 | S69 verse 4-19 | WetLeg sections changed | Fame sections changed | Chelsea dExpl/dJac | PSSOM dExpl/dJac | dfit S69 PSSOM WL Fame Ch | all 4 |
|---|---|---|---|---|---|---|---|---|---|
| C1C2_f2000_midmax_k1.5 | 4.9 `S-SSSSS-` J0.75 | 3.9 `S-S-S-S-` J0.68 | 6.3 `xxxxxxxx` ok | [0, 2, 3, 4, 5, 6, 7, 8] | [0, 1, 2, 3, 4, 5, 6, 7] | -0.05/+0.00 | +0.08/+0.08 | +0.09 +0.41 +0.27 +0.37 +0.45 |  |
| C1C2_f2000_midmax_k2 | 3.4 `S-S---S-` J0.66 | 2.7 `S-S---S-` J0.64 | 5.5 `SxxSxxxx` CHANGED | [0, 1, 2, 5, 8] | [0, 1, 2, 3, 4, 5, 6, 7] | -0.01/+0.00 | -0.16/-0.05 | +0.09 +0.41 +0.27 +0.37 +0.45 |  |
| C1C2_f2000_midmax_k2.5 | 2.8 `S-S---S-` J0.61 | 1.8 `S-----S-` J0.60 | 5.1 `xxxxxxxx` CHANGED | [0, 1, 2, 3, 5, 6, 7, 8] | [0, 1, 2, 3, 4, 5, 6, 7] | -0.05/-0.03 | -0.25/-0.07 | +0.09 +0.41 +0.27 +0.37 +0.45 |  |
| C1C2_f3000_midmax_k1.5 | 5.2 `S-SSSSS-` J0.79 | 4.8 `S-SSSSS-` J0.72 | 6.5 `xxxxxxxx` ok | [0, 2, 3, 4, 5, 6, 7, 8] | [0, 1, 2, 3, 4, 5, 6, 7] | +0.02/+0.06 | +0.12/+0.10 | +0.09 +0.41 +0.27 +0.37 +0.45 |  |
| C1C2_f3000_midmax_k2 | 4.0 `S-S-S-S-` J0.66 | 3.3 `S-S-S-S-` J0.66 | 5.8 `Sxxxxxxx` ok | [0, 2, 3, 4, 5, 8] | [0, 1, 2, 3, 4, 5, 6, 7] | -0.07/-0.01 | -0.15/+0.00 | +0.09 +0.41 +0.27 +0.37 +0.45 |  |
| C1C2_f3000_midmax_k2.5 | 3.3 `S-S---S-` J0.68 | 2.8 `S-S---S-` J0.65 | 5.5 `Sxxxxxxx` CHANGED | [0, 1, 2, 3, 5, 6, 7, 8] | [0, 1, 2, 3, 4, 5, 6, 7] | +0.02/+0.00 | -0.21/-0.05 | +0.09 +0.41 +0.27 +0.37 +0.45 |  |
| C1_median_k2 | 2.7 `S----SS-` J0.46 | 1.2 `S-------` J0.53 | 6.2 `xxxSxxxx` ok | [0, 1, 2, 3, 5, 8] | [0, 1, 2, 3, 4, 5, 6, 7] | +0.04/+0.05 | -0.12/-0.04 | +0.09 +0.41 +0.27 +0.37 +0.45 |  |
| C1_median_k3 | 0.8 `S-------` J0.50 | 0.4 `S-------` J0.42 | 4.7 `x-xSxxS-` CHANGED | [0, 1, 2, 3, 4, 5, 6, 7, 8] | [0, 1, 2, 3, 4, 5, 6, 7] | -0.12/+0.03 | -0.53/-0.01 | +0.09 +0.41 +0.27 +0.37 +0.45 |  |
| C1_median_k4 | 0.2 `--------` J0.83 | 0.2 `--------` J0.83 | 4.1 `S-SSSSS-` CHANGED | [0, 1, 2, 3, 4, 5, 6, 7, 8] | [0, 1, 2, 3, 4, 5, 6, 7] | -0.12/+0.03 | -0.58/+0.02 | +0.09 +0.41 +0.27 +0.37 +0.45 |  |
| C1_median_k5 | 0.0 `--------` J1.00 | 0.0 `--------` J1.00 | 3.1 `S-SS--S-` CHANGED | [0, 1, 2, 3, 4, 5, 6, 7, 8] | [0, 1, 2, 3, 4, 5, 6, 7] | -0.13/+0.01 | -0.67/+0.13 | +0.09 +0.41 +0.27 +0.37 +0.45 |  |
| C1_median_k6 | 0.0 `--------` J1.00 | 0.0 `--------` J1.00 | 2.6 `S--S--S-` CHANGED | [0, 1, 2, 3, 4, 5, 6, 7, 8] | [0, 1, 2, 3, 4, 5, 6, 7] | -0.20/-0.01 | -0.70/+0.19 | +0.09 +0.41 +0.27 +0.37 +0.45 |  |
| C1_midmax_k1.5 | 3.2 `S-SS-SS-` J0.54 | 1.8 `S-------` J0.44 | 6.3 `xxxSxxxx` ok | [1, 2, 5, 8] | [0, 1, 2, 3, 4, 5, 6, 7] | +0.01/+0.04 | -0.16/-0.05 | +0.09 +0.41 +0.27 +0.37 +0.45 |  |
| C1_midmax_k2 | 1.5 `S-------` J0.51 | 0.8 `S-------` J0.62 | 5.5 `xxxSxxxx` CHANGED | [0, 1, 2, 3, 4, 5, 6, 7, 8] | [0, 1, 2, 3, 4, 5, 6, 7] | -0.03/-0.02 | -0.42/-0.08 | +0.09 +0.41 +0.27 +0.37 +0.45 |  |
| C1_midmax_k2.5 | 0.8 `S-------` J0.46 | 0.5 `S-------` J0.50 | 4.5 `x-xxxxS-` CHANGED | [0, 1, 2, 3, 4, 5, 6, 7, 8] | [0, 1, 2, 3, 4, 5, 6, 7] | -0.09/+0.01 | -0.56/+0.09 | +0.09 +0.41 +0.27 +0.37 +0.45 |  |
| C1_midmax_k3 | 0.2 `--------` J0.75 | 0.2 `--------` J0.75 | 4.1 `x-xSxxS-` CHANGED | [0, 1, 2, 3, 4, 5, 6, 7, 8] | [0, 1, 2, 3, 4, 5, 6, 7] | -0.12/+0.03 | -0.55/+0.11 | +0.09 +0.41 +0.27 +0.37 +0.45 |  |
| C1_midval_k2 | 3.0 `S-SS-SS-` J0.51 | 1.3 `S-------` J0.48 | 6.2 `xxxSxxxx` ok | [0, 1, 2, 5, 8] | [0, 1, 2, 3, 4, 5, 6, 7] | -0.02/+0.03 | -0.22/-0.07 | +0.09 +0.41 +0.27 +0.37 +0.45 |  |
| C1_midval_k3 | 1.2 `S-------` J0.49 | 0.6 `S-------` J0.58 | 4.8 `xxxxxxxx` CHANGED | [0, 1, 2, 3, 4, 5, 6, 7, 8] | [0, 1, 2, 3, 4, 5, 6, 7] | -0.10/+0.02 | -0.51/-0.00 | +0.09 +0.41 +0.27 +0.37 +0.45 |  |
| C1_midval_k4 | 0.3 `--------` J0.75 | 0.2 `--------` J0.83 | 3.9 `x-xx-xS-` CHANGED | [0, 1, 2, 3, 4, 5, 6, 7, 8] | [0, 1, 2, 3, 4, 5, 6, 7] | -0.11/+0.03 | -0.53/+0.10 | +0.09 +0.41 +0.27 +0.37 +0.45 |  |
| C1_midval_k5 | 0.0 `--------` J1.00 | 0.0 `--------` J1.00 | 3.3 `S-SS--S-` CHANGED | [0, 1, 2, 3, 4, 5, 6, 7, 8] | [0, 1, 2, 3, 4, 5, 6, 7] | -0.14/+0.02 | -0.59/+0.17 | +0.09 +0.41 +0.27 +0.37 +0.45 |  |
| C1_midval_k6 | 0.0 `--------` J1.00 | 0.0 `--------` J1.00 | 3.1 `S-SS--S-` CHANGED | [0, 1, 2, 3, 4, 5, 6, 7, 8] | [0, 1, 2, 3, 4, 5, 6, 7] | -0.22/+0.00 | -0.76/+0.33 | +0.09 +0.41 +0.27 +0.37 +0.45 |  |
| C2C3_f2000_floor0.03 | 4.8 `S-SSSSS-` J0.74 | 4.4 `S-SSS-S-` J0.68 | 6.5 `xxxxxxxx` ok | [0, 2, 5, 8] | [0, 1, 2, 3, 4, 5, 6, 7] | +0.07/+0.11 | +0.17/+0.17 | +0.00 +0.03 +0.08 -0.06 -0.03 |  |
| C2C3_f2000_floor0.04 | 4.8 `S-SSSSS-` J0.74 | 4.4 `S-SSS-S-` J0.68 | 6.5 `xxxxxxxx` ok | [0, 2, 5, 8] | [0, 1, 2, 3, 4, 5, 6, 7] | +0.07/+0.11 | +0.17/+0.17 | +0.00 +0.03 +0.08 -0.05 -0.03 |  |
| C2C3_f2000_floor0.05 | 4.8 `S-SSSSS-` J0.74 | 4.4 `S-SSS-S-` J0.68 | 6.4 `xxxxxxxS` ok | [0, 2, 5, 8] | [0, 1, 2, 4, 5, 6, 7] | +0.07/+0.11 | +0.17/+0.17 | +0.01 +0.03 +0.08 -0.03 -0.03 |  |
| C2C3_f3000_floor0.03 | 4.9 `S-SSSSS-` J0.74 | 4.8 `S-SSSSS-` J0.74 | 6.7 `xxxxxxxx` CHANGED | [0, 2, 5, 8] | [0, 1, 2, 3, 4, 5, 6, 7] | +0.07/+0.11 | +0.17/+0.21 | -0.03 -0.01 +0.11 -0.02 +0.01 |  |
| C2C3_f3000_floor0.04 | 4.9 `S-SSSSS-` J0.74 | 4.8 `S-SSSSS-` J0.74 | 6.7 `xxxxxxxx` CHANGED | [0, 2, 5, 8] | [0, 1, 2, 3, 4, 5, 6, 7] | +0.07/+0.11 | +0.17/+0.21 | -0.03 -0.01 +0.11 -0.01 +0.01 |  |
| C2C3_f3000_floor0.05 | 4.9 `S-SSSSS-` J0.74 | 4.8 `S-SSSSS-` J0.74 | 6.5 `xxxxxxxx` ok | [0, 2, 5, 8] | [0, 1, 2, 3, 4, 5, 6, 7] | +0.07/+0.11 | +0.17/+0.21 | -0.01 -0.00 +0.11 +0.00 +0.01 |  |
| C2_f1500_max | 7.8 `SSSSSSSS` J0.94 | 7.8 `SSSSSSSS` J0.96 | 8.0 `xxxxxxxx` CHANGED | [0, 1, 2, 3, 4, 5, 6, 7, 8] | [0, 1, 2, 3, 4, 5, 6, 7] | +0.21/+0.30 | +0.24/+0.50 | -0.44 -0.24 -0.22 -0.17 -0.19 |  |
| C2_f1500_mean | 4.2 `S-SSSSS-` J0.66 | 3.2 `S-S---S-` J0.57 | 6.0 `xxxxxxxx` ok | [0, 5, 8] | [0, 1, 2, 3, 5, 6, 7] | +0.03/+0.07 | +0.11/+0.13 | +0.03 +0.07 +0.07 -0.01 -0.01 |  |
| C2_f2000_max | 7.8 `SSSSSSSS` J0.94 | 7.9 `SSSSSSSS` J0.97 | 7.9 `xxxxxxxx` CHANGED | [0, 1, 2, 3, 4, 5, 6, 7, 8] | [0, 1, 2, 3, 4, 5, 6, 7] | +0.18/+0.30 | +0.24/+0.49 | -0.44 -0.23 -0.20 -0.18 -0.17 |  |
| C2_f2000_mean | 4.4 `S-SSSSS-` J0.70 | 3.4 `S-S-S-S-` J0.63 | 6.0 `Sxxxxxxx` ok | [0, 2, 5, 8] | [0, 1, 2, 3, 4, 5, 6, 7] | +0.06/+0.08 | +0.16/+0.14 | +0.03 +0.05 +0.09 -0.02 +0.01 |  |
| C2_f3000_max | 7.8 `SSSSSSSS` J0.96 | 7.8 `SSSSSSSS` J0.96 | 7.9 `xxxxxxxx` CHANGED | [0, 1, 2, 3, 4, 5, 6, 7] | [0, 1, 2, 3, 4, 5, 6, 7] | +0.18/+0.29 | +0.24/+0.50 | -0.41 -0.21 -0.20 -0.18 -0.15 |  |
| C2_f3000_mean | 4.9 `S-SSSSS-` J0.74 | 4.4 `S-S-SSS-` J0.73 | 6.1 `xxxxxxxx` ok | [0, 5, 8] | [0, 1, 2, 3, 4, 5, 6, 7] | +0.06/+0.08 | +0.16/+0.18 | +0.01 +0.02 +0.12 +0.01 +0.05 |  |
| C3_floor0.02 | 3.5 `S-SS-SS-` J0.56 | 1.8 `S-------` J0.53 | 6.7 `xxxSxxxx` CHANGED | [0, 5] | [1, 2, 3, 4, 5, 6, 7] | +0.04/+0.04 | +0.08/+0.07 | -0.03 -0.03 -0.00 -0.02 -0.04 |  |
| C3_floor0.03 | 3.5 `S-SS-SS-` J0.56 | 1.8 `S-------` J0.53 | 6.7 `xxxSxxxx` CHANGED | [0, 5] | [1, 2, 3, 4, 5, 6, 7] | +0.04/+0.04 | +0.08/+0.07 | -0.03 -0.03 -0.00 -0.02 -0.04 |  |
| C3_floor0.04 | 3.5 `S-SS-SS-` J0.56 | 1.8 `S-------` J0.53 | 6.7 `xxxSxxxx` CHANGED | [0, 5] | [1, 2, 3, 4, 5, 6, 7] | +0.04/+0.04 | +0.08/+0.07 | -0.03 -0.03 -0.00 -0.02 -0.04 |  |
| C3_floor0.05 | 3.5 `S-SS-SS-` J0.56 | 1.8 `S-------` J0.53 | 6.7 `xxxSxxxx` CHANGED | [0, 5] | [1, 2, 3, 4, 5, 6, 7] | +0.04/+0.04 | +0.08/+0.06 | -0.02 -0.03 -0.00 -0.01 -0.04 |  |
| G_f2000_g0.4_replace | 4.4 `S-SSSSS-` J0.70 | 3.4 `S-S-S-S-` J0.63 | 6.1 `xxxSxxxx` ok | ok | ok | +0.01/+0.03 | +0.11/+0.11 | +0.01 +0.03 +0.00 +0.00 -0.01 |  |
| G_f2000_g0.4_union | 4.5 `S-SSSSS-` J0.71 | 3.8 `S-S-S-S-` J0.64 | 6.1 `xxxSxxxx` ok | ok | ok | +0.01/+0.03 | +0.12/+0.11 | +0.00 +0.00 +0.00 +0.00 -0.02 |  |
| G_f2000_g0.5_replace | 4.4 `S-SSSSS-` J0.70 | 3.4 `S-S-S-S-` J0.64 | 6.1 `xxxSxxxx` ok | ok | ok | +0.02/+0.04 | +0.12/+0.12 | +0.01 +0.05 +0.00 +0.00 -0.00 |  |
| G_f2000_g0.5_union | 4.5 `S-SSSSS-` J0.71 | 3.8 `S-S-S-S-` J0.64 | 6.1 `xxxSxxxx` ok | ok | ok | +0.03/+0.04 | +0.14/+0.14 | +0.00 +0.01 +0.00 +0.00 -0.03 |  |
| G_f2500_g0.4_union | 4.7 `S-SSSSS-` J0.74 | 4.3 `S-SSS-S-` J0.71 | 6.1 `xxxSxxxx` ok | ok | ok | +0.01/+0.03 | +0.10/+0.10 | -0.00 +0.00 +0.00 +0.00 -0.02 | PASS |
| G_f3000_g0.4_replace | 4.9 `S-SSSSS-` J0.74 | 4.4 `S-S-SSS-` J0.73 | 6.1 `xxxSxxxx` ok | ok | ok | +0.02/+0.03 | +0.14/+0.15 | -0.00 +0.02 +0.00 +0.00 +0.02 | PASS |
| G_f3000_g0.4_union | 5.2 `S-SSSSS-` J0.78 | 4.6 `S-SSSSS-` J0.70 | 6.1 `xxxSxxxx` ok | ok | ok | +0.02/+0.04 | +0.11/+0.10 | -0.00 -0.01 +0.00 +0.00 -0.01 | PASS |
| G_f3000_g0.4_union_gain0.5 | 5.2 `S-SSSSS-` J0.78 | 4.6 `S-SSSSS-` J0.70 | 6.1 `xxxSxxxx` ok | ok | ok | +0.02/+0.04 | +0.11/+0.10 | -0.00 -0.01 +0.00 +0.00 -0.01 | PASS |
| G_f3000_g0.5_replace | 4.9 `S-SSSSS-` J0.74 | 4.4 `S-S-SSS-` J0.73 | 6.1 `xxxSxxxx` ok | ok | ok | +0.03/+0.06 | +0.16/+0.18 | -0.00 +0.02 +0.00 +0.00 +0.02 | PASS |
| G_f3000_g0.5_union | 5.2 `S-SSSSS-` J0.78 | 4.6 `S-SSSSS-` J0.70 | 6.1 `xxxSxxxx` ok | ok | ok | +0.05/+0.06 | +0.13/+0.14 | -0.01 -0.01 +0.00 +0.00 -0.01 | PASS |
| G_f4000_g0.4_union | 5.3 `S-SSSSS-` J0.80 | 4.8 `S-SSSSS-` J0.72 | 6.1 `xxxSxxxx` ok | ok | ok | +0.01/+0.03 | +0.12/+0.10 | -0.00 -0.00 +0.00 +0.00 -0.01 | PASS |
| U_today+C2_f2000 | 4.5 `S-SSSSS-` J0.71 | 3.8 `S-S-S-S-` J0.64 | 6.5 `xxxSxxxS` ok | [0, 2, 5] | [0, 1, 3, 5] | +0.05/+0.10 | +0.17/+0.16 | +0.00 +0.02 +0.01 -0.01 -0.00 |  |
| U_today+C2_f3000 | 5.2 `S-SSSSS-` J0.78 | 4.6 `S-SSSSS-` J0.70 | 6.6 `xxxSxxxx` ok | [0, 1, 2, 3, 4, 5, 6, 7] | [0, 1, 2, 3, 4, 5] | +0.06/+0.11 | +0.17/+0.20 | -0.01 -0.00 +0.04 +0.00 +0.01 |  |
| today | 2.9 `S-S--SS-` J0.46 | 1.8 `S-------` J0.53 | 6.1 `xxxSxxxx` ok | ok | ok | +0.00/+0.00 | +0.00/+0.00 | +0.00 +0.00 +0.00 +0.00 +0.00 |  |

## 4. Per-section tables (spike_recall/tables_per_section.md)

Every section of the five songs under today's detector and four candidates, the gated union (`G_f3000_g0.4_union`) among them. Patterns use `S` for a strike and `x` for a mute.

### S69
| sec | bars | label | cand | strikes/bar | pattern | explained | Jaccard | fit |
|---|---|---|---|---|---|---|---|---|
| 0 | 0-4 | verse 2 | today | 5.00 | `S-xx-xxx` | 0.90 | 0.65 | 0.86 |
| 0 | 0-4 | verse 2 | C2_f3000_mean | 4.75 | `S-xx-xxx` | 0.89 | 0.61 | 0.85 |
| 0 | 0-4 | verse 2 | C3_floor0.05 | 5.00 | `S-xx-xxx` | 0.90 | 0.65 | 0.86 |
| 0 | 0-4 | verse 2 | C1_midmax_k1.5 | 4.50 | `S-xS--xx` | 0.83 | 0.62 | 1.00 |
| 0 | 0-4 | verse 2 | G_f3000_g0.4_union | 5.00 | `S-xx-xxx` | 0.90 | 0.65 | 0.86 |
| 1 | 4-19 | verse | today | 6.13 | `xxxSxxxx` | 1.00 | 0.66 | 0.94 |
| 1 | 4-19 | verse | C2_f3000_mean | 6.07 | `xxxxxxxx` | 1.00 | 0.65 | 0.93 |
| 1 | 4-19 | verse | C3_floor0.05 | 6.67 | `xxxSxxxx` | 1.00 | 0.70 | 0.91 |
| 1 | 4-19 | verse | C1_midmax_k1.5 | 6.33 | `xxxSxxxx` | 1.00 | 0.67 | 1.00 |
| 1 | 4-19 | verse | G_f3000_g0.4_union | 6.13 | `xxxSxxxx` | 1.00 | 0.65 | 0.94 |
| 2 | 19-31 | chorus | today | 3.92 | `S-SS-SS-` | 0.87 | 0.62 | 0.92 |
| 2 | 19-31 | chorus | C2_f3000_mean | 5.17 | `S-SS-SS-` | 0.84 | 0.75 | 0.94 |
| 2 | 19-31 | chorus | C3_floor0.05 | 4.17 | `S-SS-SS-` | 0.88 | 0.67 | 0.91 |
| 2 | 19-31 | chorus | C1_midmax_k1.5 | 4.08 | `S-SS-SS-` | 0.88 | 0.65 | 1.00 |
| 2 | 19-31 | chorus | G_f3000_g0.4_union | 3.92 | `S-SS-SS-` | 0.87 | 0.62 | 0.92 |
| 3 | 31-41 | verse | today | 4.40 | `SSSSS-S-` | 0.93 | 0.61 | 0.98 |
| 3 | 31-41 | verse | C2_f3000_mean | 5.70 | `SSSSSSS-` | 0.98 | 0.72 | 0.98 |
| 3 | 31-41 | verse | C3_floor0.05 | 5.60 | `SSSSSSS-` | 0.95 | 0.70 | 0.95 |
| 3 | 31-41 | verse | C1_midmax_k1.5 | 4.80 | `SSSSSSS-` | 0.96 | 0.60 | 1.00 |
| 3 | 31-41 | verse | G_f3000_g0.4_union | 4.40 | `SSSSS-S-` | 0.93 | 0.62 | 0.98 |
| 4 | 41-53 | chorus | today | 2.92 | `S-S--SS-` | 0.77 | 0.46 | 0.97 |
| 4 | 41-53 | chorus | C2_f3000_mean | 4.92 | `S-SSSSS-` | 0.95 | 0.74 | 0.89 |
| 4 | 41-53 | chorus | C3_floor0.05 | 3.50 | `S-SS-SS-` | 0.88 | 0.56 | 0.93 |
| 4 | 41-53 | chorus | C1_midmax_k1.5 | 3.25 | `S-SS-SS-` | 0.90 | 0.54 | 1.00 |
| 4 | 41-53 | chorus | G_f3000_g0.4_union | 5.17 | `S-SSSSS-` | 0.95 | 0.78 | 0.91 |
| 5 | 53-58 | verse | today | 5.20 | `SS-SSSSS` | 0.96 | 0.69 | 0.96 |
| 5 | 53-58 | verse | C2_f3000_mean | 6.20 | `SSSSSSSS` | 1.00 | 0.78 | 1.00 |
| 5 | 53-58 | verse | C3_floor0.05 | 6.20 | `SSSSSSSS` | 1.00 | 0.78 | 0.88 |
| 5 | 53-58 | verse | C1_midmax_k1.5 | 5.40 | `SSSSSSSS` | 1.00 | 0.68 | 1.00 |
| 5 | 53-58 | verse | G_f3000_g0.4_union | 5.20 | `SS-SSSSS` | 0.96 | 0.69 | 0.96 |
| 6 | 58-69 | verse 2 | today | 3.55 | `S-SSS-SS` | 0.87 | 0.47 | 0.85 |
| 6 | 58-69 | verse 2 | C2_f3000_mean | 5.55 | `SSSSSSSS` | 1.00 | 0.69 | 0.87 |
| 6 | 58-69 | verse 2 | C3_floor0.05 | 3.55 | `S-SSS-SS` | 0.87 | 0.47 | 0.85 |
| 6 | 58-69 | verse 2 | C1_midmax_k1.5 | 3.00 | `S-SS--S-` | 0.73 | 0.45 | 1.00 |
| 6 | 58-69 | verse 2 | G_f3000_g0.4_union | 3.55 | `S-SSS-SS` | 0.87 | 0.47 | 0.85 |
| 7 | 69-83 | verse | today | 5.21 | `SSSSSSSS` | 1.00 | 0.65 | 0.91 |
| 7 | 69-83 | verse | C2_f3000_mean | 6.29 | `SSSSSSSS` | 1.00 | 0.79 | 0.90 |
| 7 | 69-83 | verse | C3_floor0.05 | 6.21 | `SSSSSSSS` | 1.00 | 0.78 | 0.87 |
| 7 | 69-83 | verse | C1_midmax_k1.5 | 4.93 | `SSSSSSSS` | 1.00 | 0.62 | 1.00 |
| 7 | 69-83 | verse | G_f3000_g0.4_union | 5.21 | `SSSSSSSS` | 1.00 | 0.65 | 0.91 |
| 8 | 83-95 | chorus | today | 1.83 | `S-------` | 0.45 | 0.53 | 0.87 |
| 8 | 83-95 | chorus | C2_f3000_mean | 4.42 | `S-S-SSS-` | 0.91 | 0.73 | 0.93 |
| 8 | 83-95 | chorus | C3_floor0.05 | 1.83 | `S-------` | 0.45 | 0.53 | 0.87 |
| 8 | 83-95 | chorus | C1_midmax_k1.5 | 1.75 | `S-------` | 0.43 | 0.44 | 1.00 |
| 8 | 83-95 | chorus | G_f3000_g0.4_union | 4.58 | `S-SSSSS-` | 0.96 | 0.70 | 0.91 |
| 9 | 95-111 | verse | today | 3.31 | `S--SS-S-` | 0.68 | 0.43 | 0.94 |
| 9 | 95-111 | verse | C2_f3000_mean | 5.06 | `S-SSSSS-` | 0.91 | 0.69 | 0.91 |
| 9 | 95-111 | verse | C3_floor0.05 | 3.31 | `S--SS-S-` | 0.68 | 0.43 | 0.94 |
| 9 | 95-111 | verse | C1_midmax_k1.5 | 3.25 | `S--SS-S-` | 0.67 | 0.41 | 1.00 |
| 9 | 95-111 | verse | G_f3000_g0.4_union | 3.31 | `S--SS-S-` | 0.68 | 0.43 | 0.94 |
| 10 | 111-121 | outro | today | 2.60 | `SS--x---` | 0.58 | 0.30 | 0.63 |
| 10 | 111-121 | outro | C2_f3000_mean | 1.30 | `----S---` | 0.31 | 0.20 | 0.77 |
| 10 | 111-121 | outro | C3_floor0.05 | 2.60 | `SS--x---` | 0.58 | 0.30 | 0.63 |
| 10 | 111-121 | outro | C1_midmax_k1.5 | 1.60 | `S--Sx---` | 0.81 | 0.33 | 1.00 |
| 10 | 111-121 | outro | G_f3000_g0.4_union | 2.60 | `SS--x---` | 0.58 | 0.30 | 0.63 |

### PSSOM
| sec | bars | label | cand | strikes/bar | pattern | explained | Jaccard | fit |
|---|---|---|---|---|---|---|---|---|
| 0 | 0-11 | intro | today | 7.73 | `SSSSSSSSSSS-S-SS` | 0.94 | 0.47 | 0.79 |
| 0 | 0-11 | intro | C2_f3000_mean | 8.91 | `SSSSSSSSSSSSSSSS` | 1.00 | 0.52 | 0.68 |
| 0 | 0-11 | intro | C3_floor0.05 | 9.73 | `SSSSSSSSSSSSSSSS` | 1.00 | 0.57 | 0.67 |
| 0 | 0-11 | intro | C1_midmax_k1.5 | 8.18 | `SxSSSSSSSSS-SS-S` | 0.93 | 0.49 | 1.00 |
| 0 | 0-11 | intro | G_f3000_g0.4_union | 7.73 | `SSSSSSSSSSS-S-SS` | 0.94 | 0.45 | 0.79 |
| 1 | 11-28 | verse | today | 4.82 | `S-S--SSS----SS--` | 0.67 | 0.37 | 0.39 |
| 1 | 11-28 | verse | C2_f3000_mean | 6.88 | `SSS-SSSS----SS-S` | 0.83 | 0.49 | 0.54 |
| 1 | 11-28 | verse | C3_floor0.05 | 4.82 | `S-S--SSS----SS--` | 0.67 | 0.37 | 0.39 |
| 1 | 11-28 | verse | C1_midmax_k1.5 | 2.82 | `S----S-S--------` | 0.50 | 0.33 | 1.00 |
| 1 | 11-28 | verse | G_f3000_g0.4_union | 4.82 | `S-S--SSS----SS--` | 0.67 | 0.37 | 0.39 |
| 2 | 28-39 | chorus | today | 5.82 | `S--SS-S-S-S-SS-S` | 0.81 | 0.45 | 0.62 |
| 2 | 28-39 | chorus | C2_f3000_mean | 8.27 | `SSSSSS--S-S-S-SS` | 0.92 | 0.64 | 0.73 |
| 2 | 28-39 | chorus | C3_floor0.05 | 6.82 | `S--SSSS-S-S-SS-S` | 0.84 | 0.49 | 0.56 |
| 2 | 28-39 | chorus | C1_midmax_k1.5 | 3.82 | `S--S----S---S--S` | 0.69 | 0.41 | 1.00 |
| 2 | 28-39 | chorus | G_f3000_g0.4_union | 9.27 | `SSSSSSS-S-S-SSSS` | 0.94 | 0.62 | 0.63 |
| 3 | 39-55 | verse | today | 7.44 | `SS--SxSS-SSSSS-S` | 0.87 | 0.47 | 0.56 |
| 3 | 39-55 | verse | C2_f3000_mean | 10.00 | `SSS-SxSS-SSSSSSS` | 0.94 | 0.59 | 0.65 |
| 3 | 39-55 | verse | C3_floor0.05 | 7.44 | `SS--SxSS-SSSSS-S` | 0.87 | 0.47 | 0.56 |
| 3 | 39-55 | verse | C1_midmax_k1.5 | 5.00 | `S---S--S-S-S-S-S` | 0.68 | 0.35 | 1.00 |
| 3 | 39-55 | verse | G_f3000_g0.4_union | 7.44 | `SS--SxSS-SSSSS-S` | 0.87 | 0.46 | 0.56 |
| 4 | 55-67 | chorus | today | 4.17 | `----S---S-S-S---` | 0.48 | 0.31 | 0.76 |
| 4 | 55-67 | chorus | C2_f3000_mean | 8.25 | `S-SSS-S-S-S-S-SS` | 0.86 | 0.61 | 0.64 |
| 4 | 55-67 | chorus | C3_floor0.05 | 7.67 | `S--SS-SSS-S-SSSS` | 0.84 | 0.52 | 0.62 |
| 4 | 55-67 | chorus | C1_midmax_k1.5 | 3.17 | `S---S---S---S---` | 0.58 | 0.35 | 1.00 |
| 4 | 55-67 | chorus | G_f3000_g0.4_union | 8.83 | `S-SSS-SSS-S-S-SS` | 0.87 | 0.61 | 0.63 |
| 5 | 67-84 | verse | today | 5.76 | `SS-SxSSS-S-SSSSS` | 0.89 | 0.35 | 0.54 |
| 5 | 67-84 | verse | C2_f3000_mean | 9.35 | `SSSSSSSS-SSSSSSS` | 0.97 | 0.56 | 0.57 |
| 5 | 67-84 | verse | C3_floor0.05 | 5.76 | `SS-SxSSS-S-SSSSS` | 0.89 | 0.35 | 0.54 |
| 5 | 67-84 | verse | C1_midmax_k1.5 | 4.06 | `-S----------S--S` | 0.28 | 0.21 | 1.00 |
| 5 | 67-84 | verse | G_f3000_g0.4_union | 5.76 | `SS-SxSSS-S-SSSSS` | 0.89 | 0.35 | 0.54 |
| 6 | 84-103 | chorus | today | 3.42 | `S---S---S---S--S` | 0.65 | 0.36 | 0.63 |
| 6 | 84-103 | chorus | C2_f3000_mean | 9.26 | `S-SSS-SSS-SSSS-S` | 0.88 | 0.61 | 0.57 |
| 6 | 84-103 | chorus | C3_floor0.05 | 5.11 | `S---S--SS-S-S--S` | 0.73 | 0.45 | 0.57 |
| 6 | 84-103 | chorus | C1_midmax_k1.5 | 1.68 | `--------S---S---` | 0.53 | 0.31 | 1.00 |
| 6 | 84-103 | chorus | G_f3000_g0.4_union | 9.47 | `S-SSS-SSS-SSSSSS` | 0.92 | 0.61 | 0.57 |

### Chelsea
| sec | bars | label | cand | strikes/bar | pattern | explained | Jaccard | fit |
|---|---|---|---|---|---|---|---|---|
| 0 | 0-9 | verse | today | 2.00 | `S-------` | 0.17 | 0.19 | 0.27 |
| 0 | 0-9 | verse | C2_f3000_mean | 1.22 | `S-------` | 0.18 | 0.12 | 0.43 |
| 0 | 0-9 | verse | C3_floor0.05 | 2.00 | `S-------` | 0.17 | 0.19 | 0.27 |
| 0 | 0-9 | verse | C1_midmax_k1.5 | 1.33 | `S-------` | 0.33 | 0.24 | 1.00 |
| 0 | 0-9 | verse | G_f3000_g0.4_union | 2.00 | `S-------` | 0.17 | 0.19 | 0.30 |
| 1 | 9-38 | chorus | today | 2.76 | `S-S-S-S-` | 0.85 | 0.48 | 0.52 |
| 1 | 9-38 | chorus | C2_f3000_mean | 4.24 | `S-S-S-SS` | 0.89 | 0.61 | 0.64 |
| 1 | 9-38 | chorus | C3_floor0.05 | 2.76 | `S-S-S-S-` | 0.85 | 0.47 | 0.52 |
| 1 | 9-38 | chorus | C1_midmax_k1.5 | 2.45 | `S-S-S-S-` | 0.97 | 0.51 | 1.00 |
| 1 | 9-38 | chorus | G_f3000_g0.4_union | 4.38 | `S-S-S-SS` | 0.88 | 0.63 | 0.53 |
| 2 | 38-61 | verse | today | 3.91 | `S-SSSSSS` | 0.98 | 0.50 | 0.57 |
| 2 | 38-61 | verse | C2_f3000_mean | 4.52 | `S-SSSSSS` | 0.98 | 0.57 | 0.66 |
| 2 | 38-61 | verse | C3_floor0.05 | 4.83 | `S-SSSSSS` | 0.98 | 0.63 | 0.51 |
| 2 | 38-61 | verse | C1_midmax_k1.5 | 3.09 | `S-S-S-S-` | 0.87 | 0.59 | 1.00 |
| 2 | 38-61 | verse | G_f3000_g0.4_union | 3.91 | `S-SSSSSS` | 0.98 | 0.50 | 0.57 |
| 3 | 61-71 | chorus | today | 3.20 | `S-S-S-S-` | 0.84 | 0.60 | 0.53 |
| 3 | 61-71 | chorus | C2_f3000_mean | 4.70 | `S-S-SSSS` | 0.89 | 0.66 | 0.57 |
| 3 | 61-71 | chorus | C3_floor0.05 | 3.80 | `S-S-S-SS` | 0.89 | 0.63 | 0.52 |
| 3 | 61-71 | chorus | C1_midmax_k1.5 | 2.10 | `S-S---S-` | 0.90 | 0.61 | 1.00 |
| 3 | 61-71 | chorus | G_f3000_g0.4_union | 3.20 | `S-S-S-S-` | 0.84 | 0.60 | 0.53 |
| 4 | 71-93 | verse | today | 3.68 | `S-S-S-S-` | 0.75 | 0.55 | 0.56 |
| 4 | 71-93 | verse | C2_f3000_mean | 4.36 | `S-SSSSS-` | 0.90 | 0.57 | 0.64 |
| 4 | 71-93 | verse | C3_floor0.05 | 4.55 | `S-SSSSSS` | 0.97 | 0.58 | 0.52 |
| 4 | 71-93 | verse | C1_midmax_k1.5 | 2.82 | `S-S-S-S-` | 0.85 | 0.52 | 1.00 |
| 4 | 71-93 | verse | G_f3000_g0.4_union | 3.68 | `S-S-S-S-` | 0.75 | 0.54 | 0.56 |
| 5 | 93-99 | chorus | today | 5.00 | `S-SSS-SS` | 0.93 | 0.74 | 0.41 |
| 5 | 93-99 | chorus | C2_f3000_mean | 6.67 | `S-SSSSSS` | 0.97 | 0.88 | 0.44 |
| 5 | 93-99 | chorus | C3_floor0.05 | 5.00 | `S-SSS-SS` | 0.93 | 0.72 | 0.41 |
| 5 | 93-99 | chorus | C1_midmax_k1.5 | 2.00 | `--S---S-` | 0.92 | 0.89 | 1.00 |
| 5 | 93-99 | chorus | G_f3000_g0.4_union | 5.00 | `S-SSS-SS` | 0.93 | 0.72 | 0.41 |
| 6 | 99-105 | bridge | today | 3.83 | `--SSS-SS` | 0.87 | 0.62 | 0.52 |
| 6 | 99-105 | bridge | C2_f3000_mean | 5.33 | `S-SSS-SS` | 0.94 | 0.79 | 0.51 |
| 6 | 99-105 | bridge | C3_floor0.05 | 3.83 | `--SSS-SS` | 0.87 | 0.62 | 0.52 |
| 6 | 99-105 | bridge | C1_midmax_k1.5 | 2.33 | `--S---S-` | 0.71 | 0.67 | 1.00 |
| 6 | 99-105 | bridge | G_f3000_g0.4_union | 3.83 | `--SSS-SS` | 0.87 | 0.62 | 0.52 |
| 7 | 105-142 | chorus | today | 2.59 | `S-S-S-S-` | 0.88 | 0.52 | 0.66 |
| 7 | 105-142 | chorus | C2_f3000_mean | 4.84 | `S-SSSSSS` | 0.98 | 0.66 | 0.59 |
| 7 | 105-142 | chorus | C3_floor0.05 | 4.24 | `S-SSS-SS` | 0.94 | 0.64 | 0.52 |
| 7 | 105-142 | chorus | C1_midmax_k1.5 | 2.11 | `S-S---S-` | 0.78 | 0.47 | 1.00 |
| 7 | 105-142 | chorus | G_f3000_g0.4_union | 5.00 | `S-SSSSSS` | 0.98 | 0.69 | 0.57 |

### WetLeg
| sec | bars | label | cand | strikes/bar | pattern | explained | Jaccard | fit |
|---|---|---|---|---|---|---|---|---|
| 0 | 0-5 | verse 2 | today | 5.60 | `S-xSSxS-` | 0.93 | 0.68 | 0.87 |
| 0 | 0-5 | verse 2 | C2_f3000_mean | 6.40 | `SSSxSxSx` | 1.00 | 0.68 | 0.88 |
| 0 | 0-5 | verse 2 | C3_floor0.05 | 6.40 | `SSxSSxSx` | 1.00 | 0.68 | 0.74 |
| 0 | 0-5 | verse 2 | C1_midmax_k1.5 | 5.20 | `S-xSSxS-` | 0.96 | 0.70 | 1.00 |
| 0 | 0-5 | verse 2 | G_f3000_g0.4_union | 5.60 | `S-xSSxS-` | 0.93 | 0.68 | 0.87 |
| 1 | 5-18 | chorus | today | 6.92 | `SSSSSSSS` | 1.00 | 0.84 | 0.73 |
| 1 | 5-18 | chorus | C2_f3000_mean | 7.23 | `SSSSSSSS` | 1.00 | 0.86 | 0.86 |
| 1 | 5-18 | chorus | C3_floor0.05 | 6.92 | `SSSSSSSS` | 1.00 | 0.84 | 0.73 |
| 1 | 5-18 | chorus | C1_midmax_k1.5 | 6.15 | `SSSSSSSS` | 1.00 | 0.74 | 1.00 |
| 1 | 5-18 | chorus | G_f3000_g0.4_union | 6.92 | `SSSSSSSS` | 1.00 | 0.84 | 0.73 |
| 2 | 18-33 | verse | today | 3.47 | `S-S-S-SS` | 0.79 | 0.46 | 0.72 |
| 2 | 18-33 | verse | C2_f3000_mean | 3.00 | `S-S-S-SS` | 0.82 | 0.41 | 0.89 |
| 2 | 18-33 | verse | C3_floor0.05 | 3.47 | `S-S-S-SS` | 0.79 | 0.46 | 0.72 |
| 2 | 18-33 | verse | C1_midmax_k1.5 | 4.93 | `S-S-SSSS` | 0.88 | 0.66 | 1.00 |
| 2 | 18-33 | verse | G_f3000_g0.4_union | 3.47 | `S-S-S-SS` | 0.79 | 0.46 | 0.72 |
| 3 | 33-42 | chorus | today | 6.56 | `SSSSSxSS` | 1.00 | 0.69 | 0.75 |
| 3 | 33-42 | chorus | C2_f3000_mean | 6.78 | `SSSxxxSS` | 1.00 | 0.71 | 0.87 |
| 3 | 33-42 | chorus | C3_floor0.05 | 6.56 | `SSSSSxSS` | 1.00 | 0.69 | 0.75 |
| 3 | 33-42 | chorus | C1_midmax_k1.5 | 6.44 | `SxxSSSxS` | 1.00 | 0.65 | 1.00 |
| 3 | 33-42 | chorus | G_f3000_g0.4_union | 6.56 | `SSSSSxSS` | 1.00 | 0.69 | 0.75 |
| 4 | 42-58 | verse | today | 6.62 | `SSSSSSSS` | 1.00 | 0.80 | 0.82 |
| 4 | 42-58 | verse | C2_f3000_mean | 7.12 | `SSSSSSSS` | 1.00 | 0.86 | 0.94 |
| 4 | 42-58 | verse | C3_floor0.05 | 6.62 | `SSSSSSSS` | 1.00 | 0.80 | 0.82 |
| 4 | 42-58 | verse | C1_midmax_k1.5 | 7.00 | `SSSSSSSS` | 1.00 | 0.84 | 1.00 |
| 4 | 42-58 | verse | G_f3000_g0.4_union | 6.62 | `SSSSSSSS` | 1.00 | 0.80 | 0.82 |
| 5 | 58-65 | verse 2 | today | 4.71 | `S-SS-SSS` | 0.91 | 0.64 | 0.74 |
| 5 | 58-65 | verse 2 | C2_f3000_mean | 5.57 | `S-SSSSSS` | 0.95 | 0.70 | 0.91 |
| 5 | 58-65 | verse 2 | C3_floor0.05 | 6.14 | `SSSSSSSS` | 1.00 | 0.72 | 0.78 |
| 5 | 58-65 | verse 2 | C1_midmax_k1.5 | 5.86 | `SSSSSSSS` | 1.00 | 0.67 | 1.00 |
| 5 | 58-65 | verse 2 | G_f3000_g0.4_union | 4.71 | `S-SS-SSS` | 0.91 | 0.64 | 0.74 |
| 6 | 65-100 | bridge | today | 6.69 | `SSSSxxSS` | 1.00 | 0.73 | 0.69 |
| 6 | 65-100 | bridge | C2_f3000_mean | 6.91 | `SSSSSSSS` | 1.00 | 0.75 | 0.78 |
| 6 | 65-100 | bridge | C3_floor0.05 | 6.69 | `SSSSxxSS` | 1.00 | 0.73 | 0.69 |
| 6 | 65-100 | bridge | C1_midmax_k1.5 | 6.74 | `SSSSxxSS` | 1.00 | 0.71 | 1.00 |
| 6 | 65-100 | bridge | G_f3000_g0.4_union | 6.69 | `SSSSxxSS` | 1.00 | 0.73 | 0.69 |
| 7 | 100-108 | chorus | today | 6.50 | `SSSSSSSS` | 1.00 | 0.79 | 0.89 |
| 7 | 100-108 | chorus | C2_f3000_mean | 6.88 | `SSSSSSSS` | 1.00 | 0.83 | 0.87 |
| 7 | 100-108 | chorus | C3_floor0.05 | 7.00 | `SSSSSSSS` | 1.00 | 0.84 | 0.89 |
| 7 | 100-108 | chorus | C1_midmax_k1.5 | 6.38 | `SSSSSSSS` | 1.00 | 0.77 | 1.00 |
| 7 | 100-108 | chorus | G_f3000_g0.4_union | 6.50 | `SSSSSSSS` | 1.00 | 0.79 | 0.89 |
| 8 | 108-113 | outro | today | 3.80 | `SSSSSSSS` | 1.00 | 0.47 | 0.28 |
| 8 | 108-113 | outro | C2_f3000_mean | 1.40 | `-S-----S` | 0.57 | 0.32 | 0.38 |
| 8 | 108-113 | outro | C3_floor0.05 | 3.80 | `SSSSSSSS` | 1.00 | 0.47 | 0.28 |
| 8 | 108-113 | outro | C1_midmax_k1.5 | 1.60 | `-S-----S` | 0.62 | 0.42 | 1.00 |
| 8 | 108-113 | outro | G_f3000_g0.4_union | 3.80 | `SSSSSSSS` | 1.00 | 0.47 | 0.28 |

### Fame
| sec | bars | label | cand | strikes/bar | pattern | explained | Jaccard | fit |
|---|---|---|---|---|---|---|---|---|
| 0 | 0-5 | intro | today | 2.80 | `S-S-S---S-----S-` | 0.71 | 0.31 | 0.38 |
| 0 | 0-5 | intro | C2_f3000_mean | 4.60 | `S-S-S--SS---S-S-` | 0.83 | 0.42 | 0.43 |
| 0 | 0-5 | intro | C3_floor0.05 | 2.80 | `S-S-S---S-----S-` | 0.71 | 0.31 | 0.38 |
| 0 | 0-5 | intro | C1_midmax_k1.5 | 2.40 | `--S-----S-----S-` | 0.58 | 0.32 | 1.00 |
| 0 | 0-5 | intro | G_f3000_g0.4_union | 2.80 | `S-S-S---S-----S-` | 0.71 | 0.31 | 0.38 |
| 1 | 5-10 | verse 2 | today | 9.40 | `xSS-S-S-S-SSSSS-` | 0.89 | 0.68 | 0.64 |
| 1 | 5-10 | verse 2 | C2_f3000_mean | 8.60 | `SS--S-S-S-SSS-S-` | 0.86 | 0.71 | 0.57 |
| 1 | 5-10 | verse 2 | C3_floor0.05 | 10.60 | `SSS-SSS-S-SSSSS-` | 0.92 | 0.75 | 0.63 |
| 1 | 5-10 | verse 2 | C1_midmax_k1.5 | 8.60 | `S-S-S-S-S-SSSSS-` | 0.91 | 0.70 | 1.00 |
| 1 | 5-10 | verse 2 | G_f3000_g0.4_union | 9.40 | `xSS-S-S-S-SSSSS-` | 0.89 | 0.68 | 0.64 |
| 2 | 10-19 | chorus | today | 9.78 | `--S-S-S-SSSSS-S-` | 0.84 | 0.76 | 0.67 |
| 2 | 10-19 | chorus | C2_f3000_mean | 8.56 | `--S-S-S-SSSSS-S-` | 0.84 | 0.70 | 0.67 |
| 2 | 10-19 | chorus | C3_floor0.05 | 10.44 | `S-S-SSS-SSSSSSS-` | 0.91 | 0.71 | 0.68 |
| 2 | 10-19 | chorus | C1_midmax_k1.5 | 8.89 | `-SS-S-S-S-SSS-S-` | 0.86 | 0.72 | 1.00 |
| 2 | 10-19 | chorus | G_f3000_g0.4_union | 9.78 | `--S-S-S-SSSSS-S-` | 0.84 | 0.76 | 0.67 |
| 3 | 19-53 | verse | today | 8.88 | `SS--SSx-S-SSSSS-` | 0.90 | 0.62 | 0.59 |
| 3 | 19-53 | verse | C2_f3000_mean | 7.47 | `SS--xS--S-SSSSS-` | 0.93 | 0.59 | 0.63 |
| 3 | 19-53 | verse | C3_floor0.05 | 9.47 | `SSS-SSx-SSSSSSS-` | 0.96 | 0.62 | 0.58 |
| 3 | 19-53 | verse | C1_midmax_k1.5 | 6.68 | `S---SSx-S-SSS-S-` | 0.88 | 0.55 | 1.00 |
| 3 | 19-53 | verse | G_f3000_g0.4_union | 8.88 | `SS--SSx-S-SSSSS-` | 0.90 | 0.62 | 0.59 |
| 4 | 53-61 | verse 2 | today | 7.38 | `S-SSS-S-S-S-S-S-` | 0.86 | 0.64 | 0.59 |
| 4 | 53-61 | verse 2 | C2_f3000_mean | 6.25 | `S-S-S-S-S---S-S-` | 0.80 | 0.57 | 0.59 |
| 4 | 53-61 | verse 2 | C3_floor0.05 | 8.75 | `S-SSSSS-SSS-S-S-` | 0.90 | 0.64 | 0.59 |
| 4 | 53-61 | verse 2 | C1_midmax_k1.5 | 5.62 | `S-S-S-S-S-S-S-S-` | 0.87 | 0.51 | 1.00 |
| 4 | 53-61 | verse 2 | G_f3000_g0.4_union | 7.38 | `S-SSS-S-S-S-S-S-` | 0.86 | 0.64 | 0.59 |
| 5 | 61-71 | chorus | today | 10.20 | `SSSSSSS---S-SSS-` | 0.89 | 0.72 | 0.72 |
| 5 | 61-71 | chorus | C2_f3000_mean | 7.90 | `SSSSS-S---S-S-S-` | 0.85 | 0.65 | 0.70 |
| 5 | 61-71 | chorus | C3_floor0.05 | 11.20 | `SSSSSSS-SSS-SSSS` | 0.96 | 0.72 | 0.65 |
| 5 | 61-71 | chorus | C1_midmax_k1.5 | 9.20 | `S-SSS-S---S-S-S-` | 0.83 | 0.75 | 1.00 |
| 5 | 61-71 | chorus | G_f3000_g0.4_union | 10.20 | `SSSSSSS---S-SSS-` | 0.89 | 0.72 | 0.72 |
| 6 | 71-82 | bridge | today | 10.73 | `S-SSSSS-SSS-SSSx` | 0.94 | 0.67 | 0.71 |
| 6 | 71-82 | bridge | C2_f3000_mean | 8.27 | `S-xSSSS--SS-SSS-` | 0.92 | 0.61 | 0.69 |
| 6 | 71-82 | bridge | C3_floor0.05 | 11.55 | `SxSSxSS-SSSSSSSx` | 0.98 | 0.67 | 0.70 |
| 6 | 71-82 | bridge | C1_midmax_k1.5 | 9.73 | `S-xSSSS-xSSSSSS-` | 0.93 | 0.58 | 1.00 |
| 6 | 71-82 | bridge | G_f3000_g0.4_union | 10.73 | `S-SSSSS-SSS-SSSx` | 0.94 | 0.67 | 0.71 |
| 7 | 82-101 | verse | today | 9.21 | `S-SSS-S--SS-SSx-` | 0.91 | 0.72 | 0.58 |
| 7 | 82-101 | verse | C2_f3000_mean | 7.26 | `S-xSS-S--S--SS--` | 0.90 | 0.69 | 0.66 |
| 7 | 82-101 | verse | C3_floor0.05 | 9.79 | `S-SSSSS--SS-SSx-` | 0.91 | 0.70 | 0.58 |
| 7 | 82-101 | verse | C1_midmax_k1.5 | 7.63 | `S-SSS-S--SS-SSx-` | 0.88 | 0.55 | 1.00 |
| 7 | 82-101 | verse | G_f3000_g0.4_union | 9.21 | `S-SSS-S--SS-SSx-` | 0.91 | 0.72 | 0.58 |

## 5. Gate constants and regularity guards (spike_recall2/REPORT.md)

Measured on the union the gate produces for each tried section. `EXPLAINED_KEEP` was a candidate guard on the union's `explained`; it was dropped because it does not separate (5.1), as were the variability and gain guards (5.3); the eighth-note restriction replaced them.

Scripts: `measure.py` (union trial per tried section, per-bar RMS), `an.py` (tables), `excl.py` (re-vote with silent bars dropped). Data: `measure.json`. Config `G_f3000_g0.4_union`, trial union built per tried section against today's onsets (same construction as gated.py; sections are independent). Vote = > 1/3 of bars plus floor round(0.6 x median strikes/bar). Section grid fit is the union's own section fit (song-level today fit in brackets).

### 5.1 Tried sections (today spb < 0.4 x slots)

| class | song | bars | slots | today spb | union spb (share of slots) | today expl | UNION expl | union Jaccard | union raw/bar | union sec fit (today song fit) | union pattern |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ACC | S69 | 41-53 | 8 | 2.92 | 5.17 (0.65) | 0.771 | 0.952 | 0.778 | 5.4 | 0.91 (0.91) | S-SSSSS- |
| ACC | S69 | 83-95 | 8 | 1.83 | 4.58 (0.57) | 0.455 | 0.964 | 0.704 | 4.8 | 0.91 (0.91) | S-SSSSS- |
| ACC | Chelsea | 9-38 | 8 | 2.76 | 4.38 (0.55) | 0.850 | 0.882 | 0.637 | 5.2 | 0.53 (0.55) | S-S-S-SS |
| ACC | Chelsea | 105-142 | 8 | 2.59 | 5.00 (0.62) | 0.875 | 0.978 | 0.685 | 5.4 | 0.57 (0.55) | S-SSSSSS |
| REJ | PSSOM | 28-39 | 16 | 5.82 | 9.27 (0.58) | 0.812 | 0.941 | 0.622 | 10.9 | 0.63 (0.59) | SSSSSSS-S-S-SSSS |
| REJ | PSSOM | 55-67 | 16 | 4.17 | 8.83 (0.55) | 0.480 | 0.868 | 0.606 | 10.2 | 0.63 (0.59) | S-SSS-SSS-S-S-SS |
| REJ | PSSOM | 84-103 | 16 | 3.42 | 9.47 (0.59) | 0.646 | 0.917 | 0.613 | 11.3 | 0.57 (0.59) | S-SSS-SSS-SSSSSS |
| other (unlisted, must stay unchanged) | S69 | 111-121 | 8 | 2.60 | 2.90 (0.36) | 0.577 | 0.690 | 0.350 | 3.1 | 0.65 (0.91) | SSx-x--- |
| other | PSSOM | 11-28 | 16 | 4.82 | 7.71 (0.48) | 0.671 | 0.893 | 0.518 | 9.6 | 0.45 (0.59) | SSS-SSSSSS--SS-S |
| other | PSSOM | 67-84 | 16 | 5.76 | 9.71 (0.61) | 0.888 | 0.970 | 0.578 | 12.1 | 0.52 (0.59) | SSSSxSSS-SSSSSSS |
| other | Fame | 0-5 | 16 | 2.80 | 4.40 (0.28) | 0.714 | 0.773 | 0.444 | 5.6 | 0.46 (0.63) | S-S-S---S---S-S- |
| other | Chelsea | 0-9 | 8 | 2.00 | 2.11 (0.26) | 0.167 | 0.158 | 0.183 | 2.7 | 0.29 (0.55) | S------- |

Wet Leg: no section is tried. In the old run, the old gate accepted all ACC and all REJ rows, plus nothing among "other".

#### EXPLAINED_KEEP
- Lowest union `explained` among accepted: 0.882 (Chelsea 9-38). Highest among rejected: 0.941 (PSSOM 28-39).
- The ranges overlap (accepted 0.882-0.978, rejected 0.868-0.941; S69 41-53 0.952 and Chelsea 9-38 0.882 straddle PSSOM 0.941). NO threshold on union `explained` separates them. Including the unlisted "other" sections (0.158-0.970) makes it worse (PSSOM 67-84 = 0.970).
- Re-voting with silent bars dropped (0.25) does not help: Chelsea 9-38 0.878, PSSOM 55-67 0.943, PSSOM 11-28 0.886.
- Other measured quantities:
  - Union Jaccard (as produced, no bar exclusion) separates: accepted min 0.637 (Chelsea 9-38), every non-accepted section max 0.622 (PSSOM 28-39). Midpoint 0.63, margin only +/-0.008. Fragile: with silent bars dropped Chelsea 9-38 goes to 0.707 but PSSOM 67-84 goes to 0.750 and PSSOM 55-67 to 0.646, so it would no longer separate.
  - Union spb as share of slots: no (accepted 0.55-0.65, rejected 0.55-0.59).
  - Raw onsets per bar as a share of slots: no (accepted 0.60-0.68, rejected 0.64-0.71).
  - Union section fit: no (accepted 0.53-0.91, rejected 0.57-0.63).
  - Gain in explained / Jaccard / spb ratio: no (all overlap).
  - Absolute union strikes per bar and absolute raw onsets per bar separate (accepted spb <= 5.17, raw <= 5.4; rejected spb >= 8.83, raw >= 10.2), but only because PSSOM runs 16 slots per bar vs 8 for every accepted song; it is a slots-per-bar effect, not a quality measure (Fame is also 16 slots and its tried section is rejected by spb share 0.28).
- Conclusion: `explained` alone cannot separate; a floor of 0.85 would drop only the sections that are not wanted anyway (S69 outro 0.69, Chelsea intro 0.16, Fame intro 0.77) but keeps all three PSSOM rejects (0.868-0.941). PSSOM needs Jaccard (thin margin) or a slots-aware criterion.

### 5.2 Per-bar RMS share (guitar stem, share of section median bar RMS), bars < 0.5

Bar numbers are the grid bar indices (section bars are start..end-1). strikes = union strikes in that bar.

| section | median RMS | bars < 0.5 : (bar, share, strikes) | lowest-share struck bar |
|---|---|---|---|
| S69 41-53 (ACC) | 0.0747 | none | bar 48, 0.784 |
| S69 83-95 (ACC) | 0.0750 | none | bar 90, 0.684 |
| Chelsea 9-38 (ACC) | 0.0428 | 9: 0.1353 (1); 10: 0.0003 (0); 11: 0.0003 (1); 12: 0.133 (2); 13: 0.485 (5); 15: 0.449 (4); 17: 0.446 (4) | bar 11, 0.0003 (1 spurious strike); excluding 9-12: bar 17, 0.446 |
| Chelsea 105-142 (ACC) | 0.0505 | none | bar 105, 0.526 |
| S69 111-121 | 0.0597 | 118: 0.348 (2); 119: 0.311 (4); 120: 0.011 (4) | bar 120, 0.011 |
| PSSOM 11-28 | 0.0192 | 15: 0.114 (4); 16: 0.025 (2); 17: 0.001 (0); 18: 0.110 (2) | bar 16, 0.025 |
| PSSOM 28-39 (REJ) | 0.0217 | 38: 0.289 (10) | bar 38, 0.289 |
| PSSOM 55-67 (REJ) | 0.0260 | 66: 0.002 (1) | bar 66, 0.002 |
| PSSOM 67-84 | 0.0222 | 67: 0.225; 68: 0.328; 77: 0.095; 78: 0.001 (0); 79: 0.000 (0); 80: 0.210 | bar 77, 0.095 |
| PSSOM 84-103 (REJ) | 0.0248 | none | bar 97, 0.843 |
| Fame 0-5 | 0.0774 | 0: 0.080 (0) | bar 1, 0.511 |
| Chelsea 0-9 | 0.0035 | 0: 0.084 (2); 1: 0.096 (2); 2: 0.073 (2); 6: 0.212 (0) | bar 2, 0.073 |

Chelsea bars 9, 10, 11 shares: 0.1353, 0.0003, 0.0003 (bar 12 is 0.133, even lower than bar 9, so any threshold excluding bar 9 also excludes bar 12, which carries 2 strikes; bars 9, 11 and 12 are the guitar fading/entering).

#### SILENT_BAR_SHARE
- Lower bound (must exclude bars 9-11): threshold > 0.1353.
- Upper bound (must exclude no struck bar of an accepted section other than the entry bars 9-12): threshold <= 0.446 (Chelsea bar 17; next 0.449, 0.485, S69 0.684, Chelsea 105-142 0.526). Strictly "no struck bar at all" in the accepted sections has no solution, because bar 9 (0.1353) and bar 11 (0.0003) carry spurious strikes and bar 12 (0.133) is unavoidable once bar 9 is excluded.
- Largest value meeting the criterion (bars 9-12 excluded, nothing else): just under 0.446.
- Recommended with margin on both sides: **0.25** (0.115 above bar 9's 0.1353, 0.196 below bar 17's 0.446; any value 0.15 to 0.40 gives the identical result).
- Effect on accepted patterns, vote re-run with bars below the share dropped (per-threshold patterns in measure.json):
  - S69 41-53 and 83-95: unchanged at every threshold 0.0-0.5 (`S-SSSSS-`).
  - Chelsea 105-142: unchanged (`S-SSSSSS`).
  - Chelsea 9-38: unchanged for thresholds 0.1-0.4 (`S-S-S-SS`, 4 bars dropped at 0.25); changes at 0.5 (`S-S-SSSS`) because bars 13, 15, 17 are also dropped. So 0.25 changes no accepted pattern; 0.5 would change one.
  - Side effects at 0.25 on non-accepted sections: Chelsea 0-9 pattern `S-------` -> `S-SS-SS-` at >= 0.3 (not at 0.25); S69 outro `SSx-x---` -> `x---x---` at 0.1-0.3 (it is rejected anyway).

### 5.3 Added guards: raw-onset variability and gain ratio (`var.py`, `var.txt`)

Union = same trial union as above. Count = union onsets per bar (bar start inclusive to end), CV = std/mean of the per-bar count, dev25 = share of bars whose count differs from the section median by more than 25 percent, gain = union spb / today spb. Wet Leg and Fame rows use the same union computed for every section although they are not tried (dense-song values).

| class | song | bars | today spb | union spb | gain ratio | mean raw/bar | CV | dev25 | median count |
|---|---|---|---|---|---|---|---|---|---|
| ACC | S69 | 41-53 | 2.92 | 5.17 | 1.77 | 5.42 | 0.244 | 0.167 | 5.5 |
| ACC | S69 | 83-95 | 1.83 | 4.58 | 2.50 | 4.75 | 0.245 | 0.167 | 5.0 |
| other-tried | S69 | 111-121 | 2.60 | 2.90 | 1.12 | 3.10 | 0.509 | 0.800 | 3.0 |
| other-tried | PSSOM | 11-28 | 4.82 | 7.71 | 1.60 | 9.65 | 0.466 | 0.471 | 11.0 |
| REJ | PSSOM | 28-39 | 5.82 | 9.27 | 1.59 | 10.91 | 0.283 | 0.455 | 11.0 |
| REJ | PSSOM | 55-67 | 4.17 | 8.83 | 2.12 | 10.25 | 0.466 | 0.417 | 11.0 |
| other-tried | PSSOM | 67-84 | 5.76 | 9.71 | 1.68 | 12.06 | 0.532 | 0.529 | 14.0 |
| REJ | PSSOM | 84-103 | 3.42 | 9.47 | 2.77 | 11.32 | 0.292 | 0.632 | 11.0 |
| dense(not tried) | WetLeg | 0-5 | 5.60 | 6.60 | 1.18 | 7.20 | 0.184 | 0.400 | 7.0 |
| dense(not tried) | WetLeg | 5-18 | 6.92 | 7.46 | 1.08 | 8.62 | 0.174 | 0.077 | 9.0 |
| dense(not tried) | WetLeg | 18-33 | 3.47 | 3.73 | 1.08 | 4.27 | 0.791 | 0.600 | 6.0 |
| dense(not tried) | WetLeg | 33-42 | 6.56 | 7.33 | 1.12 | 8.67 | 0.172 | 0.111 | 9.0 |
| dense(not tried) | WetLeg | 42-58 | 6.62 | 7.31 | 1.10 | 8.50 | 0.220 | 0.250 | 8.0 |
| dense(not tried) | WetLeg | 58-65 | 4.71 | 6.29 | 1.33 | 7.00 | 0.153 | 0.143 | 7.0 |
| dense(not tried) | WetLeg | 65-100 | 6.69 | 7.23 | 1.08 | 9.00 | 0.270 | 0.257 | 9.0 |
| dense(not tried) | WetLeg | 100-108 | 6.50 | 7.12 | 1.10 | 8.12 | 0.226 | 0.250 | 8.0 |
| dense(not tried) | WetLeg | 108-113 | 3.80 | 3.80 | 1.00 | 7.20 | 0.812 | 0.800 | 7.0 |
| other-tried | Fame | 0-5 | 2.80 | 4.40 | 1.57 | 5.60 | 0.582 | 0.600 | 7.0 |
| dense(not tried) | Fame | 5-10 | 9.40 | 10.40 | 1.11 | 12.40 | 0.231 | 0.200 | 11.0 |
| dense(not tried) | Fame | 10-19 | 9.78 | 10.11 | 1.03 | 11.22 | 0.131 | 0.000 | 12.0 |
| dense(not tried) | Fame | 19-53 | 8.88 | 9.38 | 1.06 | 10.47 | 0.244 | 0.294 | 11.0 |
| dense(not tried) | Fame | 53-61 | 7.38 | 8.00 | 1.08 | 8.88 | 0.214 | 0.125 | 9.0 |
| dense(not tried) | Fame | 61-71 | 10.20 | 10.40 | 1.02 | 11.90 | 0.143 | 0.100 | 11.5 |
| dense(not tried) | Fame | 71-82 | 10.73 | 11.00 | 1.03 | 11.91 | 0.166 | 0.000 | 12.0 |
| dense(not tried) | Fame | 82-101 | 9.21 | 9.58 | 1.04 | 10.63 | 0.231 | 0.263 | 11.0 |
| other-tried | Chelsea | 0-9 | 2.00 | 2.11 | 1.06 | 2.67 | 0.984 | 0.778 | 2.0 |
| ACC | Chelsea | 9-38 | 2.76 | 4.38 | 1.59 | 5.17 | 0.428 | 0.379 | 5.0 |
| ACC | Chelsea | 105-142 | 2.59 | 5.00 | 1.93 | 5.43 | 0.357 | 0.405 | 6.0 |

| measure | accepted range | rejected range | other tried | margin | separates >= threshold? |
|---|---|---|---|---|---|
| CV | 0.244-0.428 | 0.283-0.466 | 0.466-0.984 | overlap (-0.145) | no |
| dev25 | 0.167-0.405 | 0.417-0.632 | 0.471-0.800 | +0.012 (midpoint 0.411) | separates, but margin 0.012 < 0.1 |
| gain ratio | 1.59-2.50 | 1.59-2.77 | 1.06-1.68 | overlap (Chelsea 9-38 1.59 = PSSOM 28-39 1.59) | no |

Dense values (not tried): CV Wet Leg 0.15-0.81 (0.79/0.81 in the two sparse-ish sections 18-33 and 108-113), Fame 0.13-0.58 (0.58 is the tried intro 0-5; dense sections 0.13-0.24); dev25 Wet Leg 0.08-0.80, Fame 0.00-0.29 (dense sections); gain ratio Wet Leg 1.00-1.33, Fame 1.02-1.11 (dense sections), i.e. a gain ratio near 1 for dense songs.
