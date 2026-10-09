# Assumption pass A5: the bass-on-stem gate (2026-10-08, main at 27bf2a2)

Spec: `docs/superpowers/specs/2026-10-08-ukulele-tab-chain-v1-8-design.md` section 6 and assumption A5. Scripts: session scratchpad `ap_bleed/measure.py`, `analyse2.py`, `badge_stems.py`; read-only on `runs/`.

## Method

For every member of every planned section of the eleven runs (the plan and members as `04_strums/strums.json` records them, members resolved through `member_spans`; 101 members, one silent), the four figures of spec section 6 on the mono mix (`00_ingest/audio.wav`), the bass stem and the stage's source stem (`strums.json` `source`: guitar stem on all eleven; `choose_source` recomputed agrees) over the member's bars, with the stage's trailing-bar trim on last members. STFT n_fft 4096, hop 2048, power, low band = bins below 250 Hz: `low_mix_share_bass` = bass low power / mix low power, `low_mix_share_source` = source low power / mix low power, `low_own_share` = source low power / source total power, `bass_stem_ratio` = RMS(bass) / RMS(mix) over the member's samples. Silence is marked the stage's way (section cut, no holding bar, empty trimmed outro). The gate: `bass_stem_ratio <= 0.05 and low_own_share >= 0.40`. Also read, for (4): the source stem's spectral centroid over the member and the mix's own low share.

Positives are the two ear-judged members, Badge Verse 1 4-28 and Verse 2 61-70. Badge's other five members are reported apart (un-judged); negatives are every member of the other ten songs. Spot checks against the review's D2 figures agree (Badge Verse 1 0.756 / 0.864, Verse 2 0.234 / 0.462, Summer of '69 intro 0.639 / 0.376).

## Findings

**(1) Where the gate fires.** On five Badge members and nothing else: Verse 1 4-28 (own 0.864, bass 0.0020), Chorus 1 34-50 (0.544, 0.0007), Instrumental 2 50-56 (0.422, 0.0010), Chorus 2 56-61 (0.595, 0.0010), Verse 2 61-70 (0.462, 0.0008). No member of the other ten songs fires, intros and outros included. A5's letter ("the verses and no other member") is wrong on Badge itself: both choruses and Instrumental 2 fire too. They are the same physical condition, not a false alarm: Badge's bass stem is empty from bar 4 to the end (0.0007 to 0.011 of the mix on every member; the six-stem landing of the mix's sub-250 Hz energy is bass 0.000 to 0.001 on all six, guitar 0.21 to 0.87, drums 0.08 to 0.50) while the published sources have the bass playing from bar 5. The ear has judged only the verses; the choruses and Instrumental 2 are un-judged, so their firing is a prediction, not a verified hit. Badge Instrumental 1 28-34 (the bridge arpeggio, where "riff heard" agrees with the published tab) does **not** fire: own share 0.223, although the guitar stem holds 0.867 of the mix's low band there. The gate reads the stem's own register, not where the bass went; a bright part over the bass hides it. Harmless on this song (the header is right there), named as a limit.

**(2) `low_own_share` among members with `bass_stem_ratio` <= 0.05** (nine members: six Badge, three intros before the bass enters):

| Member | own | bass | mix_src | centroid Hz |
|---|---:|---:|---:|---:|
| Badge Verse 1 4-28 (positive) | 0.864 | 0.0020 | 0.756 | 222 |
| Badge Chorus 2 56-61 | 0.595 | 0.0010 | 0.311 | 559 |
| Badge Chorus 1 34-50 | 0.544 | 0.0007 | 0.424 | 689 |
| Badge Verse 2 61-70 (positive) | 0.462 | 0.0008 | 0.234 | 630 |
| Badge Instrumental 2 50-56 | 0.422 | 0.0010 | 0.215 | 1087 |
| Summer of '69 Intro 0-4 | 0.376 | 0.0003 | 0.639 | 811 |
| Badge Instrumental 1 28-34 | 0.223 | 0.0113 | 0.867 | 1069 |
| Pour Some Sugar Intro 0-11 | 0.070 | 0.0184 | 0.023 | 1582 |
| AC/DC Intro 0-16 | 0.036 | 0.0003 | 0.039 | 1299 |

Highest non-Badge: 0.376 (Summer of '69 intro). Lowest judged positive: 0.462 (Verse 2). Band for `OWN_LOW_SHARE_MIN`: 0.376 to 0.462, width 0.086; the floor 0.40 sits 0.024 above the near miss and 0.062 below the lowest positive. Badge Instrumental 2 at 0.422 lies inside the band, so a floor above 0.42 drops it; the next non-Badge value below the near miss is 0.070, so the band is held by one member.

**(3) `bass_stem_ratio` among members with `low_own_share` >= 0.40** (20 members): the five firing Badge members at 0.0007 to 0.0020, then All Fired Up Verse 104-110 at 0.3169, Summer of '69 Outro 0.4223, All Fired Up 33-49 0.4259, 97-104 0.4403, Fame Intro 0.4953, All Fired Up 55-61 0.5229, 28-33 0.5475, Badge Intro 0.5482, All Fired Up 90-97 0.5784, six Wet Leg members 0.70 to 0.87. Band for `BASS_STEM_MAX`: 0.0020 to 0.3169, two orders of magnitude; 0.05 sits 25x above the positives and 6x below the nearest negative. The conjunction's margin is all on this axis.

**(4) Other thresholds and third figures.** Sweeping `BASS_STEM_MAX` from 0.01 to 0.20 brings no non-Badge member above own 0.376 under it (the members it adds are Summer of '69 Verse 1 at 0.146 with own 0.339, Pour Some Sugar's quiet-bass members with own 0.06 to 0.20, The Cars 52-68 at 0.184 with own 0.227): the own band is 0.376 to 0.462 at every value, so the bass axis cannot widen it. Sweeping `OWN_LOW_SHARE_MIN`: below 0.40 the bass band collapses to 0.0003 (Summer of '69 intro joins at 0.376; AC/DC intro at 0.036 needs the floor below 0.04); at 0.45 both positives still hold with the same bass band; at 0.50 Verse 2 is lost. Third figures among the nine members under 0.05, positives against the three intros:

| Figure | Positives | Non-Badge negatives | Band |
|---|---|---|---|
| `low_own_share` | 0.864, 0.462 | 0.376, 0.070, 0.036 | 0.376 to 0.462 (+0.086, 19 %) |
| `low_mix_share_source` | 0.756, 0.234 | 0.639, 0.023, 0.039 | none: Summer's intro (0.639) lies between the positives |
| source centroid (lower = positive) | 222, 630 Hz | 811, 1582, 1299 Hz | 630 to 811 Hz (+180 Hz, 22 %) |
| mix own low share | 0.487, 0.356 | 0.307, 0.329, 0.413 | none: AC/DC's intro (0.413) sits above Verse 2 |
| source RMS over mix | 0.652, 0.423 | 0.721, 0.326, 0.661 | none |

The centroid gives a band of the same relative width on the same near miss (Summer of '69's intro is the closest negative on both), so pairing it with the own share widens nothing; and Badge's un-judged firing members read 1069 to 1087 Hz, above the intro's 811, so a centroid floor would un-fire Instrumental 2 and Chorus 1. `low_mix_share_source` is killed as a gate input: the share of the mix's low band the stem takes is high whenever nothing else is low, bass-less intros included. Nothing measured gives a wider band than `low_own_share`.

**(5) The two intros.** Summer of '69 Intro 0-4: `low_mix_share_bass` 0.000, `low_mix_share_source` 0.639, `low_own_share` 0.376, `bass_stem_ratio` 0.0003, centroid 811 Hz, source RMS ratio 0.721, riff-flagged. The picked riff before the bass enters: the near miss on both axes that could have fired, held out by 0.024 of own share. Badge Intro 0-4: `low_mix_share_bass` 0.304, `low_mix_share_source` 0.375, `low_own_share` 0.878, `bass_stem_ratio` 0.548, centroid 192 Hz. The chord guitar is on the bass stem there (the review's "changed its mind midway"), and its own share 0.878 is the highest of all 101 members; it does not fire because the bass stem is full, which is what the conjunction is for.

**(6) Leave-one-song-out.** With Badge held out the gate fires on nothing (highest non-Badge own under 0.05 is 0.376; lowest non-Badge bass over 0.40 is 0.3169). With any other song held out, the five Badge members still fire and nothing else; the recommended constants do not move. The bands do: holding out Summer of '69 widens the own band to 0.070 to 0.462 (the near miss is one member of one song); holding out All Fired Up moves the bass band's upper edge from 0.3169 to 0.4223. Every other hold-out leaves both bands as measured.

## Verdict

Keep `BASS_STEM_MAX` 0.05 and `OWN_LOW_SHARE_MIN` 0.40 (own band 0.376 to 0.462 held by one member, bass band 0.002 to 0.317); amend A5 and section 6 to say the gate fires on five Badge members, the two judged verses plus both choruses and Instrumental 2 (same empty bass stem, un-judged by ear, so they go on the next listening list), misses Badge's bridge arpeggio 28-34 by design of the own-share figure, and that no third figure widens the band.

## Table: every member, all eleven songs

Bars are the member's grid span; a trimmed last member is measured to its trimmed end. Silent members are marked and measured anyway. Gate = `bass_stem_ratio <= 0.05 and low_own_share >= 0.40`.

| Song | Section | Member bars | Silent | low_mix_share_bass | low_mix_share_source | low_own_share | bass_stem_ratio | Gate |
|---|---|---|---|---:|---:|---:|---:|---|
| All Fired Up | 0 intro | intro 0-28 |  | 0.349 | 0.121 | 0.257 | 0.4479 |  |
| All Fired Up | 1 verse | verse 28-33 |  | 0.461 | 0.067 | 0.518 | 0.5475 |  |
| All Fired Up | 1 verse | verse 33-49 (longest) |  | 0.369 | 0.086 | 0.493 | 0.4259 |  |
| All Fired Up | 2 chorus | chorus 49-55 |  | 0.398 | 0.057 | 0.185 | 0.3795 |  |
| All Fired Up | 3 verse | verse 55-61 |  | 0.442 | 0.081 | 0.413 | 0.5229 |  |
| All Fired Up | 3 verse | verse 61-90 (longest) |  | 0.432 | 0.053 | 0.270 | 0.3814 |  |
| All Fired Up | 3 verse | verse 90-97 |  | 0.465 | 0.218 | 0.612 | 0.5784 |  |
| All Fired Up | 3 verse | verse 97-104 |  | 0.372 | 0.199 | 0.694 | 0.4403 |  |
| All Fired Up | 3 verse | verse 104-110 |  | 0.242 | 0.314 | 0.882 | 0.3169 |  |
| All Fired Up | 4 chorus | chorus 110-124 |  | 0.265 | 0.087 | 0.349 | 0.2624 |  |
| All Fired Up | 5 verse | verse 124-128 |  | 0.473 | 0.043 | 0.282 | 0.3466 |  |
| All Fired Up | 6 chorus | chorus 128-132 |  | 0.263 | 0.039 | 0.179 | 0.2372 |  |
| All Fired Up | 7 outro | outro 132-156 |  | 0.365 | 0.084 | 0.173 | 0.4161 |  |
| Chelsea Dagger | 0 intro | intro 0-20 |  | 0.273 | 0.028 | 0.299 | 0.4901 |  |
| Chelsea Dagger | 1 chorus | chorus 20-38 |  | 0.261 | 0.072 | 0.129 | 0.2997 |  |
| Chelsea Dagger | 2 verse | verse 38-61 |  | 0.232 | 0.053 | 0.312 | 0.3382 |  |
| Chelsea Dagger | 3 chorus | chorus 61-71 |  | 0.277 | 0.088 | 0.154 | 0.3102 |  |
| Chelsea Dagger | 4 verse | verse 71-93 |  | 0.232 | 0.047 | 0.266 | 0.3364 |  |
| Chelsea Dagger | 5 instrumental | instrumental 93-108 |  | 0.319 | 0.033 | 0.175 | 0.5031 |  |
| Chelsea Dagger | 6 chorus | chorus 108-142 |  | 0.146 | 0.155 | 0.198 | 0.2142 |  |
| Badge | 0 intro | intro 0-4 |  | 0.304 | 0.375 | 0.878 | 0.5482 |  |
| Badge | 1 verse | verse 4-28 |  | 0.000 | 0.756 | 0.864 | 0.0020 | **fires** |
| Badge | 2 instrumental | instrumental 28-34 |  | 0.001 | 0.867 | 0.223 | 0.0113 |  |
| Badge | 3 chorus | chorus 34-50 |  | 0.000 | 0.424 | 0.544 | 0.0007 | **fires** |
| Badge | 4 instrumental | instrumental 50-56 |  | 0.000 | 0.215 | 0.422 | 0.0010 | **fires** |
| Badge | 5 chorus | chorus 56-61 |  | 0.000 | 0.311 | 0.595 | 0.0010 | **fires** |
| Badge | 6 verse | verse 61-70 |  | 0.000 | 0.234 | 0.462 | 0.0008 | **fires** |
| Fame | 0 intro | intro 0-17 |  | 0.358 | 0.147 | 0.434 | 0.4953 |  |
| Fame | 1 verse | verse 17-29 |  | 0.416 | 0.047 | 0.220 | 0.4128 |  |
| Fame | 2 instrumental | instrumental 29-35 |  | 0.345 | 0.092 | 0.352 | 0.4865 |  |
| Fame | 3 verse | verse 35-47 |  | 0.446 | 0.071 | 0.272 | 0.4080 |  |
| Fame | 4 instrumental | instrumental 47-61 |  | 0.582 | 0.044 | 0.275 | 0.6490 |  |
| Fame | 5 chorus | chorus 61-71 |  | 0.617 | 0.011 | 0.085 | 0.6166 |  |
| Fame | 6 verse | verse 71-81 |  | 0.437 | 0.027 | 0.150 | 0.3910 |  |
| Fame | 7 instrumental | instrumental 81-85 |  | 0.360 | 0.089 | 0.316 | 0.4976 |  |
| Fame | 8 verse | verse 85-101, trimmed to 100 |  | 0.395 | 0.007 | 0.045 | 0.4689 |  |
| Wet Leg | 0 verse | verse 0-5 |  | 0.551 | 0.016 | 0.431 | 0.7007 |  |
| Wet Leg | 1 chorus | chorus 5-18 |  | 0.648 | 0.016 | 0.403 | 0.7558 |  |
| Wet Leg | 2 verse | verse 18-33 |  | 0.617 | 0.012 | 0.433 | 0.7353 |  |
| Wet Leg | 3 chorus | chorus 33-42 |  | 0.620 | 0.025 | 0.549 | 0.7361 |  |
| Wet Leg | 4 verse | verse 42-58 |  | 0.605 | 0.021 | 0.410 | 0.7079 |  |
| Wet Leg | 5 verse | verse 58-65 |  | 0.594 | 0.025 | 0.373 | 0.6774 |  |
| Wet Leg | 5 verse | verse 65-100 (longest) |  | 0.605 | 0.023 | 0.343 | 0.6739 |  |
| Wet Leg | 6 chorus | chorus 100-108 |  | 0.634 | 0.020 | 0.331 | 0.6769 |  |
| Wet Leg | 7 outro | outro 108-113, trimmed to 109 | yes | 0.885 | 0.013 | 0.829 | 0.8659 |  |
| Need You Tonight | 0 intro | intro 0-13 |  | 0.143 | 0.001 | 0.019 | 0.3442 |  |
| Need You Tonight | 1 verse | verse 13-24 |  | 0.278 | 0.000 | 0.013 | 0.4665 |  |
| Need You Tonight | 2 chorus | chorus 24-31 |  | 0.228 | 0.002 | 0.012 | 0.3898 |  |
| Need You Tonight | 3 verse | verse 31-48 |  | 0.288 | 0.006 | 0.141 | 0.4578 |  |
| Need You Tonight | 4 chorus | chorus 48-56 |  | 0.249 | 0.002 | 0.017 | 0.4168 |  |
| Need You Tonight | 5 verse | verse 56-79 |  | 0.289 | 0.013 | 0.209 | 0.4467 |  |
| Need You Tonight | 6 outro | outro 79-86, trimmed to 84 |  | 0.211 | 0.001 | 0.034 | 0.3911 |  |
| Pour Some Sugar | 0 intro | intro 0-11 |  | 0.000 | 0.023 | 0.070 | 0.0184 |  |
| Pour Some Sugar | 1 verse | verse 11-28 |  | 0.082 | 0.025 | 0.194 | 0.2058 |  |
| Pour Some Sugar | 2 chorus | chorus 28-39 |  | 0.173 | 0.017 | 0.090 | 0.2476 |  |
| Pour Some Sugar | 3 verse | verse 39-55 |  | 0.011 | 0.024 | 0.119 | 0.0703 |  |
| Pour Some Sugar | 4 chorus | chorus 55-67 |  | 0.175 | 0.019 | 0.063 | 0.2337 |  |
| Pour Some Sugar | 5 instrumental | instrumental 67-77 |  | 0.007 | 0.014 | 0.074 | 0.0631 |  |
| Pour Some Sugar | 6 verse | verse 77-84 |  | 0.026 | 0.013 | 0.199 | 0.1145 |  |
| Pour Some Sugar | 7 chorus | chorus 84-103 |  | 0.108 | 0.030 | 0.086 | 0.1729 |  |
| Summer of '69 | 0 intro | intro 0-4 |  | 0.000 | 0.639 | 0.376 | 0.0003 |  |
| Summer of '69 | 1 verse | verse 4-19 |  | 0.109 | 0.284 | 0.339 | 0.1459 |  |
| Summer of '69 | 2 chorus | chorus 19-31 |  | 0.534 | 0.015 | 0.030 | 0.4478 |  |
| Summer of '69 | 3 verse | verse 31-41 |  | 0.429 | 0.015 | 0.059 | 0.4642 |  |
| Summer of '69 | 4 chorus | chorus 41-53 |  | 0.416 | 0.014 | 0.051 | 0.3676 |  |
| Summer of '69 | 5 verse | verse 53-58 |  | 0.481 | 0.007 | 0.014 | 0.4259 |  |
| Summer of '69 | 6 bridge | verse 58-68 |  | 0.328 | 0.032 | 0.059 | 0.3125 |  |
| Summer of '69 | 7 instrumental | instrumental 68-75 |  | 0.359 | 0.021 | 0.035 | 0.3974 |  |
| Summer of '69 | 8 verse | verse 75-83 |  | 0.434 | 0.006 | 0.022 | 0.3817 |  |
| Summer of '69 | 9 chorus | chorus 83-95 |  | 0.419 | 0.016 | 0.055 | 0.3561 |  |
| Summer of '69 | 10 verse | verse 95-111 |  | 0.319 | 0.019 | 0.026 | 0.3138 |  |
| Summer of '69 | 11 outro | outro 111-121, trimmed to 120 |  | 0.241 | 0.084 | 0.554 | 0.4223 |  |
| Day Tripper | 0 intro | intro 0-11 |  | 0.409 | 0.169 | 0.166 | 0.3960 |  |
| Day Tripper | 1 chorus | chorus 11-15 |  | 0.264 | 0.038 | 0.205 | 0.3312 |  |
| Day Tripper | 2 verse | verse 15-26 |  | 0.294 | 0.059 | 0.318 | 0.3169 |  |
| Day Tripper | 3 instrumental | instrumental 26-30 |  | 0.410 | 0.040 | 0.059 | 0.4292 |  |
| Day Tripper | 4 chorus | chorus 30-35 |  | 0.195 | 0.074 | 0.207 | 0.2763 |  |
| Day Tripper | 5 verse | verse 35-46 |  | 0.377 | 0.029 | 0.220 | 0.3747 |  |
| Day Tripper | 6 instrumental | instrumental 46-52 |  | 0.616 | 0.011 | 0.031 | 0.6018 |  |
| Day Tripper | 7 verse | verse 52-58 |  | 0.255 | 0.072 | 0.205 | 0.2971 |  |
| Day Tripper | 8 instrumental | instrumental 58-63 |  | 0.372 | 0.060 | 0.160 | 0.4327 |  |
| Day Tripper | 9 chorus | chorus 63-68 |  | 0.333 | 0.037 | 0.117 | 0.3823 |  |
| Day Tripper | 10 verse | verse 68-78 |  | 0.345 | 0.035 | 0.318 | 0.3438 |  |
| Day Tripper | 11 outro | outro 78-95 |  | 0.354 | 0.127 | 0.149 | 0.3527 |  |
| The Cars | 0 intro | intro 0-11 |  | 0.208 | 0.050 | 0.159 | 0.3561 |  |
| The Cars | 1 verse | verse 11-24 |  | 0.202 | 0.059 | 0.288 | 0.3553 |  |
| The Cars | 2 chorus | chorus 24-33 |  | 0.223 | 0.054 | 0.248 | 0.3254 |  |
| The Cars | 3 verse | verse 33-45 |  | 0.225 | 0.045 | 0.242 | 0.3531 |  |
| The Cars | 4 chorus | chorus 45-52 |  | 0.235 | 0.024 | 0.210 | 0.3127 |  |
| The Cars | 5 verse | verse 52-68 |  | 0.061 | 0.049 | 0.227 | 0.1835 |  |
| The Cars | 6 chorus | chorus 68-72 |  | 0.179 | 0.087 | 0.102 | 0.2625 |  |
| The Cars | 7 instrumental | instrumental 72-76 |  | 0.189 | 0.059 | 0.055 | 0.2643 |  |
| The Cars | 8 verse | verse 76-90 |  | 0.232 | 0.042 | 0.201 | 0.3327 |  |
| The Cars | 9 chorus | chorus 90-101 |  | 0.245 | 0.035 | 0.153 | 0.3040 |  |
| AC/DC | 0 intro | intro 0-16 |  | 0.000 | 0.039 | 0.036 | 0.0003 |  |
| AC/DC | 1 chorus | chorus 16-34 |  | 0.195 | 0.022 | 0.054 | 0.2624 |  |
| AC/DC | 2 verse | verse 34-43 |  | 0.591 | 0.019 | 0.048 | 0.5027 |  |
| AC/DC | 3 verse | verse 43-57 |  | 0.509 | 0.011 | 0.053 | 0.4704 |  |
| AC/DC | 4 verse | verse 57-74 |  | 0.616 | 0.020 | 0.044 | 0.5075 |  |
| AC/DC | 5 instrumental | instrumental 74-90 |  | 0.512 | 0.053 | 0.047 | 0.4603 |  |
| AC/DC | 6 verse | verse 90-113 |  | 0.563 | 0.020 | 0.048 | 0.4871 |  |
