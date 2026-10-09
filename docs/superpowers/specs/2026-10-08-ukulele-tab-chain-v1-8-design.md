# Ukulele tab chain, version 1.8: four defects fixed, certainty earned, and the sheet says what it did not measure

Date: 2026-10-08. Amends the 1.7 spec (`2026-10-06-ukulele-tab-chain-v1-7-design.md`) section 5 (rests), the 1.6 spec sections 4.1 to 4.5 (the vote and certainty) and 3.2 and 3.5 (header phrases, legend), the 1.5 spec section 6 (key), and the ingest stage. Everything not named here stays as 1.7 built it. Research for this version: `reports/Weak music measurements research.md` (the synthesis of eight research notes) and the seven reviews under `research_notes/Weak music measurements research/review_*.md`, which compared that research with the code and the ear-truth records; the figures quoted below are theirs unless the assumptions section says the assumption pass re-measured them.

## 1. Goal and scope

The 1.6 and 1.7 listening passes left three kinds of fault on the sheet: rows printed certain that the ear rejects, rows that follow the wrong instrument, and a header that names the wrong key or the wrong artist. The reviews traced four of these to defects rather than to tuning: the rest rule measures a different window from the one the strokes are counted in; a two-bar vote over two pairs prints the union of its bars and tests the certainty of a different pattern; on one blind song the separator put the bass on the guitar stem and nothing noticed; and the key's candidate gate excluded the published tonic before any vote ran. Version 1.8 fixes those four, makes certainty a claim the data can support, and adds to the page and the harness the honesty the research recommends: say what was not measured, and measure what is claimed.

Version 1.8 therefore:

- **Measures rests on the window the strokes are counted in**, and prints a pickup bar as the partial bar it is (4).
- **Earns certainty.** A two-bar vote needs enough pairs to be a majority; a slot printed must be struck in at least two bars; a vote on fewer than four bars prints grey; and removing resting bars may not create certainty (4.4, 5). The nearest rival's score is measured and written for the harness, since the assumption pass found no margin that separates heard-right from heard-wrong patterns.
- **Notices a stem that carries the bass** and prints that section grey under "guitar not separated here" instead of a riff flag and the bass line's strokes (6).
- **Lets the chord set veto the tonic** when every chord fits another key far better, hedging with the relative key (7).
- **Resolves title and artist from evidence in order**, so an uploader is never printed as the artist unless the channel is the artist's (8).
- **Says on every sheet what is not measured**: stroke length and stroke direction (3.1).
- **Gives the harness ear truth to score against**: pattern, riff, rest, key and credit truth files, and the metrics the research uses for each, so this version and the next two are judged by numbers before the ear is asked (9).

Out of scope, each with its own version: the onset detector, strike density and the recall gate (1.9; `review_onsets_and_density.md`); the riff test, its texture features and the tab gate (1.10; `review_riff_versus_strum.md`); part assignment within one stem and stroke length (10), and AcoustID (8.4). Nothing in this version changes `grid.json`, the chord events, the onsets or `bar_onsets`.

Package version 0.9.0. Schema version 2 stays for `strums.json` and `score.json`; every new field defaults, so 1.3 to 1.7 files load.

**Generality (owner's rule, 2026-10-04).** The validation songs are where patterns are learnt, never what the program is built for. No code path, constant or test may depend on which song is processed; every constant sits inside a band measured across every available section, and the constants whose band rests on one or two examples are named in section 13: the bass-on-stem gate's low-share floor (A5, one positive song, a band 0.086 wide), the two-bar pair floor (A4, band 3 to 4), and the set-veto margin (A7, one positive song with a wide gap). Two rules the reviews proposed were dropped by the assumption pass because no constant separated the cases: the attack-rise tail test (A2) and the top-two certainty margin (A3).

## 2. What the research and the reviews established

| Fact | Source | Consequence here |
|---|---|---|
| `bar_energy_ratio` slices the exact bar; `quantise_bar` and `recall.bar_index` shift the window back half a slot. Chelsea Dagger bars 7 and 12 (ratios 0.050, 0.062) hold all their energy in the last eighth, the anticipated stab of the next bar. The assumption pass found that the full half-slot shift also pulls the previous bar's ringing last stroke into slot 0 and un-rests three confirmed rests; the window that keeps every confirmed rest and every confirmed playing bar is the bar trimmed by half a slot at its end only. | rests review A; assumption pass A1 | 4.1 |
| Summer of '69's bar 0 is a one-beat pickup (0.02 to 0.44 s); the stem is digital zero until 0.38 s and its first attack is bar 1's downbeat. The ear's "from the start" is right about the music; no guitar is inside bar 0. Of the six pickup bars on the eleven grids, four are played (All Fired Up, You Shook Me, Fame, Badge) and two are counting conventions (Summer of '69, The Cars). | rests review A; assumption pass A10 | 4.3: a pickup bar prints as a partial bar with whatever it holds |
| Six ear-confirmed tail bars carry 3 to 8 detected onsets each from flux on near-silence and rest only because their ratios happen to sit under 0.05. The assumption pass found no attack statistic separates them from playing bars: tails decay into digital silence where separator artefacts re-rise 16 to 38 dB, while densely strummed bars have flat slot profiles (median rise 4 dB); a decay-shape variant fails on whole-note playing bars. HPSS does not separate them; whole-bar max-pooling un-rests two confirmed rests. | rests review A, D; assumption pass A2 | 4.2: no tail rule; the floor keeps deciding |
| `_vote_member` computes confidence and the chance test on holding bars alone; Chelsea Dagger's intro went from 21 bars to 11 at confidence 0.49 and flipped to certain and wrong. | rests review A | 4.4 |
| With two pairs, `majority_vector`'s `STRIKE_SHARE` 1/3 keeps any slot struck once: the printed two-bar "majority" of Need You Tonight 8-12 is bar 8 ∪ bar 10 over bar 9 ∪ bar 11, verified cell by cell; `_pairs` dropped bar 12; `chance_p` re-voted a one-bar vector, so p 0.007 tested a pattern that did not print. | vote review A | 5.1 and 5.2 remove the union; 5.3 records what the test means |
| The within-bar shuffle test asks whether strikes land on consistent slots across bars, which nearly any strummed passage passes; it does not test the printed vector against its nearest rival or whether enough bars support it. A circular-shift null changes no verdict; a pair-level null reads p 0.001 to 0.002 on every two-bar member and discriminates nothing. | vote review A; assumption pass A4 | 5.3: the bar-level test stays and is read for what it tests |
| The majority-versus-medoid score gap does not separate ear-right from ear-wrong sections (both 0.00 to 0.05); a bar bootstrap on two-bar votes has zero stability by construction; and a top-two margin between distinct candidate vectors overlaps too (YES −0.026 to 0.014, NO −0.021 to 0.038 under Jaccard; the same under swap distance), because in 13 of 24 judged ranges the runner-up differs by one cell. | vote review; assumption pass A3 | 5.5: the margin is written for the harness, not used for certainty |
| No installable model beats the parity rule for stroke direction on separated stems; the cue is the first 11 to 55 ms of the strum, which separation smears, and re-entrant tuning weakens it. | vote review B.6, research | 3.1: a legend line, direction stays parity |
| Cut and ringing overlap on every decay statistic; clipping holds the level flat; `RING_MIN_GAP_SLOTS` leaves 50 to 92 % of strokes unmeasured; no product prints let-ring from audio. | stroke-length review A | 3.1: a legend line; the feature stays withdrawn |
| On Badge, htdemucs_6s put the chord guitar on the bass stem for bars 0-4 and the real bass on the guitar stem from bar 5: the guitar stem takes 0.75 of the mix's energy below 250 Hz under Verse 1 and 0.87 of its own energy is below 250 Hz; the bass stem holds 0.001 to 0.011 of the mix per section. Every other voiced section on ten songs has own low share at most 0.55 and a bass stem at or above 0.18 outside intros. The cross-stem least-squares bleed score cannot fire because the bass stem is empty. | two-parts review A, D1, D2 | 6: a gate on where the low band landed, not a bleed estimate |
| Badge's published tonics G and E were never candidates: `TONIC_MIN_SHARE` 0.2 admitted only D (0.339) and A (0.208). Re-scoring the stored chords over all twelve diatonic sets gives G 0.995 against D 0.756; on every other run the printed tonic's set share is within 0.007 of the best. The set share cannot replace the vote: Fame's best set is B flat by 0.007. | key review A, D1 | 7: a one-directional veto with a margin |
| `IngestStage` replaces yt-dlp's full info with the five fields `resolve_run_dir` kept; `artist` is null on ten of eleven run URLs; `_strip_artist_prefix` refuses to split "The Beatles - Day Tripper" because the head shares no word with "Natan Santos". `uploader_id` tells an artist's channel (`@PatBenatarVEVO`) from a label's or a fan's (`@rhino`, `@goldsongs7948`). | key review A, D3 | 8 |
| The field scores patterns by distance to a heard figure, flags by precision and recall with a majority baseline, rests by per-bar precision and recall with deletions and insertions reported apart, keys by mir_eval's weighted score with its category, all pooled over songs with leave-one-song-out for any constant. | the report's cross-cutting rules, each review's C | 9 |

## 3. The page

Everything about the 1.7 page stands except these points.

### 3.1 Two legend lines

Every sheet's legend gains two lines in the editorial register, verbatim:

- "Stroke length is not measured: hold or damp each stroke as the record does."
- "Arrows follow the hand: down on the beat, up between. Direction is not read from the recording."

They sit with the tab legend line (`TAB_LEGEND` in `render/html.py`) and print on every sheet, not only when tab prints. Nothing on the page is drawn grey or dashed for either claim.

### 3.2 A pickup bar prints as a partial bar

A bar flagged `pickup` in `grid.json` (one with fewer beats than the meter) draws only the slot columns its beats cover, right-aligned in its box, with the "pickup" label as now; a one-beat pickup on an eighth grid shows two slots. Its chord row, its strokes and the rest rule are as for any bar. The count row under a line that starts with a pickup still starts at "1".

**Amended after validation (2026-10-09).** A pickup bar's cells are the full bar's `n` slots spread by the quantiser over its short duration, so full-bar cell `j` maps onto its last `k = pickup_slots` columns by `pickup_column(j, n, k) = n - k + (j * k) // n`; where two strokes land on one column the first keeps it and where two chord starts do the later replaces the earlier, and each mapped stroke's down or up is re-derived from the column it lands on (a muted stroke stays muted), since the legend says direction follows the hand. The count row sits under the line's first full bar (not under the partial box), so it still starts at "1". The "pickup" label sits just left of the partial box's frame rather than inside it, where on a two-column box it overlapped the chord name. A holding pickup bar prints its own quantised onsets (its row of `bar_onsets`) mapped onto its columns, not its member's voted pattern: the mapping is time-correct only for the bar's own row, whose `n` cells the quantiser spread over the pickup's short duration, while the member's pattern is in full-bar time, so squeezing it printed `D U` on pickups where the ear heard one down stroke or silence (the final review, 2026-10-09). A resting pickup bar still prints nothing, its grey still follows its record, and a full bar still prints its member's pattern (1.6 design).

### 3.3 "Guitar not separated here"

The state phrase list of 1.6 spec 3.2 gains one phrase: "guitar not separated here", printed when the longest member of a section fails the gate of section 6. The section's strokes print grey (they are the bass line's rhythm, which may still help a strummer), the chord row stays black, and no riff phrase or label prints for that member. The README's limitations say what it means.

### 3.4 Title, artist and provenance

The header prints the title and artist that section 8 resolves. When a lower rung disagreed with the chosen one, a line in the smaller face follows the artist: "uploaded by <uploader>". On a video whose uploader is the artist's own channel the names coincide and nothing extra prints.

### 3.5 Considered and not taken

Printing plain stroke marks without arrows on grey rows, so a grey row carries no direction claim: not taken, because the legend line now carries the claim for every row and a second mark vocabulary would need its own listening pass. A grey or dashed mark for an unmeasured stroke length: not taken, for the reason the 1.7 spec gave (the sheet never pretends) and because the research finds no precedent for it.

## 4. Rests

The 1.7 rule (a bar holds when `energy_ratio >= REST_RATIO_MIN` and `low_share >= REST_LOW_SHARE_MIN`) stands with these amendments.

### 4.1 The window ends where the quantiser's does

`bar_energy_ratio` and `bar_low_share` slice `[bar.start, bar.end - half)` with `half = (bar.end - bar.start) / slots_per_bar / 2`: the bar line at the start, the quantiser's end. The stage passes `slots_per_bar`. The last half-slot belongs to the next bar's downbeat stroke, which is why the exact bar held Chelsea Dagger 7 and 12 on energy nobody hears in them; the first half-slot before the bar line holds the previous bar's ringing last stroke, which is why the full half-slot shift that `recall.bar_index` uses for onsets is wrong for energy (it lifted slot 0 by 15 to 26 dB and un-rested Wet Leg 18, Pour Some Sugar On Me 15 and 77; assumption pass A1). This is a convention, not a constant. Measured on all 1 201 bars: every one of the 25 ear-confirmed rests still rests, every one of the 98 ear-confirmed playing bars holds, and the rest flags that change against 1.7 are five: Chelsea Dagger 7 and 12 rest; The Cars 63 rests (digital silence; its stored energy was bar 64's downbeat); Pour Some Sugar On Me 80 rests (a lead-in fill that printed three strokes in its last slots, a cost the listening pass judges); and Pour Some Sugar On Me 7 holds at 0.0502, two ten-thousandths over the floor (a bar the published tab calls empty, a cost the listening pass judges). Need You Tonight 7 and Wet Leg 25 read 0.0002 and rest. The ten 1.7 songs' resting-bar count goes from 51 to 54.

### 4.2 No tail rule

The review proposed telling a carried tail from a new stroke by a re-rise in slot energy. The assumption pass refutes it: the six ear-confirmed tail bars read rises of 16 to 38 dB because they decay into digital silence where the separator's artefacts re-rise, while the 98 playing bars read a minimum of 0.6 dB and a median of 4 dB, dense strumming having a flat slot profile. A decay-shape variant fails on whole-note playing bars. No `tail` flag is written; the floor keeps deciding, and the carried-tail bars rest by it as in 1.7.

### 4.3 The pickup bar

Unchanged in the rest rule: a pickup bar holds or rests by 4.1 like any bar; 3.2 prints whatever it holds. Four of the six pickup bars on the eleven grids are played (All Fired Up and You Shook Me a single ringing down stroke, Badge three beats of the riff, Fame a swell with no onset) and print their strokes in a partial box; two are counting conventions (Summer of '69, whose bar 0 is drums only; The Cars, silent until bar 1's downbeat) and print an empty partial box. The 1.7 assumption A4's "wrong rest" on Summer of '69 is re-read as a page fault.

### 4.4 Certainty may not come from fewer bars

`_vote_member` keeps the vote and every figure on the holding bars (resting bars carry no rhythm, and Wet Leg 26-32 became right that way), and also computes confidence and the chance test on the member's full analysed span, as 1.6 read it. The member is uncertain when either reading is uncertain. `SectionPattern` records `confidence_all_bars` and `chance_p_all_bars`. No constant. Expected: Chelsea Dagger's intro and Need You Tonight 8-12 print grey again; every member whose 1.6 and 1.7 certainty agreed is unchanged.

### 4.5 Not changed

`REST_RATIO_MIN` 0.05 and `REST_LOW_SHARE_MIN` 0.005 (the two near-floor bars were a window fault, not a floor fault; Pour Some Sugar On Me 7 at 0.0502 is not a reason to move a floor whose band the 1.7 spec set from Need You Tonight's tab bars at 0.069 to 0.09); the section-level cut; no hysteresis or minimum durations (the data show no flicker, and an energy-only pair would un-rest tail bars that sit just under the floor); no song-relative dB reference (its bands touch at −8 dB and it cannot replace the mix ratio); no max-pooling over the bar.

## 5. The vote and certainty

### 5.1 A two-bar vote needs enough pairs

`unit_and_phase` returns unit 1 unless the pairing covers at least `PERIOD2_MIN_PAIRS` (3) full pairs, the smallest count at which the pair majority is a majority. Band (A4): of the twelve two-bar members on the eleven runs, a floor of 3 demotes exactly Need You Tonight 0-13 (two pairs, bar 12 dropped) and The Cars 72-76 (two pairs); a floor of 4 would also demote Need You Tonight 24-31 and Day Tripper 46-52; every ear-passed two-bar member has four to eight pairs. Bars a pairing leaves out are recorded, never silently dropped: `SectionPattern` gains `voted_bars` (the bar indices the vote read, in order) and `dropped_bars`.

**Amended after validation (2026-10-09).** `unit_and_phase` is shared with `riff_line.py`'s reduction, so the three-pair floor reaches the riff stage's two-bar reduction too, by the same rule and for the same reason; the validation lists every `riff.json` gate figure that moved (`2026-10-08-v1-8-validation.md`), and the one printed tab, Need You Tonight 13-24, is a one-bar reduction and is unchanged.

### 5.2 A printed slot is struck in at least two bars

`majority_vector` keeps a slot only when `strikes > STRIKE_SHARE * n` **and** `strikes >= MIN_SLOT_SUPPORT` (2). It binds only at two voted units (at three, more than a third already means two), so on the eleven runs it changes only the two members 5.1 demotes; it is the rule that stops a union ever printing again.

### 5.3 The chance test stays bar-level, and is read for what it tests

The review proposed shuffling within voted units so that a two-bar member's test is the printed unit vector's own. The assumption pass refutes it: a pair-level null gives p 0.001 to 0.002 on all twelve two-bar members (today 0.001 to 1.0), discriminates nothing, and would blacken Summer of '69 4-19, which the ear passed grey, and Day Tripper 46-52. `chance_p` and `structure_test` stay as 1.7 built them, on the one-bar topped vote with the member's start bar as seed. What they test is recorded in the README's limitation and in `evaluate`'s wording: that the section's strikes fall on consistent slots across bars, not that the printed vector beats its rivals. Certainty's other guards are 4.4 and 5.1 to 5.4.

### 5.4 Support

A member whose `voted_bars` number fewer than `MIN_VOTE_BARS` (4, the existing `MIN_SECTION_BARS`) prints grey whatever its figures say. On the eleven runs this greys one member, Summer of '69's three-bar intro 0-4 (the flagged picked riff), and no other.

### 5.5 The nearest rival is measured, not used

New `music/candidates.py`. For a member, the candidate set is: the one-bar majority and medoid; the two-bar majority and medoid when 5.1 allows; and the two real bars (or pairs) that agree best with the rest. Each candidate is scored by its mean Jaccard agreement with the voted bars (the score `choose_pattern` already uses). The printed pattern is `choose_pattern`'s as today; `top2_margin` is the printed pattern's score minus the best score among candidates whose vector differs from it, and `runner_up_vector` is that candidate. Both are written to `SectionPattern` and printed by `evaluate`; neither decides certainty. The assumption pass measured the margin on the 24 judged ranges (A3): under Jaccard the heard-right ranges span -0.026 to 0.014 and the heard-wrong -0.021 to 0.038, under swap distance -1.6 to 1.8 against -4.6 to 2.9, and the two metrics disagree on which ranges are clear; in 13 of 24 the runner-up differs by one cell. A threshold catching every wrong range would grey every right one. There is no `TOP2_MARGIN`. The figure is kept because 1.9 changes the strikes the candidates are built from, and the band is to be re-measured there.

### 5.6 Not changed

`HYBRID_DELTA`, `PERIOD2_MARGIN`, `MEDOID_MIN_STROKES`, `STRIKE_SHARE` itself, the chance test and its null (a circular-shift null was measured within 0.03 p everywhere; a pair-level null at its floor everywhere), `UNCERTAIN_BELOW`, `EXPLAINED_BELOW`, the member rule and `MEMBER_AGREE`. Stroke direction stays the parity rule (3.1). Cluster-then-prototype on a swap distance, the de-syncopation vote and a switch cost between members (vote review B.3 to B.5) wait for 1.9, where the strikes they vote on change.

### 5.7 Expected effect

Measured in the assumption pass by reconstructing every voiced member's vote from the 1.7 runs (the reconstruction reproduces all 100 members' printed rows exactly; A4). Need You Tonight 0-13 falls to a one-bar vote on five bars, `D-D-D-DUD--UD--U`, grey (confidence 0.503 under the sixteenth floor 0.53); The Cars 72-76 falls to a one-bar vote, `-UD-D-D-`, grey (p 0.067); Summer of '69 0-4 prints grey by 5.4; Chelsea Dagger 7-19 prints grey by 4.4. No other member's vector or certainty moves; the count of certain members falls from 75 to 72 of 100 (Need You Tonight 0-13 and Summer of '69 0-4 by section 5, Chelsea Dagger 7-19 by 4.4; The Cars 72-76 was grey already). The thirteen ear-passed ranges keep their vector and certainty: Summer of '69 4-19, 75-83 and 95-111, Chelsea Dagger 61-71, Need You Tonight 13-24 and 79-86, Wet Leg 26-32, All Fired Up 55-61, 33-49, 61-90 and 128-132, The Cars 11-19 and 68-72. On the 24 judged ranges (8 heard right, 16 heard wrong), the wrong ranges printed certain fall from 9 to 8 and the right ranges printed grey stay 4 of 8: the remaining false-certain rows are onset failures (density at twice the rate, re-attacked long tones) that no vote rule repairs, and are 1.9's.

## 6. The stem that carries the bass

New `music/bleed.py`; the strums stage reads `01_separate/stems/bass.wav` beside the source stem and the mix.

Per planned section, on the STFT power (n_fft 4096, hop 2048) of the mix, the bass stem and the source stem over the section's bars:

- `low_mix_share_bass`: the bass stem's share of the mix's energy below `BLEED_LOW_HZ` (250);
- `low_mix_share_source`: the source stem's share of the same;
- `low_own_share`: the share of the source stem's own energy that lies below 250 Hz;
- `bass_stem_ratio`: the bass stem's RMS over the mix's RMS for the section.

The gate: a section's longest member is `bass_on_stem` when `bass_stem_ratio <= BASS_STEM_MAX` (0.05) **and** `low_own_share >= OWN_LOW_SHARE_MIN` (0.40). Both must hold: the first says the separator found no bass to put on the bass stem, the second that the source stem's content lives in the bass register. Bands re-measured in the assumption pass on all 101 members of the eleven songs, intros and outros included (A5): among members whose `bass_stem_ratio` is at or under 0.05, `low_own_share` reads 0.462 to 0.864 on Badge against at most 0.376 elsewhere (Summer of '69's intro 0-4, a picked riff before the bass enters; the next non-Badge member reads 0.070), so the floor 0.40 sits in a band 0.086 wide held by one member on each side; among members whose `low_own_share` is at or above 0.40, `bass_stem_ratio` reads 0.0007 to 0.0020 on Badge against at least 0.317 elsewhere, so the cap 0.05 has wide margins. No third figure widens the own-share band: the source stem's share of the mix's low band has no band at all, and the stem's spectral centroid separates the same near miss while un-firing Badge's unjudged members. The gate fires on five Badge members, not two: Verse 1 4-28, Chorus 1 34-50, Instrumental 2 50-56, Chorus 2 56-61 and Verse 2 61-70, the same physical condition (the bass stem is empty from bar 4) of which only the two verses were ear-judged; the three others go on the validation's listening list. It does not fire on Badge's bridge arpeggio 28-34 (own share 0.223 although the guitar stem takes 0.867 of the mix's low band): a bright part over the bass hides it from the own-share figure, which is harmless there (the bridge agreed with the published tab) and is recorded as the gate's limit. With Badge held out nothing fires; with any other song held out the constants do not move.

When the gate fires for a member: `_riff_test` returns False for it, `uncertain` is True, the rest rule's low-share test is skipped for its bars (the energy floor still applies), and the score builder prints the section phrase of 3.3 when that member is the longest. Nothing is subtracted from the stem. The figures are written on every member whether or not the gate fires, so the next blind song's band is measurable.

**Amended after validation (2026-10-09).** The gate runs on the member's whole analysed span (the span the section-level cut reads), before the rest rule, so the gate does not depend on which bars rest; a gated member's bars then rest by the energy floor alone, the low-share test being skipped.

Not done: part assignment on a polyphonic note list (two-parts review B2), repetition as the riff-versus-solo cue (B3), any other separator (B4). Fame, AC/DC and Day Tripper have clean bass stems and are untouched by this section.

## 7. Key

### 7.1 The chord set may veto the tonic

After `decide_tonic` returns, `key_and_decision` computes `pair_shares(events, _TONICS)` over all twelve tonics (the diatonic-set share the pair rule already uses). If the best share exceeds the decided tonic's own `pair_shares` value by at least `SET_VETO_MARGIN` (0.10), the tonic is replaced and `decided_by` becomes "set". Two points the assumption pass fixed (A7): the comparison is against the decided tonic's pair share, never against its own major set's share (Pour Some Sugar On Me is C sharp minor; its C sharp major set holds 0.219 while its pair share is 0.793, and the wrong comparison would veto it to E); and because `pair_shares` scores a relative pair alike (Badge's E and G both read 0.995), the replacement tonic is chosen explicitly as the tonic of the best-scoring *major* set over the twelve (G for Badge), not by `_winner`'s pitch-class tie-break (which would name E). The veto is one-directional: it never confirms, only replaces, and the three votes keep deciding everything else. Band re-measured on all eleven runs: Badge 0.238; Fame 0.008 (B flat against F); every other run 0.000; 0.10 sits inside the gap.

### 7.2 Mode and hedge after a veto

`_mode_of` picks major or minor at the new tonic from the stem chroma as now; the hedge names the relative key (E minor for G major, or G major for E minor), because the set cannot separate those two and the published sources for the one case disagree on exactly that pair. On Badge the stem chroma gives major at G with a mode margin of 0.644 (twelve times `MODE_TIE_MARGIN`) and minor at E (0.316), so the sheet prints "G major (or E minor)" (A8). The stem chroma's own 24-way ranking still prefers D major (profile fit 0.790 against 0.687 at G): the key rests on the chord set, which is what the veto says. This is the one case where the hedge names a different mode, since it names a different tonic; the README rule against hedging with the other mode of the same tonic stands.

### 7.3 A hedge names a related key or nothing

New `relation(a, b)` in `music/key.py` (fifth, relative, parallel, other, by pitch-class arithmetic; cross-checked in tests against `mir_eval.key.weighted_score`). The three hedge rungs stand, but a hedge whose other tonic is "other" to the lead and whose margin clears `KEY_HEDGE_MARGIN` is dropped. None of the three printed hedges today (Chelsea Dagger D, Need You Tonight C, Badge A) is "other"; this guards future songs where the mix names an unrelated tonic.

### 7.4 Recorded

`TonicVotes` gains `set_tonic`, `set_share_best`, `set_share_decided` and `decided_by` admits "set"; `tonic_votes_note` and `evaluate` print them.

### 7.5 Not changed

`TONIC_MIN_SHARE` (lowering it alone leaves D first on Badge and yields a two-against-one "D major (or G major)"), the three votes, the mode test, whole-song estimation (already the case). No learned key model: none is pip-installable on Windows with a licence and weights, and the gain would land on "other" errors this project does not make.

## 8. Title and artist

### 8.1 Keep what yt-dlp fetched

`_METADATA_FIELDS`, which exists in both `models/ytdl.py` and `layout.py`, becomes one tuple in `models/ytdl.py` that `layout.py` imports, and gains `artists`, `track`, `album`, `channel`, `channel_id`, `uploader_id`, `release_year`; `resolve_run_dir` writes them all to `source_meta.json`; `IngestStage` merges the fetched details over the download's info dict instead of replacing it. `SourceInfo` gains `uploader`, `channel`, `credited_artist`, `credited_track`, `artist_source` and `title_source` (the rung that decided each), all defaulting to None.

### 8.2 Evidence in order

New `titles.resolve_credits(info) -> Credits(title, artist, title_source, artist_source, uploader)`, called by ingest and by `resolve_run_dir` for the folder name:

1. **Credited.** `track` and `artists` when both are present: the title and the artist.
2. **Title split.** When the raw title splits at its first separator (" - ", " – ", ": ") into a head of at most four words, and no upload-tag word (`UPLOAD_TAG_WORDS`) appears in the head or in the tail outside bracket groups, the head is the artist and the rest the title, both cleaned as today. The tail condition is what keeps "Song - Live at Wembley" whole (the assumption pass found the head condition alone splits it to artist "Song"); its cost is that "Band - Song - Live" also stays whole, which is recorded and accepted. The shared-word requirement of `_strip_artist_prefix` is dropped; the equal-prefix fast path stays.
3. **Channel as default artist.** When nothing split and the channel passes the test of 8.3, the uploader is the artist.
4. **Uploader.** Otherwise the uploader, as today, and `artist_source` says so.

A rung that returns nothing is absent and the next rung decides, silently. A rung below the chosen one that returns a different value (casefolded, tags stripped) is a disagreement: the uploader is recorded, and the page prints 3.4 unless the channel passes 8.3, in which case the upload is the artist's own and the line is withheld (All Fired Up's uploader name is "Benatar Giraldo" on `@PatBenatarVEVO`; no line prints). The `multiple_songs` blanking in yt-dlp's extractor is why absence and disagreement are told apart.

### 8.3 Whose channel

A channel is the artist's own when `uploader_id` or `channel`, casefolded and stripped of non-letters, contains a word of three or more letters from the artist's name, or contains the artist's name with its non-letters removed ("AC/DC" as "acdc", which no three-letter word test can pass), or ends in " - Topic". On the eleven runs: `@PatBenatarVEVO`, `@TheFratellisVEVO`, `@bryanadams` pass; `@rhino`, `@goldsongs7948`, `@GnafUtopie` fail (A9). `uploader_id` is not stored by 1.7 (`source_meta.json` holds five fields and the ingest record no channel field), so the test runs on fresh fetches only; 8.1 stores it from this version on.

**Amended after validation (2026-10-09).** The word test excludes the stopwords "the", "and" and "of", so a "the" inside a handle such as "southern" does not pass "The Cars". Either handle may pass the test. Because a YouTube channel is the uploader, rung 3's test (the channel vouches for an artist that is the uploader) is nearly a tautology, so "uploader" as an `artist_source` appears only when both handles are missing; the artist and the provenance line are the same either way. `provenance` is decided at ingest and stored in the ingest record, not at render.

### 8.4 Not changed

`clean_title`'s tag stripping, quote stripping and shouting rule; the run-folder slug from the resolved title (existing folders are matched by video id, so no folder is renamed). Two test cases change by design: `test_wider_artist_prefix_rule`'s "Of Us - Song" with uploader "Of Them" now splits to artist "Of Us" (replaced by the tag-word cases "Song - Live at Wembley" and "Live - Song", both of which stay whole), and "Pat Benatar - Song" with no artist field now splits to "Pat Benatar" and "Song" (the no-artist assertions in `tests/test_titles.py` change accordingly). AcoustID (pyacoustid, fpcalc, a key, non-commercial terms) is specified as an optional rung in the key review's M3 and not built: rung 2 fixes every case seen so far. shazamio is not added.

## 9. Measurement harness

### 9.1 Truth files

A tracked folder `truth/<run folder name>/` per song (run folders themselves are untracked), beside the existing `beats.txt` and `chords.lab` convention, holding what the ear and the published sources have settled, as plain text with one record per line and `#` comments:

- `patterns.txt`: `start end verdict [figure]`, bar range (0-based, end exclusive), verdict YES, MOSTLY or NO, and the heard figure where the owner gave one (`D-DU-UDU`, one or two bars).
- `riffs.txt`: `start end label`, label riff, strum, mixed, dyad or bleed.
- `rests.txt`: `start end label`, label rest, play, tail or contested.
- `key.txt`: `tonic mode source` and an optional second line for an alternative the sources allow.
- `credits.txt`: `title` on the first line, `artist` on the second.

The 1.6 and 1.7 listening passes, the published-source table and the AC/DC ear truth are transcribed into these files for the eleven songs as part of this version; the transcription is reviewed against the records line by line.

**Amended after validation (2026-10-09).** A `#` starts a comment only at the start of a line or after whitespace, so `C# minor` is a key and not a comment; a truth file with no record line counts as absent (`n/a` in `evaluate`), never as an error. The parsers and scorers live in `truth.py`, so `evaluate.py` does not grow further.

### 9.2 What `evaluate` prints

With `--truth truth/<song>`, in addition to the beat and chord lines:

- **Patterns.** Per judged range: the printed vector, the heard figure, Jaccard and swap distance between them (new `music/rhythm_distance.py`, swap distance after Toussaint), `voted_bars`, `top2_margin`, certainty; totals: false certain (NO ranges printed certain), false grey (YES ranges printed grey), and the song's pattern discontinuity (printed pattern changes per bar).
- **Riffs.** Flag precision and recall over the labelled sections, counting mixed as a hit, with the majority baseline both ways.
- **Rests.** Per-bar precision and recall over labelled bars, false rests (deletions) and false holds (insertions) counted apart, and an event-based F with a one-beat collar on each rest region's edges.
- **Key.** `mir_eval.key.weighted_score` of the printed lead against the truth and its category (same, fifth, relative, parallel, other), and whether the hedge, if any, names a related key.
- **Credits.** Exact match of title and artist after casefold and tag stripping; the rung that decided each.
- **Bass gate.** The four figures of section 6 per section and whether the gate fired.

`evaluate --compare` gains: certainty changes per member with both readings, `voted_bars` changes and bass-gate changes.

### 9.3 Leave-one-song-out

A new `scripts/band_sweep.py` (tooling, not a stage) reads every `truth/` folder and every run, sweeps a named constant over a range, prints the pooled metric curve and, for each song held out, the best value; the spec's constants are accepted when the chosen value sits on a flat region of the pooled curve and every held-out best lies within the band. The assumption pass uses a throwaway version of it; the tracked version is built in this version so 1.9 and 1.10 inherit it.

## 10. Recorded, not changed

- **Onsets and strike density.** The detector, `quantise_bar`, `mute_mask`, the grid choice and the recall gate are untouched; the onsets review's diagnosis (whole-stem normalisation with a fixed delta, every onset a strike, mutes against a song median) and its ranked suggestions are 1.9's spec. The README limitation line on quiet strokes stands.
- **The riff test.** Chroma entropy, the single-pitch-class share and the pitch-change floor are untouched; the riff review's diagnosis (chroma cannot tell a power chord from a note; pitch-change share has no counterpart; repetition should come first) and its suggestions are 1.10's. The 1.7 limitation lines stand.
- **Stroke length.** Withdrawn, now stated on the page (3.1). The one lead the research allows, persistence of pitched structure after the stroke (pyin voicing, flatness, harmonic share referenced to the stroke's own first 50 ms), is a spike on the existing runs that may run during this version's validation as research; it reaches the page only after the two-listener protocol of the stroke-length review's section C.
- **Stroke direction.** Parity, now stated on the page (3.1).
- **Two parts in one stem.** Only the bass-swap gate (6). Fame, AC/DC and Day Tripper print as 1.7 printed them; the README's two-guitar line stands.
- **Separators.** htdemucs_6s stays; `roformer-sw` stays rejected.
- **Chords, beats, bars, onsets, `bar_onsets`, the section plan, `HYBRID_DELTA`, `PERIOD2_MARGIN`, the tab gate**: unchanged. Chords and bars must be byte-identical to 1.7 on every re-run song.

README limitations gain, verbatim: "Stroke length and stroke direction are not measured; the legend says so." and "When the separator puts the bass on the guitar stem, the section prints grey under 'guitar not separated here'; the strokes are the bass line's rhythm." The two-guitar line and the quiet-strokes line stand.

## 11. Data formats, stages, compatibility, tooling

- **strums.json** (schema 2): `BarStrums` is unchanged; `SectionPattern` gains `voted_bars: list[int] = []`, `dropped_bars: list[int] = []`, `top2_margin: float | None = None`, `runner_up_vector: list[str] | None = None`, `confidence_all_bars: float | None = None`, `chance_p_all_bars: float | None = None`, `bass_on_stem: bool = False`, `low_mix_share_bass`, `low_mix_share_source`, `low_own_share`, `bass_stem_ratio` (all `float | None = None`). `bar_onsets` unchanged.
- **score.json** (schema 2): the section state admits "guitar not separated here"; `ScoreBar` is unchanged.
- **chords.json**: `TonicVotes` gains the fields of 7.4; `decided_by` admits "set".
- **ingest.json**: `SourceInfo` gains the fields of 8.1.
- **Stages.** `stages/strums.py` requires `bass.wav`; `music/rests.py` gains the trimmed window; `music/vote.py` and `music/as_played.py` change as 5.1, 5.2 and 5.4; new `music/candidates.py`, `music/bleed.py`, `music/rhythm_distance.py`; `music/key.py` gains the veto and `relation`; `titles.py` gains `resolve_credits`; `models/ytdl.py`, `layout.py` and `stages/ingest.py` as 8.1; `render/html.py` the legend lines and provenance line; `render/bar_svg.py` the partial pickup bar; `evaluate.py` as 9.2; `scripts/band_sweep.py` as 9.3; `truth/` as 9.1.
- **Compatibility.** 1.7 files load with the defaults; a 1.7 `score.json` renders with the two legend lines and no other change. No new dependency: STFT, RMS and pyin are librosa; `mir_eval` and `scipy` are already installed.
- **Version** 0.9.0; README stage table, limitations (10), history; the sample sheet regenerated.

## 12. Validation

Eleven known songs. Eight re-run from the harmony stage (the key veto runs there) with `grid.json` byte-identical to 1.7 and the chord events byte-identical except `TonicVotes`; the three blind-song runs (The Cars, Day Tripper, Badge) re-run from ingest so the credits are resolved from a fresh fetch, with their new `source_meta.json` and ingest record compared with the old. One new blind song chosen by the owner, run from ingest.

Expectations written before the run:

1. `grid.json` and `bar_onsets` byte-identical to 1.7 on all eleven songs; chord events identical except the tonic votes.
2. Rests: Chelsea Dagger 7 and 12, The Cars 63 and Pour Some Sugar On Me 80 rest; Pour Some Sugar On Me 7 holds; the 25 ear-confirmed resting bars still rest; none of the 98 ear-confirmed playing bars rests; the ten 1.7 songs' resting bars number 54; no other flag changes. Pour Some Sugar On Me 7 and 80 get stem-alone clips.
3. Certainty: Need You Tonight 0-13 (its bars 8-12), The Cars 72-76, Summer of '69 0-4 and Chelsea Dagger 7-19 print grey; no ear-passed range of 5.7 changes vector or certainty; no other member changes vector or certainty; `evaluate --truth` on the 24 judged ranges reports 8 wrong ranges still certain and 4 right ranges grey, each named, as the figure 1.9 starts from.
4. Badge's Verse 1, Chorus 1, Instrumental 2, Chorus 2 and Verse 2 print grey under "guitar not separated here" with no riff flag; its Intro and Instrumental 1 (the bridge) print as 1.7 printed them; no other song's gate fires; the four figures are written on every member. The three newly gated members not yet judged by ear get stem-alone clips.
5. Badge's key is G major or E minor with the other as its hedge; the lead tonic of the other ten runs is unchanged; the three printed hedges are unchanged.
6. The Cars by The Cars, Day Tripper by The Beatles, Badge by Cream, each with an "uploaded by" line; the eight known songs' credits unchanged and no "uploaded by" line on any of them (All Fired Up's uploader differs from the artist but its channel is the artist's); the run folder names unchanged.
7. The six pickup bars print as partial bars: Summer of '69 and The Cars empty, All Fired Up and You Shook Me with one down stroke, Badge with its riff strokes, Fame as the rest rule decides; page counts recorded against 1.7.
8. Every sheet carries the two legend lines.
9. `evaluate --truth` runs on all eleven truth folders and prints every line of 9.2; its totals on the 1.7 baseline runs are recorded before any change so the deltas are the version's score.
10. The blind song runs to a sheet with exit 0; its figures recorded, not judged.

**Ground truth from published sources first** (owner's instruction, 2026-10-06), then the ear where sources disagree, say nothing, or contradict the chain. Ear clips for: every member whose certainty or vector changed and is not in the truth files; the bars whose rest flag changed (stem alone); Badge's five gated members (stem alone and clicks); the blind song's sections. The listening pass remains the acceptance test; a row the sources or the ear reject is recorded, not tuned.

## 13. Assumptions

Status after the assumption pass of 2026-10-08 is written in the Status column; "unverified" names the validation step that settles it.

| # | Assumption | Status | If wrong |
|---|---|---|---|
| A1 | The end-trimmed window rests Chelsea Dagger 7 and 12, keeps the 25 confirmed rests resting and rests none of the 98 confirmed playing bars | **Refuted as first written, then measured on all 1 201 bars**: the full half-slot shift un-rested Wet Leg 18 and Pour Some Sugar On Me 15 and 77 (the previous bar's ringing stroke enters slot 0); the end-trimmed window keeps 25 of 25 rests and 98 of 98 playing bars, and changes five flags, all named in 4.1 | A playing bar near a boundary rests, or a confirmed rest holds; the two costs named in 4.1 are judged by ear |
| A2 | An attack statistic tells a carried tail from a new stroke | **Refuted in the assumption pass**: tails re-rise 16 to 38 dB on separator artefacts, playing bars 0.6 dB and up; a decay-shape variant fails on whole-note playing bars; 4.2 is dropped | n/a |
| A3 | A top-two margin band separates the heard-right from the heard-wrong judged ranges with at most one right range lost | **Refuted in the assumption pass** on the 24 judged ranges under Jaccard and under swap distance: the ranges overlap throughout; 5.5 records the margin and does not use it | n/a; the band is re-measured in 1.9 on the new strikes |
| A4 | 5.1, 5.2 and 5.4 change only Need You Tonight 0-13, The Cars 72-76 and Summer of '69 0-4, and no ear-passed range | **Measured in the assumption pass** on all 100 voiced members: exactly those three move; the pair-level chance test first proposed as 5.3 would also have blackened Summer of '69 4-19 (ear-passed) and Day Tripper 46-52, so it was dropped; `PERIOD2_MIN_PAIRS` band 3 to 4 (ear-passed two-bar members have four to eight pairs) | A future two-bar pattern on exactly two pairs prints as a one-bar vote; recorded as the rule's cost |
| A5 | `OWN_LOW_SHARE_MIN` 0.40 with `BASS_STEM_MAX` 0.05 fires on the Badge members whose stem carries the bass and on no member of any other song, intros and outros included | **Measured in the assumption pass on all 101 members**: fires on five Badge members (two ear-judged, three not), nothing else; own-share band 0.376 to 0.462, **0.086 wide, held by one member on each side, one positive song**; bass-ratio band 0.002 to 0.317; leave-one-song-out moves no constant; the bridge arpeggio 28-34 is a known miss of the own-share figure | A riff intro before the bass enters is gated grey, or a future swap with a bright part over the bass is missed; the figures are written either way, and the next blind song widens or kills the band |
| A6 | 4.4 greys the three flipped members and no member whose 1.6 and 1.7 certainty agreed | **Measured in the assumption pass on the 100 voiced members**: twelve contain resting bars; exactly three disagree between the two readings, the three flips; no ear-passed range moves; the nearest other member is Wet Leg 18-33 at 0.462 on all bars, certain both ways | A member 1.6 greyed for noise and 1.7 rightly blackened greys again; listed as a cost, not tuned |
| A7 | `SET_VETO_MARGIN` 0.10 fires on Badge and on no other run, when the comparison is against the decided tonic's pair share and the replacement is the best major set's tonic | **Measured in the assumption pass** on all eleven runs: Badge 0.238, Fame 0.008, the rest 0.000; the two hazards (own-set comparison would veto Pour Some Sugar On Me; `_winner` would name E) are written into 7.1 | A dominant-heavy song with a clear tonic is vetoed to its subdominant; the margin band is re-measured when a run is added |
| A8 | At G, Badge's mode test names major with a margin above `MODE_TIE_MARGIN`, so the sheet prints "G major (or E minor)" | **Measured in the assumption pass**: the harmony stage's stem chroma rebuilt (guitar, bass, piano, other, loud mask), `mode_at("G")` major at 0.644, `_mode_of("E")` minor at 0.316, no mode hedge | A close mode hedges as 1.5 does; either lead scores 1.0 against one published key |
| A9 | Rung 2 of 8.2 splits the three blind titles correctly and splits no known title wrongly; 8.3's channel test passes the three artist channels and fails the three others | **Measured in the assumption pass** on the eleven raw titles and the review's handles: all eleven credits as expected; the head-only rule split "Song - Live at Wembley", so the tail condition was added to 8.2; the three-letter-word test cannot pass "AC/DC", so the run-together form was added to 8.3; `uploader_id` is not stored by 1.7, so rung 1 and the handle test run on fresh fetches | A title with a tag word in neither head nor tail and a dash inside it splits wrongly; the exclusion list is widened, never a song-specific rule |
| A10 | The six pickup bars are counting conventions (silent or drums only inside them) rather than played pickups | **Refuted for four of six in the assumption pass**: All Fired Up, You Shook Me, Fame and Badge play inside their pickup bar; Summer of '69 and The Cars do not; 4.3 and 3.2 are worded for both | n/a: 3.2 prints whatever the bar holds |
| A11 | The 1.6 and 1.7 listening passes and the published-source table transcribe into the truth files without ambiguity | Unverified until the files are written and reviewed line by line against the records | A verdict is mis-copied: the review step catches it; the records stay authoritative |
| A12 | The tests and fixtures that depend on the unshifted rest window, the two-pair union or the five-field metadata are known and are changed by this spec, not discovered during implementation | **Measured**: `tests/test_rests.py` and `tests/test_html.py` call the rest functions; `tests/test_as_played.py` (20 references) and `tests/test_vote.py` (6) exercise `majority_vector`, `_pairs` and `unit_and_phase`; `tests/test_titles.py::test_wider_artist_prefix_rule` holds the "Of Us" case; `tests/test_runner.py` expects `source_meta.json` left alone; `tests/fixtures/v16_strums.json` and `v16_score.json` hold 1.7 rest figures and are regenerated | A fixture is regenerated with the change named in the commit; no test is weakened to pass |
