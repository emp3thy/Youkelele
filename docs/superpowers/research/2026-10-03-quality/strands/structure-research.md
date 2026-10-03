# Song structure segmentation and section labelling: research report

Date: 2026-10-03. Strand: "Song structure segmentation and section labelling" for the Youkelele grid stage (`src/youkelele/music/sections.py`, `src/youkelele/stages/grid.py`). Read-only; nothing under the project was changed.

How to read this document. "Verified" means I read the source (paper text, README, docs page, or the project's own code and run artefacts) and the statement is in it. "Inferred" means a conclusion I draw by combining sources with the project's behaviour; those are marked as such. Version 1.2 work (four-bar minimum, mean tempo, title cleaning, no-chord filling, passing chords, phrase alignment, repeated row blocks) is taken as given and not re-proposed; where a proposal touches the same code it is written as a step on top of 1.2.

What the project does today (verified from `sections.py` and `grid.py`): per-bar features are 12 CQT chroma (36 bins per octave, hop 512) plus 20 MFCCs, beat-synced then averaged per bar, plus per-bar RMS loudness in dB. The embedding is the librosa Laplacian segmentation recipe applied at bar resolution: chroma stacked with `stack_memory(n_steps=4)`, `recurrence_matrix(width=3, mode="affinity", sym=True)`, a time-lag median filter of size (1, 7), an MFCC path graph, the balanced `mu`, a normalised Laplacian, eigenvectors median-filtered with size (9, 1), and k-means on the first k normalised eigenvectors. k starts at 3 and rises while the largest cluster covers more than 60% of bars (max 6). Segments shorter than `min_bars` merge forward into the following segment (version 1.2 raises `min_bars` from 2 to 4). Labels: a cluster over 60% of bars is `verse`; `chorus` is the loudest recurring cluster; the remaining recurring cluster with most bars is `verse`; once-only clusters are `intro` (first), `outro` (last) or `bridge`; other recurring clusters are `verse 2`, `verse 3`. Confidence is 0.5, or 0.3 when the chorus loudness margin is under 1.5 dB.

The four real runs under `runs\` (verified from `02_grid/grid.json` and `03_harmony/chords.json`): Summer of '69 k 4, share 0.50, margin 0.70 dB, 11 sections; Chelsea Dagger k 3, share 0.58, margin 1.43 dB, 8 sections; Pour Some Sugar On Me k 3, share 0.49, margin 0.93 dB, 7 sections; Wet Leg "mangetout" k 5, share 0.42, margin 0.75 dB, 25 sections of which 17 are 2 or 3 bars. All four carry `labels_low_confidence: true`.

---

## 1. Failure modes

Each failure mode is stated, tied to what the project's runs show, and then to what the literature says about why it happens.

### 1.1 Boundaries inside a shared chord progression are invisible to chroma recurrence

Project evidence (verified, `2026-10-03-spike-grid-round3.md` and the run chord-per-bar listings): Pour Some Sugar On Me's hand-list boundaries intro / riff / verse / verse_b all sit on the same C# riff and none is found, capping recall at about 5 of 11; Summer of '69's solo and breakdown share the verse progression and are not split; Chelsea Dagger's first "chorus" starts at bar 9 on a G/D vamp eleven bars before the vocals enter, because the instrumental intro and the sung chorus share one two-chord loop. In every one of these the harmony is identical and only the arrangement changes.

Why (verified in the literature): the Laplacian method builds its repetition graph from chroma (McFee and Ellis 2014; the librosa example uses CQT chroma for recurrence and MFCC only for the local path), so two passages with the same chords are the same point in the embedding regardless of who is playing. Wang, Hung and Smith 2022 note that "some songs have the same chord progression for both the verse and chorus, with only the instrumentation and lyrics indicating a section change", and SALAMI "contains many instances of conflicting labels, including dozens of cases where one listener's 'chorus' was another's 'verse'" (arXiv 2205.14700, Section 2). Salamon, Nieto and Bryan 2021 replace MFCC and augment CQT with deep embeddings precisely because the handcrafted features miss timbre and arrangement cues; their qualitative example is a drum entrance that the baseline misses and the embedding catches (ISMIR 2021 paper, Section 6.4). Smith, Chuan and Chew 2014 found that "nearly all boundaries correspond to peaks in novelty functions" over several features, not only harmony (IEEE TMM 2014).

Inferred: in this pipeline the fix does not need deep embeddings, because the separate stage already produces a vocals stem and a drums stem before grid runs (`GridStage.requires` includes `separate/stems/drums.wav`). Per-bar vocal energy and drum energy are arrangement features that would separate the Chelsea intro from the chorus and the PSSOM solo from the verses.

### 1.2 Over-segmentation into two-bar fragments when texture alternates

Project evidence (verified): Wet Leg gives 25 sections, 17 of them 2 or 3 bars, alternating `verse` / `chorus` (F F versus C C) and `verse` / `verse 2` (Dm F versus C C). The fragments follow real texture changes (call and response, stop-start) at a two-bar period, which the k-means on eigenvectors reproduces faithfully.

Why: spectral clustering has no segment-length prior. Shibata, Nakamura and Yoshii (ISMIR 2019) state the regularity fact directly: in RWC Pop "most sections have a length of 40 beats or less" and they set the expected section length to "32 beats (8 measures)"; the Japanese journal version adds that in popular music most section lengths are 4 or 8 bars. Sargent, Bimbot and Vincent 2011 report that "more than 80% of the songs have a main structural pulsation of 32 beats" in RWC Pop. Marmoret et al. (TISMIR 2023) build a penalty where "most segments are of size 8, and the remaining segments are generally of size 4, 12 or 16", zero cost at 8 bars, a quarter penalty for multiples of 4, half for even sizes and full for odd lengths. McFee (ISMIR 2025) shows "most existing datasets exhibit regularity" in simple duration ratios. Salamon et al. 2021 set a minimum section duration of "8 seconds (= 4 bars at 120 bpm) as a reasonable lower bound" for their fusion step, and the QM Vamp segmenter defaults to a 4 s minimum segment.

Version 1.2's four-bar minimum addresses the symptom. What remains (inferred): the current merge rule always folds a short segment into the following segment and gives it the following cluster's id, which on an A B A B two-bar alternation produces whichever label happens to come last rather than a musically chosen one; and a four-bar minimum does not prevent 5- and 6-bar fragments from an 8-bar phrase being cut at the wrong place.

### 1.3 Under-segmentation: one cluster swallows the song

Project evidence (verified, spike round 3): with k 3, Riptide's body is one 107 s cluster of 66 of 83 bars; I'm Yours is one 181 s block; Over the Rainbow's 73 s A block hides three loudness-cued sections. Silhouette on the embedding picks k 3 on every song. The iterative split (k up while a cluster exceeds 60%) fixed Riptide and I'm Yours but not Rainbow.

Why: choosing k is unsolved for spectral-clustering segmentation. MSAF's `scluster` config simply fixes `scluster_k = 4` for the flat case and otherwise computes 10 hierarchical layers (`msaf/algorithms/scluster/config.py`). Salamon et al. 2021 sidestep it: "the preferred segmentation level will be preset by the application designer or set by the end user", and they evaluate by choosing the level per track. The TISMIR 2020 survey lists hierarchy and ambiguity as open problems and says segment lengths "tend to be log-normally distributed".

### 1.4 Labels: the loudest recurring cluster is not reliably the chorus, and once-only clusters are not reliably bridges

Project evidence (verified): the chorus was right on 6 of 6 verifiable choruses, yet the 1.5 dB margin flag fired on all four songs (0.70, 1.43, 0.93, 0.75 dB), so the flag carries no information. Summer of '69's F Bb C bridge clustered with the guitar-only intro and became "verse 2"; its pre-chorus sits inside the chorus cluster. Pour Some Sugar On Me's pre-chorus is absorbed and its solo and breakdown print as a "verse". Wet Leg's opening is "verse 3". Chelsea's chorus begins eleven bars before any singing.

Why: Wang, Smith et al. 2021 (chorus detection) describe the unsupervised tradition as "finding the loudest, most frequently repeated, and/or the most homogenous section" and measure it: pychorus (Goto-style repetition) reaches F 0.39 and MSAF segmenters with a "max duration" chorus rule 0.27 to 0.53, against 0.64 for a supervised CNN (arXiv 2103.14253). Van Balen et al. 2013, on 6462 Billboard sections, found that in a regression on chorusness the loudness coefficient is 0.03 with a 95% interval of -0.01 to 0.06 (not distinguishable from zero on its own), while sharpness (0.11), MFCC variance (0.12), roughness (0.12) and pitch centroid (0.10) are positive and loudness inter-quartile range is strongly negative (-0.33): "sections with high Chorusness are louder, sharper and rougher than other sections ... a smaller dynamic range and greater variety in MFCC timbre" (ISMIR 2013, Table 1 and Section 3.2). Pre-chorus is a known casualty: the 7-class taxonomy of Wang et al. 2022 maps "'pre-chorus' ... to 'verse' to disentangle the build from the true chorus", and SongFormer 2025 explicitly reverses this and retains pre-chorus "to better capture transitional passages". Wang et al. 2021 recategorise Harmonix's "post-chorus" as chorus and "pre-chorus" as non-chorus. On label agreement, Wang et al. 2022 report that if two SALAMI annotators agree on a section start they agree on the function "at least twice as often as they disagree".

Inferred: the project's rule set names clusters by recurrence count and position, not by content. A once-only cluster in the middle is a bridge by definition of the rule, whether it is a bridge, a solo, a breakdown or an instrumental; and a recurring cluster that is not the chorus is a "verse N" whether it is a pre-chorus, an instrumental riff, or (as in Summer of '69) a bridge that happened to share a cluster with the intro.

### 1.5 Boundaries land one to three bars off

Project evidence (verified): Summer of '69, 6 of 12 boundaries within 1 bar and 7 within 2; Pour Some Sugar On Me's chorus 2 is 2 bars late and its outro 3 bars late; Summer of '69's first verse row printed D A A D because the boundary is one bar into a two-bar harmonic rhythm (version 1.2 phrase alignment addresses this last case at the score stage).

Why (verified): the Harmonix set shows that "the vast majority of segments (81.1%) start in a downbeat" and 10% start on beat 4 (one-beat count-ins). Marmoret et al. 2023 post-processed Foote, McFee-Ellis and Serrà boundaries by moving each to the closest estimated downbeat and found "a strong increase in performance for F0.5s" (Foote on SALAMI-test 29.21% to 33.33%). The project already works at bar level, so it has that gain; what it lacks is any snap to novelty or to the phrase grid. Inferred: the eigenvector median filter is size 9 in this code, applied to a bar-rate sequence (nine bars, about two phrases), whereas the librosa example applies the same size-9 filter to beat-synchronous frames (nine beats, about two bars). Likewise the time-lag filter size 7 and recurrence width 3 are in bars here and in beats in the example. A nine-bar median on eigenvectors will drag a boundary toward the centre of the filter window and can shift it by several bars; this is a hypothesis to measure, not a verified defect.

### 1.6 Non-song audio becomes a section

Project evidence (verified): the Pour Some Sugar On Me music video adds 25.2 s of pre-roll which prints as an "intro" with chords; Wet Leg's last four bars hold only the "other" stem (non-song audio) and print as "outro"/N.C. Both taxonomies in the literature carry a class for this: Wang et al. 2022 have an auxiliary `silence` class, and allin1's label set includes `start` and `end` (README). Inferred: a "not music" class, decided from stem energy, belongs in the labeller.

### 1.7 Confidence is not informative

Project evidence (verified): every section on every song has confidence 0.3 because the margin rule fired everywhere. Spotify's audio-analysis API, the most widely used practitioner precedent, gives each section a 0 to 1 `confidence` and describes sections as "defined by large variations in rhythm or timbre" (developer docs). Nieto et al. 2014 found "humans tend to give more relevance to the precision component of the F-measure rather than the recall component" and propose F with alpha 0.58, which argues for reporting fewer, surer boundaries rather than many uncertain ones.

---

## 2. What others do

### 2.1 Unsupervised, CPU-cheap methods (same family as the project)

McFee and Ellis 2014, Laplacian segmentation. Verified parameters from the librosa gallery example: CQT with 36 bins per octave over 7 octaves, beat-synchronous median aggregation, `stack_memory` on chroma, `recurrence_matrix(width=3, mode='affinity', sym=True)` where width 3 "prevents links within the same bar", a time-lag median filter of size (1, 7), MFCC path similarity with sigma the median successive distance, the balanced `mu`, eigenvector median filter size (9, 1), k-means with k = 5 and the remark "see how the segmentation changes as you vary k" with no rule for k. Code: github.com/bmcfee/laplacian_segmentation (and in librosa, ISC licence). The project's `_embedding` is this recipe.

MSAF (Nieto and Bello, ISMIR 2016; MIT licence). Verified: seven boundary algorithms (checkerboard kernel, constrained clustering, convex NMF, Laplacian/spectral clustering, ordinal LDA, SI-PLCA, structural features) and five labelling algorithms (2D Fourier magnitude coefficients, constrained clustering, convex NMF, spectral clustering, SI-PLCA); features are PCP, MFCC, Tonnetz, CQT, beat-synchronous by default. Findings: algorithm rankings change with the metric; "having a stronger weight on Precision than Recall tends to better align with perception"; annotator identity has a significant effect on HR3 (two-way ANOVA F(4,1705) = 4.05, p < 0.01), so "the idea of a single 'ground-truth' for boundary detection can potentially be misleading". The `scluster` config: `scluster_k: 4`, `evec_smooth: 9`, `rec_smooth: 9`, `rec_width: 9`, `num_layers: 10`.

Salamon, Nieto and Bryan 2021, section fusion (verified from the paper text). A short section (under a minimum duration, 8 s in their experiments) is fused as follows: first or last section merges with its only neighbour; if both neighbours share an id, all three merge; otherwise look one level down the multi-level hierarchy (the k-1 clustering, which reuses the same eigenvectors) and find the section that overlaps the short one most; if its id matches the previous or next section at the current level, merge that way; if not, go down another level, and so on; if no level decides, keep whichever boundary (start or end) overlaps with the most boundaries at lower levels. Results on Harmonix, flat: LSD HR0.5 40.69 / HR3 56.50 / PFC 61.21 against DEF (deep embeddings plus fusion) 45.74 / 68.84 / 70.11; the ablation shows fusion alone improves precision. They note fusion helps less on SALAMI's fine level because many of those sections are under 8 s.

Shibata, Nakamura, Yoshii 2019 / 2020, hierarchical HSMM. Verified: a semi-Markov section chain with an explicit duration prior centred on 32 beats, timbre (MFCC) homogeneity within a section, and a section-conditioned left-to-right chord chain for repetitiveness. On 85 RWC Pop songs in 4/4: F0.5 33.0% and pairwise F 54.3% against MSAF defaults SCluster 23.4% / 45.5%, CNMF 17.4% / 41.7%, VMO 8.72% / 28.5%. "Joint modelling of homogeneity and regularity improved the performance."

Sargent, Bimbot, Vincent 2011 / 2017, regularity-constrained Viterbi. Verified: segmentation cost = content cost + lambda times a regularity cost that grows as the segment length departs from the structural pulsation period tau (32 beats on RWC Pop), with a non-convex cost (alpha 0.5) preferring a few irregular segments over many slightly irregular ones. System 1 (acoustic change detection) on RWC Pop at 3 s tolerance: F 28.2% without regularity, 61.4% with (precision 16.8% to 61.2%). At 0.5 s: 17.0% to 23.8%.

Marmoret et al. 2023, barwise Correlation Block-Matching (TISMIR 6(1); open source; licence of the code not verified). Verified: bar-scale time-frequency matrices; a modulo-8 segment-size penalty; RWC Pop F0.5 64.44% and F3 80.64% against Foote 43.30% / 65.04% and the supervised Grill and Schlüter CNN about 56% / 80%; SALAMI-test 42.00% / 60.61%. The downbeat-realignment experiment is in the same paper.

Goto 2003/2006 RefraiD and pychorus (MIT). Verified: chroma time-lag similarity, repeated-section grouping, modulation-aware; 80 of 100 songs correct in Goto's test. pychorus README admits it needs metronomic timing and returns one clip. Wang et al. 2021 measured pychorus at F 0.39.

Paulus and Klapuri 2009/2010. Verified (via Van Balen 2013 and Wang 2022 citations): label sequences such as "intro, verse, chorus, verse, chorus" are scored with Markov and variable-order Markov models over label transitions; adding section loudness and loudness deviation raised per-section accuracy by up to 4 points on TUTstructure07.

QM Vamp Segmenter (Levy and Sandler; used in Sonic Visualiser). Verified from the plugin docs: a 40-state HMM on PCA-reduced constant-Q/chroma/MFCC features, then histogram clustering of timbre-type distributions; parameters: maximum segment types (default 10), feature type, minimum segment duration (default 4 s, range 1 to 15 s); "the constrained clustering used in this plugin does not produce too many clusters ... even if this is set too high".

### 2.2 Supervised models (state of the art)

Ullrich, Schlüter, Grill 2014 (ISMIR). Verified: a CNN on mel spectrograms trained for "boundaryness" raised SALAMI F0.5 from 0.33 to 0.46 and F3 from 0.52 to 0.62; decoding is peak picking with a moving threshold. Grill and Schlüter 2015 added self-similarity lag matrices and two-level annotations.

Wang, Hung, Smith 2022 (ICASSP; arXiv 2205.14700). Verified: 7-class taxonomy intro, verse, chorus, bridge, inst, outro, silence; a substring map that sends pre-chorus and build to verse, refrain and theme to chorus; SpecTNT with a CTL loss. Harmonix results: Scluster HR.5F .263, PWF .586; DSF+Scluster .497 / .689; SpecTNT (24 s) HR.5F .565, ACC .690, PWF .687, CHR.5F .491. MuSFA (arXiv 2211.15787) adds the Hooktheory lead-sheet excerpts as partial labels, improving boundaries by about 3% and labels by about 1%.

Kim and Nam 2023, All-In-One (`allin1`, MIT, github.com/mir-aidj/all-in-one). Verified from the README: predicts tempo, beats, downbeats, segment boundaries and labels from the set `start, end, intro, outro, break, bridge, inst, solo, verse, chorus`; input is Demucs-separated stems; models trained on Harmonix with 8-fold cross-validation; dependencies are PyTorch, NATTEN ("Windows: build from source"), madmom from git, optionally FFmpeg; "With an RTX 4090 GPU ... processed 10 songs (33 minutes) in 73 seconds"; CPU is supported but no CPU timing is given. SongFormer's benchmark table (arXiv 2510.02797v2) puts All-In-One at ACC 0.740, HR.5F 0.596, HR3F 0.730 on 200 expert-verified Harmonix songs. A practitioner blog (musictechlab.io) reports allin1 "unavailable due to dependency conflicts (natten API changes ...)" in their setup and falls back to MSAF and a librosa pipeline.

Buisson, McFee, Essid 2024, LinkSeg (ISMIR 2024; model CC-BY 4.0). Verified: pairwise link prediction plus a graph attention network outputs boundaries and labels; an ONNX port for onnxruntime-web exists on Hugging Face (`elicwhite/linkseg-7c-onnx`), which means a CPU runtime without NATTEN is possible; SongFormer's table lists LinkSeg-7Labels at ACC 0.780, HR.5F 0.630, HR3F 0.762. Its feature front end and CPU cost are not verified.

SongFormer 2025 (arXiv 2510.02797; code at github.com/ASLP-lab/SongFormer). Verified: seven labels including pre-chorus; a 4-layer Transformer over MuQ and MusicFM self-supervised features at about 8.33 Hz; ACC 0.807, HR.5F 0.696, HR3F 0.780 on SongFormBench Harmonix; inference reported on an NVIDIA L40 GPU. Labels are the argmax of frame probabilities averaged within boundaries; boundaries come from local-maxima filtering and peak picking. Heavy for a CPU tool.

### 2.3 Apps and transcribers

Moises "Sections" (verified from Moises' newsroom and help pages): "automatically detects and isolates different song sections, such as Intros, Verses, Choruses, and Bridges", with "precision in synchronizing detected sections with the song's downbeat" so loops start on the right beat. No method details are published.

Spotify Audio Analysis (verified from API docs): sections are "defined by large variations in rhythm or timbre, such as chorus, verse, bridge, or guitar solo", each with start, duration, confidence, loudness, tempo, key, mode and time signature and their own confidences. No functional labels, only typed sections with confidence.

Chordify: Song Lessons are "cut into different sections (verse, chorus, bridge, etc.)" (support article). I could not verify whether Chordify derives those sections automatically or by hand, so I do not rely on it.

Practitioner pipeline (musictechlab.io, 2025): extract chroma, MFCC and spectral contrast, agglomerative clustering for boundaries, "snaps boundaries to nearest beats", "labels sections using position heuristics and K-means clustering", numbered labels like VRS1, VRS2; their own caveat: "section types (verse vs. chorus) are heuristic-based, boundaries are more reliable than labels".

Chart conventions. Ultimate Guitar tabs (the Chordonomicon corpus of 404k annotated tracks) use eight part names: "Intro, Verse, Chorus, Bridge, Interlude, Solo, Instrumental, and Outro", with "Refrain" normalised to Chorus (arXiv 2410.22046). The Hit Songs Deconstructed glossary defines an instrumental break as "typically longer than four bars", a turnaround as "four bars or shorter", a pre-chorus as a section that "functions to set-up the ensuing chorus", and a bridge as a "pronounced vocal, musical, and/or energy level departure" that typically occurs once.

---

## 3. Research summary: what is state of the art and what is good enough

Numbers (verified). Unsupervised spectral clustering on Harmonix: HR0.5 about 0.26 to 0.41 depending on implementation, HR3 about 0.56 (Wang 2022 Table; Salamon 2021 Table 3). Adding section fusion and deep embeddings: HR0.5 0.46, HR3 0.69, PFC 0.70 (Salamon 2021). Supervised 2022: HR.5F 0.565, label accuracy 0.69 (SpecTNT). 2023 to 2025: All-In-One HR.5F 0.596 / ACC 0.740; LinkSeg 0.630 / 0.780; SongFormer 0.696 / 0.807 (SongFormer table). MIREX-era state of the art on SALAMI was about 56% F at 0.5 s and 69% at 3 s with human agreement "estimated around 90%" (TISMIR 2020 survey); on SALAMI, if one annotator marks a boundary there is a 66% chance the other did within 0.5 s, 78% for chorus starts (Wang 2021).

What this means for a chord sheet (inferred): the relevant tolerance for a printed sheet is one bar, which at 85 to 160 bpm is 1.5 to 2.8 s, between the 0.5 s and 3 s windows. A good unsupervised bar-level system with a length prior should reach the 3 s regime, roughly 0.6 to 0.7 hit rate, which is where the project already sits on Summer of '69 (7 of 12 within 2 bars) and well above where it sits on Pour Some Sugar On Me (4 of 11). The remaining boundary errors are of two kinds: ones no chroma method can find (shared progression), and ones a length prior or novelty snap would fix (off by 1 to 3 bars, two-bar fragments). Labelling is the weaker half everywhere: even supervised systems reach 0.7 to 0.8 frame accuracy, and the heuristics the project uses were measured at F 0.3 to 0.5 for chorus detection.

Consensus points across the sources: process at bar level and snap to downbeats (Harmonix 81.1%; Marmoret); impose a duration prior around 8 bars with 4-bar multiples favoured (Shibata, Sargent, Marmoret, Salamon's 8 s, McFee 2025); fuse short sections using lower-level clusterings rather than a fixed direction (Salamon); value precision over recall (Nieto 2014; MSAF); label with arrangement and timbre cues, not loudness alone (Van Balen; Wang 2021); keep a separate class for silence or non-music (Wang 2022; allin1); expect pre-chorus to be hard and decide explicitly whether to merge it (Wang 2021/2022; SongFormer); offer more than one granularity because listeners disagree (TISMIR 2020; Salamon 2021; MSAF's SPAM results).

Evaluation tooling (verified in the project venv): `mir_eval` 0.8.2 is installed with `segment.detection(reference_intervals, estimated_intervals, window=0.5, beta=1.0, trim=False)`, `deviation`, `pairwise`, `nce`, `vmeasure`, `rand_index`. `librosa` 1.0.0 provides `segment.agglomerative(data, k)`, `recurrence_matrix`, `path_enhance`, `timelag_filter`, `lag_to_recurrence`, `subsegment`.

---

## 4. Easy wins

Ordered by expected effect on the printed sheet relative to the change required. Each names the code it touches, the rule, and the evidence. These are designs for the code-application agents to test against the four run folders (grid can be re-run with `--from grid` without re-separating).

### 4.1 Vocal-aware labelling: chorus needs voice, intro and solo lack it

Where: `label_sections` in `sections.py`; `bar_features` or a new helper to compute per-bar RMS of `separate/stems/vocals.wav` (grid already requires the drums stem, so adding the vocals stem to `GridStage.requires` follows the existing pattern).

Rule: compute `vocal_db[bar]` and a song threshold (for example 12 dB below the median vocal bar level, or a fraction of mix RMS as the lessons document already measures). Then: (a) the chorus candidate set is restricted to recurring clusters whose bars are mostly vocal; (b) a leading run of non-vocal bars is `intro` regardless of cluster; (c) a non-vocal segment in the middle of the song is `instrumental` or `solo` (solo if the guitar/other stem is above the song median), never `bridge` or `verse`; (d) a trailing non-vocal run is `outro`.

Evidence: Chelsea's vocals are silent for bars 0 to 19 and 93 to 108 (lessons document), which would move the first chorus start from bar 9 to bar 20 and relabel the 16-bar break as instrumental; Pour Some Sugar On Me's bars 67 to 83 (solo and breakdown) would stop being a "verse". Literature: allin1 uses demixed stems as input and carries `inst` and `solo` labels; Wang et al. 2022 include `inst`; Van Balen shows timbre variety predicts chorusness better than loudness. Inferred: this is the single change most specific to this pipeline's advantage (stems already exist).

### 4.2 Replace the loudness-only chorus score with a chorusness score and recalibrate confidence

Where: `label_sections`; `LOW_MARGIN_DB`.

Rule: per cluster, compute bar-weighted means of: loudness dB (already there), spectral centroid or MFCC brightness proxy, MFCC variance across the cluster's bars, vocal energy (4.1), and negative loudness IQR. Standardise each across clusters (z-scores) and sum; chorus is the recurring vocal cluster with the highest score. Confidence becomes the z-margin between the best and second-best candidate mapped to 0 to 1, replacing the 1.5 dB rule which fired on 4 of 4 songs while being right on 6 of 6.

Evidence: Van Balen 2013 coefficients (sharpness 0.11, MFCC variance 0.12, roughness 0.12, pitch centroid 0.10, loudness 0.03 not significant, loudness IQR -0.33); Wang 2021 showing loudest/most-repeated heuristics at F 0.27 to 0.53. The project's own data shows loudness alone separates chorus from verse by under 1.5 dB on every song, so any single-feature margin will be thin.

### 4.3 Section fusion by neighbour choice instead of always merging forward

Where: `boundaries_from_clusters` (version 1.2 sets `min_bars = 4` here) and `segment_bars`, which already runs k-means for k = 3, 4, ... in its split loop and discards the lower-k labelings.

Rule (Salamon 2021): keep every labelling from k = 3 up to the chosen k. For a short segment: if first or last, merge with its only neighbour; if both neighbours share a cluster id, merge all three; otherwise take the k-1 labelling, find the segment overlapping the short one most, and merge toward whichever neighbour shares that id; recurse to k-2 if needed; if nothing decides, keep the boundary that coincides with more boundaries at lower k. A cheaper variant that needs no hierarchy: merge toward the neighbour whose mean bar-feature vector is nearer in cosine distance.

Evidence: Wet Leg's A B A B two-bar alternation; Salamon's ablation shows fusion raises precision and removes "spurious short sections"; the version 1.2 rule's choice of the following segment is arbitrary for alternations.

### 4.4 Phrase-regular boundary snapping

Where: a new post-pass after `boundaries_from_clusters`, before labelling (or in the score stage beside version 1.2's phrase alignment, which only shifts by one bar for harmonic-rhythm parity).

Rule: compute a bar-level novelty curve (Foote checkerboard kernel of 8 bars on the bar self-similarity matrix built from the same chroma+MFCC features, which librosa makes easy with `recurrence_matrix`; or simply the cosine distance between the mean features of the 4 bars before and after each bar). For each boundary, consider shifts of -2 to +2 bars; score each candidate by novelty at that bar plus a regularity bonus when both adjacent segment lengths become multiples of 4 (Marmoret's modulo-8 penalty: 0 for 8, 1/4 for other multiples of 4, 1/2 for even, 1 for odd); move the boundary if the best candidate beats the current one by a margin. Never move a boundary past another or below the minimum length.

Evidence: PSSOM chorus 2 late by 2 bars and outro by 3; Summer of '69 7 of 12 within 2 bars but only 6 within 1; Shibata and Sargent's 32-beat prior; Smith and Chew: boundaries sit at novelty peaks; Nieto 2014: precision matters more, so moving rather than adding boundaries is the safe direction.

### 4.5 Pre-chorus and bridge by position and chord novelty (builds on validation item 8)

Where: `label_sections`, after the chorus is fixed.

Rules: (a) a recurring non-chorus cluster whose segments are immediately followed by a chorus in at least two of three occurrences, and whose segments are shorter than the chorus, is `pre-chorus`; (b) the validation document's pending rule (a segment whose chord set is mostly absent elsewhere is a `bridge`) should be made conditional on vocals being present and the segment not being first or last; a once-only cluster without novel chords and without vocals is `instrumental`, not `bridge`; (c) remaining recurring clusters are named `verse` in order of first appearance with occurrence numbers assigned at render time (`Verse 1`, `Verse 2`), which is what every chart convention does (Chordonomicon's eight names; the practitioner VRS1/VRS2 habit), instead of the current `verse 2` meaning "second cluster".

Evidence: Summer of '69's pre-chorus-plus-chorus blocks and its F Bb C bridge; PSSOM's 2-bar pre-chorus; Hit Songs Deconstructed definitions of pre-chorus and bridge; Wang 2021/2022 and SongFormer on pre-chorus handling. Inferred: a 2-bar pre-chorus cannot survive the four-bar minimum, so (a) will only name pre-choruses of 4 bars or more, which is the accepted cost in version 1.2.

### 4.6 A "not music" class for pre-roll and trailing audio

Where: `label_sections` with stem energies.

Rule: a leading or trailing run of bars where the drums, bass, guitar, piano and vocals stems are all below a floor (the lessons measured the Wet Leg tail as "only the other stem" and the PSSOM pre-roll as video audio) is labelled `pre-roll` / `tail` and the score stage omits it or prints one line. Literature precedent: `silence` (Wang 2022), `start`/`end` (allin1).

### 4.7 Measure smoothing scales at bar resolution

Where: `_embedding`: `median_filter(evecs, size=(9, 1))`, `timelag_filter(... size=(1, 7))`, `RECURRENCE_WIDTH = 3`.

Hypothesis (inferred, to measure): these sizes come from a beat-rate example and are now applied to bar-rate sequences, four times coarser. Try eigenvector filter 3 (about one phrase) and time-lag filter 3 at bar rate, or compute the embedding at beat rate (as the example does) and assign each bar the majority label of its beats. Score with `mir_eval.segment.detection` at a window of one median bar against the two hand lists and against the version 1.2 outputs; keep whichever gives higher precision at one bar.

### 4.8 A bar-tolerance regression harness

Where: tests, using `mir_eval` (already a dependency) and the two owner hand lists plus the three recurrence/novelty references assembled in spike round 3.

Rule: `detection(ref, est, window=median_bar_seconds, beta=0.58, trim=True)` per song, and `pairwise`/`nce` for labels where a label reference exists (Hooktheory's Verse / Pre-Chorus / Chorus / Bridge for Summer of '69 and PSSOM). Any labelling or boundary change must not lower precision at one bar on any song. Evidence: Nieto 2014's F0.58; MSAF's finding that rankings depend on the metric, so fix the metric first.

---

## 5. Deeper options

### 5.1 A duration-aware dynamic programme over bars (Shibata / Sargent, pure numpy)

Replace k-means plus post-hoc merging with a bar-level Viterbi over segmentations: cost = sum over segments of (within-segment feature inhomogeneity, from the existing chroma+MFCC+stem features) + lambda times a regularity cost on segment length (zero at 8 bars, small at 4, 12, 16, large at odd lengths) + a change-point reward from the novelty curve. Labels then come from clustering segment means (k-means on segment-level vectors, far fewer points), with the existing k rule. Evidence: Sargent's F3 28% to 61% from the regularity term alone; Shibata's F0.5 33.0% against SCluster 23.4%; Marmoret's modulo-8 penalty. CPU cost is trivial at 100 to 150 bars. Risk: songs whose true structure is 2-bar or 6-bar phrased (Wet Leg's middle passage is a real two-bar alternation) will be forced to 4 and 8; the user override `--sections-k` would need a sibling `--phrase-bars`.

### 5.2 Multi-level sections in `grid.json`

Store the labelling for every k from 3 to 6 (already computed in the split loop) as `levels`, and let the score or render stage, or the user, pick a level per song, with the chosen level as today's `sections`. This is Salamon's and MSAF's answer to the k problem and it makes the hand-edit workflow (sections "live in an editable file", design spec) much faster: the user picks a level rather than retyping boundaries. It also enables 4.3's fusion.

### 5.3 Deep embeddings as extra features (Salamon 2021 pattern)

Augment the bar features with an embedding that captures arrangement: per-bar mean activations from a pretrained audio tagger. Salamon used Few-Shot-Learning and DeepSim embeddings (not public as far as I could verify) and suggested OpenL3 and VGGish as alternatives; both run on CPU. Gain on Harmonix in their ablation: a large rise in label recall and HR3 from 56.5 to 68.8 with fusion. For this project the stems (4.1) already provide the most important arrangement cue, so this is a second step if 4.1 is insufficient on blind songs.

### 5.4 An optional supervised backend: `allin1` or LinkSeg

`allin1` (MIT) predicts boundaries and 10 labels including `inst`, `solo`, `break` from Demucs stems and is trained on Harmonix (EDM and pop heavy). Measured elsewhere at HR.5F 0.596 and label accuracy 0.74. Blockers verified from its README: NATTEN must be built from source on Windows; madmom is installed from git; it runs its own Demucs. CPU inference time is not published. A spike would install it in a separate venv, run the four songs, and compare its boundaries and labels against the hand lists and against the grid stage; if it wins, it becomes a `--sections-backend allin1` that writes the same `sections` schema. LinkSeg (CC-BY 4.0) has an ONNX export that would avoid NATTEN, but its input features and CPU cost are unverified. SongFormer is the current best but is built for GPU and self-supervised front ends (MuQ, MusicFM) and is not a fit for a CPU CLI.

### 5.5 Barwise CBM (Marmoret et al.)

The authors' open-source barwise block-matching segmenter reaches F0.5 64% on RWC Pop with only bar positions as side information, which this project has. It would replace the boundary half of the stage while keeping the labelling. Licence and Python packaging are not verified; a spike would check both.

### 5.6 Label transition modelling (Paulus and Klapuri)

Score candidate label assignments of the cluster sequence against a small Markov model of pop form (intro before first verse; chorus follows verse or pre-chorus; bridge after the second chorus; outro last), combined with the chorusness scores from 4.2. This would resolve cases like Wet Leg's opening being "verse 3" and would stop a "bridge" being assigned to a once-only cluster at bar 99 of 142 if it is instrumental. The Markov tables can be hand-written from the Harmonix label frequencies (chorus and verse dominate; pre-chorus, post-chorus, inst, solo, break, transition appear in that order of frequency) rather than trained.

---

## 6. Sources

Project (read-only):
- `C:\Users\gethi\sources\Youkelele\src\youkelele\music\sections.py`, `src\youkelele\stages\grid.py`
- `docs\superpowers\specs\2026-10-03-real-run-lessons.md`, `2026-10-03-v1-1-validation.md`, `2026-10-03-spike-grid-round3.md`, `2026-10-03-ukulele-tab-chain-design.md`, `2026-10-03-ukulele-tab-chain-v1-2-design.md`
- `runs\{9f06qzcvuhg,sexhetcxqy4,0uib9y4ofps,lbc6ccztp5e}\02_grid\grid.json` and `03_harmony\chords.json`

Papers and docs (verified by reading):
- McFee, Ellis, "Analyzing Song Structure with Spectral Clustering", ISMIR 2014. https://archives.ismir.net/ismir2014/paper/000319.pdf ; code https://github.com/bmcfee/laplacian_segmentation ; librosa example https://librosa.org/librosa_gallery/auto_examples/plot_segmentation.html
- Nieto, Bello, "Systematic Exploration of Computational Music Structure Research", ISMIR 2016. https://archives.ismir.net/ismir2016/paper/000043.pdf ; MSAF https://github.com/urinieto/msaf (MIT); scluster config https://raw.githubusercontent.com/urinieto/msaf/master/msaf/algorithms/scluster/config.py
- Nieto, Mysore, Wang, Smith, Schlüter, Grill, McFee, "Audio-Based Music Structure Analysis: Current Trends, Open Challenges, and Applications", TISMIR 2020. https://transactions.ismir.net/articles/10.5334/tismir.54
- Nieto, Farbood, Jehan, Bello, "Perceptual Analysis of the F-Measure to Evaluate Section Boundaries in Music", ISMIR 2014. https://archives.ismir.net/ismir2014/paper/000124.pdf
- Salamon, Nieto, Bryan, "Deep Embeddings and Section Fusion Improve Music Segmentation", ISMIR 2021. https://archives.ismir.net/ismir2021/paper/000074.pdf
- Shibata, Nishikimi, Nakamura, Yoshii, "Statistical Music Structure Analysis Based on a Homogeneity-, Repetitiveness-, and Regularity-Aware Hierarchical Hidden Semi-Markov Model", ISMIR 2019. https://archives.ismir.net/ismir2019/paper/000031.pdf ; journal version IPSJ 2020 https://ipsj.ixsq.nii.ac.jp/record/204319/files/IPSJ-JNL6104002.pdf
- Sargent, Bimbot, Vincent, "A Regularity-Constrained Viterbi Algorithm and Its Application to the Structural Segmentation of Songs", ISMIR 2011. https://archives.ismir.net/ismir2011/paper/000105.pdf ; extended: IEEE/ACM TASLP 25(2), 2017.
- Marmoret, Cohen, Bimbot, "Barwise Music Structure Analysis with the Correlation Block-Matching Segmentation Algorithm", TISMIR 6(1) 2023. https://arxiv.org/abs/2311.18604
- Nieto, McCallum, Davies, Robertson, Stark, Egozy, "The Harmonix Set", ISMIR 2019. https://archives.ismir.net/ismir2019/paper/000068.pdf ; data https://github.com/urinieto/harmonixset
- Ullrich, Schlüter, Grill, "Boundary Detection in Music Structure Analysis using Convolutional Neural Networks", ISMIR 2014. https://archives.ismir.net/ismir2014/paper/000271.pdf ; Grill, Schlüter, ISMIR 2015 https://www.ismir2015.uma.es/articles/134_Paper.pdf
- Wang, Smith, Chen, Song, Wang, "Supervised Chorus Detection for Popular Music Using Convolutional Neural Network and Multi-task Learning", ICASSP 2021. https://arxiv.org/abs/2103.14253
- Wang, Hung, Smith, "To Catch a Chorus, Verse, Intro, or Anything Else: Analyzing a Song with Structural Functions", ICASSP 2022. https://arxiv.org/pdf/2205.14700
- Wang, Hung, Smith, "MuSFA: Improving Music Structural Function Analysis with Partially Labeled Data", 2022. https://arxiv.org/abs/2211.15787
- Kim, Nam, "All-In-One Metrical and Functional Structure Analysis with Neighborhood Attentions on Demixed Audio", WASPAA 2023. https://arxiv.org/abs/2307.16425 ; code https://github.com/mir-aidj/all-in-one (MIT)
- Buisson, McFee, Essid, "Using Pairwise Link Prediction and Graph Attention Networks for Music Structure Analysis", ISMIR 2024. https://ismir2024program.ismir.net/poster_405.html ; ONNX port https://huggingface.co/elicwhite/linkseg-7c-onnx
- SongFormer, "Scaling Music Structure Analysis with Heterogeneous Supervision", 2025. https://arxiv.org/html/2510.02797v2 ; code https://github.com/ASLP-lab/SongFormer
- McFee, "Quantifying Regularity in Music Structure Analysis", ISMIR 2025. https://ismir2025program.ismir.net/poster_50.html
- Van Balen, Burgoyne, Wiering, Veltkamp, "An Analysis of Chorus Features in Popular Song", ISMIR 2013. https://webspace.science.uu.nl/~veltk101/publications/art/ismir2013-chorus.pdf
- Smith, Chuan, Chew, "Audio Properties of Perceived Boundaries in Music", IEEE TMM 2014. https://digitalcommons.unf.edu/unf_faculty_publications/2624
- Goto, "A Chorus-Section Detecting Method for Musical Audio Signals", ICASSP 2003. https://staff.aist.go.jp/m.goto/PAPER/ICASSP2003goto.pdf ; pychorus https://github.com/amrakm/pychorus (MIT)
- Paulus, Klapuri, "Labelling the Structural Parts of a Music Piece with Markov Models", CMMR 2008/2009 (Springer LNCS 5493); Paulus, "Improving Markov Model Based Music Piece Structure Labelling with Acoustic Information", ISMIR 2010.
- Serrà, Müller, Grosche, Arcos, "Unsupervised Music Structure Annotation by Time Series Structure Features and Segment Similarity", IEEE TMM 16(5) 2014.
- QM Vamp Plugins documentation, Segmenter. https://vamp-plugins.org/plugin-doc/qm-vamp-plugins.html
- Spotify Web API, Audio Analysis sections. https://developer.spotify.com/console/get-audio-analysis-track/
- Moises, "Simplify Your Music Practice with New Song Sections Feature". https://moises.ai/newsroom/product-announcements/new-song-sections-feature/ ; help https://help.moises.ai/hc/en-us/articles/10138829000988-How-do-I-use-Sections
- Chordify support, "What are Song Lessons?". https://support.chordify.net/hc/en-us/articles/33951891429917-What-are-Song-Lessons
- MusicTech Lab, "AI Song Structure Analysis: Intro, Verse, Chorus". https://www.musictechlab.io/blog/music-data/automatic-song-structure-analysis-how-ai-detects-intro-verse-chorus
- Chordonomicon dataset paper. https://arxiv.org/html/2410.22046v1
- Hit Songs Deconstructed glossary. https://reports.hitsongsdeconstructed.com/glossary/
- mir_eval (installed 0.8.2 in the project venv). https://mir-evaluation.github.io/mir_eval/
