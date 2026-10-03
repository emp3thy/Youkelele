# Chord recognition, no-chord handling and key detection: research report

Date: 2026-10-03. Strand: harmony stage of the Youkelele chain (Chord-CNN-LSTM on the mix, beat snapping, triad reduction, Krumhansl key). Written for the agents who will map this onto the code; every claim is tagged **[verified]** (read in a source or measured on the four validation runs in this session) or **[inferred]** (my reasoning from verified facts). Measurement scripts and their outputs are in `scratchpad\research\` (`stems_experiment.py`, `key_experiment.py`, `mode_experiment.py`, `beat_decode_experiment.py`, `stems_out\`, `beat_decode_out\`); the extracted paper texts are in `scratchpad\research\pdf\`. Nothing under the project tree was edited.

Version 1.2 work already in flight (four-bar sections, mean tempo, title cleaning, filling all-`N` bars by chroma template match restricted to the song's chord set, passing chords, phrase alignment, repeated row blocks) is taken as given. Where this report touches the fill rule it is to refine it with evidence, not to propose it again.

## 0. What the harmony stage does today [verified from code]

- `src/youkelele/models/chords.py` runs the vendored `chord_recognition.py` on `ingest/audio.wav` (the full mix) with the `submission` dictionary. The vendored script (cached at `~/.youkelele/models/chord_cnn_lstm/`) loads audio at 22 050 Hz, hop 512, computes a CQT, averages five `joint_chord_net_ismir_naive_v1.0_reweight(0.0,10.0)` nets and decodes with `XHMMDecoder.decode_to_chordlab(entry, probs, False)`. That call leaves `use_beats=False` and `use_downbeats=False`: the decoder is a frame-level Viterbi with a fixed change penalty `diff_trans_penalty=30` nats; it never sees the Beat This! grid the chain already has. The decoder does support beat-aware decoding (`use_beats`, `use_downbeats`, `beat_trans_penalty=(15, 45, 100)` for beat, downbeat, half-bar) via an `entry.beat` list of `[time, beat_position]` tokens (`extractors/xhmm_ismir.py`, `__get_beat_arr`).
- The `submission` dictionary (`data/submission_chord_list.txt`) holds 25 qualities: `maj min dim aug maj/3 maj/5 min/b3 min/5 maj7 7 min7 hdim7 dim7 maj9 9 min9 11 13 sus4 sus2 sus4(b7) maj/2 maj/b7 min/2 min/b7` plus `N`. There is **no power-chord class** (`5`) in any of the four dictionaries, so a no-third riff can only come out as `maj`, `min` or `N`.
- On the four validation runs the raw `.lab` labels are only `maj`, `min` and `N` (Chelsea Dagger 9 labels, Summer of '69 8, Pour Some Sugar On Me 7, Wet Leg 5). Running the same model on separated stems does produce inversions (`D:maj/5`, `F#:maj/5`), so the model can emit them; on these mixes it did not. The triad reduction in `music/triads.py` therefore changed nothing, as the lessons document already noted.
- `music/snap.py` gives each beat the label with the largest overlap and merges runs; confidence is the mean overlap share. There is no smoothing after snapping and no use of bar position.
- `music/key.py` correlates the mean `chroma_cqt` of the **full mix** with Krumhansl-Kessler profiles; confidence is the relative margin between the best and second key. Recorded confidences: 0.006 (Chelsea), 0.056 (S69), 0.010 (PSSOM), 0.136 (Wet Leg).
- The v1.2 worktree adds `music/fill.py` (`fill_silent_bars`, provisional constants `FILL_MIN_ENERGY=0.3`, `FILL_MIN_MATCH=0.5`, `FILL_MIN_MARGIN=0.1`) and sums `guitar, bass, piano, other` into a harmonic mix in `stages/harmony.py`.

## 1. Failure modes

### 1.1 `N` over intros and solos while the band plays

**Observed.** Chelsea Dagger: `N` from 0.58 s to 14.38 s (bars 0 to 8). PSSOM: 27 to 29 percent of the song is `N`, including 11 of 17 bars of the solo and breakdown (bars 67 to 83) [verified, chords.json and the lessons document].

**Why, measured this session.**

- The decoder is not the cause. In `XHMMDecoder.get_chord_tag_obs` the `N` state is *penalised* by `log(24)` relative to every chord (it has no bass term to add), so `N` is only decoded when the ensemble's triad probability for `N` dominates [verified, `xhmm_decoder.py` / `xhmm_ismir.py`].
- Separated stems do not rescue the Chelsea intro. Running the vendored model on the summed harmonic stems gives `N` 0.91 of the intro window (0.99 on the mix); on guitar+other alone it is 1.0 [verified, `stems_out/summary.json`]. Bar-level chroma of the harmonic stems over bars 1 to 7 correlates best with an **out-of-set** template, `C:min` (0.59 to 0.83 on bars 2 to 6), while the best **in-set** template is `C:maj` at 0.49 to 0.63 on bars 3 to 5 and `B:maj` at 0.47 and 0.38 on bars 2 and 6 [verified, `key_experiment.py` output]. The intro is a melodic riff, not a strummed chord: this is the "melody versus chord sequence is a matter of opinion" ambiguity Pauwels et al. list under their problem 6, and Humphrey and Bello's first insight that some passages "do not truly make use of, and are thus not well described by, chords" [verified, both papers].
- PSSOM's solo and breakdown are different: here stems help. `N` in the 189.5 to 237.5 s window falls from 0.68 (mix) to 0.52 (harmonic stems) to 0.39 (guitar+other), and the model recovers `D:maj` (0.16 and 0.21 of the window), the bridge chord the lessons document said was "never detected" [verified]. Unrestricted bar templates on the harmonic stems also pick `D:maj` on bars 67, 69, 73 and 74 (0.79, 0.37, 0.39, 0.56), whereas the best in-set template on those bars is `A:maj` (0.44, 0.23, 0.19, 0.33) [verified].

**Consequence for the v1.2 fill rule [inferred].** Restricting the template match to the song's existing chord set will (a) print `A` where the record plays `D` in PSSOM's breakdown, and (b) print `B` (a barre) on Chelsea bars 2 and 6 unless `FILL_MIN_MATCH` is at least 0.5, while the honest answer for that intro is "riff". Section 4 gives a concrete amendment.

**Literature.** Modern systems treat `N` as a first-class class but with care: the MIREX 2025 Würzburg system ignores `N` frames in the loss entirely [verified, Ding and Weiß 2025]; Jiang et al. train a distinct no-chord target as part of the structured chord vector (`N` root) [verified]. Nobody in the surveyed literature attempts to recover chords in riff-only passages; sheet makers (Ultimate Guitar style charts) write "N.C." or "riff" there, which is also what the lessons document proposes.

### 1.2 Power chords read as major, and the wrong key mode

**Observed.** PSSOM's verse riff (C#5 on the record) comes out `C#:maj` 29 percent of song time; the key comes out C# major against the published C# minor [verified].

**Why.** (a) No `5` class exists in the model's dictionaries (section 0). (b) The proposed fix in lessons item 7 (flag a major triad as a power chord when its chroma third is weak against its fifth) **does not hold on the data**: on the harmonic stems the mean third-to-fifth chroma ratio for `C#:maj` in PSSOM is 0.69, *higher* than for genuine major triads such as `D:maj` (0.56) and `G:maj` (0.57) in Chelsea Dagger or `A:maj` (0.48) in Summer of '69 [verified, `key_experiment.py`]. The fifth harmonic of a distorted root (and of the bass) lands on the major third, so chroma shows a third even when no third is played [inferred, consistent with Pauwels et al.'s remark that harmonics are "misassigned in pitch class" in log-frequency features]. A chroma threshold is therefore not a usable power-chord detector.

**Literature.** Rock harmony is not classical major or minor: in the Temperley and de Clercq rock corpus the "minor" cluster favours b7 over 7 and 6 over b6, "with a significant presence of 3 as well", and the authors "found in creating our corpus that it was often quite problematic to label songs as major or minor", so they treat a rock key as a tonic pitch class [verified, Temperley and de Clercq 2013, sections 4 and 5]. The GOAT guitar dataset and the Rock dataset used for symbolic chord recognition explicitly carry power chords as a class [verified, search results]; `mir_eval.chord.QUALITIES` has a `5` quality so a `X:5` label would survive the project's `to_triad` path if the model or a post-rule produced it [verified, `mir_eval` 0.8.2 in the project venv].

### 1.3 Relative-key and tonic ambiguity in key estimation

**Observed.** Chelsea: D major 0.766 against G major 0.762 on the mix. PSSOM: C# major 0.550 against C# minor 0.544. Chord-time diatonic matching alone gives E minor for Chelsea, a D major / B minor tie for S69 and F# minor for PSSOM [verified, `key_experiment.py`; agrees with lessons item 7].

**Measured key table (this session).** Truths: S69 D major, PSSOM C# minor; Chelsea D or G major unverified; Wet Leg C major likely.

| Source of chroma | Profile | Chelsea | S69 | PSSOM | Wet Leg |
|---|---|---|---|---|---|
| full mix (current) | Krumhansl-Kessler | D maj 0.766 > G maj 0.762 | D maj 0.844 > A maj 0.797 | **C# maj 0.550 > C# min 0.544** | C maj 0.695 |
| full mix | Temperley CBMS | D maj > G maj | D maj | B maj (wrong) | C maj |
| full mix | Kostka-Payne | G maj 0.741 > D maj 0.724 | D maj | G# min (wrong) | C maj |
| harmonic stems (guitar+bass+piano+other) | Krumhansl-Kessler | D maj 0.844 > G maj 0.778 | **A maj 0.883 > D maj 0.807** (wrong) | **C# min 0.716 > E maj 0.635** (right) | C maj 0.710 |
| HPSS harmonic of the mix (`librosa.effects.harmonic`, margin 3) | Krumhansl-Kessler | G maj 0.816 > D maj 0.787 | D maj 0.811 > A maj 0.807 | C# min 0.480 > C# maj 0.458 (right, thin) | C maj 0.611 |
| chord time, strict diatonic sets | | E min 0.955, G maj 0.947 | D maj 0.930 = B min 0.930 | F# min 0.716 (wrong) | four-way tie |

No single chroma source gets all four right at once; the stems fix PSSOM but break S69 (A, the dominant, is 40 percent of chord time and the stems make it louder than D). Chord-time matching cannot separate relative keys by construction (they share the diatonic set). But **mode decided at a fixed tonic is right four out of four on the harmonic stems** with clear margins: Chelsea major at either G or D (0.778 vs 0.464; 0.844 vs 0.498), S69 D major (0.807 vs 0.508), PSSOM C# minor (0.716 vs 0.338), Wet Leg C major (0.710 vs 0.490). The mix is what makes PSSOM a coin toss (0.550 vs 0.544) [verified, `mode_experiment.py`]. The vocals stem alone also says C# minor for PSSOM (0.521 vs 0.432) and D major for S69 (0.621 vs 0.538), a weaker but independent cue [verified].

Tonic cues measured: chord-root time share (Chelsea G 38 / D 32; S69 D 40.2 / A 39.6; PSSOM C# 41.5; Wet Leg C 53) and the final chord (G, D, B, C#). Root share alone is marginal for S69; the final chord is right for Chelsea, S69 and Wet Leg (its C# is the odd passing chord in the last bar) and wrong for PSSOM (fade on B). Section-start chords are *not* a tonic cue: S69's choruses start on Bm (vi) [verified].

**Literature.** MIREX scores relative major/minor errors at 0.3 and parallel errors at 0.2, and madmom's `evaluation.key` implements exactly that error taxonomy [verified]. Music21's notes on the classic profiles: Krumhansl-Schmuckler has a "strong tendency to identify the dominant key as the tonic" (our S69-on-stems failure), Temperley-Kostka-Payne a "strong tendency to identify the relative major as the tonic in minor keys" [verified]. Albrecht and Shanahan (2013) built profiles that handle minor better: 92.7 / 85.5 percent (major / minor) against 69.0 / 83.2 for Krumhansl-Schmuckler on symbolic data; Nápoles López's HMM key finder reaches 94.4 percent overall with a meta-classifier over several profiles [verified, napoles19key.pdf table 3]. The Albrecht-Shanahan vectors, as implemented by one practitioner project: major `[0.238, 0.006, 0.111, 0.006, 0.137, 0.094, 0.016, 0.214, 0.009, 0.080, 0.008, 0.081]`, minor `[0.220, 0.006, 0.104, 0.123, 0.019, 0.103, 0.012, 0.214, 0.062, 0.022, 0.061, 0.052]` [verified from `akoita/resonate` source; not checked against the paper]. The same project measured that HPSS (margin 3.0) before chroma raised usable key detections from 15 to 19 of 25 tracks and Albrecht-Shanahan with a 0.05 confidence cutoff raised GiantSteps exact accuracy from 49.3 to 56.9 percent [verified, their issues 2016 and 2018]. For rock specifically, Temperley and de Clercq's symbolic models: duration-weighted root distribution 86 percent, adding metrical strength 91 percent, adding melody 97 percent on 100 rock songs; Noland and Sandler's chord-transition model 87 percent on the Beatles [verified]. The supervised CNN key classifier (Korzeniowski and Widmer 2018, in madmom) scores 85.1 weighted / 79.9 percent exact on McGill Billboard and 74.3 weighted on the Rock corpus [verified].

### 1.4 Boundaries, smoothing and fragmentation

**Observed.** The model's segment boundaries lag by 0.1 to 0.4 s (spike B), so `snap_to_beats` takes a majority vote per beat; 10 of Chelsea's 68 changes land on beat 2 and S69 has 72 of 75 changes on bar starts [verified, spikes and lessons]. The vendored decoder is frame-level, so chord durations follow a geometric distribution and the only temporal knowledge is one penalty.

**Literature.** Pauwels et al. (problems 3 and 4): Viterbi smoothing of chord posteriors beats filtering chroma; explicit duration distributions "were not found to have a major influence"; beat-synchronous processing "may not be advantageous compared to smoothing with an HMM" given 2010-era beat trackers, but lowers the processing rate and is worth revisiting with today's trackers [verified]. Korzeniowski and Widmer show frame-level language models are futile and that chord-level duration plus harmonic language models add about one point (WCSR 0.7955 to 0.8047, significant) [verified, arXiv 1808.05335]. The 2026 event-based sequence-to-sequence approach reformulates ACR as segment-level prediction to cut over-segmentation [verified, arXiv 2604.24386]. `mir_eval.chord.seg/overseg/underseg` are the standard segmentation metrics [verified].

**Measured this session: feeding the chain's beats to the vendored decoder.** See section 4.3.

### 1.5 Vocabulary and class imbalance: a research problem that is not ours

Large-vocabulary accuracy is where the field's effort goes: class-wise accuracy of Jiang et al.'s own model is 0.33 to 0.38 against 0.77 frame-wise [verified, Jiang 2019 and ChordFormer table III]; maj and min are 63 and 16 percent of Isophonics frames and the five commonest qualities cover about 80 percent of pop datasets [verified, Bortolozzo 2020; Pauwels 2019]. For a ukulele chord grid that prints triads, this is mostly irrelevant: the triad reduction is the design, and on these four rock songs the model emitted no sevenths anyway. What *does* transfer: the annotator subjectivity ceiling. Human annotators agree 73 percent on maj/min labels and 54 percent on the most complex labels (Koops et al. 2019); root agreement between annotators is 76 to 94 percent (Pauwels et al.); state-of-the-art systems already score beyond that ceiling by about 10 points [verified]. Humphrey and Bello add that reference annotations are also hurt by non-A440 recordings ("some varying by more than a quarter-tone", so every label is a semitone off) [verified]. The project computes chroma without tuning estimation in `fill.py`; `librosa.feature.chroma_cqt` estimates tuning by default [verified from librosa behaviour, inferred relevance].

## 2. What others do

### 2.1 Systems and techniques

| Approach | What it does | Evidence | Fit for this chain |
|---|---|---|---|
| Chordify / HarmTrace (de Haas, Magalhães, Wiering) | Beat-synchronous chroma (Sonic Annotator, downbeats); "at beat positions where the audio matches a particular chord well, this chord is used; in case there is uncertainty ... the HarmTrace harmony model will select the correct chords based on the rules of tonal harmony" [verified, LBD42 2015]; founder quotes 70 to 95 percent correct depending on music [verified, 2013 interview] | Key-aware disambiguation only where the acoustic evidence is weak | Directly portable as a post-rule on low-confidence beats (section 4.6) |
| Mauch, Noland, Dixon 2009 | Average chroma across repeated section instances (verse 1 and verse 2 share chords) before decoding | Relative overlap 61.7 to 64.1 percent (auto segmentation), 63.4 to 65.9 with automatic beats; improves 74 percent of songs; "consistent and more readily readable chord labels" [verified] | The grid stage already has section clusters and v1.2 adds repeated-row detection; voting chords per bar position across same-cluster sections is cheap |
| Mauch and Dixon 2010 | Six-layer DBN jointly over metric position, key, chord and bass | 71 percent on 109 chords, MIREX 2008 set [verified] | Design reference for "key-aware decoding"; too heavy to port |
| Korzeniowski and Widmer 2016 / 2018 (madmom) | CNN features plus CRF; later chord-level duration and language models with beam search | 82.9 WCSR maj/min Isophonics; language models +1 point [verified] | Frame-level smoothing already present; chord-level duration model is a deeper option |
| BTC (Park et al. 2019) and ChordMini (Phan 2026) | Transformer; ChordMini distils BTC into 3.03M-parameter students with 1 000 h of pseudo-labelled audio | BTC maj/min 82.7, MIREX 80.8; ChordMini student Root 83.03, Majmin 80.24 on a 600-song set [verified] | Code MIT, BTC weights CC BY-NC-SA, ChordMini checkpoint licence unstated; pins torch 2.9.1 / numpy 1.26.4 [verified, assumption checks] |
| ChordFormer (2025) | Conformer with structured 6-component chord vector and reweighted loss | Root 84.69 / MajMin 84.09 / MIREX 83.62 against Jiang's 83.39 / 82.62 / 81.52 [verified]; no code or weights [verified] | Not usable |
| MIREX 2025 Würzburg ensemble | Transformer + CRNN, pre-trained on 100 h of classical, fine-tuned on Isophonics; predicts chord change, root, bass, pitch classes; `N` ignored in loss | Root 84.9, Majmin 84.7 on RWC Pop; segmentation under/over 89.2 / 86.7 [verified] | Shows the ceiling: about 2 points over our model |
| Event-based seq2seq (2026) | Predicts chord *segments* autoregressively | Fewer over-segmentations, gains on rare qualities [verified abstract] | Research only |
| DECIBEL (Odekerken, Koops, Volk 2021) | Align crowd-sourced tabs and MIDI to audio and fuse with ACE output | Improves every tested ACE method by 0.5 to 13.6 points [verified] | Legally and operationally awkward (scraping tab sites); conceptually the strongest lever for well-known songs |
| Source separation before recognition (Mitoma and Furuya, APSIPA 2025) | HTDemucs stems, double the `other` stem, remix, run BTC | Triads 75.52 to 75.72 percent, 2 285 net frames fixed, significant; doubling vocals *hurts* (74.75); failure case: amplified single-note guitar riffs become `sus4` / wrong chords [verified] | Matches this session's measurement: stems help specific passages (PSSOM solo) and are not a blanket win |
| Practitioner key detection (`akoita/resonate`, 2026) | HPSS margin 3 before chroma; Albrecht-Shanahan profiles; relative-margin confidence with 0.05 cutoff | 15 to 19 of 25 usable keys; GiantSteps 49.3 to 56.9 percent [verified] | Same recipe as our `estimate_key`; the stems give an even cleaner harmonic signal |
| Rare chords with unlabelled data (Bortolozzo et al. 2020) | Focal loss and noisy-student self-training | hdim7 2 to 41 percent [verified] | Only relevant if retraining |

### 2.2 Libraries and licences for a CPU-only Windows Python 3.12 chain

| Library | Vocabulary | Licence | Windows / 3.12 | Note |
|---|---|---|---|---|
| Chord-CNN-LSTM (in use) | 25-quality `submission` dict, no `5` | MIT including the committed checkpoints [verified] | Works today; 10 s per song on this CPU | Only two GitHub issues, both about reproducing training [verified] |
| ChordMini (BTC, 2E1D students) | 170 (14 qualities, no `5`) | Code MIT; checkpoint licence not stated; teacher weights CC BY-NC-SA [verified] | Same torch stack if pins are ignored (assumption checks) | 3.03M / 2.2M parameters |
| BTC original | 25 or 170 | Code MIT, weights CC BY-NC-SA 4.0 [verified] | CQT 22 050 Hz, hop 2048 | Non-commercial weights |
| madmom | maj/min only (`DeepChroma` CRF, `CNNChordFeature` + CRF); `CNNKeyRecognitionProcessor` 24 keys | Code BSD, models CC BY-NC-SA 4.0 [verified] | PyPI stops at Python 3.9; git main lists 3.9 to 3.12 classifiers, needs Cython and MSVC build tools [verified] | Key CNN is the best off-the-shelf key model but non-commercial |
| Chordino / NNLS Chroma | maj/min and a few others | GPL [verified] | Vamp plugin binary; `chord-extractor` is GPLv2, Python <3.12, ships a Linux binary only [verified] | Classic baseline, lowest accuracy in Jiang's comparison |
| autochord | 25 (maj/min/N) | open source; TensorFlow + NNLS Vamp | TF on Windows 3.12 is heavy | 67 percent test accuracy [verified] |
| crema | 602 classes incl. inversions | BSD-2-Clause [verified] | `tensorflow>=2.0`, `keras>=2.6`, `pumpp`, `jams` [verified setup.cfg] | Heavy dependency footprint |
| Essentia (`ChordsDetection`, `ChordsDetectionBeats`, `Key` with `edma`, `bgate`, `temperley` ... profiles) | maj/min | AGPL-3.0 [verified] | **No Windows wheels** (latest 2.1b6.dev1438, Linux and macOS only) [verified] | Rule out |
| libfmp (Müller) | templates + 24-state HMM | MIT, pip | Pure Python | Teaching-quality code for template/Viterbi recognisers |
| librosa `sequence.viterbi_discriminative` + `transition_loop` | any | ISC | Already installed | Self-loop 0.9 example in docs [verified] |

## 3. Research summary: state of the art and what is good enough

- **Accuracy ceiling.** Maj/min WCSR on Isophonics-style pop sits at 82 to 85 percent for every modern architecture (CNN+CRF 82.9, BTC 82.7, Jiang 82.6, ChordFormer 84.1, Würzburg 84.7) [verified]. Human annotators agree about 73 percent on the same labels [verified]. The vendored model is within about two points of the best published system. **Swapping the recogniser is not where the quality will come from; context (beats, sections, key, stems) and presentation rules are** [inferred].
- **Where the remaining errors are.** Related chords (triad vs its seventh; chords sharing two pitch classes such as F#m and A) [verified, BTC error analysis and Humphrey and Bello insight 2]; passages without chords; mis-tuned recordings; and disagreement about granularity (passing chords, anacrusis) [verified]. The 2025 to 2026 papers attack class imbalance and over-segmentation, not these.
- **Beat and structure.** The field's consensus is that chord posteriors should be smoothed with sequence decoding, that beat-synchronous decoding is promising now that beat trackers are good, and that long-range structure (repetition) gives consistent, more readable output [verified, Pauwels problem 3; Mauch 2009].
- **Stems.** One peer-reviewed study: a small global gain, bigger local gains, and a known failure on single-note riffs [verified]. This session's measurement agrees.
- **Key.** Template methods on clean harmonic chroma remain competitive; the big documented gains come from (a) removing percussion before chroma, (b) better profiles for minor, and (c) deciding tonic and mode from different evidence (rock tonic from chord roots and metrical position, mode from pitch-class content) [verified]. Supervised CNNs add about 1 to 10 points depending on genre but carry non-commercial licences [verified].
- **Good enough for this product.** A chord grid whose chord *set* matches the published chart and whose changes fall on bar lines (S69 already) is playable; the user-facing failures are whole intros printed `N.C.`, a wrong key mode in the header (which also drives the capo and the printed chord quality), and a barre chord printed where a power chord riff plays. Those are exactly the three measured failures above.

## 4. Easy wins (ordered by evidence and cost)

### 4.1 Estimate the key from the harmonic stems and decide the mode at a fixed tonic

Code: `music/key.py` (`chroma_mean_for`, `estimate_key`), `stages/harmony.py` (already builds the harmonic mix for the fill).

Evidence (section 1.3): on the harmonic stems the Krumhansl correlation at a fixed tonic picks the right mode 4 of 4 with margins of 0.2 to 0.38, where the mix gives 0.006 for PSSOM. Design:

1. Candidate tonics: chord roots covering at least 20 percent of chord time (Chelsea G, D; S69 D, A; PSSOM C#, B; Wet Leg C, F) plus the top two tonics from the stems' Krumhansl ranking.
2. Tonic score per candidate = chord-time share of that root + a bonus if it is the final sounding chord + a bonus if it is the chord sounding at the end of the longest repeated section (Mauch-style "chorus end"); the pipeline's existing section clusters give that. Do **not** use section-start chords (S69's choruses start on vi).
3. Mode at the chosen tonic = argmax of the Krumhansl major vs minor correlation of the **harmonic stems** chroma (fallback HPSS of the mix when stems are missing). Report `confidence` as that margin, not the 24-way margin.
4. Keep the current full-mix estimate in the JSON as `key_mix` for the validation table.

Caveat to state in the header: rock minor is not classical minor; print the key as "C# minor (rock)" or just the tonic plus mode, and do not use the mode to force chord qualities except through rule 4.5 [inferred from Temperley and de Clercq].

Also worth doing: run Kostka-Payne and Albrecht-Shanahan profiles alongside Krumhansl and expose all three in `--verbose`; on these four songs they disagree on the mix for PSSOM and Chelsea, which is itself a confidence signal [verified table in 1.3].

### 4.2 Refine the v1.2 fill rule with the measured bar correlations

Code: `music/fill.py` (`_best_match`, `fill_silent_bars`), spec 1.2 section 3.4.

- Match against **all 24 triad templates**, then apply the song-set restriction only as a preference: if the unrestricted best is out of set, beats the in-set best by more than `FILL_MIN_MARGIN` and is diatonic to the (new) key, allow it. Evidence: PSSOM bars 67 and 74 (`D:maj` 0.79 / 0.56 against in-set `A:maj` 0.44 / 0.33); D is in the published chart [verified].
- Require **adjacent-bar agreement** (the same label on the neighbouring filled bar or a run of at least two bars) before printing a chord in a filled region; otherwise print `riff` (a new `ChordEvent.label == "riff"` or a flag). Evidence: Chelsea bars 1 to 7 flip between `G`, `B`, `C` with correlations 0.25 to 0.63 and an out-of-set `C:min` winning most bars [verified]. Humphrey and Bello and Pauwels both describe such passages as not chord-describable [verified].
- Set `FILL_MIN_MATCH` no lower than 0.5 and `FILL_MIN_MARGIN` no lower than 0.15 on the evidence above (Chelsea bar 2: `B:maj` 0.47 would otherwise print a barre).
- Use `librosa.feature.chroma_cqt` with its default tuning estimation on the **whole** harmonic mix (already the case) and L1-normalise bar chroma before correlating; a correlation with a 0/1 template is scale-free, but the energy gate (`FILL_MIN_ENERGY`) is not, so compute it on the bass+guitar+other sum, not including `piano` noise from Demucs [inferred].

### 4.3 Give the vendored decoder the beat grid

Code: `models/chords.py` (`recognise_chords`), vendored `chord_recognition.py` call (`hmm.decode_to_chordlab(entry, probs, False)`), `stages/harmony.py` (grid is loaded before the recogniser runs, so beats can be written to a temp `.lab` or passed in-process).

The decoder already implements beat-aware transitions (`use_beats`, `use_downbeats`, `beat_trans_penalty`); the pipeline never enables them. Measured this session, see the table below (filled in from `beat_decode_out/summary.json`).

Same five-net posteriors per song, decoded five ways (`beat_decode_experiment.py`; a change "on beat" or "on bar" is within 80 ms of a Beat This! beat or bar start from `grid.json`) [verified]:

| Song | Decoding | Events | Changes on a beat | Changes on a bar start | Events under 0.5 s | `N` share |
|---|---|---|---|---|---|---|
| Chelsea Dagger | a. as the pipeline (frame HMM, penalty 30) | 69 | 62/68 | 54/68 | 0 | 0.101 |
| | b. `use_beats` | 69 | 67/68 | 57/68 | 0 | 0.102 |
| | c. `use_beats` + `use_downbeats` | 69 | 67/68 | 58/68 | 0 | 0.102 |
| | d. frame HMM, penalty 15 | 81 | 70/80 | 60/80 | 0 | 0.101 |
| | e. beats + downbeats, penalties 15 / (8, 25, 60) | 75 | 73/74 | 61/74 | 0 | 0.102 |
| Summer of '69 | a. pipeline | 76 | 67/75 | 66/75 | 0 | 0.047 |
| | b. beats | 76 | 75/75 | 72/75 | 0 | 0.047 |
| | c. beats + downbeats | 76 | 75/75 | **75/75** | 1 | 0.047 |
| | d. penalty 15 | 76 | 67/75 | 66/75 | 0 | 0.047 |
| | e. beats + downbeats, lower penalties | 76 | 75/75 | 73/75 | 0 | 0.047 |
| Pour Some Sugar On Me | a. pipeline | 84 | 51/83 | 33/83 | 1 | 0.277 |
| | b. beats | 78 | 76/77 | 45/77 | 0 | 0.278 |
| | c. beats + downbeats | **75** | 73/74 | **48/74** | 0 | **0.264** |
| | d. penalty 15 | 88 | 53/87 | 35/87 | 2 | 0.274 |
| | e. beats + downbeats, lower penalties | 80 | 78/79 | 47/79 | 0 | 0.278 |

Reading: variant c (beats and downbeats, default penalties) is a clear improvement on every song: all 75 Summer of '69 changes land on bar starts (the published chart is bar-level), PSSOM loses nine fragmentary events and 1.3 points of `N`, and the chord sets are unchanged. Lowering the penalty (d, e) only adds fragments and inversions; keep 30 / (15, 45, 100). The intro and solo `N` passages are untouched, as expected: this is a boundary fix, not a recall fix. Implementation: build `[[time, position_in_bar], ...]` from `grid.bars` (position 1 for the downbeat) and either call the vendored decoder in-process with `use_beats=True, use_downbeats=True`, or add an optional beats `.lab` argument to the vendored `chord_recognition.py` via the existing `patch_*` mechanism in `vendoring.py`. The chain's bar positions then also make `snap_to_beats`' majority vote nearly redundant, but keep it as a safety net for a `.lab` boundary that misses a beat by more than 80 ms.

### 4.4 Second pass on `N` bars using the guitar+other stems

Code: `stages/harmony.py` after `snap_to_beats`; `models/chords.py` already takes any wav.

Run the recogniser once more on the `guitar + other` (optionally `+ bass`) mix and, for bars that are all-`N` on the mix pass, take the stems pass label when it is a chord. Evidence: PSSOM solo+breakdown `N` 0.68 to 0.39 and `D:maj` recovered; the mix pass stays authoritative elsewhere because APSIPA 2025 shows amplified riffs create spurious `sus4` labels and this session saw a spurious `F#:maj/5` on the stems [verified]. Cost: one more 10 s model run. This complements, not replaces, 4.2: the model pass handles passages with real chords (PSSOM), the template fill handles what the model refuses, and `riff` handles the rest.

### 4.5 Power chords: decide by key, label as `5`

Code: `music/triads.py`, `music/arrange.py` and shapes (`music/shapes.py`), `render`.

Since chroma cannot detect the missing third (section 1.2), use the key: when the (stems-based) key is minor and a `X:maj` label sits on the tonic, or when a `maj` label's root is diatonic to the key only as a minor chord, print it as a power chord `X5` (ukulele shape with root and fifth only, for example `C#5` = `1 1 x x` style or the two-string shape) or as the key's diatonic quality (`C#m`) with the `5` kept in `label`. `mir_eval.chord.QUALITIES['5']` exists so `X:5` is a valid label downstream [verified]. The published PSSOM chart's `C#m` and lessons item 7's "let the key's diatonic quality decide what the easy tier prints" are satisfied without a fragile acoustic test. Guard: only apply when the label's own confidence is below the song median or when the chord is the tonic of a minor key [inferred].

### 4.6 Vote chords across repeated sections and low-confidence beats

Code: `music/snap.py`, grid sections (`grid.json` clusters), v1.2 repeated-row detection.

Mauch 2009: averaging evidence across instances of the same section type raised accuracy and made sheets "more readily readable" [verified]. Cheap variant: for sections in the same cluster with equal bar counts, for each bar position take the label that holds the most summed overlap share across instances, and only overwrite beats whose own `confidence` is under a threshold (HarmTrace's "only where uncertain" principle) [verified principle, inferred threshold]. S69's verse `D A A D` boundary issue is handled by v1.2 phrase alignment; this rule targets isolated one-beat flips such as Chelsea's 10 on-beat-2 changes.

### 4.7 Diagnostics the validation table should carry

Cheap to add to `evaluate.py` / the harmony stage log: `N` share, number of events shorter than one beat, share of changes on beat 0, `mir_eval.chord.overseg/underseg` against the previous run of the same song (regression guard), key margin on mix vs stems, and the list of out-of-set template winners in filled bars. All of these are in the measurement scripts in `scratchpad\research\`.

## 5. Deeper options

1. **Chord-level decoding over the beat grid (Korzeniowski 2018 style).** Treat each beat as a token with the ensemble's averaged posteriors; decode with a duration prior in beats (two- and four-beat chords favoured; one-beat chords allowed only with strong evidence) and a transition prior from the song's own key (diatonic chords cheaper than non-diatonic). Expected gain about one point of WCSR per the literature, but a larger gain in *readability* (fewer one-beat chords). Needs the raw posteriors: the vendored `chord_recognition.py` can be called in-process (as `beat_decode_experiment.py` does) to get `probs`, so no model change [verified feasible].
2. **Second recogniser as a tie-breaker.** ChordMini's 2E1D (2.2M parameters, MIT code) on the same CQT stack; agree/disagree per beat gives an honest confidence and a vote. Licence of its checkpoints must be clarified first (pseudo-labels from CC BY-NC-SA BTC teacher) [verified facts, inferred risk].
3. **Teach the model power chords.** Fine-tune Chord-CNN-LSTM's triad head with a `5` class using GuitarSet, GOAT and synthetic power-chord audio (the AAM study shows artificial audio can stand in for human-composed training data for pop [verified]). Large task; only worth it if 4.5 proves insufficient on more rock songs.
4. **Key: supervised model.** madmom's `CNNKeyRecognitionProcessor` (85.1 weighted on Billboard) is the best off-the-shelf model but CC BY-NC-SA and a Cython build on Windows [verified]; S-KEY (2025) is self-supervised and matches it but code availability is unclear [verified abstract]. A rock-specific template approach (4.1) is likely enough.
5. **Crowd-sourced chart fusion (DECIBEL).** For songs with public chord sheets, aligning an untimed chord sequence to the beat grid and fusing with the model fixes vocabulary and `N` passages at once (+0.5 to 13.6 points) [verified]. Terms of service of tab sites and the project's "no lyrics" rule make this a user-supplied-file feature at most.
6. **Melody-aware mode.** Temperley and de Clercq's melodic scale-degree model (82 percent) can run on the vocals stem's chroma; this session's vocals-stem numbers point the right way on S69 and PSSOM [verified] but with small margins; keep as a tie-breaker.

## 6. Sources

Project evidence (read-only): `docs/superpowers/specs/2026-10-03-real-run-lessons.md`, `...-v1-1-validation.md`, `...-v1-2-design.md`, `...-spike-models.md`, `...-assumption-checks-tools.md`; `runs/<slug>/02_grid/grid.json`, `03_harmony/chords.json`; `src/youkelele/{models/chords.py, music/key.py, music/snap.py, music/triads.py, stages/harmony.py}`; worktree `src/youkelele/music/fill.py`; vendored model at `~/.youkelele/models/chord_cnn_lstm/` (`chord_recognition.py`, `extractors/xhmm_ismir.py`, `data/*_chord_list.txt`).

Papers and documentation:

- Pauwels, O'Hanlon, Gómez, Sandler, "20 Years of Automatic Chord Recognition from Audio", ISMIR 2019. http://archives.ismir.net/ismir2019/paper/000004.pdf
- Humphrey, Bello, "Four Timely Insights on Automatic Chord Estimation", ISMIR 2015. http://ismir2015.uma.es/articles/294_Paper.pdf
- Jiang, Chen, Li, Xia, "Large-Vocabulary Chord Transcription via Chord Structure Decomposition", ISMIR 2019. http://archives.ismir.net/ismir2019/paper/000078.pdf ; repo https://github.com/music-x-lab/ISMIR2019-Large-Vocabulary-Chord-Recognition
- Park et al., "A Bi-Directional Transformer for Musical Chord Recognition", ISMIR 2019. https://arxiv.org/abs/1907.02698 ; https://github.com/jayg996/BTC-ISMIR19
- Phan et al., "Enhancing Automatic Chord Recognition via Pseudo-Labeling and Knowledge Distillation" (ChordMini), DAFx 2026. https://arxiv.org/abs/2602.19778 ; https://github.com/ptnghia-j/ChordMini
- ChordFormer, 2025. https://arxiv.org/abs/2502.11840
- Ding, Weiß, "System Description for the Audio Chord Estimation Task at MIREX 2025". https://futuremirex.com/portal/wp-content/uploads/2025/audio-chord-estimation/wu-ensemble.pdf
- Event-based sequence modelling for non-triad chords, 2026. https://arxiv.org/abs/2604.24386
- "From Discord to Harmony" (consonance-based training), ISMIR 2025. https://arxiv.org/abs/2509.01588
- Mitoma, Furuya, "Accuracy Improvement of Automatic Chord Recognition with Source Separation Preprocessing", APSIPA 2025. http://www.apsipa.org/proceedings/2025/papers/APSIPA2025_P307.pdf
- Mauch, Noland, Dixon, "Using Musical Structure to Enhance Automatic Chord Transcription", ISMIR 2009. https://zenodo.org/records/1414844
- Mauch, Dixon, "Simultaneous Estimation of Chords and Musical Context from Audio", IEEE TASLP 2010. https://webspace.eecs.qmul.ac.uk/s.e.dixon/pub/2010/Mauch-Dixon-TASLP-2010-real.pdf
- Korzeniowski, Widmer, "A Fully Convolutional Deep Auditory Model for Musical Chord Recognition", MLSP 2016. https://arxiv.org/abs/1612.05082
- Korzeniowski, Widmer, "Improved Chord Recognition by Combining Duration and Harmonic Language Models", ISMIR 2018. https://arxiv.org/abs/1808.05335
- Korzeniowski, Widmer, "Genre-Agnostic Key Classification with Convolutional Neural Networks", ISMIR 2018. https://arxiv.org/abs/1808.05340
- Koops et al., "Annotator subjectivity in harmony annotations of popular music", JNMR 2019. https://pure.uva.nl/ws/files/62264010/Annotator_subjectivity_in_harmony_annotations_of_popular_music.pdf
- Odekerken, Koops, Volk, "DECIBEL", TISMIR 2021. https://arxiv.org/abs/2002.09748
- Bortolozzo, Schramm, Jung, "Improving the Classification of Rare Chords with Unlabeled Data", 2020. https://arxiv.org/abs/2012.07055
- Training chord recognition on artificially generated audio, 2025. https://arxiv.org/abs/2508.05878
- Temperley, de Clercq, "Statistical Analysis of Harmony and Melody in Rock Music", JNMR 2013. https://www.midside.com/publications/temperley_declercq_2013.pdf ; corpus https://rockcorpus.midside.com/
- Albrecht, Shanahan, "The Use of Large Corpora to Train a New Type of Key-Finding Algorithm", Music Perception 2013 (via Nápoles López et al., "Key-Finding Based on a Hidden Markov Model and Key Profiles", 2019, table 3). https://napulen.github.io/media/justkeydding/napoles19key.pdf ; https://github.com/napulen/justkeydding
- Key profile vectors: partitura `utils/globals.py` (Krumhansl-Kessler, Temperley CBMS, Kostka-Payne). https://raw.githubusercontent.com/CPJKU/partitura/main/partitura/utils/globals.py ; Albrecht-Shanahan as implemented in https://github.com/akoita/resonate (issues 2016, 2018; `workers/demucs/audio_features.py`)
- music21 key-profile notes. https://www.music21.org/music21docs/moduleReference/moduleAnalysisDiscrete.html
- S-KEY, 2025. https://arxiv.org/abs/2501.12907
- Magalhães, "Chordify: three years after the launch", ISMIR LBD 2015. https://www.ismir2015.uma.es/LBD/LBD42.pdf ; de Haas et al., "Improving Audio Chord Transcription by Exploiting Harmonic and Metric Knowledge", ISMIR 2012 (abstract page https://www.cs.ox.ac.uk/publications/publication6253-abstract.html)
- Chordify accuracy quote (co-founder, 2013). https://thenextweb.com/apps/2013/05/02/chordify-taps-soundcloud-and-youtube-to-show-you-the-chords-to-your-favorite-songs/
- madmom docs: chords https://madmom.readthedocs.io/en/v0.16/modules/features/chords.html ; key https://madmom.readthedocs.io/en/v0.16/modules/features/key.html ; repo https://github.com/CPJKU/madmom
- Chordino / NNLS Chroma. https://code.soundsoftware.ac.uk/projects/nnls-chroma ; chord-extractor https://pypi.org/project/chord-extractor/
- autochord. https://pypi.org/project/autochord/ ; https://archives.ismir.net/ismir2021/latebreaking/000008.pdf
- crema. https://github.com/bmcfee/crema
- Essentia PyPI (platforms). https://pypi.org/project/essentia/ ; Key algorithm https://essentia.upf.edu/reference/std_Key.html ; ChordsDetectionBeats https://essentia.upf.edu/reference/std_ChordsDetectionBeats.html
- libfmp chord recognition notebooks. https://www.audiolabs-erlangen.de/resources/MIR/FMP/C5/C5S3_ChordRec_HMM.html
- librosa `viterbi_discriminative`. https://librosa.org/doc/0.11.0/generated/librosa.sequence.viterbi_discriminative.html
- mir_eval chord metrics. https://mir-eval.readthedocs.io/stable/api/chord.html
- MIREX key error weights (madmom evaluation.key). https://madmom.readthedocs.io/en/v0.16/modules/evaluation/key.html
