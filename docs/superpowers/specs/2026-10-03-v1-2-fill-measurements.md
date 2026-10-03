# Version 1.2: measurements for filling no-chord bars

These measurements set the three constants in `src/youkelele/music/fill.py` (spec section 3.4).

## Method

- **Runs.** Four existing runs under `runs/`, read only: `sexhetcxqy4` (Chelsea Dagger), `0uib9y4ofps` (Pour Some Sugar On Me), `9f06qzcvuhg` (Summer of '69) and `lbc6ccztp5e` (Wet Leg).
- **Inputs.** For each run: `02_grid/grid.json`, `03_harmony/chords.json` (the version 1.1 snapped events) and the guitar, bass, piano and other stems from `01_separate/stems/`, summed to mono.
- **Features.** The code under test computed them: `bar_energy` and `bar_chroma` on the summed stems, then `fill_silent_bars` with the final constants.
- **Energy ratio.** The bar's RMS divided by the median RMS of the bars that hold a chord.
- **Best r and runner-up r.** Pearson correlations between the bar's mean CQT chroma and the triad templates of the song's own chord set. Labels sharing a triad count once.
- **Margin.** Best r minus runner-up r.
- **Per-stem RMS.** Read for every all-N bar, to decide which bars the band is actually playing in.

The brief named the positive and control bars:

| Song | Role | Bars |
|---|---|---|
| Chelsea Dagger | positive | intro, bars 0 to 8 |
| Pour Some Sugar On Me | positive | the N bars of the solo, bars 66 to 80 |
| Summer of '69 | control | every all-N bar |
| Wet Leg | control | every all-N bar |

## Chosen values

| Constant | Value | Highest bar it must reject | Lowest bar it lets fill |
|---|---:|---|---|
| `FILL_MIN_ENERGY` | 0.2 | Summer of '69 bar 120 (0.111, silent fade tail). Pour Some Sugar On Me bars 15 (0.163) and 67 (0.162) are also rejected (see below). | Pour Some Sugar On Me bar 68 (0.235) |
| `FILL_MIN_MATCH` | 0.32 | Wet Leg bar 112 (0.297, a drone outside the song's chords) | Pour Some Sugar On Me bar 74 (0.334) |
| `FILL_MIN_MARGIN` | 0.05 | Pour Some Sugar On Me bar 46 (0.027, B against F sharp). This is the only bar that passes energy and match but is ambiguous. | Pour Some Sugar On Me bar 70 (0.057) |

### Match: agreement against the recogniser

The check covers every bar the recogniser labelled with a single chord, across all four songs. It compares the template match's triad with the recogniser's, at margin 0.05:

| MATCH | Single-chord bars passing | Agree | Agreement | Of those, energy ratio >= 0.2 | Agree | Agreement |
|---:|---:|---:|---:|---:|---:|---:|
| 0.30 | 330 | 318 | 96.4% | 329 | 317 | 96.4% |
| 0.32 | 330 | 318 | 96.4% | 329 | 317 | 96.4% |
| 0.35 | 329 | 318 | 96.7% | 328 | 317 | 96.6% |
| 0.40 | 324 | 314 | 96.9% | 323 | 313 | 96.9% |

**Choice.** Agreement at 0.32 is within 0.5 points of 0.40, so MATCH is lowered to the band between Wet Leg bar 112 (0.297) and Pour Some Sugar On Me bar 74 (0.334). This fills solo bars 70 and 74 as A. No control bar and no other table bar has a match in that band and passes energy and margin.

**Caveat.** The overall figure barely moves because few labelled bars match in the 0.30 to 0.40 range. Of the 6 such bars, 4 agree with the recogniser, so a fill at this level is less certain than one above 0.4. Filled cells are printed in italics on the sheet.

All-N bars filled at each setting (margin 0.05; CD is Chelsea Dagger, PSSOM is Pour Some Sugar On Me, S69 is Summer of '69):

| ENERGY | MATCH | All-N bars filled |
|---:|---:|---|
| 0.20 | 0.40 | 10: CD 3, 4, 8; PSSOM 8, 44, 45, 68, 71; S69 118, 119 |
| 0.20 | 0.35 | 11: as above plus PSSOM 70 |
| 0.20 | 0.32 | 12: as above plus PSSOM 74 (chosen) |
| 0.20 | 0.30 | 12: same as 0.32 |
| 0.15 | 0.32 | 14: as chosen plus PSSOM 15 (B) and 67 (A) |

### Energy: why not lower than 0.2

Any ENERGY in (0.111, 0.162] would also fill Pour Some Sugar On Me bars 67 (A, r 0.442) and 15 (B, r 0.499), with no control bar filling. The two bars cannot be told apart on energy:

- **Same level.** Bar 15 has ratio 0.163 (absolute RMS 0.0051); bar 67 has ratio 0.162 (absolute RMS 0.0050).
- **Bar 15 is a noise floor.** Its stems are guitar 0.002, bass 0.000, other 0.003, vocals 0.030 and drums 0.053, in the drum-and-voice opening. Its chroma is nearly flat: the top four bins are D sharp 0.71, F sharp 0.67, F 0.65 and G sharp 0.62. A B fill there would be a false chord.
- **Bar 67 has a faint guitar part.** Guitar 0.005, drums 0.060, and a peaked chroma (A 0.86).

**Choice.** ENERGY stays at 0.2. This trades positive bar 67 for keeping bar 15 empty.

### Energy: what the ratio does and does not show

The energy test only works relative to each song's own chorded bars. In absolute terms the levels overlap:

- Pour Some Sugar On Me bar 68 (filled) has absolute RMS 0.0073. Its guitar stem is 0.007, against about 0.025 in the chorded bars.
- Chelsea Dagger's drums-only bars 0 to 2 have absolute RMS 0.0053 to 0.0059.
- Summer of '69's silent fade tail, bar 120, is 0.0166. It is louder in absolute terms than bar 68.

Bar 68 passes because Pour Some Sugar On Me's chorded median is low (0.031 against 0.056 for Chelsea Dagger). The separation is therefore a property of these four songs at ratio 0.2, not a clean physical boundary. The margin is small:

- Pour Some Sugar On Me bar 68 sits at 0.235.
- Bar 80 (r 0.197, rejected on match) sits at 0.229.
- Bars 15 and 67 sit at 0.16.

### What fills

**Chelsea Dagger: 3 of the 9 intro bars.**
- Bars 3 and 4 fill as C, and bar 8 as G.
- The other six intro bars carry drums only in the stems: guitar at most 0.004 RMS and bass at most 0.002, against 0.019 to 0.032 for guitar in bars 3, 4 and 8.
- Filling bars 5 to 7 would need ENERGY under 0.064. That would also fill Summer of '69's silent bar 120 (C, r 0.414).

**Pour Some Sugar On Me, solo: 4 of the 12 N bars.**
- Bars 68 and 70 fill as A, bar 71 as E, and bar 74 as A.
- Bars 69 and 73 are loud but carry the lead line, with r 0.23 and 0.19 against the song's triads.
- Bars 66 and 77 to 80 are the drum-and-voice breakdown, with the guitar stem at 0.005 or less.
- Bar 67 is left N for the energy reason above.

**Summer of '69 (control).**
- Bars 0, 116, 117 and 120 stay N. Bar 0 is silent. Bars 116 and 117 are loud but unpitched against the song's set (r 0.03 and 0.19). Bar 120 is silent.
- Bars 118 and 119 fill as A and B minor. They are not silent: bass 0.10 to 0.11 RMS, energy ratio 0.89 to 1.01, the band playing into the fade. They are pitched (r 0.46 and 0.48), so the rule's requirement holds: no genuinely silent or unpitched control bar fills.
- Their chroma peaks on D sharp and E, as in the labelled A and D bars just before. The audio features cannot confirm that A and B minor are what is played.

**Wet Leg (control).**
- Nothing fills.
- Bars 109 to 112 are loud on the other stem (a drone on F sharp and C sharp). They match the song's triads at only 0.22 to 0.30, all below 0.32.

**Pour Some Sugar On Me, outside the solo (neither positive nor control).**
- Bar 8, in the intro after seven C sharp bars, fills as C sharp.
- Bars 44 and 45 fill as E. These are probably false fills:
  - They lie in the second verse, which the version 1.1 run lessons describe as marked N.C. by Ultimate Guitar.
  - The guitar stem there is 0.008 to 0.009 RMS, a third of its usual level, but the song's low chorded median gives energy ratios of 0.25 and 0.31.
  - Raising ENERGY to 0.32 would remove them, but would also lose solo bar 68 (0.235).

### Summary

7 of the 21 named positive bars fill: Chelsea Dagger 3, 4 and 8; Pour Some Sugar On Me 68, 70, 71 and 74.

No silent or unpitched control bar fills. Two band-playing control bars fill: Summer of '69 118 and 119.

The chosen values give up two kinds of positive bar for precision:

- Pour Some Sugar On Me bar 67, to keep the noise-floor bar 15 empty.
- Chelsea Dagger bars 5 to 7, to keep Summer of '69's silent bar 120 empty.

The 14 positive bars left as N fall into three groups:

- Chelsea Dagger bars 0 to 2 and 5 to 7: drums only in the stems.
- Pour Some Sugar On Me bars 66, 67 and 77 to 80: guitar stem at 0.007 RMS or less.
- Pour Some Sugar On Me bars 69 and 73: lead line, r under 0.25.

## Per-bar table (all-N bars only)

### Chelsea Dagger (`sexhetcxqy4`), positive (intro bars 0 to 8)

Reference RMS (median over chorded bars): 0.0559. Chord set: G:maj, D:maj, A:maj, C:maj, B:min, E:min, A:min, B:maj.

| Bar | Energy ratio | Best | Best r | Runner-up r | Margin | Filled |
|---:|---:|---|---:|---:|---:|---|
| 0 | 0.103 | B:maj | 0.254 | 0.245 | 0.009 | no |
| 1 | 0.095 | G:maj | 0.404 | 0.385 | 0.019 | no |
| 2 | 0.106 | B:maj | 0.465 | 0.210 | 0.255 | no |
| 3 | 0.362 | C:maj | 0.492 | 0.218 | 0.274 | C:maj |
| 4 | 0.579 | C:maj | 0.625 | 0.190 | 0.436 | C:maj |
| 5 | 0.074 | C:maj | 0.421 | 0.268 | 0.154 | no |
| 6 | 0.013 | B:maj | 0.379 | 0.322 | 0.058 | no |
| 7 | 0.064 | C:maj | 0.290 | 0.185 | 0.105 | no |
| 8 | 1.259 | G:maj | 0.430 | 0.350 | 0.079 | G:maj |

Filled bars: 3, 4, 8.

### Pour Some Sugar On Me (`0uib9y4ofps`), positive (solo, bars 66 to 80)

Reference RMS (median over chorded bars): 0.0311. Chord set: C#:maj, F#:maj, B:maj, E:maj, A:maj, C#:min.

| Bar | Energy ratio | Best | Best r | Runner-up r | Margin | Filled |
|---:|---:|---|---:|---:|---:|---|
| 0 | 0.014 | F#:maj | 0.415 | 0.092 | 0.323 | no |
| 8 | 0.438 | C#:maj | 0.572 | 0.444 | 0.128 | C#:maj |
| 9 | 0.181 | C#:maj | 0.509 | 0.467 | 0.042 | no |
| 10 | 0.101 | C#:maj | 0.638 | 0.574 | 0.063 | no |
| 15 | 0.163 | B:maj | 0.499 | 0.332 | 0.167 | no |
| 16 | 0.016 | C#:maj | 0.860 | 0.496 | 0.364 | no |
| 17 | 0.001 | A:maj | 0.382 | 0.327 | 0.055 | no |
| 18 | 0.069 | C#:maj | 0.387 | 0.261 | 0.126 | no |
| 43 | 0.189 | F#:maj | 0.596 | 0.577 | 0.019 | no |
| 44 | 0.306 | E:maj | 0.655 | 0.427 | 0.228 | E:maj |
| 45 | 0.245 | E:maj | 0.719 | 0.417 | 0.302 | E:maj |
| 46 | 0.360 | B:maj | 0.583 | 0.556 | 0.027 | no |
| 66 | 0.002 | C#:min | 0.484 | 0.359 | 0.125 | no |
| 67 | 0.162 | A:maj | 0.442 | -0.034 | 0.476 | no |
| 68 | 0.235 | A:maj | 0.685 | 0.213 | 0.472 | A:maj |
| 69 | 0.702 | A:maj | 0.228 | 0.186 | 0.042 | no |
| 70 | 0.838 | A:maj | 0.382 | 0.324 | 0.057 | A:maj |
| 71 | 0.849 | E:maj | 0.427 | 0.353 | 0.074 | E:maj |
| 73 | 0.728 | A:maj | 0.190 | 0.149 | 0.041 | no |
| 74 | 0.961 | A:maj | 0.334 | 0.252 | 0.081 | A:maj |
| 77 | 0.069 | C#:min | 0.526 | 0.446 | 0.080 | no |
| 78 | 0.001 | C#:min | 0.244 | 0.193 | 0.051 | no |
| 79 | 0.007 | C#:min | 0.200 | 0.190 | 0.010 | no |
| 80 | 0.229 | C#:min | 0.197 | 0.155 | 0.042 | no |

Filled bars: 8, 44, 45, 68, 70, 71, 74.

### Summer of '69 (`9f06qzcvuhg`), control

Reference RMS (median over chorded bars): 0.1502. Chord set: D:maj, A:maj, B:min, G:maj, F:maj, Bb:maj, C:maj.

| Bar | Energy ratio | Best | Best r | Runner-up r | Margin | Filled |
|---:|---:|---|---:|---:|---:|---|
| 0 | 0.023 | A:maj | 0.344 | 0.261 | 0.083 | no |
| 116 | 1.159 | C:maj | 0.029 | 0.020 | 0.009 | no |
| 117 | 1.244 | C:maj | 0.187 | -0.010 | 0.197 | no |
| 118 | 1.014 | A:maj | 0.464 | 0.027 | 0.437 | A:maj |
| 119 | 0.887 | B:min | 0.476 | 0.325 | 0.151 | B:min |
| 120 | 0.111 | C:maj | 0.414 | 0.289 | 0.125 | no |

Filled bars: 118, 119.

### Wet Leg (`lbc6ccztp5e`), control

Reference RMS (median over chorded bars): 0.2716. Chord set: C:maj, F:maj, D:min, C#:maj.

| Bar | Energy ratio | Best | Best r | Runner-up r | Margin | Filled |
|---:|---:|---|---:|---:|---:|---|
| 109 | 0.423 | C#:maj | 0.265 | -0.144 | 0.409 | no |
| 110 | 1.094 | C#:maj | 0.267 | -0.073 | 0.340 | no |
| 111 | 1.330 | C#:maj | 0.222 | -0.183 | 0.405 | no |
| 112 | 1.500 | C#:maj | 0.297 | -0.181 | 0.479 | no |

Filled bars: none.

## Per-stem RMS behind the judgements

| Song, bars | Guitar | Bass | Other | Drums | Reading |
|---|---:|---:|---:|---:|---|
| Chelsea Dagger 0 to 2 | 0.000 | 0.001 to 0.002 | 0.004 to 0.005 | 0.007 to 0.017 | drums only |
| Chelsea Dagger 3 and 4 | 0.019 to 0.032 | 0.002 to 0.005 | 0.001 to 0.004 | 0.003 to 0.013 | guitar enters |
| Chelsea Dagger 5 to 7 | 0.001 to 0.004 | 0.000 to 0.001 | 0.000 | 0.069 to 0.071 | drums only |
| Chelsea Dagger 8 | 0.030 | 0.052 | 0.000 | 0.064 | guitar and bass |
| Pour Some Sugar On Me 15 | 0.002 | 0.000 | 0.003 | 0.053 | drum-and-voice opening, noise floor (vocals 0.030) |
| Pour Some Sugar On Me 66 to 68 | 0.000 to 0.007 | 0.000 | 0.000 | 0.041 to 0.071 | into the solo |
| Pour Some Sugar On Me 69 to 74 | 0.022 to 0.030 | 0.000 to 0.006 | 0.000 | 0.057 to 0.069 | solo |
| Pour Some Sugar On Me 77 to 80 | 0.000 to 0.005 | 0.000 to 0.004 | 0.000 | 0.056 to 0.066 | drum-and-voice breakdown |
| Summer of '69 116 to 119 | 0.019 to 0.037 | 0.082 to 0.110 | 0.019 to 0.097 | 0.012 to 0.078 | band into the fade |
| Wet Leg 109 to 112 | 0.000 to 0.001 | 0.000 to 0.001 | 0.115 to 0.407 | 0.000 to 0.001 | drone on the other stem |

The per-bar chroma is normalised frame by frame. A bar with near-silent harmonic stems therefore still shows a full-scale chroma made of noise, sometimes with a respectable match (Pour Some Sugar On Me bar 16: r 0.86 at energy 0.016). Only the energy test protects those bars.
