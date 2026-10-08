# Review: per-section strum pattern vote, its certainty test, and stroke direction

Read: `music/vote.py`, `music/as_played.py`, `music/members.py`, `stages/strums.py`, `onsets.py` `direction_for_slot`, `evaluate.py`, `tests/test_vote.py`, both listening passes, the pattern-vote spike and `strum_pattern_and_direction.md`. Figures marked "measured" come from a scratchpad script over the 1.7 `runs\*\04_strums\strums.json` files (holding bars' `bar_onsets`, D/U folded to S) that recomputed the vote, the shuffle p, a circular-shift p and a bar-bootstrap winner stability.

## A. Diagnosis

### A.1 Failures the vote causes or worsens

**Need You Tonight 8-12 (1.7 clip 10, "no, it's one, two, three ... and then 9 notes twice as fast"; printed certain two-bar `D---D---D---D---` / `D-D---DU---U---U`, 1.6 printed one grey down stroke).** Three mechanisms stack:

1. `vote.py` `_pairs` (line ~118) builds pairs with `range(phase, len(bars) - 1, 2)`: on five bars it yields pairs (8,9) and (10,11) and **drops bar 12** (`SSS-S-S-S-xSxS-S`, the only bar where the fast run was detected) from the vote entirely.
2. `as_played.py` `majority_vector` (line 72) keeps a slot when `strikes > threshold * n` with `STRIKE_SHARE = 1/3`. With two pairs, `n == 2`, so `1 > 0.667` is true: **the "majority" of two pairs is their union.** Measured: the printed first half is exactly bar 8 ∪ bar 10 and the second half bar 9 ∪ bar 11.
3. `as_played.py` `chance_p` (line 160) computes `vote_confidence(bars)`, which re-votes the **one-bar** topped vote; `structure_test` uses `vector` only in the `full_vote` branch. For a unit-2 section the chance test therefore tests a different pattern from the printed one; p 0.007 says nothing about the union on the page. `member_figures` then scores bars against their halves of that union, lifting agreement over the 0.53 floor.

The under-firing is an onsets failure (`strokes.md` section 3); turning five unrepeating bars into a *certain* two-bar figure is the vote's own doing.

**The Cars 72-76 (1.6 clip 25, "not enough clicks"; grey `-UD-D-D-` / `DUD-DUDU`).** Four bars, phase 1, so `_pairs` yields one pair (bars 73, 74) printed verbatim; bars 72 and 75 never enter. `score_majority == score_medoid == 0.909` because a one-element vote is its own medoid. Grey only because p was 0.067.

**Chelsea Dagger intro 7-19 (1.7 clip 9, "the clicks do not fit"; certain `D-xxxUx-`, 1.6 grey).** The eleven holding bars are heterogeneous: `-----S--`, `--------`, `----S--S` (bars 7, 9, 12, holding at ratios 0.050 to 0.062) beside stab bars like `S-x-xx--`, `x-x-x-x-`. Measured: majority 0.43, medoid 0.42, confidence 0.49 against `UNCERTAIN_BELOW` 0.45, shuffle p 0.001. The mute classes are an onsets question (`mute_mask` on stabs). The vote's part: `_vote_member` (`strums.py` 216-227) prints certain whenever confidence clears a point floor and the shuffle test passes, with no notion of how many bars support the vector or how close the runner-up is. 1.6 was grey only because resting bars 0-6, 10, 11 dragged confidence down; 1.7 removed them (spec 5), fewer bars voted, certainty rose: the "fewer bars per decision" effect the research note attributes to Yousician.

**Need You Tonight 24-31 (1.6 clip 23, "syncopation when it does not exist").** Unit 2 fired at `PERIOD2_MARGIN` 0.10 on detector noise (the fast run is detected in alternate bars); the period rule amplified under-firing into a figure.

**Summer of '69 53-58 (clip 14) and 31-41 (clip 13).** The medoid picks the densest bar: 53-58's is `SS-S-SSS`, six strikes against a median of five, because Jaccard rewards a bar that covers every slot any other bar strikes (the spike measured +0.86 strikes for the medoid, +1.36 for the majority). The density itself is onsets.

**All Fired Up member 90-97 (clip 27, "completely, hilariously, wrong").** Four sparse or empty bars and three all-mute bars; `_topped_vote` prints `xSSxxxx-`, p 0.97, grey. The vote cannot say "two kinds of bar"; it prints a blend of neither.

### A.2 Failures that belong to the onsets reviewer

Density at twice the heard rate (Summer of '69 53-58, 95-111 tail, Fame 61-71 and 71-81), re-attacked long tones (Summer of '69 31-41), under-firing on fast runs (Need You Tonight 8-12, 24-31), stabs and sustained strums classed as mutes (Chelsea Dagger 7-19, All Fired Up 90-97), riffs printed as strums (Summer of '69 outro, Day Tripper, Wet Leg 58-65, All Fired Up 97-104), two parts on one stem (Fame, Pour Some Sugar On Me 67-77, Cream). No vote repairs a wrong strike grid; the vote's job is to refuse certainty when the bars disagree.

### A.3 What the within-bar shuffle test actually tests

`chance_p` permutes each bar's cells independently, keeping its strike and mute counts, and asks how often a majority vote over such copies fits its bars as well as the real vote does. It tests **"do strikes land on consistent slot positions across bars"**. Any passage with a stroke on beat 1 of most bars passes, including Chelsea Dagger's stabs (slot 0 struck in 7 of 11 bars, slot 2 muted in 8). It does not test whether the printed vector is right among near alternatives, nor whether enough bars support it. Measured: a circular-shift null gives p within 0.03 of the shuffle p on all ten sections checked and flips no verdict, so swapping nulls buys nothing. What it does well: All Fired Up 90-97 (p 0.97) and Summer of '69 53-58 (p 0.33) correctly fail.

## B. Suggestions, ranked by benefit to the reader

### B.1 Minimum support and an honest small-n vote (fixes the unit-2 mechanics)

Files: `music/vote.py` `unit_and_phase`, `_pairs`, `choose_pattern`; `music/as_played.py` `majority_vector`, `chance_p`, `structure_test`; `stages/strums.py` `_vote_member`.

- `unit_and_phase`: unit 1 unless the pairing covers at least `PERIOD2_MIN_PAIRS` full pairs (3 is the smallest count at which `majority_vector` is a real majority; band in D.1).
- `majority_vector`: a floor `strikes >= MIN_SLOT_SUPPORT` (2), so a slot seen once never prints; unchanged at n ≥ 6, stops the union at n ≤ 3.
- `chance_p`: take `unit` and `phase` and shuffle within the voted units, so the statistic is the printed vote's.
- Write `voted_bars` and `dropped_bars` to `SectionPattern`, so `evaluate` shows support; a member voted on fewer than `MIN_VOTE_BARS` prints grey.

Addresses: Need You Tonight 8-12 certain, The Cars 72-76, part of Need You Tonight 24-31 and Chelsea Dagger 7-19. Research: fewer bars per decision raises Yousician's discontinuity, and a transition cost beat a larger margin (https://arxiv.org/html/2510.05756v1); Dixon's cluster size as reliability (https://archives.ismir.net/ismir2004/paper/000165.pdf). Risk: the unit-2 passes (Summer of '69 4-19, 75-83, 95-111) have 8 to 16 bars and keep three or more pairs; Wet Leg 26-32, Chelsea Dagger 61-71, Need You Tonight 13-24 and All Fired Up 55-61 are unit 1 with n ≥ 6. Generality: constants are counts. Install: none.

### B.2 Certainty from a top-two margin over distinct candidates, plus the existing structure test

Files: new `music/candidates.py`; `vote.py` `choose_pattern` returns the ranked list; `as_played.py` gains `TOP2_MARGIN`; `_vote_member` combines.

Candidate set per member: one-bar majority and medoid, two-bar majority and medoid (when B.1 allows), de-syncopated root (B.4), and the two best *distinct* real bars. Score every candidate against every voted bar with one distance (B.3) and sum. Certainty requires the structure test (as now), the support floor (B.1), and a gap between the best and the best *different* vector above `TOP2_MARGIN`. The gap must be between distinct vectors: measured, `score_majority` versus `score_medoid` does not separate (ear-right 0.03 to 0.05, ear-wrong 0.00 to 0.05) because both rules often return the same bar.

Addresses: every "certain but wrong" case, and gives grey a meaning ("two readings fit about equally"). Research: Yousician's Viterbi score gap; Holzapfel's mutual-agreement confidence (https://www.inesctec.pt/pt/publicacoes?page=3357); the research note's inference that the top-two margin is the cheap signal the pipeline lacks. Risk: Chelsea Dagger 61-71 (medoid 0.57 vs majority 0.52) could go grey under a tight band; it is in the regression set. Generality: the band is measured pooled across all judged sections (D.3). Install: none.

### B.3 Cluster-then-prototype with a swap or chronotonic distance

Files: new `music/rhythm_distance.py` (`swap_distance`, `chronotonic_distance` on 8/16-cell strings, mutes as strikes for rhythm); `vote.py` `medoid`, `best_pair` take a distance; new `cluster_bars` (agglomerative, `scipy.cluster.hierarchy`, already installed with librosa) returning the largest cluster and its share.

Vote on the largest cluster only; its share becomes a support figure for B.2; a member whose largest cluster is under half its bars prints grey as "mixed playing". Addresses: All Fired Up 90-97 (two kinds of bar), Chelsea Dagger 7-19 (near-empty bars versus stabs), the medoid's pull to the densest bar (Summer of '69 53-58), since a one-slot push costs one swap rather than two Jaccard errors. Research: Dixon, Gouyon and Widmer's k-means then largest cluster "to remove outliers", and their warning that point-wise distances penalise "peaks which almost match as heavily as peaks which are far from being aligned" (https://archives.ismir.net/ismir2004/paper/000165.pdf); Toussaint's swap and chronotonic measures (https://archives.ismir.net/ismir2004/paper/000134.pdf); k-medoids' robustness to outliers (https://arxiv.org/pdf/1509.00692). Risk: Need You Tonight 13-24 and Wet Leg 26-32 have one dominant cluster and must not move; Summer of '69 75-83 alternates by design, so clustering runs on the voted units after B.1. Generality: no k per song; cut the dendrogram at a pooled distance band. Install: none.

### B.4 De-syncopation vote: root pattern first, pushes second

Files: new `music/syncopation.py` (`desyncopate(bar, slots_per_bar, meter)` per Sioros and Guedes: an onset on a weak slot followed by a silent stronger slot moves forward, never past another onset); `vote.py` votes the root, then per strong slot whether its anticipation is the majority, and re-applies the winning pushes.

Addresses: "majority erases pushes, medoid keeps the wrong ones" (the spike: 0.59 pushes per bar played, 0.25 kept) without inflating strike count, and gives B.2 a candidate that is a real pattern rather than a union. Research: https://bpb-us-e1.wpmucdn.com/wp.nyu.edu/dist/4/23414/files/2022/01/SiorosGuedes2014.pdf. Risk: Need You Tonight 13-24's pushes are the figure; the push vote must keep a push most bars play. Generality: meter-driven weights only. Install: none.

### B.5 Switch cost between adjacent members and sections

Files: `stages/strums.py` after `_vote_member`: when a member's best candidate beats the previously printed pattern, scored on this member's own bars, by less than `SWITCH_MARGIN`, print the previous. Generalises `MEMBER_AGREE` (0.35 rests on one section, A4) into a scored decision. Addresses: All Fired Up Verse 2's three styles of one figure; Fame's medoid flips. Research: Yousician's transition cost (https://arxiv.org/html/2510.05756v1). Risk: Summer of '69 75-83 and 95-111 are adjacent and genuinely different. Ranked low because most adjacent-section failures here are onsets failures. Install: none.

### B.6 Stroke direction: do not measure; say so on the sheet

The research finds one audio-only accuracy on real strumming, about 70 to 72 % (https://publikationen.bibliothek.kit.edu/1000183784); the ISMIR 2025 CRNN at 85.5/79.0 down/up on clean phone audio with no released model (https://arxiv.org/html/2508.07973v1); Barbancho's cue in the first 11 to 55 ms of the strum, which Demucs smears (https://archives.ismir.net/ismir2014/paper/000130.pdf); and a re-entrant ukulele breaking the low-to-high cue. `direction_for_slot` (parity) is the alternation baseline every paper beats, but nothing installable beats it here. Keep parity and change what the sheet claims: a legend line on every sheet, "Arrows follow the hand: down on the beat, up between; direction is not read from the recording", plus the README limitation. Optional: `render_directions` prints arrows only on certain rows and plain stroke marks on grey rows, so grey never carries a direction claim. Install: none.

### B.7 Enabler: a pattern score in `evaluate.py`

`evaluate.py` reports confidence, p and candidate but no agreement with ear truth. Add `truth/<song>/patterns.txt` (bar range, verdict YES/MOSTLY/NO, the heard figure where given) and a `--patterns` report: per judged range, printed-versus-heard Jaccard and swap distance, support, margin, and pattern discontinuity (changes per bar, Yousician's readability metric). Every criterion in C reads from this.

## C. Success criteria

Ground truth: the 25 judged ranges in 1.6 clips 12-29 and 1.7 clips 9-14 (10 YES/MOSTLY, 15 NO) entered in `truth/*/patterns.txt`, plus 12 new ranges of four to eight bars labelled by ear before tuning (four from AC/DC, Cream and Day Tripper, eight from sections whose row never changed and so were never judged, such as All Fired Up 33-49 and The Cars 11-19). Regression set (print and certainty must not change): Summer of '69 4-19, 75-83, 95-111; Chelsea Dagger 61-71; Need You Tonight 13-24, 79-86; Wet Leg 26-32; All Fired Up 55-61, 33-49, 61-90, 128-132; The Cars 11-19, 68-72.

| Suggestion | Metric | Threshold | Regression check |
|---|---|---|---|
| B.1 | sections printed certain whose ear verdict is NO ("false certain"), over all judged ranges | 0 of the 15 NO ranges certain (today 2 in 1.7 plus Need You Tonight 24-31); grey count on YES ranges unchanged | every regression range prints the same vector and certainty; unit-2 YES sections keep unit 2 |
| B.2 | false certain, and "false grey" (YES ranges printed grey) | false certain 0; false grey at most 1 of 10 | as above; Chelsea Dagger 61-71 stays certain |
| B.3 | swap distance printed-versus-heard on ranges with a heard figure; largest-cluster share on NO ranges | median swap distance falls against the 1.7 rows; All Fired Up 90-97 and Chelsea Dagger 7-19 report share under 0.5 and print grey | regression ranges' largest cluster holds at least 0.7 of bars and the prototype equals today's vector |
| B.4 | pushes kept per bar versus bars' mean (spike: 0.59 played, 0.25 majority) on the regression set; strikes per printed bar versus median bar | printed pushes within 0.15 of the bars' mean; density inflation under +0.3 strikes | Need You Tonight 13-24 vector unchanged |
| B.5 | pattern discontinuity (changes per printed bar, whole song) | falls on All Fired Up and Fame with no new NO on judged ranges | Summer of '69 75-83 and 95-111 still differ |
| B.6 | none measurable; legend present on every sheet | rasterised pages show the line | n/a |

A threshold is accepted only if it sits on a flat region of the pooled curve with leave-one-song-out: drop each song, refit the band, and the band must still contain the chosen value.

## D. Spikes before a plan

1. **Unit-2 support.** Over the eleven run folders, for every `unit == 2` member: pairs voted, bars dropped by `_pairs`, whether the printed vector is the union of its pairs. Confirms B.1 if every ear-NO unit-2 section has ≤ 2 pairs or a union and every ear-YES one has ≥ 3; kills the 3-pair constant if a YES section has 2.
2. **Chance test on the printed vote.** Recompute `chance_p` with pair-level shuffles; list certainty flips against verdicts. Confirms if Need You Tonight 8-12 goes grey and no YES section flips.
3. **Top-two margin band.** Gap between the best candidate and the best distinct vector, under Jaccard and swap distance, plotted against the 25 verdicts. Confirms B.2 if a band separates with at most one YES lost; kills it if YES and NO overlap throughout (the majority-versus-medoid gap already fails this).
4. **Cluster share.** Agglomerative clustering on swap distance per member. Confirms B.3 if the largest-cluster share is under 0.5 on All Fired Up 90-97 and Chelsea Dagger 7-19, over 0.7 on every regression range, and the prototype equals today's vector there.
5. **Swap-distance medoid.** Re-run the spike's ten sections: strikes added over the median bar, and the printed bar for Summer of '69 53-58. Confirms if inflation falls below the Jaccard medoid's +0.86 with no regression vector moving.
6. **Pair-preserving bootstrap.** Measured: bootstrapping over bars gives winner stability 0.00 to 0.06 on every unit-2 section because resampling breaks phase, and one-bar sections overlap (NO 0.02 to 0.29, YES 0.29 to 0.49). Resample voted units instead; keep it only if YES and NO separate, else rely on D.3.
7. **Support in bars versus share.** Chelsea Dagger 7-19 has 11 holding bars and is wrong, so a bar floor alone will not catch it; plot bar count and cluster share against verdicts to decide which carries support.

## E. Do not do

- Audio stroke direction: no released model, about 70 % audio-only on clean solo guitar, the cue is destroyed by separation and weakened by re-entrant tuning.
- A fixed beginner-pattern vocabulary: the round-2 spike found records do not play them; Yousician's 924 patterns are proprietary and its flat prior over patterns "did not help".
- Fine-tuning a MERT strum detector: the training data is proprietary and the head unreleased.
- Replacing the shuffle null with a circular-shift null: measured within 0.03 p on every section, no verdict changes.
- Bootstrap over bars for unit-2 votes: stability is zero by construction (D.6).
- Tuning `HYBRID_DELTA` or `PERIOD2_MARGIN` alone: both rank the same noisy statistic; Yousician found a switch cost beat a larger margin, and the errors here are support and union errors, not margin errors.
- The spike's "prefer fewer mutes" tie-break: it rests on one section (The Cars 52-60).
- A supervised mute classifier from IDMT or Stefani data for the stab-versus-mute problem: solo-guitar training, never validated on stems, non-commercial or GPL licences; that is the onsets reviewer's area in any case.
