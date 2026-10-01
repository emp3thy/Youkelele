# Scout: missing topics for the audio/MIDI/YouTube -> ukulele tab pipeline

Date: 2026-10-01. Method: ~30 web searches/fetches (Brave Search, arXiv API, GitHub issues API, Semantic Scholar, direct page reads). Scope: topics NOT covered by round 1 (chord recognition, note transcription, separation/ingest, tab theory/strumming, existing implementations, visualisers) and NOT assigned in round 2 (A rhythm quantisation/MIDI input, B lyrics, C song-ID/tuning offset/stereo tricks, D technique detection/arrangement/difficulty, E evaluation/HITL, F Windows engineering/licensing/LLM post-processing/legality).

Caveat on method: the session's WebSearch budget was exhausted before this task started, and Brave/DuckDuckGo/Semantic Scholar rate-limited or CAPTCHA-blocked part-way through. Every topic below is grounded in at least one fetched source; where a thread could not be sourced it is marked as a gap rather than guessed.

---

## Prioritised list of missing topics

### 1. Tempo-grid robustness: drift, tempo maps, and the half-time/double-time decision — HIGH

Why it matters: Everything downstream (chord-per-bar, strum pattern, bar numbering, section labels) hangs off the beat grid, and round 1 only chose a beat tracker (Beat This!/madmom) without asking how reliable the resulting grid is over a whole song. A practitioner building exactly this pipeline reports that beat trackers "land a percent or so off ... which drifts a bar away over a song", and that fitting the grid to transcribed note onsets gave ~0.01% BPM error versus ~2.5% for librosa. Tempo-octave errors (reporting 176 vs 88 BPM, or 8ths-as-quarters) are a well-known failure mode and directly change whether a strum pattern is written as D-DU-UDU or as a half-time feel; Chordify users' most common complaint is wrong BPM ("bpm is wrong 80% of the time"). Rubato intros, ritardando endings and live recordings need a tempo map rather than a constant BPM.

Key questions:
- Should the bar grid be fitted from beat-tracker output, from transcribed note onsets (least-squares/tempo-map fit), or a hybrid, and how is the residual (e.g. "grid_fit_ms") measured and surfaced?
- How to decide the metrical level (quarter = 88 vs 176) for strum-pattern notation: downbeat tracker, drum-stem kick/snare periodicity, or a genre prior? What does the published-tab convention for the two target songs imply?
- When to switch from constant tempo to a per-beat tempo map (threshold such as "notes fit within 0.08 of a 16th on average"), and how do tab/MusicXML/alphaTex renderers represent tempo changes?
- How should intros without drums, count-ins, fermatas and fade-out endings be handled so they do not corrupt the global tempo estimate?

Sources:
- https://github.com/swwallowws/coming-undone (practitioner pipeline README: grid fit from onsets, tempo maps, drift figures)
- https://lacuna.tiptreesystems.com/direction/resolving-octave-ambiguity-in-automatic-tempo-estimation/txn_c03e48e641364f4a98671709ccb40fcc (tempo octave ambiguity causes/solutions, cites Krebs/Böck, Davies/Böck)
- http://librosa.org/doc/0.11.0/auto_examples/plot_dynamic_beat.html (time-varying tempo beat tracking)
- https://www.reddit.com/r/edmproduction/comments/mabg9r/i_pay_for_chordifynet_i_suggest_nobody_do_that/ ; https://www.reddit.com/r/edmproduction/comments/1r6gq9/chordify_a_free_service_that_gives_you_the_chords/ (user reports of wrong tempo)
- https://music.stackexchange.com/questions/144011/how-to-transcribe-a-song-that-seems-to-drift

### 2. Cross-stage time alignment and latency (stems vs. mix vs. MIDI vs. video) — HIGH

Why it matters: The pipeline chains yt-dlp -> ffmpeg -> separation -> transcription -> beat grid -> alphaTab sync with the YouTube player. Each stage can introduce constant offsets, truncation or accumulating drift, and nobody in round 1 measured them. Basic Pitch's frame-level output drifts by ~2.7 s over a 530 s file (188-sample per-window hop mismatch), its output was truncated at the end until a 20 s silent-buffer workaround was merged, and Demucs degrades at non-44.1 kHz input. The "coming-undone" project found it necessary to cross-correlate every transcribed track against its own stem's onsets (within 300 ms) and warn when a track runs 100 ms+ off. For a scrolling tab synced to a YouTube video, a 100 ms error is visible.

Key questions:
- What are the measured constant offsets and drifts introduced by each stage (ffmpeg decode/resample, Demucs/RoFormer padding and overlap-add, Basic Pitch/Transkun hop rounding, MIDI tick rounding), and how to verify them with a click-track test file?
- Where should the canonical timeline live (original decoded audio at 44.1/48 kHz) and how should every stage's output be re-aligned to it (per-track onset cross-correlation, sample-position mapping)?
- Does the YouTube stream served by yt-dlp (Opus/AAC with encoder priming/delay) start at the same instant as the embedded player's t=0, and how to calibrate the alphaTab sync offset?
- How to chunk long files for memory-bound models without duplicate/missed notes at chunk boundaries (overlap, note merging), and which libraries already do this correctly?

Sources:
- https://github.com/spotify/basic-pitch/issues/190 (frame-level temporal drift, 2.7 s over 530 s, cause analysis)
- https://github.com/spotify/basic-pitch/pull/199 (sample-position mapping utility) ; https://github.com/spotify/basic-pitch/pull/173 (audio truncation fix)
- https://github.com/facebookresearch/demucs/issues/609 (htdemucs_ft performance drops at 96 kHz)
- https://github.com/swwallowws/coming-undone (per-track latency measurement by cross-correlation; "Realign" stage)

### 3. Note-event cleanup before quantisation (staccato/legato, minimum length, octave errors, spurious notes) — HIGH

Why it matters: Round 1 picked transcribers and round 2 (topic A) quantises durations, but there is a missing middle step: turning noisy raw note events into musically plausible ones. Practitioners report Basic Pitch's default frame_threshold produces output that is "too staccato" (a bass stem came out 68% silence), that it is "too good at interpreting 1/32 rests", that minimum note length was inconsistently 127.7 ms, and that MIDI from piano covers arrives as "62 instruments". Octave errors (right pitch class, wrong register) are listed as a standard AMT failure and are especially damaging for a 4-string instrument with a two-octave range. These cleanups (legato extension to next onset under a threshold, de-overlap, velocity floor, duration caps, octave-fold toward instrument range, pitch-bend/contour merging) are cheap and determine how usable the tab is.

Key questions:
- What are the sensible defaults and thresholds (onset/frame thresholds, min note length, legato-gap threshold in beats, min velocity) for Basic Pitch / Transkun / YourMT3+ output on separated guitar and vocal stems, and how were they validated?
- Which octave-error correction strategies work on guitar/ukulele material (harmonic-energy check on the CQT, continuity with neighbouring notes, instrument-range priors), and what is their false-correction rate?
- How to merge the transcriber's pitch-bend/contour output into discrete notes versus slide/bend markers (hand-off to topic D)?
- Should cleanup be done per stem before merging (the cited project found this prevents "walls of sustained overlapping notes")?

Sources:
- https://github.com/swwallowws/coming-undone (frame_threshold staccato finding, --legato, velocity floor, duration caps, per-stem transcription)
- https://github.com/spotify/basic-pitch/issues/93 and https://github.com/spotify/basic-pitch/pull/97 (minimum note length 127.7 ms) ; https://github.com/spotify/basic-pitch/issues/72 (granularity / 1/32 rests) ; https://github.com/spotify/basic-pitch/issues/170 (noisy MIDI vs "arrangement mode") ; https://github.com/spotify/basic-pitch/issues/14 (62-instrument MIDI)
- https://lacuna.tiptreesystems.com/direction/overcoming-octave-ambiguity-in-automatic-music-transcription/txn_277c0af4156f491fb2c661fcabf51a79 (octave ambiguity overview)
- https://archives.ismir.net/ismir2014/paper/000333.pdf (spurious notes from octave errors) ; https://ieeexplore.ieee.org/document/5744990/ (transcription system with octave detection)

### 4. Vocal melody extraction and "instrumentalisation" for ukulele (lead vs. backing vocals, legato-to-notes, range placement) — HIGH

Why it matters: For a sung rock song the ukulele melody line is the vocal, not a guitar part, so the pipeline needs singing-voice transcription (SVT), which behaves differently from instrument AMT: portamento, vibrato and melisma must be segmented into discrete notes; the separated vocal stem still contains backing/harmony vocals so a pitch tracker "jumps between voices"; and audio engineers state that "separating vocals from vocals is currently beyond any software tooling", although MelBand-RoFormer lead/backing models (UVR, LALAL, Moises, AudioShake) now exist. Round 1 noted the CREPE-jumping problem in passing but did not cover SVT models (ROSVOT 2024, STARS 2025, VocalParse 2026) or how to place a vocal melody in the ukulele's C4-A5-ish range. No web source on the ukulele-specific range-mapping question was found (engines throttled), so that part is a research gap.

Key questions:
- Which SVT model (ROSVOT, VocalParse LALM, phoneme-informed note models, YourMT3+ vocal head) gives the best note-level F1 on separated pop/rock vocals, and how do they handle vibrato/portamento segmentation?
- Which lead/backing vocal separation models are open and how much do they improve note-level accuracy versus using the plain vocal stem?
- What is the rule for octave placement and transposition of a vocal melody onto re-entrant GCEA ukulele (range limits, when to fold phrases up/down an octave, key choice vs. singer's range)?
- Should melody be transcribed from the vocal stem, the lead-guitar stem, or both, and how to choose per section (verse vocal, solo guitar)?

Sources:
- https://arxiv.org/abs/2605.04613 (VocalParse, LALM-based unified SVT, 2026) ; https://arxiv.org/abs/2405.09940 (ROSVOT) ; https://arxiv.org/abs/2507.06670 (STARS) ; https://arxiv.org/abs/2304.05917 (phoneme-informed note transcription) ; https://arxiv.org/abs/2203.13422 (SVT from polyphonic music via pseudo labels)
- https://www.reddit.com/r/audioengineering/comments/176qaar/separating_main_vocals_and_backup_vocals/ ; https://www.reddit.com/r/audioengineering/comments/1jqcofy/how_can_i_separate_a_backing_vocal_track_into/ (practitioner limits)
- https://neuralanalog.com/stems/separate-main-vocal-from-back-vocals-ai (MelBand RoFormer lead/back) ; https://github.com/Anjok07/ultimatevocalremovergui/discussions/1250 ; https://www.audioshake.ai/audioshake-models/backing-vocals-separation ; https://moises.ai/features/vocal-stems/
- https://github.com/spotify/basic-pitch/issues/42 (Basic Pitch on human voice "unusable")

### 5. Bass stem as the harmonic anchor: root, inversion and slash-chord disambiguation — HIGH

Why it matters: The most-reported chord-recogniser failures are wrong roots and major/minor confusion ("Wrong roots, confuses minor and major chords, wrong transition times"; "ONLY able to identify the root note"), and chroma-based recognisers cannot tell inversions apart because "different inversions, voicings, and octaves produce the same chromagram pattern". The bass stem (consistently the best-separated stem after vocals) carries the bass note, which is what commercial tools (Chord ai) use for slash notation. For ukulele the arranger must then decide whether C/E becomes C, Em or a bass-note run. Round 1 covered chord vocabularies and simplification, not using a bass transcription to correct/validate chords.

Key questions:
- Does bass-stem pitch tracking (SwiftF0/RMVPE/Basic Pitch on the Demucs bass stem, or raraz15's bass-line transcriber) measurably improve root accuracy of madmom/BTC/ChordMini output on rock mixes?
- What logic decides between "slash chord", "inversion", "bass walk/passing tone" and "the chord recogniser was wrong" when bass and chord disagree?
- How are slash chords conventionally written in ukulele chord sheets, and when should they be dropped?
- Does the bass line also help the beat/downbeat tracker (root changes on downbeats) and section detection?

Sources:
- https://brizm.dev/chord-detector/ (inversions produce identical chromagrams) ; https://apps.apple.com/us/app/chord-ai-play-any-song/id1446177109 (slash notation from lowest note)
- https://www.reddit.com/r/WeAreTheMusicMakers/comments/178zv1/chordify_is_awsome/ ; https://www.reddit.com/r/transcribe/comments/4l1v0h/chordify_does_this_seem_to_be_correct_for_the/ (root/major-minor errors)
- https://github.com/raraz15/automatic_bass_line_transcriber (ISMIR 2021 LBD bass transcriber) ; https://www.songscription.ai/blog/best-bass-line-transcription-tools (octave ambiguity in low register)
- https://arxiv.org/abs/2107.14653 (DadaGP, guitar-bass transcription dataset)

### 6. Local key estimation and modulation handling (per-section key, truck-driver key changes) — MEDIUM

Why it matters: Round 1 only covered global key (madmom key CNN, Essentia). Pop/rock songs modulate (final-chorus semitone/whole-tone lifts, relative-minor bridges, "Summer of '69" bridge moving to F/Bb/C), and a ukulele sheet needs either a section-wise transposition/capo note or re-voiced shapes after the change. Local key estimation (LKE) is a distinct MIR task with its own literature (Schreiber/Weiss/Müller ICASSP 2020; EUSIPCO 2024 musically-inspired network) and annotator disagreement issues; it is also the natural input for choosing uke-friendly keys per section.

Key questions:
- Which open LKE implementation (if any) works on pop/rock audio, and what accuracy/latency does it have at section granularity?
- Can local key be inferred cheaply from the chord-sequence output (DP over chord labels, as in symbolic key-finding) rather than from audio?
- How should the arranger represent a modulation on a ukulele chord sheet (transposed shapes vs. "capo +1 from here"), and how do existing UkuTabs/Chordify sheets do it?
- How does LKE interact with the tuning-offset detection in topic C (a half-step-sharp recording vs. a true modulation)?

Sources:
- https://www.audiolabs-erlangen.de/content/05-fau/professor/00-mueller/03-publications/2020_SchreiberWM_LocalKey_ICASSP_PrintedVersion.pdf (Local Key Estimation in Classical Music Recordings)
- https://eurasip.org/Proceedings/Eusipco/Eusipco2024/pdfs/0000026.pdf (Towards Robust Local Key Estimation with a Musically Inspired Neural Network)
- https://www.researchgate.net/publication/347172749_Local_Key_Estimation_in_Music_Recordings_A_Case_Study_Across_Songs_Versions_and_Annotators
- https://arxiv.org/abs/2402.10247 (joint pitch spelling + local/global key from MIDI, DP) ; https://arxiv.org/abs/1808.05340 (genre-agnostic key CNN)

### 7. Robustness/distribution shift of transcription models and input conditioning (loudness, resampling, codec) — MEDIUM

Why it matters: A Dec 2025 systematic analysis finds deep AMT systems lose ~20 F1 points from sound/recording-condition shift and ~14 from genre shift, with dynamics estimation more fragile than onsets and a "persistent Corpus Bias" toward classical piano. YouTube audio arrives as Opus/AAC at modest bitrates with unknown loudness, often sped-up or re-encoded; a 2014 study specifically examined "Effects of Audio Compression on Chord Recognition" (abstract not retrievable), while a transcription vendor argues format is "rarely the bottleneck" above ~256 kbps MP3. Practitioners also warn against peak normalisation per file and recommend resampling to the model's expected rate. None of this preprocessing (LUFS normalisation, mono downmix choice, resample quality, DC/true-peak) was specified in round 1.

Key questions:
- What exact preprocessing chain (sample rate, mono vs. stereo, LUFS target, resampler) does each chosen model expect, and how much does deviating cost in note/chord F1?
- What bitrate/codec does yt-dlp actually deliver for typical music videos, and does Opus 128k vs. AAC 128k measurably change Demucs/Basic Pitch/chord output?
- How to detect and handle degraded inputs (low-bitrate re-uploads, live phone recordings, heavy limiting) and whether to warn the user or adjust thresholds?
- Which of the round-1 models were trained on polyphonic rock mixes vs. piano, and what does the corpus-bias finding imply for expected accuracy on distorted-guitar material?

Sources:
- https://arxiv.org/abs/2512.14602 (Sound and Music Biases in Deep Music Transcription Models, Dec 2025)
- https://link.springer.com/chapter/10.1007/978-3-319-04117-9_34 (Uemura, Ishikura, Katto 2014, Effects of Audio Compression on Chord Recognition) ; https://archives.ismir.net/ismir2019/paper/000004.pdf (20 Years of ACR, mentions compression)
- https://www.songscription.ai/blog/best-audio-formats-for-music-transcription (vendor guidance on formats/bitrates)
- https://bioacoustics.stackexchange.com/questions/846/should-we-normalize-audio-before-training-a-ml-model ; https://huggingface.co/learn/audio-course/chapter1/audio_data (normalisation and resampling practice) ; https://csteinmetz1.github.io/pyloudnorm-eval/paper/pyloudnorm_preprint.pdf (pyloudnorm)
- https://github.com/facebookresearch/demucs/issues/609 (sample-rate sensitivity)

### 8. Audio language models as perception components or verifiers (2025-2026 state) — MEDIUM

Why it matters: Topic F covers LLMs for symbolic post-processing; what is uncovered is whether audio-capable models (Gemini 2.5, Qwen2.5-Omni, LALM-based VocalParse, MuseAgent) can replace or verify any audio stage. Current evidence is cautionary: on chord-quality identification, transposition and syncopation tasks, multimodal LLMs "perform near ceiling on MIDI but show accuracy drops on audio" and "do not yet 'listen' reliably from audio"; an LLM chain-of-thought coordinator over MIR tool outputs improved chord recognition by only 1-2.77%. Yet LALM-based SVT (VocalParse) claims SOTA. The team needs a calibrated view before spending API budget.

Key questions:
- On a small in-house test (the two target songs), how do Gemini 2.5 Pro / Qwen2.5-Omni compare with madmom/BTC for chord labels per bar, and with Beat This! for tempo/metre?
- Is there a benchmark (e.g. MARBLE, music-perception evaluations) with chord/key/tempo tasks on audio that reports audio-LLM numbers?
- Where is an audio LLM plausibly useful now: section labelling, instrument presence, "is this a key change", or arbitration between disagreeing tools?
- What are the cost/latency and licensing implications of routing audio through hosted models?

Sources:
- https://arxiv.org/abs/2510.22455 (Evaluating Multimodal LLMs on Core Music Perception Tasks: Gemini 2.5 Pro/Flash, Qwen2.5-Omni)
- https://arxiv.org/abs/2509.18700 (LLM chain-of-thought coordinator for chord recognition, +1-2.77%)
- https://arxiv.org/abs/2601.11968 (MuseAgent-1, grounded multimodal music agent with AMT/OMR modules)
- https://arxiv.org/abs/2605.04613 (VocalParse LALM SVT) ; https://arxiv.org/abs/2509.20641 (modality contribution in audio LLMs for music) ; https://arxiv.org/abs/2306.10548 (MARBLE benchmark)

### 9. Instrument presence detection and "which stem drives the arrangement" — MEDIUM

Why it matters: Round 1 assumed a guitar stem exists and is meaningful. Many rock/pop songs are piano-, synth- or riff-driven; the 6-stem Demucs guitar/piano stems are "okay"/poor; and the strum pattern should be derived from whichever instrument actually plays the rhythmic chordal part. Predominant-instrument recognition (Han et al. 2016), instrument-conditioned transcription (Jointist) and query-based separation (Banquet) exist but were not evaluated for this routing decision.

Key questions:
- Which open instrument-recognition model (OpenMIC-style taggers, Jointist's recognizer, Essentia/CLAP zero-shot) reliably tells "acoustic guitar / electric rhythm guitar / piano / synth pad is the chordal instrument" per section?
- How to decide which stem(s) feed chord recognition, strum detection and melody extraction, and when to fall back to the full mix?
- Can stem energy ratios and chord-stability statistics substitute for a trained instrument classifier?

Sources:
- https://arxiv.org/abs/1605.09507 (predominant instrument recognition CNN) ; https://arxiv.org/abs/2302.00286 (Jointist: instrument recognition + transcription + separation) ; https://arxiv.org/abs/2406.18747 (Banquet, query-based stem-agnostic separation)
- https://github.com/facebookresearch/demucs (guitar "okay", piano poor in 6-stem model)

### 10. Non-music and structural-edge handling for YouTube inputs (talking intros, applause, silence, fades) — MEDIUM

Why it matters: YouTube sources are often live videos or lyric videos with spoken intros, crowd noise, applause, long silences and fade-outs. These corrupt tempo estimation, key detection and section detection, and produce garbage bars at the start/end of the tab. Open MIT-licensed speech/music/noise segmenters exist (inaSpeechSegmenter, MIREX 2018 speech-detection winner) and one practitioner pipeline trims silence and sections before separation, but round 1 did not address pre-segmentation. No source was found specifically on fade-out/ritardando ending detection (engines throttled); treat that as a sub-gap.

Key questions:
- Which segmenter (inaSpeechSegmenter, Essentia/CLAP tagging, simple RMS gating) best isolates the musical span of a YouTube video, and how does it treat singing (tagged as music)?
- How to detect and trim fade-outs, applause and count-ins so the last/first bars are not transcribed, while still reporting song length correctly?
- Should the beat tracker and key estimator run only on the trimmed span, and how are timestamps mapped back for video sync (links to topic 2)?

Sources:
- https://github.com/ina-foss/inaSpeechSegmenter (speech/music/noise CNN segmenter, MIT)
- https://github.com/swwallowws/coming-undone ("Fetch & Prepare: optionally trim silence and section")
- https://stemsplit.io/blog/demucs-online-tutorial (live recordings produce artifacts)

### 11. Per-note dynamics and accent estimation from audio (for strum accents and melody phrasing) — LOW

Why it matters: Round 1 found no model handles strum accents, and the corpus-bias study reports dynamics/velocity estimation is the most fragile AMT output. If the tab is to show accents (>) or loud/soft strums, the pipeline needs a velocity estimate per onset from the separated stem; score-informed refinement exists for piano but nothing guitar-specific was found.

Key questions:
- How well do Basic Pitch / Transkun velocities correlate with perceived accent on strummed guitar stems, and does per-stem loudness envelope at onset do as well?
- What is a usable mapping from velocity/onset energy to accent marks or dynamics in alphaTex/MusicXML?

Sources:
- https://arxiv.org/abs/2508.07757 (score-informed velocity refinement) ; https://arxiv.org/abs/2512.14602 (dynamics estimation more vulnerable than onsets)
- https://github.com/swwallowws/coming-undone (velocity floor as cleanup step)

### 12. Groove and swing-ratio estimation from the drum stem to set strumming feel — LOW

Why it matters: Round 1 (Q6) decided to represent swing as a triplet feel but gave no method for measuring it. The swing ratio is tempo-dependent and measurable from drum onsets (ride/hi-hat), with a published literature on jazz and funk microtiming; for ukulele strum notation the decision "straight 8ths vs shuffle" should be made from the drum stem rather than guessed.

Key questions:
- Can a simple onset-interval histogram on the Demucs drum stem give a reliable swing ratio per section, and what thresholds map to "straight / light shuffle / triplet"?
- Does the strumming feel of the recorded guitar match the drums, and which one should the tab follow?

Sources:
- https://arxiv.org/pdf/1904.03442 (Does it Swing? microtiming deviations and swing feel) ; https://www.academia.edu/30689017/AUTOMATED_ESTIMATION_OF_RIDE_CYMBAL_SWING_RATIOS_IN_JAZZ_RECORDINGS ; https://www.academia.edu/2756208/Preferred_swing_ratio_in_jazz_as_a_function_of_tempo
- https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0199604 (groove in drum patterns, 8th-note swing definition) ; https://www.gmth.de/zeitschrift/artikel/1224.aspx (swing ratios in funk)

---

## Threads surfaced but left unsourced (research gaps, not topics)

- Chord-change timing relative to the beat (anticipated "pushed" chords on the "and of 4", and how to snap chord boundaries to the grid without losing the push). Only indirect evidence found (Chordify "wrong transition times" complaints; per-track latency warnings in coming-undone). Worth folding into topic 1 or topic A if the quantisation researcher has room.
- Ukulele-specific guidance on vocal-melody range placement and key choice for singing along: no usable web source retrieved before engines throttled; folded into topic 4 as an open question.
- Fade-out / ritardando ending detection: no dedicated source; folded into topics 1 and 10.
- ISMIR 2025 tutorial list: the site returned no content; ISMIR 2024 tutorials (DL 101 for audio MIR; Lyrics and Singing Voice Processing; Music audio + language) contain nothing beyond what rounds 1-2 cover. https://ismir2024.ismir.net/tutorials

## Considered and rejected (already adequately covered, or out of scope)

- Demucs stem bleed/artifacts and separation quality: covered in round 1 (source_separation_and_ingest.md Q4-Q7).
- Capo / drop-tuning / alternate-tuning detection of the source guitar: assigned to topic C (tuning offset) and largely irrelevant once the arrangement is re-targeted to GCEA; only one academic source (Cardiff DLFM 2024 tuning classifier, https://dl.acm.org/doi/fullHtml/10.1145/3660570.3660574) and it is guitar-only.
- Octave errors as a transcription-model selection criterion: covered as a cleanup problem in topic 3 rather than a separate topic.
- Chunking long audio for models: merged into topic 2.
- MIR reproducibility / runtime divergence (Basic Pitch Python vs. web demo giving different notes, issues #126/#134): real but small; belongs under topic F's engineering notes. https://github.com/spotify/basic-pitch/issues/126 ; https://github.com/spotify/basic-pitch/issues/134
- GPU-free / real-time inference: not investigated (search budget); topic F (CUDA/PyTorch on Windows) is the natural home and round 1 already records CPU-only options (SwiftF0 ONNX, Beat This! CPU fallback).
- Fretboard ergonomics and fingering cost models: covered by tablature_theory_and_strumming.md Q1 (DP over biomechanical costs).
- Music structure analysis / repeats: covered by allin1 in Q7; the only new angle (trimming non-music edges) is topic 10.
- Drum transcription per se: only needed as a feel/metre cue (topics 1 and 12).
- Bass-line tablature as an output: out of scope (ukulele only), but bass transcription as a harmonic cue is topic 5.
