# Assumption pass, 1.8 spec section 5: the vote (A3, A4)

Date 2026-10-08. Measured on the eleven 1.7 run folders (`runs\*\04_strums\strums.json`, with `02_grid\grid.json` and `03_harmony\chords.json` for the trailing-bar drop), read only. Every voiced member's vote was reconstructed as `stages\strums.py` builds it: holding bars (`rests` false, trailing silent bars dropped), `bar_onsets` with D and U folded to S, `choose_pattern`, `structure_test` seeded by the member's start bar, `member_figures`, and the rule-5 page print. The reconstruction reproduces every section pattern and every printed bar row of the eleven runs exactly (100 voiced members, 0 mismatches), so the "before" column below is what 1.7 prints. Scripts: scratchpad `ap_vote\recon.py`, `a4.py`, `a4b.py`, `a3.py`, `a3b.py`.

Two notes on the inputs. The 1.7 runs hold eleven songs and 100 voiced members (the spec's A6 says 93). The review's "25 judged ranges" come to 24 in the records (1.6 clips 12 to 29, 1.7 clips 9 to 14): 8 YES or MOSTLY (1.7 clip 12, "almost fit", counted MOSTLY) and 16 NO, not 10 and 15. Ranges are read as the member that contains them: Chelsea Dagger 7-19 is the intro member 0-20 (11 holding bars), Need You Tonight 8-12 is 0-13 (5), Pour Some Sugar On Me 1-7, 19-27 and 80-84 are 0-11, 11-28 and 77-84, Wet Leg 26-32 is 18-33 (7).

## A4: 5.1 to 5.4 move only Need You Tonight 8-12, The Cars 72-76 and unjudged members

Method: each rule switched on alone against the 1.7 baseline, then all four together; a member "moves" when its own vote vector or its certainty changes. The page print (rule 5: section pattern or own) was checked too and moves on the same members only.

### (a) `PERIOD2_MIN_PAIRS` 3

Twelve members vote unit 2 today. Pairs, bars `_pairs` drops, and the unit at floors 2, 3 and 4:

| member | holding | phase | pairs | dropped | floor 2 / 3 / 4 | print today |
|---|---|---|---|---|---|---|
| Need You Tonight 0-13 (8-12) | 5 | 0 | 2 | 12 | 2 / **1** / 1 | certain |
| Need You Tonight 24-31 | 7 | 0 | 3 | 30 | 2 / 2 / **1** | certain |
| Summer of '69 4-19 (R) | 15 | 1 | 7 | 4 | 2 / 2 / 2 | grey |
| Summer of '69 31-41 | 10 | 0 | 5 | none | 2 / 2 / 2 | certain |
| Summer of '69 75-83 (R) | 8 | 0 | 4 | none | 2 / 2 / 2 | certain |
| Summer of '69 95-111 (R) | 16 | 0 | 8 | none | 2 / 2 / 2 | certain |
| Day Tripper 46-52 | 6 | 0 | 3 | none | 2 / 2 / **1** | grey |
| Day Tripper 78-95 | 16 | 0 | 8 | none | 2 / 2 / 2 | certain |
| The Cars 72-76 | 4 | 0 | 2 | none | 2 / **1** / 1 | grey |
| AC/DC 0-16 | 16 | 1 | 7 | 0, 15 | 2 / 2 / 2 | certain |
| AC/DC 16-34 | 18 | 1 | 8 | 16, 33 | 2 / 2 / 2 | certain |
| AC/DC 43-57 | 14 | 1 | 6 | 43, 56 | 2 / 2 / 2 | certain |

(R) marks the regression set. Kept at unit 2: 12 of 12 at floor 2, 10 at floor 3, 8 at floor 4. Floor 3 demotes exactly the two members the spec names; floor 4 also demotes Need You Tonight 24-31 (ear NO; it then prints a one-bar `DUDUD-DUDUDU-U-U`, still certain, so nothing is gained) and Day Tripper 46-52 (unjudged, goes grey by p 0.092). The regression members have 4 to 8 pairs, so the band that leaves them alone is 3 to 4; at floor 2 the rule does nothing and, with (c) on, The Cars 72-76 would print certain. The review's "phase 1, one pair, bars 72 and 75 never enter" describes the 1.6 run; in 1.7 all four bars hold at phase 0 and nothing is dropped.

Alone, (a) moves two members: Need You Tonight 0-13 `D---D---D---D--- / D-D---DU---U---U` certain to one-bar `D-D-D-DUD--UD--U` grey (confidence 0.503 against the sixteenth floor 0.53; explained 0.89, p 0.007); The Cars 72-76 `DUD-DUDU / -UD-D-D-` grey to one-bar `-UD-D-D-` grey (p 0.067, confidence 0.750, explained 0.71).

### (b) `MIN_SLOT_SUPPORT` 2

The floor binds only at one or two voted units: at three, `strikes > n/3` already demands two. Members with three or fewer voted units: Need You Tonight 0-13 (2), The Cars 72-76 (2), Need You Tonight 24-31 (3), Summer of '69 0-4 (3), Day Tripper 46-52 (3). Only the two with two units change, as the spec expects.

Need You Tonight 8-12: the printed unit vector `S---S---S---S---S-S---SS---S---S` **is exactly the union of its two pairs** (8+9, 10+11), as the review claims. With the floor, `majority_vector` gives `S---S---S-------S------S---S---S`; `fill_to_floor` then tops it back up to the density floor and the print becomes `D---D---D---D--- / D------U---U---U` (slot 12 of the first bar returns by rate, 0.5 tie to the earlier slot), still certain under (b) alone. The Cars 72-76 goes `D-D-DUDU / -UD-D-D-`, still grey. (b) on its own therefore cures neither; it matters only as the fallback when (a) is off.

### (c) chance test on the printed unit vector

Shuffling within each voted pair (16 or 32 cells per unit) and scoring `vote_confidence` over the pairs, same seed, gives **p 0.001 to 0.002 on all twelve unit-2 members** (today 0.001 to 1.0). The pair-level null is far weaker than the bar-level one: a shuffled pair loses the alternation as well as the slot positions, so every two-bar figure looks structured. Structured flips, all false to true: Summer of '69 4-19 (p 1.0 to 0.001, grey to **certain**, regression set, ear YES), Day Tripper 46-52 (0.092 to 0.001, grey to certain, unjudged), The Cars 72-76 (0.067 to 0.002, certain under (c) alone; moot once (a) sends it to unit 1). No unit-1 member changes.

### (d) `MIN_VOTE_BARS` 4

One member has fewer than four voted bars: Summer of '69 0-4 (the intro, riff, three holding bars; `D-xx-xxx`, confidence 0.868, p 0.005) prints grey. Under the combined rules no other member falls under four: Need You Tonight 0-13 votes five bars and The Cars 72-76 four, so neither is greyed by support.

### Combined

Five members move (certain count stays 75 of 100):

| member | before | after | by |
|---|---|---|---|
| Need You Tonight 0-13 (8-12) | `D---D---D---D--- / D-D---DU---U---U` u2 certain | `D-D-D-DUD--UD--U` u1 grey (conf 0.503 < 0.53) | (a) |
| The Cars 72-76 | `DUD-DUDU / -UD-D-D-` u2 grey | `-UD-D-D-` u1 grey (p 0.067) | (a) |
| Summer of '69 0-4 | `D-xx-xxx` certain | same, grey | (d) |
| Summer of '69 4-19 (R) | `xxxxxxD- / D-DU-xxx` u2 grey | same, **certain** (p 1.0 to 0.001) | (c) |
| Day Tripper 46-52 | `D-DUDUDU / -UDU-UD-` u2 grey | same, certain | (c) |

Regression set: all thirteen keep their vector; twelve keep their certainty; Summer of '69 4-19 goes grey to certain. Need You Tonight 8-12 prints grey, The Cars 72-76 prints grey; Chelsea Dagger 7-19 is untouched by 5.1 to 5.4 (11 voted bars, p 0.001, certain) and waits on 4.4 as the spec says. Both new greys rest on figures near their floors (0.503 against 0.53; 0.067 against 0.05), not on the support rule.

**Verdict: refuted on one member.** 5.1, 5.2 and 5.4 hold exactly; 5.3 moves Summer of '69 4-19 from grey to certain, an ear-YES regression member, and Day Tripper 46-52 likewise. The change is in the right direction for the ear, but the regression criterion (vector and certainty unchanged) is broken, and the unit-level shuffle stops discriminating among two-bar members at all (every p ≤ 0.002, including the ear-NO Need You Tonight 24-31 and Summer of '69 31-41, which were already certain). Recommended: keep `PERIOD2_MIN_PAIRS` 3 (band 3 to 4), `MIN_SLOT_SUPPORT` 2, `MIN_VOTE_BARS` 4; amend 5.3 and 5.7 to list Summer of '69 4-19 and Day Tripper 46-52 as members 5.3 blackens and to say the pair-level p is near its floor on every two-bar member, or drop 5.3 and keep the bar-level test, which under (a), (b) and (d) alone already yields the two intended greys and no regression move.

## A3: a `TOP2_MARGIN` band separates ear-YES from ear-NO

Method: for each of the 24 ranges, under the combined 5.1 to 5.4 rules, the candidate set of 5.5 (one-bar majority and medoid, the two real bars agreeing best with the rest, and when the vote is unit 2 the two-bar majority and medoid and the two best pairs); every candidate scored by its mean Jaccard with the holding bars at each bar's own half (`member_figures` confidence, the score the printed pattern carries); the margin is the printed pattern's score minus the best score among candidates whose two-bar expansion differs. Swap distance repeats this with Toussaint's distance (mutes as strikes; unequal counts cost the slot count), margin = runner-up's mean distance minus the printed pattern's, so positive still means clear.

| clip | member | verdict | n | printed | runner-up (Jaccard) | J margin | runner-up (swap) | swap margin |
|---|---|---|---|---|---|---|---|---|
| 1.6 c12 | Summer of '69 4-19 | YES | 15 | `xxxxxxD- / D-DU-xxx` | `xxxxxxx- / D-DU-xxx` | 0.001 | same | 0.00 |
| 1.6 c13 | Summer of '69 31-41 | NO | 10 | `D--U--D- / DUD-DUD-` | `D-DU--D- / DUDUDUD-` | 0.034 | `D--U--D-` | 0.80 |
| 1.6 c14 | Summer of '69 53-58 | NO | 5 | `DU-U-UDU` | `DU-UDUDU` | 0.013 | `D--U-UD-` | -1.20 |
| 1.6 c15 | Summer of '69 75-83 | YES | 8 | `D-DU-UD- / DU-UD-D-` | `D--U-UD- / DU-UD-D-` | 0.008 | same | -1.62 |
| 1.6 c16 | Summer of '69 95-111 | MOSTLY | 16 | `D--U---- / DUDUDUDU` | `D--U---- / DUDUDUD-` | 0.007 | same | -0.56 |
| 1.6 c17 | Summer of '69 111-121 | NO | 9 | `xU--DU--` | `xx--x--x` | 0.028 | same | 0.22 |
| 1.6 c18 | Chelsea Dagger 61-71 | YES | 10 | `D-D---D-` | `D-D-D-D-` | 0.012 | same | 1.80 |
| 1.6 c19 | Pour Some Sugar 55-67 | NO | 11 | `D---D-DUD---D--U` | `D---D-DUD-D-D---` | -0.021 | `D---D---D-D-D---` | -1.27 |
| 1.6 c20 | Wet Leg 58-65 | NO | 7 | `D-DU-UDU` | `D-D---DU` | -0.005 | same | -0.29 |
| 1.6 c21 | Fame 61-71 | NO | 10 | `DUDUDUD---D-D-D-` | `D-DUD-D---D-D-D-` | 0.007 | `DUDUDUD---D-DUD-` | 0.90 |
| 1.6 c22 | Fame 71-81 | NO | 10 | `D-DUDUD--UD-DUxx` | `D-DUDUD-DUD-DUxx` | 0.006 | `D-DU-UD--UD-DUx-` | 2.90 |
| 1.6 c23 | Need You Tonight 24-31 | NO | 7 | `D---D---D--UxU-U / D-DUD-DU-UDU-U-U` | `D---D-D-D--UxU-U / ...` | 0.007 | `... / DUDUD-DUDUDU-U-U` | 0.00 |
| 1.6 c24 | Need You Tonight 79-86 | MOSTLY | 5 | `DU-U-UDU--DU-U-x` | `DU-UDUDUD-xU-UDU` | -0.026 | `D---D-D----U--DU` | 1.60 |
| 1.6 c25 | The Cars 72-76 | NO | 4 | `-UD-D-D-` | `DUD-DUDU` | 0.000 | same | 2.00 |
| 1.6 c26 | All Fired Up 55-61 | MOSTLY | 6 | `D-Dx-U-U` | `D-DxDU-U` | 0.004 | same | -0.83 |
| 1.6 c27 | All Fired Up 90-97 | NO | 7 | `xUDxxxx-` | `xxxxxxxx` | -0.005 | same | -0.86 |
| 1.6 c28 | All Fired Up 97-104 | NO | 7 | `xxDxDxDx` | `xxxxxxD-` | 0.011 | same | -0.29 |
| 1.6 c29 | All Fired Up 104-110 | NO | 6 | `Dxxxxxxx` | `DxxxDxxx` | 0.010 | same | 0.00 |
| 1.7 c9 | Chelsea Dagger 0-20 | NO | 11 | `D-xxxUx-` | `D-xxx-x-` | 0.011 | `D-x-x-x-` | -1.00 |
| 1.7 c10 | Need You Tonight 0-13 | NO | 5 | `D-D-D-DUD--UD--U` | `D---D---D---D---` | 0.038 | same | -4.60 |
| 1.7 c11 | Pour Some Sugar 0-11 | NO | 6 | `-UDUDUDUDUD-D-D-` | `DUDUDUxUDUDUD-D-` | 0.009 | same | -2.67 |
| 1.7 c12 | Pour Some Sugar 11-28 | MOSTLY | 13 | `DUD-D-DU----D---` | `DUD-DUDU----DU--` | -0.020 | `DUD----U----DU--` | -0.31 |
| 1.7 c13 | Pour Some Sugar 77-84 | NO | 4 | `D-----D----U----` | `---U--D---------` | 0.028 | same | -2.00 |
| 1.7 c14 | Wet Leg 18-33 | YES | 7 | `D-D-DUDU` | `D-D-D-DU` | 0.014 | same | -1.29 |

Jaccard: YES/MOSTLY margins run -0.026 to 0.014, NO margins -0.021 to 0.038. Catching every NO needs T > 0.038, which greys all eight YES/MOSTLY; the largest T that loses at most one YES (T ≤ -0.020) leaves 15 of 16 NO ranges above it. Swap: YES/MOSTLY -1.62 to 1.80, NO -4.60 to 2.90; every NO below T needs T > 2.90, losing all eight; T ≤ -1.29 leaves 13 NO above. The two metrics do not even agree on which ranges are clear (Chelsea Dagger 61-71 is the clearest under swap, 1.80, and eighth under Jaccard). The reason is structural: in 13 of 24 ranges the Jaccard runner-up differs from the print by one cell, so the margin measures how contested one slot is, never whether the figure is right. Within the judged ranges, the combined rules of 5.1 to 5.4 leave 8 of 16 NO ranges certain (today 9: Need You Tonight 8-12 is the one fixed) and 3 of 8 YES/MOSTLY grey (today 4; Summer of '69 4-19 is the one blackened).

**Verdict: no band exists**, under either distance. As 5.5's own fallback says: record `top2_margin` and `runner_up_vector` for `evaluate`, do not use them for certainty, and strike `TOP2_MARGIN` from the constants; A3's "if wrong" column applies, with certainty resting on 4.4 and 5.1 to 5.4.
