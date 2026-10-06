# Spike: how a section's strum pattern is chosen (2026-10-05)

Throwaway scripts: `%TEMP%\claude\...\scratchpad\spike-pattern-vote\` (candidates.py, summarise, hybrid.py, sustain). Data: the eight kept 1.5 run folders under `runs\` (68 planned sections).

## Question

The strums stage prints the slot-wise majority vector over a section's bars. The 1.5 listening pass heard that rule flatten syncopation (Summer of '69 53-58, All Fired Up 55-61) and make strokes equal where the playing is not. Does choosing a real bar (the medoid) fix that without breaking the patterns the ear passed?

## Findings

- The recomputed majority equals the printed pattern on 68 of 68 sections. The majority is an actual played bar on only 30 of 68.
- The medoid (the real bar with the highest mean Jaccard agreement to the section's other bars) differs from the majority on 43 of 68: 20 by one slot, 8 by two, 8 by three, 7 by four or more.
- Like for like (medoid against the other bars; majority leave-one-out), the medoid is better on 30, worse on 34, tied on 4; mean difference +0.021. No systematic winner.
- The majority is denser than the median bar on 47 of 68 (mean +1.36 strikes); the medoid +0.86. Slot-wise voting inflates strike count.
- Pushes (strokes anticipating the beat): bars average 0.59 per bar; the majority keeps 0.25, the medoid 0.44. In the 23 sections averaging at least 0.75 pushes, the majority has none in 11, the medoid in 4. Slot-wise voting erases syncopation.
- Two-bar period: lag-2 minus lag-1 similarity has median +0.034 and 90th percentile +0.204; the two-bar medoid wins by at least 0.10 on 7 sections, several of which are sparse-busy alternations in intros and outros rather than two-bar figures.

## Against the ear truth

| Range | Ear | Majority | Medoid | Verdict |
|---|---|---|---|---|
| Summer of '69 53-58 | `DU-UDUDU` wrong, syncopated eighths | `DU-UDUDU` (0.58) | `DU-U-UDU` bar 55 (0.63, two pushes) | medoid |
| All Fired Up 55-61 | `D-Dx-U-U` wrong | 0.42 | `D-DxDU-U` 0.44; closer to Verse 2's pattern (0.57 vs 0.43) | neither; bars heterogeneous |
| All Fired Up 33-49 | `DUDUDUDU` right | right | `D-DUDUDU` | majority |
| All Fired Up 61-90 | `D-D-D-DU` accepted | right (0.55) | `D-D-D-D-` (0.54) | tie |
| All Fired Up 128-132 | `D---DUD-` right | right (0.46) | `DU--DUD-` (0.40) | majority |
| All Fired Up 90-97 | sparse sustained | `xUDxxxx-` 0.24 | `xxxxxxxx` 0.34 | neither; no slot rule fits |
| Need You Tonight 13-24 | perfect | 0.79 | 0.82 (bar 14) | both |
| The Cars 11-19 | right | `DUDUDUDU` 0.96 | same | both |
| The Cars 52-60 | `DUDUDUDU` right | `xxDUDUDU` 0.63 | `DUDUDUDU` 0.62 | medoid (mutes) |
| The Cars 68-72 | `-UDUDUD-` right | right 0.80 | `DUDUDUD-` 0.67 | majority |

Scorecard where they disagree: majority 3, medoid 2, neither 3.

## Hybrid rule: majority unless the medoid beats it by delta

| delta | sections switched | ear ranges switched |
|---|---|---|
| 0.00 | 25 | S69 53-58, AFU 33-49 (regression), AFU 55-61, AFU 90-97, NYT 13-24 |
| 0.03 / 0.04 / 0.05 | 17 / 14 / 10 | S69 53-58 (good), AFU 90-97 (both bad) |
| 0.08 | 7 | AFU 90-97 only |

Delta 0.03 to 0.05 catches the syncopated verse and leaves every ear-correct majority alone. The Cars 52-60 (medoid right, mutes wrong) is not caught at any delta of 0.03 or more (like-for-like gain -0.01); it needs a tie-break: when the two candidates are within 0.01, prefer the one with fewer mute slots. That rests on one section.

## Sustain

Ring measured as RMS decay after each detected onset on the guitar stem.

- On the distorted-rock stems (All Fired Up, Summer of '69, The Cars) the level never falls 12 dB before the next stroke; "ring until cut" saturates at the gap and cannot tell All Fired Up 90-97 (sparse, sustained) from 33-41 (dense). Those differ by density, not decay.
- Decay over the first slot after the peak is the usable signal. Medians: 3.3 dB (AFU 90-97), 2.2 (AFU 33-41), 2.2 (AFU 61-69), 1.0 (AFU 128-132), 2.0 (S69 53-58), 2.1 (Cars). Need You Tonight 13-19 (muted funk): 13.5 dB per slot (quartiles 10.9 to 17.8), ring median 1.09 slots of a 2-slot gap.
- Pooled, the decay is bimodal: 51 strokes under 6 dB per slot, 21 over 10, none between on these sections.

A per-stroke "rings" flag at a threshold between 6 and 10 dB per slot separates muted from ringing playing. Whether a ringing stroke is held is then a matter of the empty slots after it: a ringing stroke followed by empty slots is drawn as held through them.
