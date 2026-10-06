# Assumption pass on the 1.6 spec (2026-10-05)

Run on this machine against the eight kept 1.5 run folders before the owner's review, per the design-document rule. Scripts (throwaway): `%TEMP%\claude\...\scratchpad\spike-pattern-vote\followup.py` (A3, A6) and `%TEMP%\youkulele-v16-assumptions\` (`v16_common.py`, `a2_mute_tiebreak.py`, `a4_member_threshold.py`, `a5_ring_band.py`, `a14_geometry.py`, `a14_pages.py`). Numbers below are what changed the spec.

## A3: two-bar strike floor

Of the seven sections where the two-bar medoid wins by at least 0.10, six have 2 to 11 strikes in each bar of the pair and one is `--------|-------U`; the floor of two strikes per bar drops exactly that one at every margin tried (0.08, 0.10, 0.15 give 8, 6, 4 two-bar sections across the 68). Kept as written.

## A6: chance test on a medoid candidate

The stage's statistic (`vote_confidence`, bars against their own topped vote) does not read the printed candidate, so the p-value is identical for majority and medoid in all 14 switch sections and no certain or uncertain state changes. A medoid-based statistic (mean Jaccard to the medoid, same seed and shuffle order) also changes no state; where the medoid is all rests its p goes to 1.0. Four of the 14 switch targets are all-rest medoids and one is all mutes, hence the two-stroke floor (down or up strokes only) on a medoid switch; 10 sections switch with it.

## A2: mute tie-break

Refuted and dropped. Over 68 sections the medoid and majority differ only by mutes in four; a tie-break at 0.01 fires on two (Summer of '69 bars 4-19, Fame 85-100) and in both the majority already has fewer mutes. The motivating range, The Cars 52-60, scores 0.633 against 0.616 (gap 0.017, so a 0.01 margin does not fire) and is not a planned section; its planned section 52-68 already votes `DUDUDUDU`.

## A4: member threshold

All nine members of the three merged sections, each member's hybrid-rule pattern against its section's pattern (Jaccard on strike slots):

| Section | Member | Member pattern | Section pattern | Agreement |
|---|---|---|---|---|
| Wet Leg Verse 4 | 58-65 | `D-DU-UDU` | `DUDUxxDU` | 0.69 |
| All Fired Up Verse 1 | 28-33 | `DUxxxUxU` | `DUDUDUDU` | 0.75 |
| All Fired Up Verse 2 | 55-61 | `D-Dx-U-U` | `D-D-D-DU` | 0.43 |
| All Fired Up Verse 2 | 90-97 | `xxxxxxxx` (medoid) | `D-D-D-DU` | 0.31 |
| All Fired Up Verse 2 | 97-104 | `xxDxDxDx` | `D-D-D-DU` | 0.50 |
| All Fired Up Verse 2 | 104-110 | `Dxxxxxxx` | `D-D-D-DU` | 0.375 |

The spec's first draft said 0.57 and 0.24 for 55-61 and 90-97; those were the medoid's agreement (not picked by the hybrid rule) and a leave-one-out score, not an agreement. At the draft threshold of 0.5, 55-61 would have printed its own `D-Dx-U-U`, which the ear rejected. The ear wants 55-61 and 104-110 on the section's pattern and 90-97 on its own, so the threshold moved to 0.35 (band 0.31 to 0.375).

## A5: ring band

2,114 measurable strokes (gap of at least 1.5 slots) across the eight songs, decay in the first slot after the peak, 2 dB bins from 0: 764, 461, 242, 128, 74, 91, 90, 49, 43, 46, 32, 24. The 6 to 10 dB band holds 202 strokes (9.6%), 151 of them on the three sixteenth-grid songs; they are not ghost strokes (peaks at +0.2 dB against the song median). Song medians: Summer of '69 2.0, Chelsea Dagger 2.6, Pour Some Sugar On Me 2.1, Wet Leg 1.8, Fame 8.3, All Fired Up 2.0, Need You Tonight 8.7, The Cars 2.7. A per-stroke cut at 8 dB would have marked 47% of Need You Tonight's strokes as ringing. The decision moved to the section median with the threshold at 5 dB per slot, in the gap between 2.7 and 8.3.

## A14: pages

Geometry measured from the 1.5 sheets (content height 269 mm, chord cell 10.08 mm, row pitch 11.58 mm, example strip 23.8 mm, preamble 70 to 112 mm); a paginator on those blocks reproduces all eight 1.5 page counts. For 1.6 a bar box is assumed 1.6 cells plus a 1.5 mm gap (17.6 mm per line), a riff line 1.5 times that, Need You Tonight's verses and choruses the riff lines.

| Song | Bars (split) | 1.5 pages | Lines four-per / eight-bar rule | Pages four-per / eight-bar rule |
|---|---|---|---|---|
| Summer of '69 | 120 (0) | 2 | 34 / 20 | 4 / 3 |
| Chelsea Dagger | 142 (9) | 3 | 39 / 26 | 4 / 3 |
| Pour Some Sugar On Me | 103 (23) | 2 | 28 / 28 | 3 / 3 |
| Wet Leg | 109 (1) | 2 | 30 / 18 | 3 / 2 |
| Fame | 100 (6) | 2 | 28 / 28 | 3 / 3 |
| All Fired Up | 156 (4) | 2 | 41 / 25 | 4 / 3 |
| Need You Tonight | 84 (10) | 2 | 24 / 24 | 3 / 3 |
| The Cars | 101 (15) | 3 | 28 / 22 | 3 / 3 |

With the eight-bar rule five songs gain one page and none gains two; without it two gain two. The rule does nothing on the sixteenth-grid songs, whose headroom before another page is 69 mm (Need You Tonight), 101 mm (Pour Some Sugar On Me) and 106 mm (Fame); at a bar-box factor of 2.0 all three and Wet Leg reach two pages more.
