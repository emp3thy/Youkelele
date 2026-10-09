# Review: riff versus strum texture and riff tab (2026-10-08, main at 74c11e0)

Line numbers are from the files at 74c11e0.

## A. Diagnosis

The riff decision is three point thresholds on one pooled feature set per member, computed on the strum detector's onsets, with repetition consulted only afterwards as a tab gate. Each verified failure follows from one of those choices.

**Missed one-pitch riffs** (All Fired Up 61-90 and Day Tripper 52-58 in 1.6). `pitch.py` `pitch_change_share` (l.193-197) counts consecutive named onsets whose rounded MIDI differs; `_riff_test` (`stages/strums.py` l.276-280) requires it at or above `PITCH_CHANGE_MIN` 0.26 (l.143). A riff on one pitch has share 0 and can never pass; the two recovered riffs passed only because the floor fell from 0.40 to 0.26 into a band 0.238-0.282 resting on one weakly labelled strum (1.7 A1). The research (Q5) finds no counterpart for an interval-change ratio; Régnier's non-rhythm bars are characterised by single notes, not pitch variety, and Pati's riff definition is repetition. The feature measures melodic variety, which is orthogonal to the question.

**Missed chord-like and busy riffs** (Day Tripper 0-11 entropy 0.86; Summer of '69 111-121 entropy 0.90; Need You Tonight 8-13; AC/DC's riff-over-chords sections at 0.89-0.93). `riff.py` `riff_features` (l.63-82) folds CQT power into twelve classes over a 40-130 ms window after each onset (`onset_chroma` l.28-60) and `is_riff` (l.85-89) requires median entropy at or below `RIFF_ENTROPY_MAX` 0.82. Any second voice, double stop (Need You Tonight's own riff has them per the Lick Library lesson) or bend spreads chroma over the ceiling. The report's measurement-theory paragraph says why: chroma is the wrong coordinate system for mono-versus-poly; nobody surveyed gates on it.

**The power-chord hook false positive** (The Cars 0-11: entropy 0.735, single 0.638, pitch change 0.282). A root-plus-fifth dyad in `onset_chroma` looks like a single note with its third harmonic, and `_SINGLE_PC_RATIO` 0.5 (l.24, l.81) counts a fifth below half the root's power as absent, so the dyad is "single". The research (Q5: Kehling, Foulon, Lachambre) discriminates dyads in the harmonic domain: tracker confidence, inharmonicity, odd/even partial energy. `track_pitch` (`pitch.py` l.158) already receives pyin's voiced probability and discards it.

**The riff-over-strum miss** (Day Tripper 52-58 flagged but the clicks follow the strum; AC/DC 0-16, 34-43, 74-90, 90-113 printed as strums). `_riff_inside` (l.238-252) takes every detector onset in the holding bars and `riff_times = today.times` (l.522) is the strum detector's list, so one feature vector describes both parts; `_section_pattern` (l.310-330) then prints the member's strokes, which are the strum's. No per-onset partition exists. The research offers per-onset texture (Foulon, frame-level then aggregated) as the route to a mixed-section label, not a better pooled threshold.

**Only one tab in eleven songs.** `riff_line.py` `note_jaccard` (l.34-44) scores exact MIDI equality per slot; `gate` (l.115-125) wants agreement 0.70, support 0.75, named 0.6 from pyin at the stroke slots (`stages/riff.py` l.291-303). Octave flips, the spike's named failure mode, score zero. Need You Tonight Verse 2 and 3 play the same riff as Verse 1 by the published source and fail at 0.43 and 0.24: a source-verified miss inside the one song that works. The research (Q2) puts the best GuitarSet transcribers at onset-level F 0.79-0.90; a 0.70 exact-pitch agreement from pyin on a stem asks more than the field achieves.

**Pour Some Sugar On Me 67-77 through the rest rule.** `_riff_inside` reads holding bars only; resting bars 67-68 removed 15 of 94 onsets and moved single share from 0.426 to 0.468 across the 0.45 floor: a point threshold on a statistic whose sample another rule changes, with no margin (report rule 2). The ear found a two-part passage, the riff-over-strum failure again.

`evaluate.py` carries no riff truth (`_section_diags` l.270-349 prints flags and gate figures, scores nothing), so every riff number in the records was counted by hand.

## B. Suggestions, ranked

### S1. Repetition first, texture second

Change: new `music/repeats.py` with `bar_chroma(y, sr, bars, slots) -> (n_bars, slots, 12)` from the CQT `onset_chroma` already computes (expose the frame-level chroma), and `repeat_score(member_bars) -> float`: median over bars of the max cosine similarity to the bar one or two later, transposition-free. `_riff_test` becomes: repeat score at or above `RIFF_REPEAT_MIN`, then the texture test (S2). Record `repeat_score` on `SectionPattern` beside `bar_repeat`.
Addressed: one-pitch riffs (repetition is strong when pitch-change share is 0), busy riffs whose bars repeat, the rest-rule flicker. Not addressed alone: a strummed progression repeats too, so S1 is a necessary filter, not a sufficient one.
Support: Pati and Lerch's structural repetition feature (https://musicinformatics.gatech.edu/wp-content_nondefault/uploads/2017/06/Pati_Lerch_2017_A-Dataset-and-Method-for-Electric-Guitar-Solo-Detection-in-Rock-Music.pdf); Weiss and Bello on beat-synchronous chroma (https://musicmachinery.com/2010/08/10/identifying-repeated-patterns-in-music/); report rule 4.
Risk: Need You Tonight 13-24 repeats bar to bar (0.74 on exact notes) and passes any sane floor; the verified non-riffs also repeat, so S1 neither flags nor clears them. Generality: a loudness-invariant ratio. Install: none.

### S2. Harmonic-domain texture replaces chroma entropy

Change: `pitch.py` `PitchTrack` gains `voiced_prob` (pyin's third output, l.158). New `music/texture.py`: per onset, over the steady-state window (skip `NOTE_SKIP_IN_S`, Foulon's transient rejection), (a) mean voiced probability, (b) non-harmonic share: from the CQT frames of `onset_chroma`, energy in bins not within 50 cents of k·f0 (k = 1..6) of the named pitch, over total; a root-plus-fifth dyad puts energy at 1.5 f0, a single note does not. Member features: median and variance of each (Lachambre). `is_riff` takes these instead of entropy; keep `single_share` only if D2 shows it adds separation.
Addressed: the dyad false positive, chord-like riffs misread by chroma; it also supplies the per-onset single-note probability S4 needs.
Support: Lachambre (https://irit.fr/SAMOVA/site/?p=454); Foulon, Roy, Pachet 2013, F 0.96 after one-bar aggregation (https://www.francoispachet.fr/wp-content/uploads/2021/01/foulon2013classification.pdf); Kehling's odd/even partial rule (https://www.dafx14.fau.de/papers/dafx14_christian_kehling_automatic_tablature_trans.pdf); report rule 1.
Risk: Need You Tonight's riff carries double stops and palm muting; D2 must show it lands with the riffs before adoption. Foulon's timbre caveat applies. Generality: scale-invariant ratios. Install: none.

### S3. Tab gate: tolerant agreement, song-level figure, graded print

Change in `riff_line.py`: `note_jaccard` matches on `a % 12 == b % 12` (octave-folded), exact agreement kept as a second figure; `choose_riff` runs once over all riff members of a song (a song-level medoid, Pati's "repeats in the song"), each member scored by support against it, so Verse 2 and 3 inherit Verse 1's figure (`inherited_from` on `RiffSection`, as patterns have). In `stages/riff.py`, agreement in a lower band (0.5-0.7) prints the figure grey under "riff heard, tab uncertain" (Area 8's vocabulary) rather than nothing.
Addressed: one tab in eleven; the source-verified Need You Tonight verses.
Support: guitar papers score onset-only, pitch within 50 cents (https://mir-eval.readthedocs.io/stable/api/transcription.html); Régnier's leave-one-piece-out because bars repeat within a song (https://archives.ismir.net/ismir2021/paper/000006.pdf).
Risk: Fame Instrumental 1 (verified wrong) sat at 0.39-0.52; the grey band must stay above it. Need You Tonight Verse 1's tab must stay byte-identical. Install: none.

### S4. "Mixed" label for riff over strum, from per-onset texture

Change: with S2's per-onset single-note probability, a member whose single-note onsets are a 0.3-0.7 share and themselves repeat (S1 on that subset) gets `riff_rule = "mixed"`, header "riff over strum"; the strokes stay the strum's (the ear said the clicks fit the strum) with the riff onsets marked. No transcription of the riff part.
Addressed: Day Tripper 52-58, Pour Some Sugar On Me 67-77 and AC/DC's four sections become honest prints.
Support: Foulon's frame-level classification before aggregation; report rule 2. Risk: none to the verified tab (share near 1.0). Install: none. Overlaps area 5; this only labels.

### S5. Dyad riff class

Change: `riff_rule` gains `"dyad"`: non-harmonic share high, repetition high, pitch change low. Header "power-chord hook"; strum strokes print (today's outcome, by accident of the failed gate).
Addressed: The Cars 0-11 becomes a correct label. Support: Régnier and Pati put power-chord riffs in the rhythm class; the report asks for a separate class. Risk: none to the tab. Install: none.

### S6. Margin band on the flag

Change: `is_riff` returns three states; within 0.03 of any floor is `uncertain` and prints "riff heard?" grey. Addressed: the rest-rule flicker on Pour Some Sugar On Me 67-77 and other near-floor members. Support: report rule 2 (Böck's band, Basic Pitch's 0.5/0.3 split). Risk: Need You Tonight 13-24 sits at 0.54/0.78, far from any floor. Install: none.

### S7. Basic Pitch as an optional polyphonic note source, isolated

Change: `models/notes.py` with a `NoteSource` protocol; the Basic Pitch implementation runs as a subprocess `uv run --no-project --python 3.11 --with basic-pitch --with "setuptools<81" <script> <stem.wav> <notes.json>` (the project memory's recipe; `requires-python` stays `==3.12.*`), exchanging (onset, offset, midi, confidence) as JSON cached at `05_riff/notes.json`. Used only as the riff stage's note namer under `--notes basic-pitch`; pyin stays the default.
Addressed: the tab layer on two-voice riffs and double stops. The 1.7 spike showed its polyphony count does not separate riffs from strums, so it buys nothing for the flag.
Support: Apache-2.0, 16.8 k parameters, 24 s per 7 min file on CPU (https://github.com/spotify/basic-pitch; https://arxiv.org/pdf/2203.09893).
Risk: none to the tab under the default; under Basic Pitch the figure must reproduce the verified notes. Install: a second interpreter and a TensorFlow or ONNX wheel set, an opt-in step in `install.ps1`. Ranked last because the gate, not the namer, is the bottleneck until D3 says otherwise.

## C. Success criteria

**Truth table available today** (my count from the records, spikes and AC/DC table; the owner's tally is authoritative). Riff by ear or source: Need You Tonight 8-13, 13-24, 24-31; Fame 1-17, 29-35; The Cars 52-68; Wet Leg 58-65; All Fired Up 97-104; Summer of '69 0-4, 111-121; Day Tripper 0-11, 52-58; Badge 28-34; All Fired Up 61-90 (ear yes, source no); Pour Some Sugar On Me 67-77 (two-part); AC/DC 0-16, 34-43, 90-113 (riff over chords), 74-90 (solo over strum): 19, of which 7 mixed or disputed. Non-riff: The Cars 11-19, 0-11 (dyad hook); All Fired Up 33-49, 55-61; AC/DC 16-34, 43-57; Chelsea Dagger 13-19; Badge 4-28, 61-70 (bass bleed): 9. Twenty-eight of 93 voiced members; the majority baseline is "not riff" over the 93 (about 0.7) and "riff" over the 28 (0.68), since clips were cut where riffs were suspected. Report both, as Pati does.

**Current operating point** on the 28: recall 12/19 (0.63), precision 12/15 (0.80), counting mixed flags as hits; the misses are Need You Tonight 8-13, Summer of '69 111-121, Day Tripper 0-11 and AC/DC's four.

Adopt a suggestion only if, computed by a new `evaluate --riff-truth <file>` (tab-separated "song, start, end, label" beside the chord truth) with leave-one-song-out over eleven songs:

- S1 + S2: recall at least 16/19 and precision at least 0.80 on the 28; macro-accuracy above the stated baseline; no constant whose fold optimum moves by more than its band width; Need You Tonight 13-24 flagged and the six clean non-riffs (The Cars 11-19, All Fired Up 33-49, 55-61, AC/DC 16-34, 43-57, Chelsea Dagger 13-19) unflagged in every fold.
- S4: the seven mixed or disputed sections labelled "mixed"; no clean riff or strum so labelled. S5: The Cars 0-11 "dyad"; no single-line riff "dyad".
- S3: `mir_eval.transcription.precision_recall_f1_overlap`, `offset_ratio=None`, onset 50 ms, pitch 50 cents: Need You Tonight 13-24 stays 1.0 against the verified figure (it is the reference); Verse 2 and 3's inherited figure reaches F at least 0.8 against it; Fame 29-35 prints nothing in black. Tab: TDR, the share of correctly pitched notes on the string `to_tab` gives the reference MIDI, at least 0.95 on every printed tab. A second reference (The Cars 52-61 or Wet Leg 58-65, read from Songsterr by hand) is needed before any gate constant moves.
- S6: every member within 0.03 of a floor prints grey; no ear-passed black row changes. S7: under Basic Pitch the Need You Tonight figure equals the verified one; F at least 0.7 on the second reference.
- Regression, all: the 822 tests pass with `test_riff.py` l.84, `test_pitch.py` l.39 and the fret sequence in `test_stage_riff.py` l.97 changed only where the spec changes them; `evaluate <1.7 baseline> --compare <run>` on all eleven runs lists riff-flag changes only in the truth table's direction and no pattern row change on an ear-passed section (1.7 A10); `tab_identical` true for Need You Tonight.

## D. Spikes on the existing runs

The pitch track and the detector's own onsets are not persisted; `riff.json` holds per-onset named MIDI for flagged members only. D2, D4 and D5 re-run the strums stage in-process as `probe.py` did (byte-identical `strums.json` confirmed in 1.7).

- **D1, repetition.** Does bar-to-bar chroma similarity separate the 19 riffs from the 9 non-riffs, and what does `bar_repeat` in `strums.json` already give? Measure `repeat_score` at lags 1 and 2 per member, tabled with the label. Kill if the riff and non-riff ranges overlap over more than a third of either; confirm if a band exists with Need You Tonight 13-24 on the riff side. The useful output is whether the misses (Day Tripper 0-11, Summer of '69 111-121) score high.
- **D2, harmonic texture.** Do pyin voiced probability and the non-harmonic share put The Cars 0-11 with the strums and Need You Tonight 13-24, The Cars 52-68, Wet Leg 58-65 with the riffs? Measure per-onset values on the steady-state window, median and variance per member, all 93 members. Kill if The Cars 0-11 is not below Need You Tonight on both, or Need You Tonight (double stops) falls among the strums; confirm if the five source-verified riffs and six clean strums separate with a band at least 0.05 wide.
- **D3, gate tolerance.** How many flagged members cross 0.70 with octave-folded agreement and a song-level figure? Re-run `choose_riff` on `riff.json` `onsets` (no audio) with `% 12` matching, per member and pooled per song. Confirm if Need You Tonight Verse 2 and 3 cross with Verse 1's notes; kill if Fame 29-35 (verified wrong) or a Badge verse crosses.
- **D4, mixed sections.** Is the single-note onset share in 0.3-0.7 on Day Tripper 52-58, Pour Some Sugar On Me 67-77, AC/DC 34-43 and 90-113, and outside it on the clean riffs and strums? Measure from D2's per-onset values. Kill on either side failing.
- **D5, floor margin.** How many members sit within 0.03 of a floor on holding bars versus all analysed bars? Recompute entropy and single share both ways for all 93. Confirm S6 if any member beyond Pour Some Sugar On Me 67-77 crosses a floor between the two.
- **D6, Basic Pitch at the tab layer.** Only if D3 shows the named notes, not the agreement rule, limit the gate: note F against a hand-read Songsterr reference on The Cars 52-61 and Wet Leg 58-65, pyin versus Basic Pitch at the stroke slots. Kill if Basic Pitch is not above pyin by 0.1 F on both.

## E. Do not do

- Do not lower `RIFF_ENTROPY_MAX` to reach AC/DC: its riffs sit at 0.835-0.926 and its strums at 0.942-0.946; the ceiling would be fitted to one song.
- Do not revive Rule B or any `root_share` rule: refuted on AC/DC; All Fired Up 61-90 (0.95) and Day Tripper 52-58 (0.76) are riffs with high root share.
- Do not move `PITCH_CHANGE_MIN` again; its band is 0.044 wide on one weakly labelled strum. Replace the feature or leave it.
- Do not print tab from the majority figure without a gate: the 1.5 spike turned both strum controls into fake one-note tab.
- Do not split parts by register or a MIDI 60 line, nor by high-band naming (one positive example each).
- Do not make Basic Pitch, CREPE, Omnizart or TabCNN a hard dependency or change `requires-python`; TabCNN has no licence, CREPE and Omnizart need TensorFlow.
- Do not treat Songsterr tabs as truth over the ear: on the seven disputed rests the ear sided with the chain six times.
- Do not fit a constant on the eleven songs without leave-one-song-out, nor count the 28 labelled sections as a random sample of the 93.
- Do not touch a riff section's stroke rhythm: it comes from the strum detector's onsets and was verified; pyin names pitch only.
