# Beat tracking, tempo octave, downbeats and the bar grid: research report

Date: 2026-10-03. Strand: "Beat tracking, tempo octave, downbeats and the bar grid" for the Youkelele chain (ingest -> separate -> grid -> harmony -> strums -> arrange -> score -> render). The grid stage is `src/youkelele/stages/grid.py` with the rules in `src/youkelele/music/tempo.py`, `src/youkelele/music/backbeat.py` and the detector wrapper `src/youkelele/models/beats.py` (Beat This! `final0`, `dbn=False`, CPU). Everything below is grounded in the four run folders under `runs\` (Chelsea Dagger `sexhetcxqy4`, Summer of '69 `9f06qzcvuhg`, Pour Some Sugar On Me `0uib9y4ofps`, Wet Leg "mangetout" `lbc6ccztp5e`), the spike and lessons documents under `docs\superpowers\specs\`, and the external sources listed at the end.

Conventions: **Verified** means I read the source or measured the run data myself. **Inferred** means a conclusion I draw from verified material; it has not been measured on the project's songs. Version 1.2 items already approved (four-bar section minimum, mean-interval header tempo, title cleaning, no-chord filling, passing chords, phrase alignment, repeated row blocks, narrow pickup cell) are taken as given and not proposed again.

---

## 0. What the current grid does, and what the runs show

Verified from the code and `grid.json`:

- Beat This! is run on the mono mix with minimal post-processing (no DBN). Beat times come out at the model's 50 fps frame rate, so every beat is on a 20 ms lattice. In all four runs the inter-beat intervals take only the values 0.34 to 0.42 s (Chelsea), 0.40 to 0.46 s (Summer of '69), 0.68 to 0.74 s (Pour Some Sugar), 0.44 to 0.50 s (Wet Leg), all multiples of 0.02 s. This is why the median interval gives a biased tempo (136.4 for a 139 song: 60/0.44) and why the spec moved the header to the mean. See section 4.1 for a better estimator.
- `fill_gaps` inserts beats where an interval exceeds 1.6 times the local median (window of 17 intervals). `decide_octave` halves only when bpm > 140, bpm/2 is in 60 to 95, and the drum backbeat ratio is below 1.0 or the drum stem is silent. `normalise_octave` drops beats locally when halving (repairs a mid-song octave switch, but only when the global decision is "half"). `build_bars` uses the modal downbeat phase (beat index mod numerator over the Beat This! downbeats within 70 ms of a beat), with a chroma-change tie-break after halving. The meter comes from `--meter`, default 4/4; nothing detects it. The pickup is "beats before the first modal-phase downbeat".
- Per-32-beat local tempo is flat within about 1 bpm on all four songs (Chelsea 152.9 to 156.9, Summer of '69 137.9 to 139.1, Pour Some Sugar 84.5 to 85.1, Wet Leg 127.7 to 128.7). No interval outliers remain after gap filling. So tempo drift is not a problem on this material; octave, phase, pickup and meter are.
- Chord changes by beat position after snapping: Chelsea 58 on beat 0 and 10 on beat 2; Summer of '69 73 on beat 0 and 3 on beat 1; Pour Some Sugar 48 on beat 0, 25 on beat 2, 7 on beat 1, 2 on beat 3; Wet Leg 62 on beat 0, 2 on beat 1, 2 on beat 3, 1 on beat 2. Bar phase is therefore right on all four (the strong majority of changes land on bar starts), and the half-bar changes in Pour Some Sugar are musically right (the published chart moves E to A on beat 3).
- The spike (`2026-10-03-spike-grid-round3.md`) recorded the two real octave failures: I'm Yours (150 detected, true 75) and Over the Rainbow (167 detected, true about 83, and the detector switched octave mid-song: 167 bpm for 0 to 59 s and 90 to 178 s, 86 bpm in between). Riptide had a dropped beat at 37.4 s (2.04x interval) that flipped the bar phase for the rest of the song until `fill_gaps` was added. Summer of '69 has two Beat This! downbeats one beat apart at 0.02 and 0.44 s, which is why the halving parity rule uses the modal phase rather than the first downbeat.

---

## 1. Failure modes

### 1.1 Tempo octave errors (half and double time)

**Why they happen.** Beat trackers select one metrical level from several plausible ones; half and double are both periodic and both fit the onset pattern. Smith (ISMIR 2010, "Beat Critic") states the problem exactly: "such systems often make 'octave errors', identifying the beat period at double or half the beat rate than that actually recorded in the music" [S1]. Schreiber and Müller (ISMIR 2017) report that for a simple tempo estimator on their Combined test set 68.1% of estimates are correct, 12.3% are half-tempo errors and 11.2% are double-tempo errors, with other factors (3, 1/3, 3/2, 4/3) under 1% each; on GiantSteps (EDM) 21.5% are double errors [S2, Table 1]. Verified from the paper text.

**Human listeners disagree too.** McKinney and Moelants (ISMIR 2004) found that "in most cases at least two beat periods were perceived by the subjects" when tapping to musical excerpts, with a global preference ("resonance") near 120 bpm, and that for some excerpts the salient tempo sits well above or below that [S3]. So "the" tempo of a strumming chart is a convention, not a fact of the signal; the chart should state the convention it chose (section 4.3).

**Neural trackers are confidently wrong, not unsure.** The SMC failure-mode analysis (arXiv 2605.12287, May 2026) evaluates Beat This!, madmom's DBNBeatTracker and Beat Transformer and finds "octave errors (correct phase but wrong metrical level)" on 8% of SMC tracks, "continuity errors" on 18% and complete failure on 5%; it reports that models "produce confident but wrong activations" (maximum activation 0.931 on failing tracks) and that the standard DBN's default minimum tempo of 55 bpm "forces double-tempo predictions on slow music" for 21% of SMC tracks; lowering it to 30 bpm fixes those [S4]. Beat This! peak-picking scores F = 0.627 on SMC; an adaptive DBN tempo-continuity parameter reaches 0.642 [S4]. Verified from the PDF.

**Beat This! specifics.** The authors state the model "can still fail, especially for difficult and underrepresented genres, and performs worse on continuity metrics", and that "for complex or underrepresented pieces, our network introduces non-periodic beats, which drastically lower the continuity" [S5]. Downstream projects report exactly the project's two failure shapes: (a) a whole slow song tracked at double time (the project's I'm Yours and Over the Rainbow; Drumscore's and subwave's reports of 76 bpm songs read as 152 [S6, S7]); (b) a mid-song metrical-level switch, "bars 1 to 16 lasted about 1.84 s (about 130 bpm), bars 17 onward about 3.70 s (about 65 bpm)", rendering as "half-time at a faster tempo" (sheetydrums backlog [S8]; the project's Over the Rainbow case).

**Why the project's band rule is fragile.** The spike showed real 141 to 190 bpm songs sit inside the halving band (Chelsea Dagger at 158 is correct; I'm Yours at 150 and Over the Rainbow at 167 are doubled), so only the drum backbeat test separates them, and that test is uninformative when drums are absent or when the snare sits on beat 3 (I'm Yours measured 0.57 with "snare peak on beat 3"). Verified from `2026-10-03-real-run-lessons.md` item 3 and `tempo.py`. The half-time feel is precisely the case where the snare moves "from beats 2 and 4 to beat 3" (Soundbrenner [S9]; Wikipedia "Half-time" [S10]), so a backbeat test at the fast octave sees snare on "beat 3" of a 4-beat group that is really beats 1 and 3 of the half grid. This is the genre-conventional trap: trap and dubstep are counted at 140 while the felt pulse is 70 [S11].

### 1.2 Bar phase (downbeat) errors

- Beat This! downbeat F1 is well below its beat F1: 85.4 vs 92.6 on its validation split; per dataset, Harmonix 90.7, RWC Pop 93.7, Beatles 88.8, GuitarSet 88.1, Hainsworth 80.0, RWC Jazz 80.7 [S5, Table 1]. On GTZAN a third party lists Beat This! at 88.9 beat F1 and 75.5 downbeat F1 [S12]. Roughly one downbeat in four is wrong on genre-mixed material; on pop and rock about one in ten.
- The minimal post-processing moves each downbeat to the nearest beat and de-duplicates (`beat_idx = np.argmin(np.abs(beat_time - d_time))`, `np.unique`) [S13], so two downbeats can land one beat apart (Summer of '69 at 0.02 and 0.44 s). The model has a "sum head" so that downbeat logits are a function of beat logits, which "almost halves the percentage of downbeats that are more than 70 ms away from the closest beat, from 1.1% to 0.62%" [S5].
- Legato and quiet intros are a known weak spot: stagehand's comparison found "bar phase remains unreliable on legato intros because Beat This's downbeat detection is unreliable", and BeatNet better on quiet legato intros (41.8 ms vs 118.4 ms) while Beat This! + DBN was far better on rubato (25.6 ms vs 225.5 ms) [S14]. The standard evaluation convention trims the first 5 s of every track before scoring beats (mir_eval default, used by Beat This! and BeatFM) [S5, S12], which is a tacit admission that the opening seconds are unreliable, exactly where a chord sheet's pickup and first bar come from.
- A single dropped beat flips the phase of every later bar when bars are built from beat indices modulo 4 (Riptide, fixed by `fill_gaps`). A spurious extra beat does the same in the other direction; the current code does not remove extra beats (only `normalise_octave` drops beats, and only when halving).

### 1.3 Time signature

- Beat This! has no meter output; the downbeats imply it. Training data is dominated by 4/4: Morais, McFee and Fuentes ("Skip That Beat", 2025) state that "current datasets for beat and downbeat tracking are biased towards music in 4/4 meter" and in their data 993 tracks of 4/4 make 80% of the whole; their beat-removal augmentation raised BayesBeat downbeat F1 from 0.41 to 0.49 overall [S15]. Beat This! itself scores 95.3 downbeat F1 on Ballroom (which contains waltzes) [S5], so its downbeats carry 3/4 information on dance music, but the time-signature survey notes "mistaken results were produced for meters such as 2/4 with 4/4 or 5/4; 7/8 with 3/4 or 4/4" and that compound meters (6/8, 9/8, 12/8) are "multiples of the simple time signatures" and hard to separate [S16].
- The madmom DBN handles meter by enumerating `beats_per_bar=[3, 4]` and letting the HMM choose; Beat This!'s optional DBN uses exactly `beats_per_bar=[3, 4], min_bpm=55.0, max_bpm=215.0, fps=50, transition_lambda=100` [S13, S17]. But "the DBN is inherently bound to fail for pieces with time signature changes, pieces whose tempo falls outside the tempo range, and pieces whose number of beats per measure are not included in the list" [S5]. 6/8 is not in that list; it is tracked as 3 or as 2 (dotted crotchets).
- The project hard-codes 4/4; a waltz or a 6/8 ballad would be forced into 4-beat bars with a phase that drifts one beat every bar, and `backbeat_ratio` would be computed on the wrong positions. Nothing in the data set so far exercises this (all four runs are 4/4), so this is a latent failure, not a measured one.

### 1.4 Tempo drift, rubato intros, free time

- Tempo drift is small on produced pop and rock (the four runs vary under 1 bpm). It matters for live recordings, singer-songwriter material and anything played without a click. Schreiber and Müller state their global-tempo method "is only suitable for music with such a global tempo" [S2]; Capo (a commercial transcription tool) deliberately maps "the eighth note (or triplet) pulse over the recording, allowing it to handle a little bit of drift over time" rather than applying one bpm [S18].
- Rubato and free-time intros produce beats whose intervals bear no stable ratio to the song tempo. Beat This! without DBN follows them (good: no imposed grid), but the project then builds bars of four beats across them, each bar a different length, and the strum stage quantises onsets to those bars. SMC's ground-truth inter-beat intervals are "2.5 to 5.3x more variable than those of standard training datasets" and tempo instability "causes failures at the activation level, not just the DBN level" [S4].

### 1.5 Pickup bars and the start of the grid

- A musical pickup (anacrusis) is "a partial bar preceding the downbeat of the first complete bar" [S19]. The detector's first beat is not necessarily musical: Summer of '69's "pickup" at 0.02 s is one beat 20 ms into the upload, before the published chart's count-in; Beat This! also places "a downbeat at exactly 30.0 s (the clip end) as well as 0.0 s" on the synthetic clip (spike models, verified). Pour Some Sugar On Me's video pre-roll produced a false intro of six A chords (lessons, verified). So the first and last beats need an energy and content test, not just a time test.

### 1.6 Chord changes versus bar lines

- Chord changes in pop sit mostly on downbeats, sometimes on beat 3. The Rolling Stone 200 corpus analysis gives a modal chord duration of 1.00 bar and a median of 1.23 bars [S20]. Papadopoulos and Peeters (2011) built an HMM in which chord transitions depend on the position in the bar and showed "the downbeat positions of a music piece can be estimated in terms of its harmonic structure and that conversely the chord progression estimation benefits from considering the interaction between the metric and the harmonic structures" [S21]. A madmom user measured that chord changes from the CNN/CRF chord recogniser "consistently occur late relative to downbeats, approximately 10% misclassification on US pop music" [S22]; the project's own spike found the vendored chord model's boundaries "lag by 0.1 to 0.4 s" (spike models, Spike B, verified). `snap_to_beats` votes per beat by overlap share, so a lagging boundary pushes a change from beat 0 to beat 1 whenever the lag exceeds half a beat (0.19 s at 158 bpm, 0.22 s at 139 bpm), which is exactly the 3 beat-1 changes on Summer of '69 and the 7 on Pour Some Sugar.

---

## 2. What others do

### 2.1 Libraries and models, with licences and CPU practicality

| System | What it gives | Octave and meter handling | Licence | CPU practicality | Verified? |
|---|---|---|---|---|---|
| Beat This! (CPJKU, ISMIR 2024) | Beats and downbeats; no tempo, no meter | None in minimal mode (peak-pick logits > 0, 7-frame max-pool, downbeats snapped to beats). Optional madmom DBN with `beats_per_bar=[3,4]`, 55 to 215 bpm | Code MIT; weights trained partly on copyrighted data (README note) | `final0` 20.3 M params (about 80 MB), `small0` 2.1 M params (about 10 MB) "faster but slightly less accurate" [S23]; a Rust ONNX port runs a 4:32 track in 4.6 s on an M4 [S24]; the project's grid stage took 7 s including features | Yes [S5, S13, S23, S24] |
| madmom (CPJKU) | RNN beat and downbeat activations; DBN decoding with tempo range and `beats_per_bar` list; `DBNBarTrackingProcessor` | Explicit: DBN chooses among listed bar lengths; `transition_lambda` controls tempo switching; maintainer advice to clip activations to 0 to 0.5 and raise `transition_lambda` on unstable material [S25] | Code BSD-2-Clause; models CC BY-NC-SA 4.0 (commercial use needs permission) [S26] | Fast on CPU, but the PyPI release targets Python < 3.10 and NumPy 1.x; Beat This! issue #9 says the DBN path "requires python<=3.9" [S27]; installing from git on 3.12 is reported to need Cython and NumPy pinned first [S28] | Yes |
| BeatNet (Heydari et al., ISMIR 2021) | Online and offline joint beat, downbeat, tempo and meter tracking (CRNN + particle filter) | Estimates meter without being primed [S29] | CC BY 4.0 | Depends on madmom (same install problem) and PyAudio; three genre models; stagehand found it better on quiet legato intros, worse on rubato [S14] | Yes [S29] |
| allin1 (Kim and Nam, ISMIR 2023) | Tempo, beats, downbeats, section boundaries and labels from Demucs stems | Joint model; outputs bpm directly | MIT | CPU supported; needs NATTEN, which on Windows "requires building from source using ninja"; recommends WAV input because MP3 decoders shift by 20 to 40 ms [S30] | Yes [S30] |
| librosa `beat_track` / `feature.tempo` | Ellis 2007 dynamic programming; tempogram with a log-normal prior at `start_bpm=120`, `tightness=100`, `trim=True` | No octave correction; the 120 bpm prior "favors doubled tempos" on slow material (subwave issue: 76 bpm track read as 152, 25% of 27,860 tracks above 140) [S7, S31] | ISC | Trivial | Yes |
| Essentia RhythmExtractor2013 / TempoCNN | Beats, bpm, confidence (multifeature) | "degara" method "locks onto the half-time pulse of fast genres, drum & bass at 174 reads as roughly 87"; multifeature 87.9% within 2% on a 953-song benchmark vs TempoCNN 84.8% [S32] | Essentia AGPL-3.0 (from memory, not re-verified); TempoCNN models CC BY-NC-SA (from memory) | C++ core, no Windows wheels in the main line | Partly |
| BeatFM (2025) | Beats and downbeats on a music foundation model (MERT / MusicFM) | GTZAN downbeat F1 79.6 vs Beat This! 75.5, AMLt 93.5 vs 89.4 | Paper only; no code found [S12] | Not practical | Yes (paper) |
| Masked diffusion beat tracking (2026) | Coherent beat sequences; addresses "consecutive downbeats and erratic tempo changes" | Iterative inference with peak-picking across steps | CC BY 4.0 paper; code not seen | Not assessed | Abstract only [S33] |

### 2.2 Post-hoc octave correction practised downstream of Beat This!

- **Drumscore (PR #116)** abandoned a librosa phase-error octave selector (which read CCR at 229.7 instead of 114.8) and instead regularises Beat This! output: anchor on a stable run of detections, drop double-time, triplet and spurious detections, fill skipped beats evenly, take bar phase by "downbeat voting", and derive tempo from the regularised beats. 8 of 8 labelled songs correct, versus 1 of 8 for librosa [S6].
- **stagehand (PR #22)** adds `fix_metrical_level()` (repairs stretches tracked at half or double "the song's dominant pulse", touching only ratios "within tolerance of exactly 0.5x/2.0x so genuine tempo changes are never altered"), `bridge_unreliable_stretches()` (re-grids low-confidence spans only when the confident segments either side agree on tempo), and `detect_tempo_segments()` (a piecewise tempo map "via regression of beat time against beat index, gated on fit residual", recovering 137.056 bpm as 137.07). Tolerances are derived "from the song's own measured tempo spread" rather than a fixed ±12% [S14].
- **Beat This! issue #13** (GiantSteps benchmarking) infers bpm "through a phase-aware circular mean and linear regression on the beat grid" and applies an octave heuristic with a 78 to 185 bpm range, reaching Accuracy1 89.3% (single model) and 90.9% (ensemble of checkpoints) on 664 EDM tracks [S34].
- **madmom issue #416**: a user obtained tempo "within 0.01 of the actual bpm" with `scipy.stats.linregress` on beat positions, against the processor's 1 bpm rounding [S35].
- **sheetydrums** plans "a beats-stage post-process to snap the whole song to one metrical level" after a 2x split at bar 16 [S8].
- **vscode-guitar-dsl issue #59** (drumless guitar audio) reports Accuracy2 96.7% but Accuracy1 66.7% from Beat This!, with guitar at 90% and piano, strings and pads at 40 to 50%, and proposes a "post-inference metrical-level choice between ×1/2, ×1 and ×2" using inter-beat logit and onset evidence plus the downbeat output [S36].

### 2.3 Research methods for the octave decision

- **Beat Critic (Smith 2010)**: compute a 16-semiquaver metrical profile per bar in eight spectral subbands at the detected tactus, and at the half-time, half-time counter-phase and double-time hypotheses; measure "quaver alternation" (variation between adjacent sub-beat positions). "A low quaver alternation measure indicates ... the structural level chosen as the quaver is incorrect, i.e. an octave error has occurred." A threshold half a standard deviation above the dataset mean (e' = 3.34) reduced octave errors "to 43% of the previous error rate" on RWC [S1].
- **Schreiber and Müller 2017**: a random forest (300 trees, depth 25) classifies the estimate into error classes (E1/2, E1, E2, ...) from a log beat spectrum (10 log-spaced bands, 40 to 500 bpm), spectral flatness and temporal flatness features; it raised Accuracy1 on the Combined set from 69.0% to 77.4% for their own estimator and improved every published estimator it was applied to. They also tabulate "sweet octaves": 69 to 138 bpm covers 72.9% of the Combined set, 66 to 132 covers 80.9% of GTZAN, while 91 to 182 covers 88.1% of GiantSteps [S2]. The lesson: a fixed band is a genre prior, which is why the project's 60 to 95 halving window works on ballads and fails on fast rock.
- **Krebs, Böck and Widmer 2013**: modelling rhythmic patterns explicitly in a bar-pointer HMM "drastically reduces octave errors ... and substantially improves downbeat tracking" on 697 ballroom pieces, with meter (3/4 vs 4/4) inferred jointly [S37].
- **Multi-hypothesis tempo** is the SMC paper's main recommendation: "replace fixed DBN parameters with context-adaptive approaches", because "no single fixed setting can serve both populations" [S4].
- **Chordify** (ISMIR 2015 late-breaking): downbeats from Sonic Annotator, then a harmony model (HarmTrace) over beat-synchronous chroma; a "chord change possibility" is "estimated by differentiating the average chroma vectors for each beat ... motivated by the musicological knowledge that chord changes often occur at downbeats", and the time signature is estimated "by examining the similarity of frames at the beat level" [S38].
- Commercial tools make the octave user-correctable: Traktor has "x2" and "/2" buttons; Moises documents that its single static bpm cannot follow tempo changes and tells users to correct it [S11, S39].

### 2.4 How a human transcriber decides the "feel" tempo of a strumming chart

Verified statements: half-time is a change of accent placement at the same pulse, "the snare often lands on beat 3" instead of 2 and 4, while "the BPM remains constant" [S9, S10]; listeners split between two levels in most excerpts, with a global preference near 120 bpm [S3]; rock corpora change chords about once per bar [S20]. Inferred rule set (what a transcriber does implicitly, and what the project can compute):

1. Count at the level where the snare is on 2 and 4. If the snare is on 3 of a 4-group, you are counting at double speed.
2. Prefer the level at which most chord changes fall on bar lines and a typical chord lasts one or two bars, not half a bar or four bars.
3. Prefer the level at which the strum pattern fits eight slots per bar with 2 to 6 strikes per bar (the project already caps sixteen slots above 140 bpm for exactly this reason; spec 1.1, section 4.1).
4. Prefer a tempo in roughly 60 to 180 bpm; when both octaves are inside, items 1 to 3 decide; when the chart is for a slow ballad with a strummed eighth-note pulse, charts are usually written at the slow tempo with eighth-note strums rather than the fast tempo with quarter-note strums.
5. State the alternative on the sheet ("or 79 bpm counted in half time") when the evidence is split.

---

## 3. Research summary: state of the art and "good enough"

- **Beat tracking on pop and rock is solved to about 95% F1**; downbeats are at 88 to 94% on pop datasets (Harmonix 90.7, RWC Pop 93.7, Beatles 88.8 for Beat This!) [S5]. The residual errors are structural (octave, phase, meter, continuity), not jitter. BeatFM's gains over Beat This! are mostly in continuity (AMLt 93.5 vs 89.4 beat, 88.7 vs 75.5 downbeat) [S12], which says that coherence post-processing is where the remaining value lies, and that is doable without a new model.
- **The DBN trade-off is now well characterised.** Beat This! with DBN: "increases our CMLt downbeat performance by correcting some of the (wrongly) non-periodic outputs, but it reduces our F1 performance, by changing other otherwise correct predictions that fall outside the DBN assumptions" [S5]; the DBN row on GTZAN reads beat F1 88.1, CMLt 80.5, AMLt 91.1 and downbeat F1 77.4, CMLt 73.3, AMLt 87.8 [S5, Table 2]. The SMC paper adds that fixing the DBN tempo range to within ±20% of the true tempo "improves metrical coherence (CMLt) but does not improve beat placement (F-measure)" [S4]. For a chord grid, coherence (one metrical level, one phase for the whole song) is worth more than per-beat placement, so a light coherence pass is the right investment.
- **Tempo accuracy**: Accuracy1 for the best systems is in the high 80s to low 90s on EDM and mixed sets (Beat This! + heuristic 89.3 to 90.9% on GiantSteps [S34]; Schreiber's post-processing lifts Böck et al. and others by 2 to 8 points [S2]). Accuracy2 is at 95 to 96%, so almost all residual tempo error is octave error. For this project the four known songs are octave-correct and the two known failures are both ballads at the doubled level: the "fast ballad" case is the one to engineer for.
- **Meter**: 3/4 vs 4/4 from downbeat spacing is reliable when the downbeats are reliable; 6/8 is ambiguous with 3/4 and 2/4 by construction [S16]. Good enough for this project: detect 3 vs 4 and flag everything else.
- **Rubato**: unsolved in general; SMC F1 is 0.63 for the best models [S4]. Good enough: detect it and mark bars as free time rather than pretend.
- **Chord to bar alignment**: joint models exist (Papadopoulos and Peeters [S21]) but a position-dependent change penalty on a beat lattice captures most of the benefit, which is what Chordify's HarmTrace stage and the patent literature (chord-change likelihood plus accent likelihood for downbeats) do [S38, S40].

---

## 4. Easy wins

Each item names the code it touches, the evidence, and how to measure it. "Measure on the six songs" means the four run folders plus the spike's I'm Yours and Over the Rainbow beat lists (`SP\spike_audio2\{imyours,sotr}\beats.json` as described in the spike report).

### 4.1 Tempo by regression, not by median or mean (`music/tempo.py: bpm_from_beats`)

Beat This! beat times are quantised to 20 ms (verified from `grid.json`). The median of quantised intervals is one of a few lattice values (136.4 or 142.9 for a 139 bpm song). The mean is better (spec 1.2) but is still dragged by a long pickup or outro interval and ignores the 20 ms noise structure. Fit `t_i = a + b * i` over the gap-filled beats by least squares (or `scipy.stats.linregress`), optionally after dropping the first and last two beats; tempo is `60 / b`. madmom issue #416 reports "within 0.01 of the actual bpm" [S35]; stagehand recovers 137.056 as 137.07 [S14]; Beat This! issue #13 uses regression plus a circular mean [S34]. Keep the median for the octave decision thresholds (they were measured on it). Expected: 139.0 for Summer of '69, 85.0 for Pour Some Sugar, within 0.2 bpm; report the residual standard deviation as `tempo_jitter_ms` in `grid.json`. Add a test with a 20 ms-quantised synthetic beat list at 139 bpm asserting the regression recovers 139.0 ± 0.1 where the median gives 136.4.

### 4.2 Tempo ambiguity flag and alternative tempo on the sheet (`stages/grid.py`, `schemas.Grid`, render header)

Compute a cheap ambiguity score and never hide it. Two measures, both from material already in the stage: (a) the ratio of `librosa.feature.tempogram` strength at the chosen tempo lag to the strength at the half and double lags (the subwave fix: "use the tempogram peak ratio between the chosen lag and its octave counterpart to flag genuinely ambiguous readings" [S7]); (b) whether the chosen tempo and its alternative both lie inside 60 to 180. Add `Grid.tempo_alternative: float | None` and `Grid.tempo_ambiguous: bool`. The header prints "139 bpm" or "158 bpm (or 79 in half time)" and the CLI log prints the `--beat-octave half` hint. This does not change any decision; it tells the player what a tap test would. Measure: the four runs should show the alternative only where the backbeat ratio is near 1 or the tempogram ratio is under about 1.3 (threshold to be set on the six songs).

### 4.3 Multi-hypothesis octave scoring instead of a band (`music/tempo.py: decide_octave`)

Replace the hard "bpm > 140 and 60 <= bpm/2 <= 95" gate by a score over the three hypotheses {half, detected, double}, each cue voting with a weight, with the band kept only as a soft prior (a log-normal centred near 110 to 120 bpm, per the resonance literature [S3] and the GTZAN sweet octave 66 to 132 [S2]). Cues, all computable in the grid stage:

1. **Backbeat ratio** at each hypothesis (already implemented for the detected grid; run `backbeat_ratio` on the halved and doubled beat lists too). A ratio well above 1 at the detected level and near 1 at the halved level says "detected is right"; the reverse says "halve". I'm Yours' snare-on-3 pattern becomes snare-on-2-and-4 after halving, so the halved grid scores high. Verified values exist for the detected grid only; measure the halved grid.
2. **Quaver alternation (Beat Critic)** [S1]: build a 16-slot metrical profile per bar of the drum stem's high-band onset strength at each hypothesis; compute the mean absolute difference between adjacent odd and even slots. At the correct level the eighths alternate strong/weak; at a doubled grid the "eighths" are sixteenths and alternation collapses. The spike's "percussive backbeat asymmetry over the four beat positions" (uninformative, hi-hats fill every beat) is a different statistic (beat-level, not sub-beat), so this is untested, not refuted.
3. **Harmonic rhythm**: median chord duration in bars at each hypothesis, using a cheap chroma-change detector (the stage already computes beat chroma for the phase tie-break) or, later, the harmony stage's events. Target: median between 0.5 and 2 bars [S20]. The spike showed that adjacent-bar chroma alternation alone fails on two-bar harmonic rhythm (Summer of '69), so use it as a bounded vote, not a decider: strongly against a hypothesis only when the median chord lasts under half a bar or over four bars.
4. **Tempo prior**: soft, not a gate.
5. **Drum stem silent**: removes cue 1 and 2 and raises the prior's weight, as now.

Decision: pick the hypothesis with the highest total; if the top two are within a margin, keep "detected" and set `tempo_ambiguous`. Record every cue in `grid.json` (`octave_cues: dict`) so the decision is auditable and so thresholds can be re-fitted when new songs are run. Measure on the six songs: must keep Chelsea 158, Summer of '69 139, Pour Some Sugar 85, Wet Leg 128, Riptide 103, and halve I'm Yours and Over the Rainbow. Keep `--beat-octave` as the override.

### 4.4 Metrical-level regularisation independent of the global decision (`music/tempo.py: fill_gaps`, new `regularise_beats`)

Today a mid-song octave switch is repaired only when the global decision is "half" (`normalise_octave`), and extra beats are never removed. Generalise, following stagehand's `fix_metrical_level` and Drumscore's regularisation [S14, S6]: (1) compute the dominant interval (median of the middle 80% of intervals); (2) find runs of at least 8 intervals whose local median is within 10% of 0.5x or 2.0x the dominant interval; (3) in a 0.5x run drop every other beat starting on the beat whose parity matches the downbeat parity in that run (the existing `normalise_octave` logic, applied locally); in a 2.0x run insert midpoints (the existing `fill_gaps` logic); (4) leave runs at other ratios alone and mark them (section 4.6). Then re-run the global decision on the regularised list. Test with the Over the Rainbow shape (fast for 0 to 59 s, half speed for 60 to 90 s) asserting one bar length throughout, and with a doubled 8-beat stretch inside a correct song.

### 4.5 Beats-per-bar detection, 3 against 4 (`stages/grid.py` before `build_bars`; `options.meter` becomes `auto`)

From the Beat This! downbeat indices (`downbeat_indices`), take the histogram of beats between consecutive downbeats. If the mode is 3 with share at least 0.6 and the mode-4 share is under 0.2, set `Meter(3, 4)`; if the mode is 6 or the detected tempo is above 160 with mode 3, offer 6/8 as the halved alternative; otherwise 4/4. Record `meter_detected`, `meter_shares` in `grid.json` and print them. This is the information the madmom DBN would extract from `beats_per_bar=[3, 4]` [S17], without the madmom dependency. Beat This! trained on Ballroom (waltzes) and scores 95.3 downbeat F1 there [S5], so the downbeat spacing is informative on dance-like 3/4; expect weaker results on folk waltzes (4/4 bias [S15]), hence the share thresholds and a visible flag rather than a silent switch. Downstream: `backbeat_ratio` already takes `numerator`; the strum stage's `slots_per_bar` (8 or 16) assumes 4 beats and must become `2 * numerator` or `4 * numerator`; the renderer's rows of four bars are fine. Add a synthetic 3/4 test (the existing synthetic clip generator can place downbeats every three beats).

### 4.6 Free-time and drift annotation (`music/tempo.py`, `schemas.Bar`, `schemas.Grid`)

Compute per-section tempo by regression (section 4.1) and the local interval ratio per bar. Add `Bar.free_time: bool` when a bar's beats deviate more than 17.5% from the song tempo (the CMLt tolerance [S4]) and the drum stem is silent in that bar; add `Grid.tempo_range: tuple[float, float]` over sections. The sheet prints "free time" over a run of such bars and "tempo 118 to 124" in the header when the range exceeds 3%. The four runs will show nothing (verified flat), which is the correct outcome; the value is on the next ballad with a rubato intro, which today becomes four-beat bars of random length and a nonsense strum pattern.

### 4.7 Pickup and leading-beat hygiene (`music/tempo.py: build_bars`)

Keep a leading partial bar only if (a) its beats have onset energy (drum or harmonic stem RMS in the pickup span above the song's 10th percentile of per-beat RMS) and (b) the chord model later labels it with a non-N chord that differs from, or leads into, bar 1. Otherwise start the grid at the first full downbeat and drop the stray beat. Summer of '69's 0.02 s beat fails (a); the 30 s synthetic clip's end downbeat is already excluded by the `< duration` test. Also apply the standard-evaluation idea in reverse: treat downbeats inside the first two beats of audio as unreliable for the modal phase (they are the ones the detector most often gets wrong on quiet intros [S14]); the modal vote across the song is unaffected.

### 4.8 Chord boundary lag compensation and position-dependent snapping (`music/snap.py`)

The vendored chord model lags by 0.1 to 0.4 s (spike, verified) and madmom users report the same lateness [S22]. Two steps: (1) shift every `LabelSpan` earlier by a fixed `CHORD_LAG_S` measured on the synthetic clip (where true changes are at exact 4 s multiples), clamped at 0; (2) when a run would start on beat 1 or 3 and the previous run's label covers the preceding beat 0 or 2 with a share under 0.75, move the change back to that beat. This is the position-dependent transition penalty of Papadopoulos and Peeters in its cheapest form [S21]. Measure: Summer of '69's 3 beat-1 changes and Pour Some Sugar's 7 beat-1 and 2 beat-3 changes should move to beats 0 and 2; the 25 beat-2 changes on Pour Some Sugar must stay. Record `ChordEvent.snapped_from: int | None` for auditing. Do not add bar-level forcing: the data shows half-bar changes are real.

### 4.9 Bar-phase confidence from chords (`stages/harmony.py` after snapping, or a small check in `stages/score.py`)

Count chord changes per beat position (the numbers in section 0). If another phase would put more changes on beat 0 than the current one by a factor of 1.5 and the downbeat modal share was under 0.6, set `Grid.phase_low_confidence = True` and print a one-line warning with the suggested shift; do not re-phase automatically in the first iteration (the data shows the modal phase is right on 4 of 4 and the spike's chroma rule agreed with the chord model on the halved songs). The spike measured 0.908 and 0.644 of chord changes on bar starts at the chosen phase on the two halved songs; this makes that check permanent and visible.

---

## 5. Deeper options

### 5.1 Decode from the logits, not from the peaks (`models/beats.py`)

Beat This! exposes `Audio2Frames` (spectrogram to beat and downbeat logits) separately from the `Postprocessor` [S13]. Keeping the frame logits allows: (a) an ensemble of `final0`, `final1`, `final2` by averaging logits before peak-picking, which issue #13 reports lifts Accuracy1 from 89.3% to 90.9% on GiantSteps [S34], at roughly three times the model time (the stage currently takes about 7 s including features, so this remains CPU-practical); (b) scoring the octave hypotheses by the mass of downbeat logits on each hypothesis' bar starts; (c) a small Viterbi of the project's own (no madmom) over a beat lattice with a tempo-continuity penalty and `beats_per_bar in {3, 4}`, which is a DBN in all but name, so one gets the coherence benefit (CMLt) the papers describe [S5, S4] while keeping Python 3.12. The SMC paper's finding that an adaptive continuity penalty per track beats any fixed one [S4] argues for making that penalty a function of the measured interval jitter (section 4.1), as stagehand does with its data-derived tolerances [S14].

### 5.2 Optional madmom DBN path

Beat This! `dbn=True` gives the madmom DBN with `beats_per_bar=[3, 4]` [S13]. Costs: madmom's PyPI release needs Python < 3.10 and NumPy 1.x [S27, S28]; a git install on 3.12 may work with Cython and NumPy pinned first but is fragile; madmom's code is BSD-2 and only the DBN code is used (the CC BY-NC-SA model restriction applies to madmom's own model files, which this path does not load) [S26]. Benefit: meter choice and coherence for free; cost: a lower F1 on pieces outside the DBN assumptions [S5] and a dependency the spike could not install. Recommendation: implement 5.1(c) instead, and keep this as a documented manual fallback.

### 5.3 A second opinion for the opening bars

stagehand's measurement (BeatNet 41.8 ms vs Beat This! 118.4 ms on quiet legato intros, the reverse on rubato) [S14] suggests a hybrid: Beat This! for beats, a different source for the first downbeat. Without adding BeatNet (madmom dependency, CC BY 4.0), the project can use its own bass and chord evidence for the opening phase: the first chord change and the first bass note onset after the intro's energy rises (the patent literature's "chord change likelihood plus accent-based downbeat likelihood" [S40]). This is the natural extension of 4.9 once the harmony stage is trusted.

### 5.4 Joint chord and downbeat decoding

Papadopoulos and Peeters' HMM topology (chord states crossed with position-in-bar states, transitions preferring changes on beat 1 and beat 3) [S21] can be implemented on the project's beat-synchronous `LabelSpan` posteriors if the chord model's per-frame probabilities are exposed (the vendored Chord-CNN-LSTM produces them before its own decoding). This would replace `snap_to_beats` with a decoder that places changes where both the chroma and the metre agree, and would give a principled phase estimate. It is the right long-term design but needs the chord model's posteriors and a validation set with bar-level chord annotations (the hand lists exist for two songs).

### 5.5 Tempo map rather than one tempo

For live and acoustic recordings, store a piecewise-linear tempo map (segments found by regression of beat time on index, split where the residual exceeds a threshold, as in stagehand [S14] and the piecewise tempo-arc literature [S41]) and render "rit." and "a tempo" markings. Capo's approach of storing every beat mark and following drift [S18] is what the grid already does implicitly; the map is a presentation layer over it. Low value on the current material; high value for singer-songwriter uploads.

### 5.6 allin1 as a cross-check, not a replacement

allin1 gives tempo, beats, downbeats and sections jointly from Demucs stems (MIT, CPU capable) [S30]. The project already separates with Demucs, so the marginal cost is the model plus NATTEN, which "requires building from source using ninja" on Windows [S30]. Use it offline as a second annotator to score the grid stage on new songs (agreement on bpm octave and downbeat phase), not in the chain.

---

## 6. What to measure before changing thresholds

1. Backbeat ratio at the halved grid for all six songs (4.3 cue 1).
2. Quaver alternation at detected, halved and doubled grids for all six (4.3 cue 2); if it does not separate I'm Yours from Chelsea Dagger, drop it.
3. Median chord duration in bars at each hypothesis using beat chroma change (4.3 cue 3), and using the harmony events for the four runs.
4. Tempogram ratio at the chosen lag against its octave counterparts (4.2).
5. Regression tempo and residual for the four runs against 139 and 85 (4.1).
6. The chord model's boundary lag on the synthetic clip and on the three songs with published charts (4.8).
7. Downbeat spacing histograms on the four runs (expected: mode 4 with share above 0.9) and on at least one 3/4 and one 6/8 recording to be chosen (4.5).

---

## Sources

- [S1] L. M. Smith, "Beat Critic: Beat Tracking Octave Error Identification by Metrical Profile Analysis", ISMIR 2010. https://archives.ismir.net/ismir2010/paper/000019.pdf (PDF read in full)
- [S2] H. Schreiber and M. Müller, "A Post-Processing Procedure for Improving Music Tempo Estimates Using Supervised Learning", ISMIR 2017. https://archives.ismir.net/ismir2017/paper/000137.pdf (PDF read; Tables 1 to 4)
- [S3] M. F. McKinney and D. Moelants, "Extracting the Perceptual Tempo from Music", ISMIR 2004. https://archives.ismir.net/ismir2004/paper/000197.pdf and the RPPW abstract https://cspeech.ucd.ie/rppw/rppw10/mckinney/abstract.html
- [S4] "The SMC Blind Spot: A Failure Mode Analysis of State-of-the-Art Beat Tracking", arXiv 2605.12287, May 2026. https://arxiv.org/abs/2605.12287 (PDF read)
- [S5] F. Foscarin, J. Schlüter and G. Widmer, "Beat this! Accurate beat tracking without DBN postprocessing", ISMIR 2024. https://arxiv.org/abs/2407.21658 (PDF read: abstract, Tables 1 to 3, Sections 3.3, 3.4, 4.1, 4.4, 4.5) and README https://github.com/CPJKU/beat_this/blob/main/README.md
- [S6] Drumscore PR #116, "Tempo octave-error correction (Beat This! beat tracking)". https://github.com/simbasang/Drumscore/pull/116
- [S7] subwave issue #1417, "BPM is double-time on slow material". https://github.com/perminder-klair/subwave/issues/1417
- [S8] sheetydrums PR #37, "v2-backlog item for beat-tracker metrical-level consistency". https://github.com/bradrogan/sheetydrums/pull/37
- [S9] Soundbrenner, "Half time feel". https://www.soundbrenner.com/blogs/articles/half-time-feel
- [S10] Wikipedia, "Half-time (music)". https://en.wikipedia.org/wiki/Half-time_(music)
- [S11] niew.ai, "Why your MP3 BPM finder reads half the tempo and how to fix it". https://niew.ai/blog/mp3-bpm-finder
- [S12] "BeatFM: Improving Beat Tracking with Pre-trained Music Foundation Model", arXiv 2508.09790 (2025). https://arxiv.org/html/2508.09790v1 (results table with Beat This! baseline)
- [S13] Beat This! post-processor source, `beat_this/model/postprocessor.py`. https://raw.githubusercontent.com/CPJKU/beat_this/main/beat_this/model/postprocessor.py and `beat_this/inference.py` https://github.com/CPJKU/beat_this/blob/main/beat_this/inference.py
- [S14] stagehand PR #22, "self-repairing beat analysis + mid-song tempo support". https://github.com/dsoto1998/stagehand/pull/22
- [S15] G. Morais, B. McFee and M. Fuentes, "Skip That Beat: Augmenting Meter Tracking Models for Underrepresented Time Signatures", 2025. https://arxiv.org/abs/2502.12972 (PDF read: Section 2.2, Table 1)
- [S16] J. Abimbola, D. Kostrzewa and P. Kasprowski, "Time Signature Detection: A Survey", Sensors 2021. https://pmc.ncbi.nlm.nih.gov/articles/PMC8512143/
- [S17] madmom documentation, `DBNDownBeatTrackingProcessor`. https://madmom.readthedocs.io/en/v0.16/modules/features/downbeats.html
- [S18] Capo user guide, "Beat and Tempo Estimation in Capo". https://supermegaultragroovy.com/products/capo/user-guide/4.7/concepts/about-beat-tracking.html
- [S19] Wikipedia, "Anacrusis". https://en.wikipedia.org/wiki/Anacrusis
- [S20] T. de Clercq, harmonic rhythm statistics for the Rolling Stone 200 corpus (mode 1.00 bar, median 1.23 bars). https://www.midside.com/presentations/declercq_2018_smt_miig_slides.pdf
- [S21] H. Papadopoulos and G. Peeters, "Joint Estimation of Chords and Downbeats from an Audio Signal", IEEE TASLP 19(1), 2011. https://hal.archives-ouvertes.fr/hal-00525172
- [S22] madmom issue #403, "Beat-aligned chords". https://github.com/CPJKU/madmom/issues/403
- [S23] Beat This! ONNX model card (parameter counts for `final0` and `small0`). https://huggingface.co/ashudesai/songbird-models
- [S24] `beat-this` Rust crate benchmarks. https://docs.rs/crate/beat-this/1.0.0
- [S25] madmom discussion #503 (maintainer advice on `transition_lambda`, clipping activations). https://github.com/CPJKU/madmom/discussions/503
- [S26] madmom LICENSE (BSD-2 code; CC BY-NC-SA 4.0 models). https://github.com/CPJKU/madmom/blob/main/LICENSE
- [S27] Beat This! issue #9, "`madmom` dependency requires python<=3.9". https://github.com/CPJKU/beat_this/issues/9
- [S28] madmom installation notes and third-party reports on Cython and NumPy pinning. https://madmom.readthedocs.io/en/latest/installation.html
- [S29] BeatNet repository and ISMIR 2021 paper. https://github.com/mjhydri/BeatNet
- [S30] All-In-One Music Structure Analyzer (allin1). https://github.com/mir-aidj/all-in-one
- [S31] librosa `beat_track` documentation. https://librosa.org/doc/0.10.2/generated/librosa.beat.beat_track.html
- [S32] Essentia beat detection tutorial and the deeprhythm comparison. https://essentia.upf.edu/tutorial_rhythm_beatdetection.html and https://pypi.org/project/deeprhythm/
- [S33] "Masked diffusion enables coherent beat tracking", arXiv 2608.04624 (2026). https://arxiv.org/abs/2608.04624
- [S34] Beat This! issue #13, "Script for Giant Steps benchmarking & improved BPM inference (Octave Correction)". https://github.com/CPJKU/beat_this/issues/13
- [S35] madmom issue #416, "Accurate Tempo Estimation". https://github.com/CPJKU/madmom/issues/416
- [S36] vscode-guitar-dsl issue #59, "Audio MIR tempo-octave disambiguation for non-guitar drumless audio". https://github.com/puchinya/vscode-guitar-dsl/issues/59
- [S37] F. Krebs, S. Böck and G. Widmer, "Rhythmic Pattern Modeling for Beat and Downbeat Tracking in Musical Audio", ISMIR 2013. https://archives.ismir.net/ismir2013/paper/000051.pdf
- [S38] Chordify system description, ISMIR 2015 late-breaking demo. https://www.ismir2015.uma.es/LBD/LBD42.pdf
- [S39] Moises help, "The BPM is wrong; what should I do?". https://help.moises.ai/hc/en-us/articles/16697903875484-The-BPM-is-wrong-what-should-I-do
- [S40] US patent 9,653,056, "Evaluation of beats, chords and downbeats from a musical audio signal" (chord-change likelihood plus accent likelihood for downbeats). https://patents.google.com/patent/US9653056
- [S41] D. Stowell and E. Chew, "Maximum a posteriori estimation of piecewise arcs in tempo time-series", arXiv 1302.0136. https://arxiv.org/abs/1302.0136
- [S42] S. Böck, M. E. P. Davies and P. Knees, "Multi-Task Learning of Tempo and Beat: Learning One to Improve the Other", ISMIR 2019. http://archives.ismir.net/ismir2019/paper/000058.pdf
- Project evidence (read in full): `docs\superpowers\specs\2026-10-03-real-run-lessons.md`, `2026-10-03-v1-1-validation.md`, `2026-10-03-spike-grid-round3.md`, `2026-10-03-ukulele-tab-chain-v1-1-design.md`, `2026-10-03-ukulele-tab-chain-v1-2-design.md`; code `src\youkelele\stages\grid.py`, `src\youkelele\music\tempo.py`, `src\youkelele\music\backbeat.py`, `src\youkelele\music\snap.py`, `src\youkelele\models\beats.py`; run artefacts `runs\<slug>\02_grid\grid.json` and `03_harmony\chords.json` for the four slugs.
