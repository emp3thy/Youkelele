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

| Constant | Value | Lower side | Upper side |
|---|---:|---|---|
| `FILL_MIN_ENERGY` | 0.2 | loudest all-N bar with silent harmonic stems: 0.111 (Summer of '69 bar 120, the last 0.4 s of the fade). Chelsea's drum-only intro bars reach 0.106. | quietest filled band bar: 0.235 (Pour Some Sugar On Me bar 68) |
| `FILL_MIN_MATCH` | 0.4 | best unpitched or off-set control: 0.297 (Wet Leg bar 112, a drone outside the song's chords) | weakest filled match: 0.427 (Pour Some Sugar On Me bar 71) |
| `FILL_MIN_MARGIN` | 0.05 | bars that pass energy and match but are ambiguous: 0.019, 0.027 and 0.042 (Pour Some Sugar On Me bars 43, 46 and 9) | smallest filled margin: 0.074 (Pour Some Sugar On Me bar 71) |

**Sanity check on labelled bars.** Take every bar the recogniser labelled with a single chord in the four songs. The template match agrees with the recogniser's triad on:

- 314 of 324 bars (97%) that pass match 0.4 and margin 0.05;
- 274 of 279 (98%) at margin 0.10;
- 343 of 366 (94%) with no margin test.

When a bar passes both tests, the chosen chord is therefore usually the one the recogniser itself would have given.

**What fills.**

- **Chelsea Dagger.** 3 of the 9 intro bars: 3 and 4 as C, and 8 as G. The other six intro bars carry drums only in the stems: guitar at most 0.004 RMS and bass at most 0.002, against 0.019 to 0.032 for guitar in bars 3, 4 and 8. They stay N. No setting could fill them without also filling Summer of '69's silent bar 120, which matches C at 0.414.
- **Pour Some Sugar On Me, solo.** 2 of the 12 N bars: 68 as A and 71 as E. Bars 69, 70, 73 and 74 are loud (energy 0.70 to 0.96) but carry the lead line. They match the song's triads at only 0.19 to 0.38, so they stay N. Bars 66 and 77 to 80 are the drum-and-voice breakdown, with the guitar stem at 0.005 or less. They stay N.
- **Summer of '69 (control).** Bars 0, 116, 117 and 120 stay N. Bar 0 is silent. Bars 116 and 117 are loud but unpitched against the song's set (best r 0.03 and 0.19). Bar 120 is silent. Bars 118 and 119 fill as A and B minor. They are not silent: bass 0.10 to 0.11 RMS, energy ratio 0.89 to 1.01, the band playing into the fade. They are pitched (r 0.46 and 0.48 with margins 0.44 and 0.15), so the rule's requirement holds: no genuinely silent or unpitched control bar fills. The chroma there peaks on D sharp and E, as it does in the labelled A and D bars just before. Whether A and B minor are what is played cannot be confirmed from the audio features alone.
- **Wet Leg (control).** Nothing fills. Bars 109 to 112 are loud on the other stem (a drone on F sharp and C sharp), but match the song's triads at only 0.22 to 0.30.
- **Pour Some Sugar On Me, outside the solo** (neither positive nor control).
  - Bar 8, in the intro after seven C sharp bars, fills as C sharp.
  - Bars 44 and 45 fill as E. They lie in the second verse, which the version 1.1 run lessons describe as marked N.C. by Ultimate Guitar. The guitar stem there is 0.008 to 0.009 RMS, a third of its usual level. The song's chorded-bar median is low (0.031), so this still gives energy ratios of 0.25 to 0.31. These are probably false fills.
  - Raising `FILL_MIN_ENERGY` to 0.32 would remove bars 44 and 45. It would also lose solo bar 68 (0.235). Because the brief puts filling the positives first, the lower value was kept.

**Separation.** On energy and match together, the band-playing positives and the silent or unpitched controls separate cleanly. They do not separate completely, because most of the positive bars cannot be filled at all:

- Chelsea's intro is mostly drums only in the stems.
- Pour Some Sugar On Me's solo is mostly lead lines that do not match a triad.

In all, 5 of the 21 named positive bars fill. The 16 left as N fall into three groups:

- Chelsea Dagger bars 0 to 2 and 5 to 7: drums only in the stems.
- Pour Some Sugar On Me bars 66, 67 and 77 to 80: guitar stem at 0.007 RMS or less. Bar 67 is the nearest miss, at energy ratio 0.162.
- Pour Some Sugar On Me bars 69, 70, 73 and 74: loud, but carrying the lead line, with best r under 0.4.

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
| 70 | 0.838 | A:maj | 0.382 | 0.324 | 0.057 | no |
| 71 | 0.849 | E:maj | 0.427 | 0.353 | 0.074 | E:maj |
| 73 | 0.728 | A:maj | 0.190 | 0.149 | 0.041 | no |
| 74 | 0.961 | A:maj | 0.334 | 0.252 | 0.081 | no |
| 77 | 0.069 | C#:min | 0.526 | 0.446 | 0.080 | no |
| 78 | 0.001 | C#:min | 0.244 | 0.193 | 0.051 | no |
| 79 | 0.007 | C#:min | 0.200 | 0.190 | 0.010 | no |
| 80 | 0.229 | C#:min | 0.197 | 0.155 | 0.042 | no |

Filled bars: 8, 44, 45, 68, 71.

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
| Pour Some Sugar On Me 66 to 68 | 0.000 to 0.007 | 0.000 | 0.000 | 0.041 to 0.071 | into the solo |
| Pour Some Sugar On Me 69 to 74 | 0.022 to 0.030 | 0.000 to 0.006 | 0.000 | 0.057 to 0.069 | solo |
| Pour Some Sugar On Me 77 to 80 | 0.000 to 0.005 | 0.000 to 0.004 | 0.000 | 0.056 to 0.066 | drum-and-voice breakdown |
| Summer of '69 116 to 119 | 0.019 to 0.037 | 0.082 to 0.110 | 0.019 to 0.097 | 0.012 to 0.078 | band into the fade |
| Wet Leg 109 to 112 | 0.000 to 0.001 | 0.000 to 0.001 | 0.115 to 0.407 | 0.000 to 0.001 | drone on the other stem |

The per-bar chroma is normalised frame by frame. A bar with near-silent harmonic stems therefore still shows a full-scale chroma made of noise, sometimes with a respectable match (Pour Some Sugar On Me bar 16: r 0.86 at energy 0.016). Only the energy test protects those bars.
