# Review: stroke length (cut versus ringing), the withdrawn sustain line

Written 2026-10-08 against main at the 1.7 merge (74c11e0). Read-only review; the measurements quoted below were read from the eleven `runs\*\04_strums\strums.json` files as they stand.

## A. Diagnosis: why the dB-decay measure failed

`stroke_decay_db` (`src\youkelele\music\ring.py`) takes the loudest 10 ms RMS frame within half a slot of the onset and compares it with the frame exactly one slot later, clipped at 0 dB; `section_rings` calls a member ringing when the median of its measurable strokes is under `RING_SECTION_DB` 5. Four mechanisms, each visible in the ear clips, each named in the research.

**1. Clipping holds the level flat, so the slope measures the amplifier, not the hand.** On distorted stems amplitude sits near the clipper's ceiling for most of the ring (`note_duration_and_damping.md`, Q3 inferences; Herbst 2017's "frequency-related compression"). A damped stroke on such a stem can still read 0 to 3 dB in the first slot because the clipped sustain has not yet fallen out of the knee. Chelsea Dagger bar 61 (clip 3, "cut on the third note") and Wet Leg bar 18 (clip 4, "cut") sit at 10 dB-fall/gap ratios of 0.91 and 3.70 in the spike, inside the "rings" range (0.47 to 12.1). Across the eleven runs, 2 to 77 printed strokes per song measure exactly 0.0 dB (All Fired Up 77, Pour Some Sugar 60): the frame one slot later was louder than the peak frame, which is the compressor or the next stroke, never a string.

**2. The offset is ambiguous, so the clip itself cannot be labelled consistently.** The research's central finding is that offsets are the weakest output of every transcription model (Basic Pitch GuitarSet F 0.79 without offsets, 0.56 with; vocadito two-annotator agreement 0.64 with offsets, 0.74 without) because "the definition of offsets is less objective than onsets". The 1.6 pass shows the same thing in one listener: Need You Tonight bar 24 is "rings" in clip 7 and "all cut off" in clip 23. The spike's eleven ear bars are a single listener's single pass; the 8-of-11 ceiling it found is as likely the label's noise as the feature's.

**3. Per-section decisions hide per-stroke mixing.** The 1.6 A5 claim was a song-level separation (medians 1.8 to 2.7 dB on six songs against 8.3 and 8.7 on Fame and Need You Tonight). Sections are mixed: clips 1 and 3 are bars where one stroke rings and the next is cut, and a member-level flag draws the line through both. Nine of 68 section medians sat within 1 dB of the threshold. The research says the same: per-section flags must be derived statistics ("fraction of strokes labelled stops"), never the decision unit (`note_duration_and_damping.md`, Q5 inferences).

**4. Most strokes are never measured, and the measured ones are the sparse exceptions.** `RING_MIN_GAP_SLOTS` 1.5 drops any stroke whose next onset is nearer than 1.5 slots. On the current runs that is 50 to 92 % of printed strokes (The Cars 639 of 694 unmeasured, Wet Leg 536 of 643, Day Tripper 395 of 537, Summer of '69 306 of 533). A section's median therefore comes from its held strokes only, which biases every dense section toward "rings" by construction and makes the flag say most about density, not damping. The 1.6 spec admitted this ("no sustained-vs-dense distinction within a song").

A fifth, smaller mechanism: the separator's noise floor is time-varying, so a quiet tail on a Demucs stem is partly separator residue, which inflates any "fall to −X dB" statistic (Q3 inferences). Chelsea Dagger's intro at 12.16 dB "short" was a doorbell with no guitar (clip 31).

## B. Options, ranked

### Option 1 (recommended now): keep it withdrawn, and say so on the sheet

The renderer already ignores `rings` (`render\bar_svg.py` docstring "no sustain lines"; `render\html.py` sets every 1.5 stroke `rings=True` for the schema). What the sheet should say instead:

- A one-line legend phrase, in the editorial register the report recommends, for example "Stroke length is not measured; hold or damp as the record does." Place it with `TAB_LEGEND` in `render\html.py`, not per bar, so nothing on the page is drawn grey or dashed.
- The empty slots after a stroke already carry the rhythm; the line said nothing a strummer cannot hear.
- `stroke_decay_db`, `decay_db` and `rings` stay written (1.7 spec 6) so the spike in D can run on existing folders without a re-run.

Failures addressed: all four mechanisms, by not asserting anything. Research support: AnthemScore's documented rule is "each note ends where the next note starts" ([lunaverus.com/documentation](https://lunaverus.com/documentation)); Soundslice's let-ring is a manual marking ([soundslice.com/help/.../let-ring](https://soundslice.com/help/en/creating/tablature/121/let-ring)); no product prints let-ring from audio. Risk: none to correctness; the sheet under-informs on genuinely staccato songs (Fame, Need You Tonight). Generality: full. Install cost: none.

### Option 2: a per-stroke "pitched structure persists" feature

The research's one positive lead: Liang et al. found pitch confidence beat energy for soft decays (F 0.654 vs 0.508) because the decay tail "exhibits similar signal characteristics as soft onsets when looking reversely" ([ismir2015.uma.es/articles/118_Paper.pdf](https://www.ismir2015.uma.es/articles/118_Paper.pdf)); Kehling's decay-segment spectral features (flatness, crest, inharmonicity) classify plucking style at 93 % on clean notes ([dafx14 Kehling](https://www.dafx14.fau.de/papers/dafx14_christian_kehling_automatic_tablature_trans.pdf)). Whether any of it survives clipping and separation is untested anywhere; the notes call it "an inference, not a tested result".

Exact computation, if tried:

- Input: the strums stage's source stem (`y`, `sr`), the gate-passed onset times, each onset's bar and slot width, as `_stroke_decays` already receives them.
- Per onset: the window from onset + 20 ms to the earlier of the next onset and the bar end (the same window `name_notes` in `music\pitch.py` uses). Compute three frame series on it: (a) pyin `voiced_prob` from `librosa.pyin` (the third return value `track_pitch` currently discards; frame 2048, hop 256 as `PYIN_FMIN`/`PYIN_FMAX`); (b) spectral flatness, `librosa.feature.spectral_flatness`, same hop; (c) a harmonic share: `librosa.effects.hpss` once per stem, then the harmonic RMS over the full RMS per frame. No new dependency.
- Per-stroke statistic: the sounding fraction, the KOR-style number the research recommends ([arXiv 2406.08454](https://arxiv.org/pdf/2406.08454)): the last frame at which voiced_prob is at least half its value in the first 50 ms of the window, divided by the window length. Report the same for flatness (first frame where flatness doubles its early value) and harmonic share (first frame below half).
- Scale invariance (the cross-cutting rule): each series is referenced to the stroke's own early frames, never to an absolute threshold.
- Where it would live: a `stroke_sounding_fraction` function beside `stroke_decay_db` in `music\ring.py`; the stage calls it where `_stroke_decays` runs; the per-stroke value joins `Stroke.decay_db` in `schemas.py`. The section flag, if any, becomes "share of strokes with fraction under 0.5", a derived statistic.
- It is cheap: pyin already runs once per voiced stem in the strums stage (the 1.7 code path tracks pitch for every voiced member).

Failures addressed: mechanism 1 (timbre persists under clipping while amplitude is flat) and 4 (every stroke gets a value, including those with short gaps, since the fraction is of the gap). Not addressed: mechanism 2 (label ambiguity), which is why C must run first. Risk: on a Demucs stem the separator may hold a pitched residue in the tail, so voicing persists for a damped stroke; pyin on a strummed chord is monophonic over a polyphonic signal and its voicing may flicker. Generality: constants are ratios to the stroke's own start, checked by pooled sweep in D. Install cost: none.

### Option 3: a per-song or per-section articulation label only

The song-level verdict was right on 4 of 5 short clips (clips 8 to 11 damped, clip 7 not; 1.7 spec 6). A header phrase ("played damped" or "played ringing") in the state vocabulary, never a per-stroke line. Mechanism 4 still biases it: on The Cars only 8 % of strokes are measured. If taken, the label must come from the Option 2 statistic over all strokes, not the current median over the held few, and the label should print only when the share is outside a band (for example under 0.25 or over 0.75 of strokes damped) measured across every section of the eleven songs, with the middle band silent. Research support: palm mute as a per-note timbre class is the only articulation the literature finds measurable (Su, Yu, Yang 2014, muting F 68.7 % with 35 % leaking to "normal", [archives.ismir.net/ismir2014/paper/000213.pdf](https://archives.ismir.net/ismir2014/paper/000213.pdf); TART 2026 palm-mute F1 97.9 % on pooled clean sets, [arxiv.org/abs/2609.11904](https://arxiv.org/abs/2609.11904)). Risk: one song (Need You Tonight) mixes damped verses with a ringing chorus, so a song label is wrong somewhere on it; a section label needs the D spike to show sections are not mixed. Generality: moderate. Install cost: none.

### Option 4: a supervised palm-mute classifier

Kehling's attack/decay feature statistics or TART's 160k-parameter CNN-BiLSTM in torch, trained on Guitar-TECHS (CC BY 4.0, 138 palm-muted notes per player) and EGFxSet (CC BY 4.0). Supported as feasible by the research; not supported on separated or distorted stems (no paper evaluates either), and Su's one distortion-inclusive result is the overlap 1.7 already found. Risk: a model fitted to isolated clean notes applied to strummed chords on a Demucs stem; the two-dataset shift TART itself reports. Install cost: dataset download, a training script, a checkpoint in the repo. Not recommended before Option 2's spike shows a signal exists.

## C. Success criteria

Protocol (the notes' own, Q5 inferences, assembled from Liang 2015 and vocadito):

1. Two listeners, independently. Slowed playback of the separated stem, the mix available for context, the existing `make_clips.py` click track so the stroke under judgment is unambiguous.
2. Per stroke, a three-way label: rings into the next stroke / stops before it / undecidable. No timestamps. Define "stops" as audibly silent before half the gap (a KOR-style rule) so both listeners use one rule.
3. How many: 120 strokes, drawn as 10 from each of the eleven runs plus 10 more from Need You Tonight (the one song with mixed sections), stratified so half have a gap of 1.5 slots or more and half under (the half the current measure skips). Across all songs, never one.
4. Report agreement first: raw agreement and Cohen's kappa on the two-way label after dropping strokes either listener called undecidable; also the undecidable share. If kappa is under 0.4 on the decided strokes, or more than a third are undecidable, the feature stays withdrawn and the record says the label is not reproducible on these stems. That is a legitimate finding (vocadito's 0.64 is on clean solo vocals).
5. Metric for a detector: balanced accuracy on the strokes both listeners agreed on, against the majority-class baseline, with a leave-one-song-out check of the single threshold on the sounding fraction. Threshold to ship a per-stroke mark: balanced accuracy at least 0.80 and no song below 0.70, and the chosen ratio sitting on a flat region of the pooled curve. For a per-section label (Option 3): every agreed section's damped share must fall outside the silent middle band on the correct side, with the two listeners' section shares within 0.2 of each other.
6. What keeps it withdrawn: kappa under 0.4; or balanced accuracy under 0.80 pooled; or any one song under 0.70; or a threshold that moves by more than the band's width when one song is left out. Any one of these.

## D. Spikes on the existing runs

Both read `strums.json` and the guitar stem; no stage re-run.

**Spike 1 (decides Option 2 against Option 1).** Compute the three sounding fractions of Option 2 for every printed stroke of all eleven songs. Then, on the fourteen ear bars already labelled (clips 1 to 10, 30, 32, 33, and the spike's eleven), plot each fraction against the ear label. Confirm: "cut" bars cluster below some ratio and "rings" bars above it with at most one crossing, and the ordering is in the physical direction (damped means shorter). Kill: the ranges overlap as fully as the dB-fall ratios did (0.31 to 19.7 against 0.47 to 12.1), or the best split runs backwards. A confirm earns the C protocol; a kill closes Option 2 without labelling anything.

**Spike 2 (decides Option 3).** With the same per-stroke fractions, compute each section's damped share (fraction under 0.5) across all sections of all songs. Confirm: Fame's and Need You Tonight's verse sections sit above 0.75 and the ringing songs' sections below 0.25, with Need You Tonight's chorus 24-31 on the ringing side and Summer of '69's intro (clip 30, "not damped") and The Cars Chorus 2 and Verse 3 (clips 32, 33, "damped") on their heard sides. Kill: more than a quarter of sections land in the middle band, or any of those five ear-judged sections lands on the wrong side. A kill means sections are mixed and no section label is well defined.

## E. Do not do

- Do not re-tune `RING_SECTION_DB`, `RING_MIN_GAP_SLOTS`, the RMS frame or the band. The spike already tried bands and fall depths; the measure is wrong in kind, not in constant.
- Do not draw a per-stroke mark from a per-section flag again, or a grey or dashed line to hedge it. 4 of 6 held clips contradicted the line; the report's rule is editorial words, not grey.
- Do not lower the 1.5-slot gap to measure more strokes with the dB method; the next onset's attack enters the window and every stroke reads 0 dB.
- Do not use GuitarSet offsets as ground truth; they are an energy/flux heuristic, not a perceptual label ([ismir2018 GuitarSet](https://ismir2018.ismir.net/doc/pdfs/188_Paper.pdf)).
- Do not add Basic Pitch, Omnizart or Kong's model for offsets; each ends a note at a decay-threshold crossing, which is the measure that failed.
- Do not label strokes with one listener in one pass; clip 7 against clip 23 shows a single ear contradicts itself on this question.
- Do not score a detector before the two-listener agreement is reported; a feature cannot beat a label that does not exist.
