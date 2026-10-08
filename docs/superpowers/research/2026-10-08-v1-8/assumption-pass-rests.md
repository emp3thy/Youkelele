# Assumption pass, rests (A1, A2, A6, A10)

Run 2026-10-08 against main at 27bf2a2 on the eleven `runs\` folders (1 201 bars, 100 voiced members; the review's 1 131 and 93 were estimates). Read-only; scripts in the session scratchpad under `ap_rests\`. Every run reads the guitar stem. "Stored" is the 1.7 figure in `strums.json`; "shifted" is spec 4.1's window `[start − half, end − half)`; "trimmed" is `[start, end − half)`, measured for the A1 amendment. The labelled set is review section C: 25 ear-confirmed rests, 98 ear-confirmed playing bars, Chelsea Dagger 7 and 12.

## A1. The shifted window

Method: `bar_energy_ratio` and `bar_low_share` recomputed on the shifted window for every bar, `bar_holds` applied, compared with `bar_holds` on the stored figures (the stored `rests` flag equals that on all 1 201 bars).

Bars whose hold changes (7, not 3):

| Song | Bar | energy stored → shifted | low_share stored → shifted | holds | Label |
|---|---|---|---|---|---|
| Chelsea Dagger | 7 | 0.050 → 0.006 | 0.348 → 0.0001 | → rests | false hold, expected |
| Chelsea Dagger | 12 | 0.062 → 0.021 | 0.369 → 0.160 | → rests | false hold, expected |
| Wet Leg | 18 | 0.029 → 0.058 | 0.574 → 0.539 | → holds | confirmed rest, tail |
| Pour Some Sugar On Me | 15 | 0.033 → 0.071 | 0.076 → 0.062 | → holds | confirmed rest |
| Pour Some Sugar On Me | 77 | 0.029 → 0.055 | 0.131 → 0.106 | → holds | confirmed rest, tail (spec expected 0.068) |
| Pour Some Sugar On Me | 80 | 0.055 → 0.033 | 0.326 → 0.194 | → rests | unlabelled; prints 3 strokes in slots 12, 14, 15 (a lead-in fill), which a resting row would drop |
| The Cars | 63 | 0.133 → 0.000 | 0.280 → 0.260 | → rests | unlabelled; stem is digital silence (slots −87 to −99 dB), the 0.133 was bar 64's downbeat in the last half-slot; prints no stroke; rests rightly |

Labelled set: Chelsea 7 and 12 rest; 98/98 playing bars hold (lowest shifted energy 0.080, lowest low_share 0.033); 22/25 confirmed rests rest. Need You Tonight 7 falls 0.0195 → 0.0002, Wet Leg 25 0.0170 → 0.0001, Summer of '69 0 reads 0.0024: all rest. Total rests 51 → 52.

The three un-rested rests share one mechanism: the half-slot before the bar line carries the previous bar's ringing last stroke (bars 17, 14 and 76 end at −22, −34, −33 dB), so slot 0 is each bar's loudest slot by 15 to 26 dB. The trimmed window `[start, end − half)` keeps the quantiser's end (an anticipation belongs to the next bar) without taking that ring: 25/25 rests rest, 98/98 playing bars hold, Chelsea 7 and 12 rest (0.006, 0.022), Pour Some Sugar On Me 77 reads 0.030 and rests without 4.2. Its changes against stored: Chelsea 7, 12, The Cars 63, Pour Some Sugar On Me 80 (0.034) and Pour Some Sugar On Me 7, a tail at the floor's edge (0.04988 stored, 0.04946 shifted, 0.05023 trimmed). Total rests 54.

**Verdict: refuted as written.** The shift un-rests three confirmed rests, not one, and 4.2 cannot rescue them (A2). Amendment: measure on `[bar.start, bar.end − half)`; expected changes are Chelsea 7 and 12, The Cars 63 (right), Pour Some Sugar On Me 80 (a cost: three printed strokes) and Pour Some Sugar On Me 7 (a cost: 0.0002 over the floor; 4.5's no-hysteresis ruling stands, record it).

## A2. The attack statistic

Method: per-slot RMS in dB (floor −100 dB; the stem is digital zero in places) on the shifted window, `slots_per_bar` slots per bar. Attack = max(largest rise of a slot after the first over the minimum of the slots before it, slot 0's rise over the previous bar's last slot).

| Bar | Slot dB | Rise after slot 0 | Slot-0 rise | Attack |
|---|---|---|---|---|
| PSSOM 7 | −65 −47 −45 −44 −45 −63 −72 −70 −83 −94 −97 −94 −93 −89 −88 −85 | 21.0 | −8.8 | 21.0 |
| PSSOM 8 | −79 −50 −47 −49 −54 −70 −83 −90 −76 −100 … | 31.7 | 5.8 | 31.7 |
| PSSOM 9 | −86 −82 −83 −76 −79 −83 −87 −76 −70 −89 … | 16.3 | 4.6 | 16.3 |
| PSSOM 10 | −67 −60 −59 −60 −62 −78 −61 −49 −49 −70 −87 −89 −81 −55 −55 −62 | 33.9 | 27.8 | 33.9 |
| PSSOM 77 | −36 −62 −76 −87 −86 −89 −86 −92 −98 −99 −99 −74 −61 −83 −89 −98 | 37.8 | −3.4 | 37.8 |
| Wet Leg 18 | −25 −41 −47 −60 −65 −49 −50 −44 | 20.5 | −3.5 | 20.5 |

Tails: 16.3 to 37.8 dB. The 98 playing bars: min 0.59 dB (All Fired Up 46), then 1.1, 1.3, 1.3, 1.4, 1.5; over all 1 149 holding bars the median is 4.0 dB. The band is −37 dB: the statistic separates the sets the wrong way round. A bar strummed on every slot has a flat profile (slot RMS averages the attacks away) and reads no rise; a tail decays into digital silence where Demucs artefacts at −60 to −100 dB re-rise by 15 to 30 dB. At `ATTACK_RISE_DB` 6, 77 of the 98 playing bars and 771 of 1 149 holding bars read no attack; at 20, 89 of 98. The bars 4.2 would decide (stored rest, both floors passed on the shifted window) are Wet Leg 18 (20.5 dB), PSSOM 15 (28.9) and PSSOM 77 (37.8): all read an attack, so 4.2 would rest none.

Synthetic case (120 bpm, 8 slots, a four-partial chord decaying over 0.6 s): the bar struck on slot 0 after a silent bar reads a slot-0 rise of 85 dB; the bar holding only the tail reads −3.5 dB. The statistic behaves on the synthetic and fails on the stems. A decay-shaped variant (loudest slot of the first half minus loudest of the second) also fails: the ear-confirmed playing bars Chelsea 9 and PSSOM 65 are single whole-note strokes falling 58 and 48 dB, the tails' shape (19 to 40 dB).

**Verdict: refuted; no value exists (band −37 dB).** By 4.2's own clause the rule and the `tail` flag are dropped. With the A1 amendment the six tail bars rest by the floor (PSSOM 7 excepted, 0.0002 over).

## A6. Two certainty readings

Method: members rebuilt as `new_member` does (plan, grid sections, `trailing_silent_bars`, the section cut on the stems, `bar_holds` on the stored figures); `choose_pattern`, `structure_test` (seed = first bar) and `member_figures` run on the holding bars (the longest member's confidence, chance p and flag match the stored `patterns` on all 55 sections) and on the full analysed span against the printed vote, flag `confidence < floor or not structured`. The 1.6 reading (its own vote on all bars) gives the same flags on every member.

100 voiced members; 12 contain resting bars; the other 88 are identical under both readings. The members whose flags disagree are exactly the three named:

| Member | Bars all/holding | Conf holding | p holding | Conf all | p all | Uncertain holding → all |
|---|---|---|---|---|---|---|
| Chelsea Dagger intro 0-20 | 20/11 | 0.487 | 0.001 | 0.325 | 0.001 | no → yes |
| Need You Tonight 0-13 | 13/5 | 0.747 | 0.007 | 0.287 | 0.989 | no → yes |
| PSSOM instrumental 67-77 | 10/8 | 0.548 | 0.047 | 0.505 | 0.051 | no → yes |

The other nine members with resting bars agree, among them Wet Leg 18-33 (0.847 holding, 0.462 all, p 0.006, certain both ways, 0.012 above the floor) and PSSOM 77-84 (uncertain both ways). No ear-passed member moves: every listed range reads the same confidence, p and flag under both readings (Summer of '69 4-19, All Fired Up 55-61 and 128-132, The Cars 72-76 are uncertain today and stay so). Explained on all bars drops below 0.6 on no member, so leaving it out of the all-bars flag costs nothing.

**Verdict: held.** 4.4 as written; name Wet Leg 18-33 at 0.462 as the member nearest the floor.

## A10. The pickup bars

Method: per pickup bar, guitar and drums stem RMS over mix RMS on both windows, the stored onsets and strokes, and the slot profile (a pickup bar is cut into `slots_per_bar` slots like any bar).

| Song | Bar 0 | Beats | Seconds | Guitar/mix exact / shifted | Drums/mix exact / shifted | Mix RMS re song | Onsets in bar | Slot dB | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| All Fired Up | 0.04-0.44 | 1 | 0.40 | 0.991 / 0.992 | 0.000 / 0.000 | 0.07 | D on slot 0, 1 stroke | −38 −34 −34 −41 −45 −49 −55 −59 | played: one guitar stroke, decaying |
| Cream, Badge | 0.46-2.16 | 3 | 1.70 | 0.341 / 0.346 | 0.001 / 0.001 | 0.41 | D--UxU-x, 5 strokes | −35 −34 −36 −38 −39 −36 −43 −36 | played: the riff's three beats |
| Fame | 3.38-4.02 | 1 | 0.64 | 0.338 / 0.338 | 0.014 / 0.014 | 0.14 | none | −54 rising to −40 (bar 1 at −41 to −23) | played, no stroke: a swell into the downbeat |
| Summer of '69 | 0.02-0.44 | 1 | 0.42 | 0.024 / 0.002 | 0.837 / 0.843 | 0.59 | none | −80 to −61 | counting convention: drums only |
| The Cars | 0.86-1.32 | 1 | 0.46 | 0.970 / 0.956 | 0.017 / 0.004 | 0.13 | none (bar 1 slot 0 is D) | −94 … −81 −37 | counting convention: silent until the last 60 ms, the start of bar 1's downbeat; 0.97 is a ratio of two near-silences |
| You Shook Me All Night Long | 0.46-0.94 | 1 | 0.48 | 1.006 / 1.006 | 0.000 / 0.000 | 0.48 | D on slot 0, 1 stroke | −22 −20 −19 −19 −20 −20 −21 −21 | played: a chord struck and ringing |

Four of the six carry guitar (three struck, one swell), two are conventions; only Summer of '69 rests today, and it rests on every window.

**Verdict: refuted for four of six.** A10's "if wrong" clause applies: 3.2 prints a partial bar with whatever strokes the row holds and the rest rule needs no change; the record should say three struck pickups, one swell, two conventions.
