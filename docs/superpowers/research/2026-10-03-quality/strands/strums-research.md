# Research strand: strumming pattern and rhythm extraction

Date: 2026-10-03. Scope: the `strums` stage (`src/youkelele/stages/strums.py`, `src/youkelele/music/onsets.py`, `src/youkelele/music/as_played.py`) and how its output reaches the sheet (`src/youkelele/render/strum_box.py`). Evidence base: the four real runs under `runs\` (Chelsea Dagger `sexhetcxqy4`, Summer of '69 `9f06qzcvuhg`, Pour Some Sugar On Me `0uib9y4ofps`, Wet Leg `lbc6ccztp5e`), the lessons and validation specs, the two audio spike reports, the installed librosa 1.0.0 source, and the external sources listed at the end.

Where a statement is measured or quoted it is marked **verified**; where it is my reading of the evidence it is marked **inferred**. Numbers from the runs were recomputed from `04_strums/strums.json` and `02_grid/grid.json` with a script in this scratchpad (`research/strike_rates.py`), not copied from the specs.

Nothing here re-proposes the version 1.2 items (four-bar minimum, mean tempo, title cleaning, chroma filling, passing chords, phrase alignment, repeated rows). The 1.2 plan does not touch the strums stage beyond keeping `check_strums_match_grid` valid, so everything below is open.

## 1. Failure modes

### 1.1 The majority vote erases strikes that are musically "always played" (verified)

`as_played.majority_vector` marks a slot struck only when strictly more than half the bars in the section have an onset there. Per-slot strike rates from the runs:

| Song, section | bars | detected strikes per bar | per-slot strike rate (8 slots) | slots kept at > 1/2 | at > 1/3 |
|---|---|---|---|---|---|
| Chelsea, first chorus (9 to 38) | 29 | 2.8 | 0.41 0.00 0.86 0.10 0.45 0.17 0.62 0.14 | 2 (`--D---D-`) | 4 (`D-D-D-D-`) |
| Chelsea, verse (38 to 61) | 23 | 3.9 | 0.61 0.09 0.91 0.39 0.57 0.35 0.61 0.39 | 4 | 7 |
| Chelsea, last chorus (105 to 142) | 37 | 2.6 | 0.46 0.03 0.81 0.05 0.54 0.05 0.46 0.19 | 2 | 4 |
| Summer of '69, third chorus (83 to 95) | 12 | 1.8 | 0.83 0.08 0.25 0.25 0.08 0.00 0.25 0.08 | 1 (`D-------`) | 1 |
| Summer of '69, verse (4 to 19) | 15 | 6.1 | 0.93 0.53 0.87 0.93 0.47 0.87 1.00 0.53 | 7 | 8 |
| Wet Leg, verse (42 to 58) | 16 | 6.6 | 0.94 0.62 0.88 0.81 0.81 0.88 1.00 0.69 | 8 | 8 |

Across the four songs the rest share of the per-bar vectors is 0.60, 0.51, 0.66 and 0.26 (Chelsea, S69, PSSOM, Wet Leg). The lessons document counted 16 of 26 section patterns at 75% or more rests. A slot struck in 41 to 49% of bars (Chelsea beats 1 and 3) is, to a player, a stroke that is always there; the detector simply misses it half the time, and the vote turns a 50% recall into a 0% output. The threshold compounds an upstream recall problem; it does not cause it.

### 1.2 Onset recall collapses in open-chord, dense-mix sections (verified effect, inferred mechanism)

Summer of '69 detects 6.1 strikes per bar in the palm-muted verse and 1.8 to 3.9 in the choruses, although the record strums through the choruses (lessons, section "Strums"). Chelsea Dagger averages 3.2 strikes per bar on a song whose guitar part is continuous. Two mechanisms in `detect_onsets` are the likely cause:

- `librosa.onset.onset_detect` with `normalize=True` (the default, and what the code uses) rescales the onset envelope to [0, 1] over the **whole song** before peak picking, and then `peak_pick` keeps a frame only if it exceeds the local 200 ms mean by an absolute `delta` of 0.07 (defaults read from the installed librosa 1.0.0 source: `pre_max` 30 ms, `post_max` 0 ms, `pre_avg` 100 ms, `post_avg` 100 ms, `wait` 30 ms, `delta` 0.07). A section whose stem is quiet or smeared relative to the loudest section of the song sits low in the normalised envelope and clears `delta` rarely. The round 1 spike found that lowering `delta` globally to 0.03 doubled the onsets and produced `DUDUDUDU` everywhere, so a global change is not the fix; a section-relative threshold is (section 4.2).
- `onset_strength` with the default `aggregate=np.mean` sums positive spectral flux over all mel bands, so the envelope "tends to be dominated by the loudest events" (McFee and Ellis 2014). In a smeared guitar stem the loudest flux is often the bleed, not the strum.

The Yousician paper tuned exactly this detector (librosa peak picking, 100 trials of hyper-parameter search) on **isolated** guitar tracks and reached 83.0% F1, 79.7% precision, 89.1% recall at a 50 ms tolerance; on a mix or a separated stem a classical detector will do worse (Lukoianov and Klapuri 2025, Table 1 and text).

### 1.3 Drum bleed in the guitar stem (verified pattern, inferred cause)

Chelsea Dagger's strike rates peak on beat 2 (slot 2: 0.81 to 1.00 in every section) and beat 4 (slot 6: 0.46 to 1.00), with beats 1 and 3 at about half that. The lessons attribute this to snare bleed into the `guitar` stem; the first chorus box printed on the sheet (`--D---D-`) is the backbeat, not the guitar. On the mix the mute rule fires on kick drums (round 2 spike: "On a mix it fires on kick drums"). The Yousician paper notes that published separation evaluations give "roughly 10 dB SNR for vocals, bass, and drums, but barely above 0 dB SNR for the remaining instruments, including guitars", and that their strum detector did **better** on the `other` stem (96.9% F1) than on the `guitar` stem (95.4%) because the guitar stem amplifies additional guitar parts and is itself lower quality. The project picks the louder of `guitar` and `other` by RMS ratio (`choose_source`); louder is not cleaner.

### 1.4 Binary strikes discard strength, so a ghost onset and a full strum count the same (verified)

`quantise_bar` reduces each onset to `S`, `x` or `-`. The round 2 spike found that keeping only onsets above the section's median onset strength turns a wall of sixteenths into an accent skeleton (`--D---D---D---D-`), "useful as an accent overlay, not as the pattern". The information is available (the envelope is computed anyway) and is thrown away before the vote. Dixon, Gouyon and Widmer (2004) extract bar-length rhythmic patterns as **continuous amplitude-envelope profiles** (72 samples per bar), cluster the bars with k-means (k = 4) and take the centre of the largest cluster as the piece's pattern, precisely to be robust to noisy individual bars. Ultimate Guitar's notation has an explicit accent mark (`>` above the arrow), so accents are something players expect to see.

### 1.5 Confidence does not detect the sparse-but-certain case (verified)

`section_summary` reports the mean Jaccard between each bar and the majority vector; Jaccard skips slots where both rest, so a 2-strike vector against 2-to-3-strike bars scores 0.5 and is printed as certain (Chelsea choruses at 0.51 and 0.52, S69 third chorus at 0.53, all 75 to 88% rests; lessons, lesson 5). Nothing in the score penalises a pattern that explains only a fraction of the onsets actually heard.

### 1.6 Section patterns wobble around one groove (verified)

Summer of '69's choruses come out as `D-DU--D-`, `DU-U-UD-` and `D--UDUD-` where the record has one pattern (validation, "Quality"). Each section is summarised independently; nothing favours continuity between sections of the same label or neighbouring sections. The Yousician system adds a transition cost for changing pattern between bars and reports that it cut pattern discontinuities from 27.8% to 15.4% at equal strum F1 (94.7%).

### 1.7 Mute detection is song dependent (verified)

The relative centroid and zero-crossing rule (`MUTE_CENTROID` 0.85, `MUTE_ZCR` 0.65 of the song medians) separates S69's chug well (verse bars 84 to 87% `x`) but reads quiet open chords in the outro as muted (29 to 32%) and does not work on PSSOM (round 1 spike, section (b)). Both features are brightness measures that also fall when a chord is simply quieter or lower. The playing-technique literature characterises palm muting by **shorter sustain** and **faster decay of the high frequencies after the attack**, not by brightness alone (Reboursière et al., NIME 2012: "shorter sustain period where high frequencies decrease faster than other parts of the spectrum"). No decay feature is used.

### 1.8 Grid choice and non-binary subdivisions (verified rules, inferred gaps)

The 8/16 decision uses the odd-sixteenth share with a 140 bpm cap; PSSOM at 86 bpm gets 16 slots on a 44% share and then every section is uncertain. There is no provision for swing or triplet feel: `check_strums_match_grid` only accepts `2 x numerator` or `4 x numerator` slots, so a shuffled song can only be quantised wrongly. None of the four runs is swung, so this is a latent gap, not an observed failure.

### 1.9 Direction is positional and cannot be anything else today (verified)

`direction_for_slot` prints D on even slots and U on odd slots. Audio-only direction classification is a research problem: the best published model (CRNN trained on 90 minutes of motion-sensor-labelled real recordings plus 4 hours of synthetic audio) reaches F1 85.5% for down and 79.0% for up strokes on microphone audio, and the authors needed a wrist sensor to label the training data (Murgul, Schimper and Heizmann, ISMIR 2025). The 2022 LBD states plainly that "conventional note-based transcription methods cannot distinguish the direction of the strumming movement". The positional convention is also how every published pattern on UkuTabs, Roadie and Ultimate Guitar is laid out (down on the beat and on-beat eighths, up on off-beats), so printing positional directions matches what players expect. This is not a failure to fix; the exception is pure off-beat patterns (UkuTabs pattern 12, `- d - d - d - d`, reggae) where the convention says down on the off-beat.

## 2. What others do

### 2.1 Commercial chord sites and apps

| Product | What it does about rhythm | Source |
|---|---|---|
| Chordify | Does not attempt it. Support article: "We're not able to accurately detect strumming patterns on Chordify - this is near-impossible to detect accurately with algorithms"; they point users to the Loops feature instead. The iOS app's lessons teach human-authored patterns per song section. **Verified.** | [Chordify support](https://support.chordify.net/hc/en-us/articles/360019489618-Does-Chordify-show-the-strumming-patterns-) |
| Ultimate Guitar | Human-authored strumming pattern per tab version (not per section), shown under the chord diagrams with a BPM; arrows for direction, a small x above an arrow for a muted stroke, a large X in place of an arrow for palm mute, `>` for accent, empty space for a rest; "not present in all tabs". **Verified.** | [UG help](https://help.ultimate-guitar.com/en/articles/6744662-strumming-patterns-how-to-read-play) |
| JustinGuitar app | Human-authored per-song pattern behind a button; a moderator concedes "some of the given strumming patterns are not entirely accurate. You can sometimes clearly hear that the pattern being used in the actual backing track is different." **Verified.** | [JustinGuitar community](https://community.justinguitar.com/t/strum-patterns-for-songs-in-app/102499) |
| Yousician | Expert musicians transcribe each song into patterns from a 924-pattern vocabulary (one or two bars, sixteenth resolution, with time signature); their research prototype automates this (section 3.1). The product data is proprietary. **Verified** from the paper. | [arXiv 2510.05756](https://arxiv.org/html/2510.05756v1) |
| Moises | Chords, key, BPM, beats, stems, speed and pitch change; no strum or rhythm pattern feature in the 2025 release notes. **Verified absence.** | [Moises blog](https://moises.ai/blog/latest/improvements-latest-releases) |
| Soundslice | Manual transcription editor synced to audio; automatic stems but no automatic rhythm transcription. **Verified absence.** | [Soundslice](https://www.soundslice.com/help/en/creating/transcribing/) |

The takeaway: nobody ships automatic strum patterns from a full mix. The closest is Yousician's 2025 research system, which relies on their own labelled catalogue. Everyone who shows a pattern shows **one pattern per song or section** from a small human vocabulary, with accents and mutes marked; nobody shows a per-bar transcription.

### 2.2 Pattern libraries (the vocabulary a player expects)

UkuTabs' beginner guide lists eighteen patterns; the island strum `d - d u - u d u` is "the go-to for a huge number of songs and the most used pattern on UkuTabs by a wide margin" (**verified** quote). The full list, in 8-slot or 6-slot notation:

- 4/4, one bar: `d d d d` (all downs, quarters); `d u d u d u d u`; `d - d u - u d -`; `d - d u - u d u` (island); `d - d - d u d u`; `d - d u d u d u`; `d u d U d u d U` (accented ups); `- d - d - d - d` (off-beat reggae); `- - d u - - d -`; `d - - -` (one stroke per bar).
- 4/4, half bar (repeat twice): `d - d u`; `d u x u` (chunk).
- 4/4, two bars: `d - d u - u d u` x2 (ballads); `d u x u d u x u`.
- 3/4: `d - d u d -`; `d - d u d u`.
- 6/8: `d - - d - u`; `d - u d - u`.

Roadie's five beginner patterns are `D U D U`, `D D D D`, `D D D UD`, `D DU D DU`, `D DU U D` (**verified**). Ultimate Guitar's own example pattern is `D - D U D U D - D U D U` at 156 bpm, that is sixteenths with rests on beats 1 and 3 (**verified**). For Summer of '69 UkuTabs and ukulelearn publish `D-DU-DU-DU`-type eighth patterns while the record itself plays a muted eighth chug in the verses (project research notes and round 1 spike). The round 2 spike found 0 of 14 sections on three songs matched the published beginner pattern, which is why the stage went "as played". That is the right conclusion about **matching**; it does not mean a vocabulary is useless for **naming** or for **regularising** (section 4.7, 5.3).

### 2.3 Research systems

**Yousician / KIT, "Transcribing Rhythmic Patterns of the Guitar Track in Polyphonic Music" (Lukoianov and Klapuri, arXiv 2510.05756, 2025).** This is the closest published system to this stage and it is worth copying its structure. **Verified** from the paper:

- Source: HTDemucs 4-stem `other` (best), also tested guitar stem and full mix. Reasoning: suppress the well-separated sources rather than trust the poorly separated guitar.
- Strum detector: MERT-v1-95M (pre-trained music transformer, 75 Hz frames) fine-tuned with a 256-unit MLP head and the Beat This shift-tolerant weighted BCE loss; peak picking "the frame with the highest probability above 0.5 inside every ±40ms neighborhood". Strum F1 96.9% on `other`, 95.4% on `guitar`, 96.5% on the mix, 98.3% on the isolated track; the tuned librosa baseline on the isolated track is 83.0%.
- Pattern decoding: Viterbi over a vocabulary of 924 expert-defined one-or-two-bar patterns at sixteenth resolution plus ten empty patterns. Emission is a **two-way mismatch** score: the product over observed strums of a Gaussian on the distance to the nearest pattern strum, and the same from pattern strums to observed strums. Transition: cost 0 to repeat a pattern, `-c1` to change pattern, `-c1 - c2` to change time signature. Result: reconstructed strum F1 94.7%, pattern discontinuity 15.4% (27.8% without the transition cost).
- Bars: Beat This downbeats with a dynamic-programming clean-up that cuts bar-length discontinuities from 4.88% to 0.41%.
- Data: 931 recordings of 410 pop/rock songs at four difficulty levels, proprietary; synthetic guitar stems (80 presets, 11 acoustic and 6 electric) mixed into the backing tracks doubled the training data; ±2/-3 semitone transposition augmentation.
- Release: ten-second excerpts and the downbeat post-processing script at [github.com/YousicianGit/rhythmic-pattern-transcription](https://github.com/YousicianGit/rhythmic-pattern-transcription); paper CC BY-NC-ND 4.0. No model weights, no vocabulary file. MERT-v1-95M weights are CC-BY-NC-4.0 ([Hugging Face mirror](https://portrait.gitee.com/modelee/MERT-v1-95M)).

**Murgul, Schimper and Heizmann, "Joint Transcription of Acoustic Guitar Strumming Directions and Chords" (ISMIR 2025, arXiv 2508.07973).** **Verified**: CRNN on log-mel (229 bins, 16 kHz, 10 ms hop), BiGRU 256, three heads (strum onset, direction, 24 major/minor chords). Data: 90 minutes of real recordings by three guitarists with an ESP32 wrist sensor providing direction labels, plus 4 hours synthesised from GuitarPro via DAWDreamer and Ample Sound instruments with effects and noise. On **pickup** audio the classical baselines scored spectral flux 79.5%, SuperFlux 74.4%, complex domain 79.3% F1 against the CRNN's 97.6%. On microphone audio: any-direction F1 92.8%, down 85.5%, up 79.0%. Muted strokes could not be annotated. No code or dataset release found; the paper is CC BY 4.0. The 2022 LBD predecessor used a hand-mounted IMU for direction and audio for onsets (F1 85% up, 92% down) and released five minutes of test data ([ISMIR 2022 LBD](https://ismir2022program.ismir.net/lbd_393.html)).

**Dixon, Gouyon and Widmer, "Towards characterisation of music via rhythmic patterns" (ISMIR 2004).** **Verified** from the PDF: amplitude envelope resampled to a fixed number of samples per bar (best b = 72), bar boundaries refined by correlating each bar with the running sum of previous bars (search ±5% of the bar length), bar vectors clustered with k-means (k = 4), the largest cluster's centre taken as the piece's characteristic pattern. Designed for ballroom genre classification, but the mechanism (continuous per-bar profiles, averaged within the dominant cluster) is exactly a robust "one pattern per section" estimator.

**McFee and Ellis, "Better beat tracking through robust onset aggregation" (ICASSP 2014).** **Verified** from the PDF: replacing the sum across frequency bands with the **median** gives an onset envelope that "captures temporally synchronous onsets, and is robust to spurious, large spectral deviations"; they also evaluate onset detection on a single component of a spectrogram decomposition (HPSS) "allowing the onset detector to suppress noisy or arrhythmic events". librosa exposes both: `onset_strength(aggregate=np.median)` and `librosa.decompose.hpss(margin=...)` (Fitzgerald 2010; Driedger, Müller and Disch 2014).

**Onset detection state of the art.** SuperFlux (Böck and Widmer, DAFx 2013) is the standard classical detector; on guitar datasets a 2024 study reports SuperFlux F1 0.884 (IDMT) and 0.916 (GuitarSet) against a CNN at 0.874 and 0.930 ([arXiv 2408.13734](https://arxiv.org/pdf/2408.13734), via search summary, **not independently verified**). madmom's `CNNOnsetProcessor` and `RNNOnsetProcessor` are the MIREX-winning models; madmom code is BSD but the model files are CC BY-NC-SA 4.0 ("for commercial use of model files ... contact Gerhard Widmer"), and the PyPI release 0.16.1 still breaks on NumPy >= 1.20 (`np.float` removed; [issue 527](https://github.com/CPJKU/madmom/issues/527), open since August 2023), so it needs a patched install from git. **Verified.**

**Datasets.** IDMT-SMT-Guitar subset 4 has 64 short pieces with onset positions, chords and rhythmic pattern length annotations, and subset 1 includes muted and dead-note playing styles; licence CC BY-NC-ND 4.0, Zenodo record 7544110 (**verified**). GuitarSet (ISMIR 2018) has acoustic guitar "comp" recordings with beats, downbeats, chords and playing style via hexaphonic pickup (**verified** from the paper abstract; licence not checked here). Neither is ukulele and neither is a mix, but both are usable for tuning an onset detector on isolated strummed guitar.

**Separation alternatives.** htdemucs_6s is described even by Demucs commentators as "okay" for guitar with "a lot of bleeding and artifacts" on piano; MVSep's guitar model is reported at 7.93 SDR against htdemucs_6s at 7.22 on their validation set, and a BS-RoFormer six-stem model ("BS-Rofo-SW") separates guitars and keys ([search summary](https://mvsep.com/en/algorithms), **not independently verified**; the ZFTurbo MDX23 repository itself has no guitar model). `audio-separator` (MIT, already a dependency, CPU supported) can run Roformer and MDXC checkpoints and lists models with `--list_models --list_filter=guitar` (**verified** from PyPI).

**Hobby projects.** StrumSight (on-device chord plus up/down arrows, Flutter and C++) and strum-trainer (practice tool, typed patterns) exist on GitHub but publish no evaluation; not worth adopting.

## 3. Research summary: what is state of the art and what is good enough

1. **Strum onset detection** on a separated stem or mix is solved to about 95 to 97% F1 by a trained frame model (fine-tuned MERT; a CRNN reaches 97.6% on pickup audio). Classical spectral-flux detectors reach 79 to 83% F1 on **isolated** guitar and less on stems. The gap is in recall on quiet or smeared passages and in false positives from bleed. Everything downstream (direction, mute, pattern) is bounded by this.
2. **Direction** from audio alone is 79 to 86% per class even with a trained model and sensor-labelled data; the positional convention is what humans write, so "good enough" is positional direction plus honest wording ("directions follow the beat").
3. **Mutes and accents** have no published audio model for strumming; the 2025 paper excludes muted strokes. Palm-mute cues in the technique-detection literature are decay rate and high-frequency decay, which are level-independent and not yet used here.
4. **Pattern decoding**: the published approach is Viterbi over a vocabulary with a continuous (Gaussian) two-way mismatch emission and a pattern-change penalty, giving 15% bar-to-bar discontinuity on real songs. Dixon et al. show the cheaper alternative: average continuous bar profiles within the dominant cluster.
5. **Bar lines**: Beat This downbeats need a continuity clean-up (4.9% to 0.4% discontinuities in the Yousician post-processing). The project already uses Beat This and has its own octave rule; the Yousician `downbeat.py` is open and worth reading for the dynamic-programming formulation.
6. **Good enough for a chord sheet**: one box per section with the right density (strikes per bar within a third of what is heard), accents marked, mutes marked where the stem supports it, positional directions, and a sentence saying how repeatable it was. That is what Ultimate Guitar prints and what Chordify refuses to print at all.

## 4. Easy wins

Each item names the code it changes and the evidence it rests on. All should be measured on the four existing run folders with `--from strums` before adoption (separation dominates runtime; stages 4 to 7 take seconds).

### 4.1 Replace the binary vote with a slot-strength profile (as_played.py, onsets.py)

Sample the onset-strength envelope at each slot centre (maximum over ±1 frame) for every bar in the section, average across bars, normalise by the section's maximum slot value, and mark a slot struck when its mean is at least a fraction `t` of the maximum (start at 0.4 and measure). This is Dixon et al.'s averaged bar profile with the beat grid already known. `detect_onsets` already computes the envelope implicitly; return it (`Onsets.envelope`, `hop`, `sr`) so no second pass is needed. Expected effect from the run data: Chelsea's choruses have beats 1 and 3 at roughly half the rate of beats 2 and 4, so a profile would keep all four beats where the vote keeps two; Wet Leg's dense sections are unaffected because every slot is near the maximum. Keep the binary `bar_onsets` for the sheet's "as played" claim and tests.

Cheaper interim variant if the profile is deferred: lower `majority_vector`'s threshold from > 1/2 to > 1/3 **and** require the result to have at least `round(0.6 x median strikes per bar)` strikes, filling from the highest-rate slots. On the current runs that moves Chelsea's first chorus from `--D---D-` to `D-D-D-D-` and the last chorus likewise, and leaves S69's verse and Wet Leg unchanged. It does not rescue S69's third chorus (1.8 strikes per bar); that needs 4.2 to 4.4.

### 4.2 Section-relative peak-picking threshold (onsets.py `detect_onsets`)

Compute the envelope once for the song with `onset_strength`, then peak-pick **per section** (or per 8-bar window) with `normalize=False` and `delta = 0.07 x` the window's 95th-percentile envelope value, so a quiet chorus is judged against itself rather than against the loudest verse. Guard against the spike's degenerate outcome by rejecting any window that yields more onsets than `slots_per_bar x bars x 1.2`, falling back to the global threshold there. Evidence: the global normalisation and absolute `delta` in librosa 1.0.0 (section 1.2); S69's 6.1 versus 1.8 strikes per bar between verse and chorus.

### 4.3 Median aggregation and SuperFlux settings in onset_strength (onsets.py)

Call `librosa.onset.onset_strength(y, sr, hop_length=256, aggregate=np.median, max_size=3, lag=2)` (median across bands per McFee and Ellis; `max_size > 1` and `lag > 1` is librosa's SuperFlux configuration per the library's own example). Also restrict the mel range to roughly 150 Hz to 5 kHz (`fmin`, `fmax`) to reduce kick and cymbal bleed influence. Both are one-line changes; measure grid fit and strikes per bar on all four runs before and after. **Inferred** benefit; cheap to test.

### 4.4 Drum veto using the drums stem the stage already has on disk (strums.py, onsets.py)

`separate/stems/drums.wav` exists when strums runs (the grid stage already requires it). Detect onsets on the drums stem with the same detector; drop a guitar-stem onset that lies within ±20 ms of a drum onset **unless** the guitar envelope at that frame exceeds the guitar section's median by a margin (a real strum on the backbeat survives, bleed does not). Alternatively subtract a scaled drum envelope from the guitar envelope before peak picking. Evidence: Chelsea's slot 2 at 0.81 to 1.00 in every section with the guitar part continuous; McFee and Ellis on using decomposition "to suppress noisy or arrhythmic events". Add `drums_vetoed: int` to `strums.json` for visibility.

### 4.5 Coverage-aware confidence and an explicit sparse flag (as_played.py, schemas.py)

Replace the mean Jaccard with a per-bar F1 between the pattern's struck slots and the bar's onsets (precision: pattern strikes with an onset; recall: onsets landing on pattern strikes), averaged over bars, and additionally set `uncertain=True` when the pattern's strike count is below half the section's median strikes per bar. On the current runs this flags Chelsea's 0.51/0.52 choruses and S69's 0.53 chorus, which the lessons already identified as wrong to print. Record `explained_onsets: float` (share of the section's onsets that fall on a pattern strike) so the sheet can say "this box covers 85% of what was heard".

### 4.6 A decay feature in the mute rule (onsets.py `mute_mask`)

Add a third, level-independent feature: the ratio of RMS in the 60 to 120 ms window after the onset to RMS in the first 20 ms. Palm-muted and chucked strokes decay fast; ringing open chords do not (Reboursière et al. 2012 on sustain and high-frequency decay). Use it to **rescue** quiet open chords the brightness rule mislabels (S69 outro 29 to 32% `x`): mark `x` only if brightness **and** decay agree. Measure on S69 (chug versus chorus), Wet Leg (18% mutes) and PSSOM.

### 4.7 Name the nearest library pattern without matching to it (as_played.py, schemas.py, render)

Keep the as-played vector as the output but add `nearest_named: str | None` and `nearest_distance: float`, computed by Euclidean distance between the section's slot profile (4.1) and the UkuTabs and Roadie patterns of section 2.2 encoded as 8- or 16-slot vectors (with accented ups and the chunk `x` included). Print the name on the sheet when the distance is small ("close to the island strum"). The spike's recommendation 3 in round 2 proposed exactly this field and it was never shipped. Players recognise names; this costs nothing in accuracy because it never overrides the as-played box.

### 4.8 Section continuity (strums.py)

After computing profiles, merge adjacent or same-label sections whose profiles correlate above 0.8 into one pattern, choosing the profile averaged over the union of their bars. This is a section-level version of the Yousician transition cost and would collapse S69's three chorus variants into one. Record `shared_with: list[int]`.

### 4.9 Accents in the box (render/strum_box.py)

Mark the two highest-profile struck slots per bar with `>` above the arrow, as Ultimate Guitar does. The profile from 4.1 provides this for free; the round 2 spike already showed that strength-filtered onsets yield the accent skeleton.

### 4.10 Wording on the sheet (render/html.py templates)

Replace "Strum as played, N% repeatable" with a sentence a player can act on: "Strum pattern heard in this section (covers 85% of the strokes detected); up and down follow the beat." The repeatability number (`bar_repeat`, mean consecutive-bar Jaccard) is 0.3 to 0.7 even on steady songs and reads as a failure.

## 5. Deeper options

### 5.1 A trained strum-onset detector on synthetic data (new module, new dependency on torch, already present)

Both 2025 papers show that synthetic strummed audio mixed into real backing tracks is enough to train a small frame model that beats spectral flux by 15 to 20 F1 points. A CRNN of the Murgul size (conv stack, BiGRU 256) runs on CPU at well above real time. Training data can be made in-house: render chord strums from GuitarPro files via pyguitarpro (already in the research notes) with a FluidSynth soundfont for ukulele and guitar, apply random transposition, EQ, reverb and noise, and mix at random levels into the project's own `drums`, `bass`, `vocals` stems from runs. Labels are exact. Risk: the acoustic gap between soundfonts and records (Murgul saw a 40% upstroke F1 improvement from adding real microphone data); mitigation is the shift-tolerant loss and a small hand-labelled validation set (5.6). Licence: everything generated is the project's own.

### 5.2 Fine-tune or probe MERT as Yousician did

Highest published accuracy on exactly this task (96.9% F1 on the `other` stem), but MERT-v1-95M weights are CC-BY-NC-4.0, which rules out any commercial distribution, and a 95M-parameter transformer at 75 Hz on a four-minute song is slow on CPU. Probing (frozen encoder) underperformed fine-tuning in every experiment of theirs. Suitable only as a research baseline to calibrate 5.1 against.

### 5.3 Viterbi decoding with a continuous two-way mismatch emission and a song-specific vocabulary

The round 1 spike dropped Viterbi because Jaccard emission over 37 textbook patterns was "forced into the densest row". The Yousician formulation differs in two ways that address that: the emission is a Gaussian two-way mismatch on **continuous onset times** (so a bar with one stray onset is not punished the way a slot vector is), and the vocabulary is large. A practical variant without 924 patterns: cluster the song's own bar profiles (Dixon's k-means, k = 3 or 4) and use the cluster centres **plus** the library of section 2.2 as the candidate set, with the transition cost favouring repeats. This gives a per-bar path, a per-section mode, and a measured discontinuity rate, while still allowing an "as played" pattern that is not in any book. Schema change: `SectionPattern.path: list[int]` or a per-bar pattern id list.

### 5.4 Better source for the strummed instrument

Three measurable alternatives to "louder of guitar and other":
- Use the `other` stem by default (Yousician's result) and fall back to `guitar` only when `other` is nearly silent; cheap, re-run on the four songs.
- Build a residual stem: mix minus `drums` minus `bass` minus `vocals` (the sum of `guitar`, `other`, `piano`), which keeps the strummed instrument wherever Demucs filed it; the round 2 spike tried `guitar + other` and it did not change the hit rate against published patterns, but the target then was matching, not onset recall.
- Try a Roformer or MDXC guitar model through `audio-separator` and compare onset recall per section; licensing and runtime unknown and must be checked per checkpoint.

### 5.5 Swing and triplet grids

Add a 12-slot (3 per beat) candidate alongside 8 and 16, chosen when the onset phase histogram within the beat (the round 2 spike's `phase_check.py` already computes 8 phase bins) peaks near 2/3 rather than 1/2. Swing-ratio estimation from onset autocorrelation is established (Gouyon's rhythm description work; the ISMIR 2015 ride-cymbal swing study). Requires relaxing `check_strums_match_grid` and `Strums._check_slot_lengths` to accept `3 x numerator`, and a 12-column strum box.

### 5.6 A small evaluation set, without which none of the above can be tuned

Hand-correct strum onsets for 30 seconds of each of the four songs (export the detected onsets as a Sonic Visualiser or Audacity label track, fix by ear, save as `runs/<slug>/eval/strums.txt`), then score each change with onset F1 at 50 ms exactly as the papers do, plus the per-section "explained onsets" number. IDMT-SMT-Guitar subset 4 (CC BY-NC-ND, research use) and GuitarSet comp tracks give isolated-guitar sanity checks. Without this the stage will keep being tuned against published beginner patterns that the records do not play.

### 5.7 Direction from audio: do not pursue

Even with wrist-sensor labels and a CRNN the per-class F1 is 79 to 86%; no labelled ukulele data exists; and every published chart uses the positional convention. Spend the effort on onset recall and accents instead. If anything, consider a per-slot **energy** marker (louder versus lighter) rather than a direction marker, which is what up and down strokes mostly encode for a reader.

## 6. Sources

Project files (read-only):
- `docs/superpowers/specs/2026-10-03-real-run-lessons.md` (lessons 2 and 5, strums sections per song)
- `docs/superpowers/specs/2026-10-03-v1-1-validation.md` (ranked improvements; strum boxes per song)
- `docs/superpowers/specs/2026-10-03-spike-audio.md` (Spike 3: grid fit, mute features, Viterbi over 37 patterns)
- `docs/superpowers/specs/2026-10-03-spike-audio-round2.md` (Spike 1: five songs, as-played decision, `nearest_named` recommendation)
- `research_notes/tablature_theory_and_strumming.md` Q5 and Q6
- `src/youkelele/music/onsets.py`, `as_played.py`, `stages/strums.py`, `render/strum_box.py`, `schemas.py`
- `runs/<slug>/04_strums/strums.json` and `02_grid/grid.json` for the four slugs; recomputed with `scratchpad/research/strike_rates.py`
- Installed `librosa` 1.0.0 source for `onset_detect` peak-picking defaults and `peak_pick` semantics

Papers and documentation:
- Lukoianov and Klapuri (Yousician / KIT), "Transcribing Rhythmic Patterns of the Guitar Track in Polyphonic Music", arXiv 2510.05756 (2025): https://arxiv.org/html/2510.05756v1 ; code and excerpts: https://github.com/YousicianGit/rhythmic-pattern-transcription
- Murgul, Schimper and Heizmann, "Joint Transcription of Acoustic Guitar Strumming Directions and Chords", ISMIR 2025, arXiv 2508.07973: https://arxiv.org/html/2508.07973 ; programme page: https://ismir2025program.ismir.net/poster_89.html
- Murgul and Heizmann, "A Multimodal Approach to Acoustic Guitar Strumming Action Transcription", ISMIR 2022 LBD: https://ismir2022program.ismir.net/lbd_393.html
- Dixon, Gouyon and Widmer, "Towards Characterisation of Music via Rhythmic Patterns", ISMIR 2004: https://archives.ismir.net/ismir2004/paper/000165.pdf
- McFee and Ellis, "Better Beat Tracking Through Robust Onset Aggregation", ICASSP 2014: https://brianmcfee.net/papers/icassp2014_beats.pdf
- Böck and Widmer, "Maximum Filter Vibrato Suppression for Onset Detection" (SuperFlux), DAFx 2013: https://dafx.de/paper-archive/details/0oee-99Z88WL7pSo749gcA ; librosa SuperFlux example: https://librosa.org/doc/main/auto_examples/plot_superflux.html
- FitzGerald, "Harmonic/Percussive Separation using Median Filtering", DAFx 2010: https://www.audiolabs-erlangen.com/resources/aps-w23/papers/2010_FitzGerald_HarmonicPercussiveSep_DAFx.pdf ; librosa `decompose.hpss`: https://librosa.org/doc/0.10.2/generated/librosa.decompose.hpss.html
- Reboursière et al., "Left and right-hand guitar playing techniques detection", NIME 2012: https://nime.org/proceedings/2012/nime2012_213.pdf
- Chirp group delay onset detection (guitar dataset F1 figures for SuperFlux and CNN), arXiv 2408.13734: https://arxiv.org/pdf/2408.13734
- Foscarin, Schlüter and Widmer, "Beat This! Accurate beat tracking without DBN postprocessing", ISMIR 2024 (MIT): https://arxiv.org/pdf/2407.21658
- librosa `onset_detect`: https://librosa.org/doc/0.10.2/generated/librosa.onset.onset_detect.html ; `onset_strength`: https://librosa.org/doc/0.10.2/generated/librosa.onset.onset_strength.html
- madmom onsets module: https://madmom.readthedocs.io/en/v0.16/modules/features/onsets.html ; repository and licence: https://github.com/cpjku/madmom ; NumPy breakage issue: https://github.com/CPJKU/madmom/issues/527
- MERT-v1-95M model card (CC-BY-NC-4.0): https://portrait.gitee.com/modelee/MERT-v1-95M
- IDMT-SMT-Guitar dataset: https://www.idmt.fraunhofer.de/en/publications/datasets/guitar.html
- GuitarSet, ISMIR 2018: https://archives.ismir.net/ismir2018/paper/000188.pdf
- Swing ratio estimation (ISMIR 2015): https://www.ismir2015.uma.es/articles/143_Paper.pdf ; Gouyon, "A computational approach to rhythm description": https://courses.cs.washington.edu/courses/cse590m/08wi/Gouyon%20-%20A%20COMPUTATIONAL%20APPROACH%20TO%20RHYTHM%20DESCRIPTION.pdf
- Cemgil et al., rhythm quantisation and tempo tracking: https://arxiv.org/abs/1106.4863

Products and pattern libraries:
- Chordify support, "Does Chordify show the strumming patterns?": https://support.chordify.net/hc/en-us/articles/360019489618-Does-Chordify-show-the-strumming-patterns-
- Ultimate Guitar help, "Strumming patterns: how to read and play": https://help.ultimate-guitar.com/en/articles/6744662-strumming-patterns-how-to-read-play
- JustinGuitar community thread on app strum patterns: https://community.justinguitar.com/t/strum-patterns-for-songs-in-app/102499
- Moises release notes: https://moises.ai/blog/latest/improvements-latest-releases
- Soundslice transcription help: https://www.soundslice.com/help/en/creating/transcribing/
- UkuTabs, ukulele strumming patterns for beginners (18 patterns): https://ukutabs.com/ukulele-guides/ukulele-strumming-patterns-beginners/
- Roadie Music, five ukulele strumming patterns: https://www.roadiemusic.com/blog/5-ukulele-strumming-patterns-for-beginners/
- audio-separator on PyPI (MIT, model listing): https://pypi.org/project/audio-separator/
- MVSep algorithm list (guitar model SDR claims, unverified): https://mvsep.com/en/algorithms
- StrumSight (hobby, on-device direction display): https://github.com/wolfcasaba/strumsight
