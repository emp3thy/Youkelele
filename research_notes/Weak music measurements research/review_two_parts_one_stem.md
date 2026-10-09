# Review: two parts in one separated stem (2026-10-08, main at 74c11e0)

Scope: a riff or solo over a strum, two guitars, and bass bleed on the guitar stem. Read-only review; the two spike scripts live in the session scratchpad (`bleed_spike.py`, `lowband_spike.py`) and read only `runs\`. Figures quoted below are from those runs.

## A. Diagnosis

The chain has one source stem per song and one onset list per stem; every failure below inherits that.

- `music/onsets.py` `choose_source` (75-84) picks guitar or other by whole-song RMS ratio; `stages/strums.py` `run` (494) calls it once and line 495 detects onsets on that signal with full-band `onset_strength` (`detect_onsets`, 48). Two parts give one merged onset list.
- `quantise_bar` (onsets.py 130-152) and `_slot_onsets` (strums.py 184-202) put either part's onset in a slot; `_vote_member` (216-227) votes on the union. Nothing downstream knows a slot came from a second part.
- `_riff_test` (strums.py 341-359) names pitches with `track_pitch` (pitch.py 33-51, pyin, 82 Hz floor) on the whole stem (533); pyin returns the loudest periodic line, on a bleedy stem the bass.
- `section_has_instrument` (onsets.py 87-88) and the rest rule (`bar_low_share`, strums.py 572-574, power below 330 Hz) pass trivially when the stem carries a bass.
- `stages/separate.py` writes the bass stem but no stage reads it (`StrumsStage.requires`, strums.py 391-396). `roformer-sw` (`options.py:17`, `cli.py:50`) is a stub `preflight.py:139-140` rejects.

Per failure:

**Fame, Chorus 61-71 and Verse 3 71-81 (1.6 clips 11, 21, 22).** Two rhythm guitars, the second higher; "too many clicks, I think it's clicking to the higher pitched strumming". Bass is clean on its own stem (0.39 to 0.62 of the mix), guitar stem's own low share 0.08 to 0.43: a pure two-guitar case. The union of both guitars' onsets fills the sixteenth grid, and every Fame section is flagged riff (the second guitar's line raises the single-pitch-class share). Research: GuitarDuets leaves the second of two same-timbre guitars near 1 dB SDR even when trained for it; the gain is in assigning detected notes to parts (two_part_separation.md KQ2).

**AC/DC, four of six sections (acdc-ear-truth.md).** Riff over chords (34-43, 90-113), solo over strum (74-90), riff alternating with chord stabs (0-16). Bass clean (0.46 to 0.51), guitar stem low share 0.04 to 0.05: a clean stem carrying two guitar parts. The intro's clicks fit the riff; the 1.7 spike's kept fact is that the merged pattern equals the 400 Hz high band's, so the printed strokes follow the higher part. No section is flagged riff (entropy 0.84 to 0.95: power chords plus a riff is not a single-pitch texture). Research: Pati and Lerch define a solo as non-repeating over measures and a riff as repeating; repetition separates 74-90 from 34-43, and register cannot tell which instrument sounds (KQ5).

**Day Tripper, Verse 3 52-58 (1.6 clip 37).** "The clicks match the strum, not the riff". Riff and strum share the eighths (the spike's rhythmic-unison case), so the merged onsets are the strum's; the 1.7 flag prints "riff heard" over a correct strum, the honest outcome today. Stem figures normal. Research: contig creation (segments with two simultaneous notes) detects "two parts here" at 99.4 % transition precision; onset coincidence never will (KQ3).

**Badge, Verse 1 4-28 and Verse 2 61-70 (1.7 clips 15, 16).** "It's confusing the bass, which has the melody". The bass stem is empty from bar 4 on (0.001 to 0.011 of the mix per section, 0.067 song-level, against 0.18 to 0.76 on every other song's voiced sections); the guitar stem holds 75 % of the mix's energy below 250 Hz under Verse 1, 87 % of its own energy there, centroid 202 Hz. In bars 0-4 Demucs put the low chord guitar on the *bass* stem (0.55); from bar 5 it put the real bass on the *guitar* stem: the LALAL.AI "changed its mind midway" failure, not bleed at −12 dB. pyin tracks the bass melody (pitch change 0.57, 0.70), rule A fires, and the strokes are the bass line's. Research: Seipel and Lerch's crosstalk weights hold at −12 to −18 dB and fail at −6 dB; here the "bleed" is the whole source (KQ4, spike D1).

## B. Suggestions, ranked

### B1. A per-section "stem is bass" gate from stem landing shares (new `music/bleed.py`; `StrumsStage` gains `separate/stems/bass.wav`)

Change: per planned section, on 4096/2048 STFT power, compute (a) the bass stem's share of the mix's energy below 250 Hz, (b) the guitar stem's share of the same, (c) the guitar stem's own share below 250 Hz, and song-level (d) the bass stem's RMS share of the mix; write them into `SectionPattern`. Gate: "bass on the guitar stem" when (d) is near empty while (b) and (c) are high. Measured band (spike D2): Badge verses b 0.75 and 0.23, c 0.87 and 0.46, d 0.001; every other voiced section c at most 0.55, d at least 0.07 song-level and 0.18 per section after intros. Near miss: Summer of '69 intro 0-4 (b 0.62, c 0.37, a picked riff before the bass enters), excluded by (c) and (d).

When it fires: `_riff_test` returns False for the member, its strokes print grey under "guitar not separated here" (Area 8: say what was not measured), and the rest rule's low-share test is skipped. Do not subtract the bass: spectral subtraction is harshest when λ is large, and separation quality is irrelevant to annotation.

Addresses: Badge Verse 1 and Verse 2, and any future bass/guitar swap. Nothing for Fame, AC/DC, Day Tripper (clean bass stems, c under 0.45).

Research: Seipel and Lerch 2018 (https://musicinformatics.gatech.edu/wp-content_nondefault/uploads/2018/06/Seipel-and-Lerch-2018-Multi-Track-Crosstalk-Reduction.pdf); MoisesDB bleed (https://arxiv.org/abs/2307.15913); LALAL.AI midway switch (https://www.lalal.ai/blog/andromeda-supports-guitars-updates-piano/). The explained-energy form is killed by D1; the landing-share form is this project's inference, measured on eleven songs with one positive.

Risk: no clean voiced section crosses c 0.55 or has an empty bass stem; the gate is a conjunction. Generality: stem-to-mix ratios only; thresholds stated as bands with the near miss recorded. Install cost: none.

### B2. Note-to-part assignment on a polyphonic note list, reference pitches per song (new `music/parts.py`; strums and riff stages read parts)

Change: a note list (onset, pitch, duration) for the source stem; two reference pitches per song, the mean of the lower and upper notes in the frames with the most simultaneous notes (the ISMIR 2015 baseline's rule, which the fitted MIDI 60 split omitted); each note to the nearer reference; contig creation (segment by simultaneous-note count) and a member is "two-part" when its bars with two sustained voices exceed a pooled share. In two-part members the strum vote reads the lower voice's onsets and the riff test and tab read the upper; one-part members are untouched.

Note source: basic-pitch is the only open polyphonic transcriber with a clean licence, but the 1.7 spike needed Python 3.11 and TensorFlow; verify its onnxruntime backend on the project's interpreter first (D3). Fallback with no dependency: CQT harmonic salience with per-frame peaks, accepting noisy notes (GuitarDuets saw little gain from estimated notes, so decide per bar, not per note).

Addresses: Fame (the lower guitar's strokes print; the upper line goes to the riff test), AC/DC 0-16, 34-43, 90-113 (chords lower, riff upper), Day Tripper 52-58 (confirms the strum; the riff reaches the tab gate), PSSOM 67-77 (contigs split chord bars from riff bars). Not AC/DC 74-90 without B3; not Badge unless B1 runs first.

Research: Guiomard-Kagan et al. ISMIR 2015 (https://www.ismir2015.uma.es/articles/180_Paper.pdf); Chew and Wu (https://infolab.usc.edu/imsc/research/project/vosa/vosa.pdf); partitura `estimate_voices` as a reference implementation (https://partitura.readthedocs.io/en/latest/_modules/partitura/musicanalysis/voice_separation.html); GuitarDuets (https://arxiv.org/html/2507.01172).

Risk: a one-part strum whose voicings straddle the references would split into two false voices, so the two-part call needs sustained polyphony across bars and a one-part member keeps today's path byte-for-byte (C2). Crossing parts and shared notes are the documented failure. Generality: references per song; the share pooled across ear-marked sections. Install cost: basic-pitch (ONNX path to verify) or none.

### B3. Repetition as the riff-versus-solo cue on the upper voice (extend `music/riff_line.py`)

Change: for a two-part member, bar-to-bar `note_jaccard` support of the upper voice's note bars (`choose_riff` and `_support` already compute it); high support is a riff (existing gate and tab), low is a solo, printed "solo over strum" with the lower voice's strokes and no tab. The same statistic is a second vote for the riff flag on one-part members pyin names (Day Tripper intro, All Fired Up 61-90), where the chroma features miss one- or two-pitch riffs.

Addresses: AC/DC 74-90, Badge's bridge and solo after B1, single-note riff false negatives. Research: Pati and Lerch's segment-repetition feature (https://musicinformatics.gatech.edu/wp-content_nondefault/uploads/2017/06/Pati_Lerch_2017_A-Dataset-and-Method-for-Electric-Guitar-Solo-Detection-in-Rock-Music.pdf); the report's rule four. Risk: low; it changes a header. Install cost: none.

### B4. Another separator: no

No open model separates lead from rhythm; every open guitar target is the MoisesDB sum. The RoFormer guitar checkpoints that beat htdemucs_6s (7 to 9 dB on MVSep's undisclosed set, https://www.mvsep.com/algorithms/17) are hosted or hundreds of MB and need the ZFTurbo or audio-separator RoFormer stack; the vocal checkpoint of that family is 640 MB. htdemucs_6s stays (55 MB, MIT, pip). Leave `roformer-sw` rejected or remove it. One cheap check (D6): whether the Badge swap is stable across seeds and the 4-stem `htdemucs` bass, since B1 only needs a trustworthy bass stem.

## C. Success criteria

**C1. Per-section ear truth table.** What exists today: Fame 61-71 and 71-81 (clips 11/21, 22: both wrong, two guitars); AC/DC 0-16 (clicks fit the riff), 16-34 (strum, wrong), 34-43 (riff over chords, wrong), 43-57 (strum, wrong), 74-90 (solo over strum, wrong), 90-113 (riff over chords, wrong); Day Tripper 0-11 (riff, unflagged, wrong), 52-58 (riff over strum, strokes fit the strum); Badge 4-28 and 61-70 (bass bleed, both wrong), 28-34 (bridge, agrees with the published tab, not ear-judged); PSSOM 67-77 (clip 8, chords then riff). Thirteen judged sections, nine two-part or bleed, four one-part, 3 of 13 right. Target: every two-part section prints the strum part's strokes or an honest "not separated" header; the four one-part verdicts unchanged; measured by a new listening pass with the same click-clip protocol, one clip per section.

**C2. Regression.** The ear-accepted strum sections (1.6 clips 12 to 29 marked YES or MOSTLY, 1.7 clip 14, AC/DC intro) print byte-identical `strums.json` pattern rows: `evaluate --compare` before and after shows zero changes on members the parts module calls one-part and a listed, explained change on every member it calls two-part.

**C3. Per-part onset F-measure.** Label the strum part's onsets from published tab rhythms at the grid's bar and beat times (AC/DC, Badge from Songsterr, Day Tripper) or an ear-placed click track (Fame). Score printed strokes against them with mir_eval onset F at 50 ms per section (https://mir-eval.readthedocs.io/latest/api/transcription.html) and report the share of printed strokes matching the lead part only. Pass: strum-part F rises on every two-part section against today's union and the lead-only share falls below 0.2; per song, no pooled mean (Pati and Lerch's macro rule).

**C4. Bleed-score separation.** One table of the three ratios and the song-level bass share for every voiced section of eleven songs. Pass: the gate fires on Badge 4-28 and 61-70 and on no ear-accepted section; the gap between the highest clean and lowest flagged section is stated per ratio, with a leave-one-song-out check that the band moves by less than the gap. Synthetic (SDX recipe, https://arxiv.org/html/2308.06979v4): on Need You Tonight, replace the guitar stem with the bass stem, and separately add the bass at −7 and −12 dB; the gate fires on the first, stays off at −12 dB, and the −7 dB result is recorded.

**C5. Optional GuitarSet test (CC BY 4.0, https://guitarset.weebly.com/).** Mix a player's comp and solo of the same lead sheet at 0, −6 and −12 dB solo level; run B2; score the lower voice against the comp annotation and the upper against the solo (mir_eval, 50 ms, `offset_ratio=None`). Thresholds set after the first run and frozen: comp-voice F at −6 dB above the unsplit union's by a margin reported with the curve; the two-part call true on every mix and false on every unmixed comp.

## D. Spikes on the existing runs (all six stems exist per song)

**D1. Cross-stem NNLS bleed score (Seipel and Lerch form). Run; killed.** One weight λ per section of the guitar-stem magnitude on the bass-stem magnitude, explained energy fraction. Badge: λ 71 to 255, explained 0.04 to 0.15, because the bass stem is empty; clean songs explain 0.00 to 0.15 too. No separation: the form assumes the bass stem holds the bass.

**D2. Low-band landing shares. Run; confirmed.** Badge Verse 1: guitar stem takes 0.75 of the mix's sub-250 Hz energy, bass stem 0.000, own low share 0.87, centroid 202 Hz. Every other voiced section on ten songs: own low share at most 0.55 (Summer of '69 outro, All Fired Up verses), bass stem share of the low band 0.08 to 0.65 outside intros. Badge Verse 2 reads 0.46 and is separated only by the empty bass stem (song-level 0.067). Summer of '69 intro 0-4 (0.62 of the low band on the guitar, bass not yet in) is the near miss. Badge's intro has the chord guitar on the bass stem (0.55); its verses have the bass on the guitar stem.

**D3. Polyphonic notes on this interpreter. Not run.** Does basic-pitch's onnxruntime backend install into the project venv? Run it on the four guitar stems, count notes per bar. Kill the basic-pitch route if it needs Python 3.11; fall back to CQT salience.

**D4. Reference-pitch split and contig share. Not run (needs D3).** Estimate two reference pitches from the maximal-polyphony frames, assign, count bars with two sustained voices per section. Confirm if the share separates AC/DC's four two-part sections from its two strums, and Fame from Need You Tonight's single riff, by a band at least as wide as the MIDI 60 split's (1.04 to 4.38 against 0.50 on AC/DC); kill otherwise.

**D5. Repetition of the upper voice. Not run (needs D4).** Bar-to-bar `note_jaccard` support: AC/DC 74-90 must read below 34-43 and 90-113, and Need You Tonight Verse 1 (the verified riff) high. Kill if the solo does not sit below both riffs.

**D6. Separator stability on Badge. Not run.** Re-run htdemucs_6s with other `SHIFT_SEED` values and the 4-stem `htdemucs`; measure the bass stem's share per section. If the 4-stem bass is clean, B1's song-level cue reads it instead.

## E. Do not do

- Do not subtract the bass from the guitar stem, by λ or a high-pass: under Badge's verses the bass is the content, and what remains is "single notes cut off in the background".
- Do not split by a fixed frequency (400 Hz, 260 Hz, MIDI 60) or by HPSS: the 1.7 spike showed the frequency splits overlap and HPSS breaks on The Cars and Need You Tonight; MIDI 60 is the baseline with its per-song estimate removed.
- Do not pursue `roformer-sw`, MVSep, Moises or any hosted or 600 MB separator; do not fine-tune Spleeter.
- Do not make `choose_source` per-section on Badge's evidence: its other and piano stems (0.02 to 0.32) hold no better guitar.
- Do not narrow B1's band on Badge, one positive song; wait for the next blind song with a swap.
- Do not treat a riff flag on a two-part member as wrong by default: on Day Tripper 52-58 the strokes fit the strum and "riff heard" is true; B2 and B3 refine the header there, not the strokes.
