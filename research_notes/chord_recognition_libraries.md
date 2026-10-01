# Python Libraries and Models for Automatic Chord Recognition (ACR) from Audio — state as of 2026-10-01

Scope: Python-usable tools that take an audio file and return a time-aligned chord sequence, for a Windows 11 pipeline targeting rock/pop full mixes (e.g. "Summer of '69", "Pour Some Sugar On Me"). Also covers beat/downbeat trackers, key detection, and chord simplification. Dates and maintenance status are noted on every tool; all facts are cited inline. Where a figure could not be verified from a primary source it is listed under Gaps rather than guessed.

Note on sources: Papers With Code (previously the go-to "chord recognition" leaderboard) was shut down by Meta on 24-25 July 2025; paperswithcode.com now redirects to Hugging Face and the old leaderboards are only available as a static snapshot in the `pwc-archive` Hugging Face org — [Coursera](https://www.coursera.org/articles/papers-with-code); [HyperAI](https://hyper.ai/en/news/42900). The MIREX 2025 Audio Chord Estimation results page is therefore the best current public cross-system benchmark — [MIREX 2025 ACE Results](https://music-ir.org/mirex/wiki/2025:Audio_Chord_Estimation_Results).

## Key Question 1: What are the leading options, and how do they compare (install, license, maintenance, accuracy, vocabulary, GPU, Windows, output)?

### Takeaway
There is no single "pip install and go" state-of-the-art ACR package in 2026. The practical open-source options split into (a) DSP/Vamp-based (Chordino via chord-extractor/vamp, librosa chroma templates, Essentia) — easy to understand, weakest accuracy; (b) 2016-2019 deep models with Python packaging (madmom CNN/CRF majmin, crema 602-class, BTC, music-x-lab ISMIR2019 Chord-CNN-LSTM, Omnizart HT) — best accuracy/effort ratio but mostly unmaintained and with dependency breakage; (c) 2025-2026 research models (ChordFormer, Mamba/BMACE, consonance-trained conformer, ChordMini pseudo-labelled BTC) — most of which have no pip package, and some have no code at all. For a Windows pipeline the lowest-friction high-accuracy choice is a PyTorch model (BTC / ChordMini / ISMIR2019 Chord-CNN-LSTM) run from a git checkout, with madmom-from-git as the beat/majmin fallback.

### Cited Findings — summary table

| Tool | Approach | Install | License | Last release / activity | Vocabulary | GPU | Windows | Output |
|---|---|---|---|---|---|---|---|---|
| madmom | DNN "deep chroma" + CRF; CNN features + CRF | pip (0.16.1, broken on py>=3.10) or `pip install git+https://github.com/CPJKU/madmom` (0.17.dev0) | BSD code; models CC BY-NC-SA 4.0 | PyPI 0.16.1 = 2018-11-14; last commit 2024-08-25 | maj/min + N (25 classes) | No (CPU) | Yes via git install; Cython build needed | (start, end, label) tuples at 10 fps |
| Chordino (Vamp) via chord-extractor / vamp | NNLS chroma + HMM/Viterbi, template dictionary | `pip install chord-extractor` (bundled Linux .so) or `pip install vamp` + Vamp plugin pack binary + VAMP_PATH | chord-extractor GPL-2.0 | Vamp plugin v1.0 2015-09-09; used as MIREX 2025 baseline | Configurable chord.dict; labels like Am7b5 appear (7ths, dims) | No | Yes (Windows binaries exist; set VAMP_PATH) | list of ChordChange(chord, timestamp) |
| librosa chroma + templates (FMP) | chroma_stft/cqt vs 24 binary templates (+ optional HMM) | `pip install librosa` (your own ~50 lines) | librosa ISC | librosa active | 24 maj/min (extensible) | No | Yes | Whatever you write (frame labels) |
| Essentia ChordsDetection / ChordsDetectionBeats | HPCP + maj/min template, 2 s window or per-beat | `pip install essentia` (Linux/macOS wheels only) | AGPL-3.0 | 2.1b6.dev1438, 2026-05-19 | maj/min triads only | No | NO Python bindings on Windows -> WSL | per-frame chord strings + strengths |
| autochord | NNLS-Chroma Vamp -> Bi-LSTM-CRF (TensorFlow) | `pip install autochord` | MIT | 0.1.4, 2021-10-07; inactive | 25 (maj/min/N) | No | Needs Vamp plugin + old TF | (start, end, label) list; optional .lab |
| crema (McFee) | CNN/RNN structured prediction (TF/Keras) | `pip install crema` or git | BSD-2-Clause | 0.2.0 (Zenodo archive); no newer release found | 602 effective classes incl. inversions | No | Unverified (old TF stack) | JAMS file / object |
| BTC (Park et al. ISMIR 2019) | Bi-directional Transformer on CQT, PyTorch | git clone; `python test.py --audio_dir ... --voca True` | MIT | 2019 code; repo static (14 commits) | majmin (voca=False) or large vocab (voca=True) | Optional | Yes (PyTorch) | .lab + MIDI |
| music-x-lab ISMIR2019 Chord-CNN-LSTM (Jiang et al.) | CNN+BLSTM, chord-structure decomposition, PyTorch | git clone; `python3 chord_recognition.py audio out [chord_dict]` | MIT | 2019; 7 commits; used as MIREX 2025 "ISMIR2019" baseline | Large vocab (configurable dict; MIREX or full MARL list) | Optional | Yes (PyTorch) | .lab |
| ChordMini (Phan et al. 2026) | BTC student trained on 1,000 h pseudo-labels + distillation | git clone + requirements.txt; checkpoints in repo | MIT | arXiv 2602.19778 (2026); 216 commits, active 2026 | Large-vocab BTC teacher (`btc_model_large_voca.pt`) | Optional | Yes (PyTorch) | .lab |
| Omnizart (chord module) | Harmony Transformer on Chordino NNLS chroma | `pip install omnizart`; `omnizart download-checkpoints`; `omnizart chord transcribe x.wav` | MIT | 0.6.3, 2026-05-31; py>=3.8 | 25 (maj/min/N), 230 ms resolution | Optional | Not stated; Docker/pip/conda; ARM-mac broken | MIDI + CSV (chord, start, end) |
| ChordFormer (2025) | Conformer, structured 6-part chord representation | No code link in paper | CC BY-NC-SA 4.0 (paper) | arXiv 2025-02-17 | 301 classes (triads, bass, 7/9/11/13) | — | — | — |
| Basic Pitch (Spotify) | Note-level AMT (not chords) | `pip install basic-pitch` | Apache-2.0 | 0.4.0, 2024-08-16; py3.7-3.11 | n/a (notes) | No | Yes (macOS/Windows/Linux) | MIDI, note CSV, NPZ |
| music.ai Chords (commercial) | Hosted API | REST API, business plans only | Commercial | Live 2025-26 | Complex/Simple Jazz/Pop classes, bass, key | n/a | n/a | JSON timeline + key |

### Cited Findings — per tool

**madmom (CPJKU)**
- Provides DNN-based chroma extraction, "CRF chord recognition using DNN chroma vectors" and "CNN chord recognition using CRF decoding"; also DBN beat tracking, RNN downbeat tracking, bar tracking (added in 0.16) and key recognition (added in 0.16). Latest PyPI release 0.16.1 on 2018-11-14. Source code BSD; model/data files CC BY-NC-SA 4.0 (commercial use of models requires contacting Gerhard Widmer) — [PyPI madmom](https://pypi.org/project/madmom/)
- DeepChromaChordRecognitionProcessor: major/minor only, 10 fps, output array of (start, end, label), from Korzeniowski & Widmer ISMIR 2016 "The Deep Chroma Extractor". CNNChordFeatureProcessor + CRFChordRecognitionProcessor: major/minor + 'N', 10 fps, from the MLSP 2016 fully-convolutional paper — [madmom chords docs](https://madmom.readthedocs.io/en/v0.16/modules/features/chords.html)
- Most recent commit on main is 2024-08-25 "CI and NumPy compatibility updates (#540)"; the five most recent commits are 2024-08-25, 2023-09-10, 2023-09-09, 2022-01-06, 2021-12-29 — [madmom commits](https://github.com/CPJKU/madmom/commits/main)
- Repo: 1,753 commits, ~60 open issues; models are a git submodule so clone with `git clone --recursive`; no formal maintenance statement — [madmom GitHub](https://github.com/CPJKU/madmom)
- The madmom "FK" model (Korzeniowski) "achieves state-of-the-art scores in the MIREX Audio Chord Estimation (ACE) campaign" (historical, 2016-era claim) — [Harmony Transformer paper, ISMIR 2019](https://archives.ismir.net/ismir2019/paper/000030.pdf)

**Chordino / NNLS Chroma (Vamp plugin) and Python wrappers**
- Chordino and NNLS Chroma v1.0 released 2015-09-09 — [Vamp forum](https://www.vamp-plugins.org/forum/index.php/topic,294.0.html)
- Chord profiles come from a user-editable `chord.dict` file; parameters include boost-N (default 0.1), HMM/Viterbi smoothing toggle, NNLS approximate transcription toggle; defaults are "those used for Matthias Mauch's 2010 MIREX submissions"; "readily compiled binaries for Windows and Mac OSX (Intel)"; authors Matthias Mauch and Chris Cannam — [isophonics.net/nnls-chroma](http://www.isophonics.net/nnls-chroma)
- MIREX 2025 ran Chordino (NNLS Chroma v1.1) as a baseline: Billboard 2013 Root 71.06 / MajMin 67.18 / Sevenths 48.88; Yamaha Balanced Root 77.57 / MajMin 74.64 / Sevenths 56.38 — [MIREX 2025 ACE Results](https://music-ir.org/mirex/wiki/2025:Audio_Chord_Estimation_Results)
- chord-extractor: GPL-2.0, wraps Chordino; bundled compiled Chordino is for Linux 64-bit; other OSes must install the Vamp plugin pack and set `VAMP_PATH`; numpy must be installed before `pip install chord-extractor` because the `vamp` dependency needs it at setup; output is a list of `ChordChange(chord, timestamp)`; labels seen include 'N', 'C', 'Am7b5' — [chord-extractor GitHub](https://github.com/ohollo/chord-extractor); [chord-extractor PyPI](https://pypi.org/project/chord-extractor)
- Chordino "uses non-negative least squares (NNLS) based approximate note transcription prior to chroma mapping"; deep learning systems "outperform Chordino by large margins in certain chord categories like sevenths" — [arXiv 1709.07153 (Large-vocab ACE with DNNs)](https://arxiv.org/pdf/1709.07153)

**librosa chroma + template matching (DIY) / FMP notebooks**
- The FMP (Fundamentals of Music Processing) notebook C5S2 implements template-based recognition with STFT, IIR filterbank and CQT chroma, 24 binary maj/min templates, normalised inner product similarity, argmax per frame; it acknowledges the maj/min-only vocabulary is "problematic from a musical point of view", and points to C5S3_ChordRec_HMM.html for the HMM post-filtering version. No accuracy percentages are reported in the notebook — [FMP C5S2](https://www.audiolabs-erlangen.de/resources/MIR/FMP/C5/C5S2_ChordRec_Templates.html)
- "chroma-CQT does comparatively poorly at identifying thirds and sevenths when used for chord recognition" — [arXiv 2512.22621 (Mackenzie 2025)](https://arxiv.org/html/2512.22621v1)

**Essentia**
- `ChordsDetection` "estimates chords given an input sequence of harmonic pitch class profiles (HPCPs), finding the best matching major or minor triad"; `ChordsDetectionBeats` does the same on segments between consecutive beats; default window 2 s — [Essentia tonal chords tutorial](https://essentia.upf.edu/tutorial_tonal_chords.html); [Essentia issue #769](https://github.com/MTG/essentia/issues/769)
- Installation docs: "Python bindings are not yet supported on Windows"; recommended route is cross-compilation with MinGW or installing in WSL — [Essentia installing](https://essentia.upf.edu/installing.html)
- PyPI: 2.1b6.dev1438 released 2026-05-19, AGPL-3.0-only, wheels for manylinux2014 x86-64 and macOS 15+ (x86-64 and arm64); no Windows wheels — [PyPI essentia](https://pypi.org/project/essentia/)

**autochord**
- `pip install autochord`; runs the NNLS-Chroma Vamp plugin for chroma then a Bi-LSTM-CRF in TensorFlow; 25 classes (12 maj, 12 min, N); output list of (start, end, label) tuples, optional .lab; latest version 0.1.4 released 2021-10-07; MIT; Python >=3.6; "measured test accuracy of the TensorFlow model is 67.33%" — [PyPI autochord](https://pypi.org/project/autochord/); [ISMIR 2021 LBD](https://archives.ismir.net/ismir2021/latebreaking/000008.pdf)
- Libraries.io flags maintenance as inactive, no PyPI release in the past 12 months — [libraries.io autochord](https://libraries.io/pypi/autochord)

**crema (Brian McFee)**
- Chord model "based on the structured prediction model of McFee and Bello", "enhanced to support inversion (bass) tracking, and predicts chords out of an effective vocabulary of 602 classes"; `pip install crema` — [crema docs](https://crema.readthedocs.io/en/latest/); [crema models](https://crema.readthedocs.io/en/latest/models.html)
- BSD-2-Clause; CLI `python -m crema.analyze file.mp3 -o file.jams`; Python API `analyze(filename=...)`; output JAMS — [crema GitHub](https://github.com/bmcfee/crema)
- Version 0.2.0 archived on Zenodo — [Zenodo 6475980](https://zenodo.org/records/6475980)
- Underlying method: McFee & Bello, "Structured training for large-vocabulary chord recognition", ISMIR 2017 — [ISMIR 2017 paper](https://archives.ismir.net/ismir2017/paper/000077.pdf)

**BTC — Bi-directional Transformer for Chord recognition (Park et al., ISMIR 2019)**
- MIT; PyTorch >=1.0; deps librosa, numpy, pandas, pyrubberband, pyyaml, mir_eval, pretty_midi; inference `python test.py --audio_dir audio_folder --save_dir save_folder --voca False`; `voca=True` selects large-vocabulary labels; outputs .lab and MIDI; 14 commits total — [BTC-ISMIR19 GitHub](https://github.com/jayg996/BTC-ISMIR19)
- Paper: single training phase, results comparable to systems using separate feature extractors or HMM/CRF decoders; evaluated on Isophonics, RWC, USPop with root/majmin/thirds/triads/sevenths/tetrads/mirex metrics; CQT input — [arXiv 1907.02698](https://arxiv.org/pdf/1907.02698); [ISMIR 2019 paper](https://archives.ismir.net/ismir2019/paper/000075.pdf)

**music-x-lab ISMIR2019 Large-Vocabulary Chord Recognition (Jiang, Chen, Li, Xia)**
- MIT; pretrained models in repo (without label reweighting, "best overall accuracy"), reweighted variants on Google Drive; `python3 chord_recognition.py path_to_audio_file path_to_output_file [chord_dict]`; alternative chord dictionaries include the MIREX vocabulary and the full MARL list; output .lab; 7 commits — [ISMIR2019-Large-Vocabulary-Chord-Recognition GitHub](https://github.com/music-x-lab/ISMIR2019-Large-Vocabulary-Chord-Recognition)
- Paper: "Large-vocabulary chord transcription via chord structure decomposition", ISMIR 2019 — [ISMIR 2019 paper 78](https://archives.ismir.net/ismir2019/paper/000078.pdf)
- This model was run as the "ISMIR2019" baseline at MIREX 2025 and remained competitive with all 2025 submissions: Billboard 2013 Root 78.61 / MajMin 76.39 / Sevenths 64.15; Yamaha Balanced Root 82.00 / MajMin 81.16 / Sevenths 66.97 (best Sevenths on that set); Yamaha JPop Root 81.49 / MajMin 79.99 / Sevenths 62.81 (best MajMin and Sevenths on that set) — [MIREX 2025 ACE Results](https://music-ir.org/mirex/wiki/2025:Audio_Chord_Estimation_Results)

**ChordMini (Phan, Jin, Liu, Dong, arXiv 2602.19778, 2026) and ChordMiniApp**
- Uses a pre-trained BTC as teacher to pseudo-label >1,000 hours of unlabeled audio, trains a student on pseudo-labels, then continues on ground truth with selective knowledge distillation; the BTC student "surpasses the traditional supervised learning baseline by 2.5% and the original pre-trained teacher model by 1.55% on average across all metrics" — [arXiv 2602.19778](https://arxiv.org/abs/2602.19778); [awesomepapers summary](https://awesomepapers.io/speech-audio/papers/2602.19778)
- Repo: MIT; venv + `pip install -r requirements.txt`; checkpoints `btc_model_best.pth`, `2e1d_model_best.pth`, and original teacher `btc_model_large_voca.pt`; inference `python src/evaluation/test.py --model_type ChordNet --checkpoint ... --audio_dir x.mp3 --save_dir outputs/`; .lab output; 216 commits — [ChordMini GitHub](https://github.com/ptnghia-j/ChordMini)
- ChordMiniApp (Next.js + Flask backend, Python 3.10.x, Git LFS for checkpoints, MIT, 458 commits, 401 stars) integrates Chord-CNN-LSTM (music-x-lab ISMIR2019), BTC-SL / BTC-PL, and ChordMini for chords, plus Beat-Transformer and madmom for beats; useful as a reference integration of exactly this pipeline — [ChordMiniApp GitHub](https://github.com/ptnghia-j/ChordMiniApp)

**Omnizart (Music and Culture Technology Lab)**
- Chord module implements the Harmony Transformer (encoder does chord segmentation, decoder recognises progression); input is Chordino NNLS chromagram; output 25 chord types (12 maj, 12 min, N) at 230 ms resolution; `transcribe` writes MIDI and CSV with chord name, start, end — [Omnizart chord API docs](https://music-and-culture-technology-lab.github.io/omnizart-doc/chord/api.html); [JOSS paper](https://www.theoj.org/joss-papers/joss.03391/10.21105.joss.03391.pdf)
- PyPI 0.6.3 released 2026-05-31; MIT; Python >=3.8; "Currently, Omnizart is incompatible for ARM-based MacOS"; Windows not addressed — [PyPI omnizart](https://pypi.org/project/omnizart/)

**ChordFormer (Akram, Dettori, Colla, Buttazzo, arXiv 2502.11840, 2025-02-17)**
- Conformer (4 layers, 4 heads, FFN 1024, d=256, kernel 31); CQT 22,050 Hz, hop 512, 36 bins/octave, 252 bins; pitch-shift augmentation -5..+6; trained on the Humphrey & Bello 1,217-song collection (Isophonics + Billboard + MARL), 5-fold; 6-part structured chord representation (root+triad, bass, 7th, 9th, 11th, 13th) covering 301 unique chords; reweighted loss for class imbalance — [arXiv 2502.11840 HTML](https://arxiv.org/html/2502.11840)
- Results vs CNN+BLSTM (Jiang et al. 2019): Root 84.69 vs 83.39; MajMin 84.09 vs 82.62; Thirds 81.75 vs 80.04; Triads 77.55 vs 75.91; Sevenths 72.28 vs 69.78; Tetrads 65.32 vs 62.87; MIREX 83.62 vs 81.52. Large-vocab frame-wise acc 0.7877, class-wise 0.4471. Abstract claims "2% improvement in frame-wise accuracy and a 6% increase in class-wise accuracy". No GitHub link in the paper — [arXiv 2502.11840 HTML](https://arxiv.org/html/2502.11840); [arXiv abstract](https://arxiv.org/abs/2502.11840)
- A third-party repo benchmarks "pretrained Chordformer" fine-tuned on synthetic data, implying some reimplementation/weights exist outside the paper, but this is not the authors' official release — [shojha24/ChordFormer-Artificial-Dataset-Benchmarking](https://github.com/shojha24/ChordFormer-Artificial-Dataset-Benchmarking)

**Other 2025-2026 research systems (no pip package found)**
- MIREX 2025 submissions: MD1 (Masayuki Doai), wu-single/wu-ensemble (Yiwei Ding, Christof Weiss — CRNN/transformer ensemble), YK1 (Yiming Wu, Kento Yoshida), BMACE (Chunyu Yuan, Jiyeoung Sim, Johanna Devaney — bidirectional Mamba). Test sets: Billboard 2013, Yamaha_JPOP (200 songs, private), Yamaha_Balanced (241 songs). Best Billboard 2013: MD1 Root 81.35 / MajMin 79.15 / Sevenths 66.40; YK1 Root 81.01 / MajMin 78.10. BMACE collapsed to MajMin 8.88 on Billboard (Root 55.72), suggesting a label-format or submission bug rather than a true accuracy. No submission lists public code on the results page; YK1 system description was listed "TBA" — [MIREX 2025 ACE Results](https://music-ir.org/mirex/wiki/2025:Audio_Chord_Estimation_Results); [wu-ensemble system description PDF](https://futuremirex.com/portal/wp-content/uploads/2025/audio-chord-estimation/wu-ensemble.pdf); [Mamba-based ACR (ResearchGate)](https://www.researchgate.net/publication/399478191_A_Mamba-Based_Model_for_Automatic_Chord_Recognition)
- "From Discord to Harmony: Decomposed Consonance-based Training for Improved Audio Chord Estimation" (Poltronieri, Serra, Rocamora, ISMIR 2025, Daejeon, Sept 21-25 2025): conformer with consonance-based label smoothing and separate root/bass/note-activation heads; no code link in abstract — [arXiv 2509.01588](https://arxiv.org/abs/2509.01588)
- "An event-based sequence modeling approach to recognizing non-triad chords with oversegmentation minimization" (Kim & Park, ICASSP 2026, arXiv 2026-04-27): segment-level seq2seq instead of frame classification, targets non-triad chords; no code indicated — [arXiv 2604.24386](https://arxiv.org/abs/2604.24386)
- "Enhancing Automatic Chord Recognition through LLM Chain-of-Thought Reasoning" (Chang, Chen, Chen, Su, 2025-09-23): GPT-4o coordinates outputs of source separation, key detection, chord recognition and beat tracking in a 5-stage CoT; gains of 1-2.77% on the MIREX metric across three datasets; no code info — [arXiv 2509.18700](https://arxiv.org/abs/2509.18700)
- "Chord Recognition with Deep Learning" (Mackenzie, 2025-12-27): finds classifiers "perform poorly on rare chords", pitch augmentation helps, features from generative models (i.e. foundation-model embeddings) "did not improve performance", synthetic data is promising; incorporates beat detection into outputs — [arXiv 2512.22621](https://arxiv.org/abs/2512.22621)
- "Training chord recognition models on artificially generated audio" (Majchrzak & Mandziuk, 2025-08-07): two transformer models trained on AAM, Winterreise, McGill Billboard; concludes synthetic audio "can even be used as a standalone training set for a model that predicts chord sequences in pop music" — [arXiv 2508.05878](https://arxiv.org/abs/2508.05878)

**Spotify Basic Pitch (note-level, not chords)**
- Apache-2.0; 0.4.0 released 2024-08-16 (added training code); Python 3.7-3.11; macOS, Windows, Linux supported; backends TensorFlow, CoreML, TFLite, ONNX (TF no longer installed by default since 0.3.0; TF upper bound 2.15); outputs MIDI with pitch bends, note-event CSV, NPZ; polyphonic so it captures simultaneous notes — [PyPI basic-pitch](https://pypi.org/project/basic-pitch/); [basic-pitch releases](https://github.com/spotify/basic-pitch/releases); [basic-pitch GitHub](https://github.com/spotify/basic-pitch)
- A PyTorch port exists (`basic-pitch-torch`) — [gudgud96/basic-pitch-torch](https://github.com/gudgud96/basic-pitch-torch)

**Commercial APIs**
- music.ai Chords module: transcribes chords and root key, timeline of chord annotations in classes "Complex Jazz, Simple Jazz, Complex Pop, and Simple Pop" with bass detection; output includes `key` string and `chordMap`; $0.04/min pay-as-you-go, $0.038/min Professional; individual API keys no longer offered, business plans only — [music.ai Chords](https://music.ai/modules/transcription/chords/); [music.ai pricing](https://music.ai/pricing/)
- Chordify: no public API; developer requests for an API/SDK are on its support forum unanswered — [Chordify support post](https://support.chordify.net/hc/en-us/community/posts/360005529718-Share-Chordify-API); [What is Chordify](https://support.chordify.net/hc/en-us/articles/360002221018-What-is-Chordify)
- Chord ai (mobile app) offers chord recognition, beat tracking, voicings; only a Lyrics API is advertised — [Chord ai on Google Play](https://play.google.com/store/apps/details?id=com.chordai&hl=en_US)

### Inferences
- The MIREX 2025 table shows that the 2019 Chord-CNN-LSTM baseline (pip-free but git-runnable, MIT, PyTorch) is within ~1-3 points of the best 2025 submissions on Root/MajMin and sometimes better on Sevenths; combined with ChordMini's 2026 BTC student (also MIT, PyTorch, checkpoints in repo) these are the most practical "near-SOTA" choices for a Windows Python pipeline today.
- Chordino is roughly 7-10 points behind the deep models on Root/MajMin and 15+ points behind on Sevenths on MIREX 2025 test sets, so it is a reasonable fallback or sanity-check but not a primary engine.
- ChordFormer reports the best published numbers (MIREX 83.62 on the Isophonics+Billboard+MARL collection) but has no official code, so it is not usable in a pipeline unless a third-party reimplementation is trusted.
- Foundation-model (MERT/Jukebox) embeddings have not been shown to help ACR; the one 2025 study that tried generative-model features reported no improvement.

### Gaps
- BTC paper's exact per-metric numbers on Isophonics/RWC/USPop could not be extracted (PDF parsing failed twice); the paper at https://arxiv.org/pdf/1907.02698 Tables 2-3 should be read directly.
- crema's release date, Python/TensorFlow version pins and Windows installability could not be verified (PyPI page failed to load); the codebase dates from 2017-2022 and is likely pinned to TF1/Keras-era deps.
- No official code or weights were found for ChordFormer, the ISMIR 2025 consonance model, the ICASSP 2026 event-based model, or any MIREX 2025 submission.
- Omnizart's Windows support is unstated; it depends on the Chordino Vamp plugin for chroma, so the Vamp setup caveats apply.
- No source gives accuracy figures for Essentia's ChordsDetection or for madmom's chord models on the current MIREX test sets.

## Key Question 2: Which perform best on rock/pop full mixes with distorted guitars?

### Takeaway
No benchmark isolates "distorted-guitar rock"; the closest public evidence is MIREX 2025's Billboard 2013 and Yamaha Balanced sets (Western pop/rock) where the deep models cluster at Root ~78-82 / MajMin ~76-81, and the literature consistently says distortion/dense mixes degrade chroma and especially 3rds/7ths. Practical mitigation is source separation or HPSS before ACR, which recent work (incl. the 2025 LLM-CoT paper) already builds in.

### Cited Findings
- "Distorted guitars smear the spectrum, making chord identification harder in dense full-band mixes"; "Solo piano, fingerstyle guitar, and string quartet recordings give near-perfect results because every audible pitch belongs to the harmony" — [Brizm chord detector page](https://brizm.dev/chord-detector/) (vendor page; treat as anecdotal)
- "Chroma features possess a considerable amount of robustness to changes in timbre and instrumentation" — [Jiang, Grosche, Konz, Mueller 2011](https://www.audiolabs-erlangen.de/content/05_fau/professor/00_mueller/03_publications/2011_JiangGroscheKonzMueller_ChordRecognitionEvaluation_AES42-Ilmenau.pdf)
- "chroma-CQT does comparatively poorly at identifying thirds and sevenths"; chord classifiers "perform poorly on rare chords" — [arXiv 2512.22621](https://arxiv.org/html/2512.22621v1)
- Harmonic/Percussive Source Separation "can suppress percussive sounds and emphasize harmonic sound components to improve accuracy in complex recordings" — [IJACSA 2025 Intelligent Guitar Chord Recognition](https://thesai.org/Downloads/Volume16No4/Paper_75-Intelligent_Guitar_Chord_Recognition.pdf)
- The 2025 LLM-CoT ACR pipeline explicitly feeds "music source separation, key detection, chord recognition, and beat tracking" outputs into GPT-4o and gains 1-2.77% MIREX — [arXiv 2509.18700](https://arxiv.org/abs/2509.18700)
- A student project "Automatic Chord Recognition by Music Source Separation" explores separating stems before chord recognition — [ko28 chord-transcription](https://ko28.github.io/chord-transcription/)
- MIREX 2025 Billboard 2013 (Western pop incl. rock): MD1 Root 81.35 / MajMin 79.15; YK1 81.01 / 78.10; ISMIR2019 baseline 78.61 / 76.39; Chordino 71.06 / 67.18 — [MIREX 2025 ACE Results](https://music-ir.org/mirex/wiki/2025:Audio_Chord_Estimation_Results)
- ChordFormer/CNN-BLSTM were trained with pitch-shift augmentation (-5..+6 semitones) on Isophonics/Billboard/MARL, i.e. rock/pop studio recordings — [arXiv 2502.11840 HTML](https://arxiv.org/html/2502.11840)

### Inferences
- For "Summer of '69" / "Pour Some Sugar On Me" (mostly power chords and major triads, straightforward progressions), a majmin-vocabulary model is sufficient; the main risk is 3rd ambiguity in power chords (no 3rd present) and distortion harmonics biasing toward 5ths/octaves. A large-vocab model would spend capacity on 7ths/extensions these songs rarely use.
- Running ACR on a Demucs-separated "other/guitar" stem or a drum-less (vocals+bass+other) mix is the cheapest way to reduce percussive smearing; models trained on full mixes (all of the above) still expect full-mix timbre, so evaluating both inputs is worth doing.
- The deep models trained on Billboard/Isophonics have seen 1980s rock production styles; Chordino/template methods have not been trained at all and will suffer most from distortion.

### Gaps
- No paper or benchmark found that reports ACR accuracy specifically on distorted-guitar rock subsets or on the two target songs.
- No study found comparing ACR accuracy on separated guitar stems versus full mixes with current models.

## Key Question 3: Which tools also provide beat/downbeat tracking for aligning chords to bars?

### Takeaway
madmom (DBN beat + RNN downbeat + bar tracking), Beat This! (CPJKU, transformer, pip, MIT, v1.1.0 April 2026) and BeatNet (CRNN + particle filter, pip, CC-BY-4.0) all give beats and downbeats in Python; Beat This! is the most current and cleanly packaged, and it can optionally use madmom's DBN post-processing. Essentia's ChordsDetectionBeats shows the "chord per beat segment" pattern natively.

### Cited Findings
- madmom: DBN beat tracking, RNN downbeat tracking, both with live-audio support, bar tracking added in 0.16 — [PyPI madmom](https://pypi.org/project/madmom/)
- Beat This!: official implementation of ISMIR 2024 "Accurate Beat Tracking Without DBN Postprocessing" (Foscarin, Schlueter, Widmer); `pip install beat-this`; PyTorch 2.0+; deps tqdm, einops, soxr, rotary-embedding-torch; ffmpeg for non-WAV; uses first GPU by default and falls back to CPU; outputs beat and downbeat lists, `.beats` export for Sonic Visualiser; transformer runs over overlapping 1500-frame (30 s) chunks; MIT — [beat_this GitHub](https://github.com/CPJKU/beat_this)
- Beat This! PyPI 1.1.0 released 2026-04-14; optional madmom DBN post-processing; optional PyTorch Lightning / mir_eval for evaluation — [PyPI beat-this](https://pypi.org/project/beat-this/)
- Beat This! issue #9: the madmom dependency "requires python<=3.9" (only relevant if you enable DBN post-processing with PyPI madmom) — [beat_this issue #9](https://github.com/CPJKU/beat_this/issues/9)
- BeatNet: `pip install BeatNet`; CC-BY-4.0; modes streaming / real-time / online / offline; returns numpy array (num_beats, 2) of beat time and downbeat flag; device 'cpu' / 'cuda' / 'mps'; depends on PyTorch, librosa, madmom (for inference), PyAudio; on Windows PyAudio must be installed from a pre-built wheel; v1.2.0+ ships training pipeline; ISMIR 2021 paper — [BeatNet GitHub](https://github.com/mjhydri/BeatNet)
- Beat-Transformer (Zhao et al.) is used by ChordMiniApp for beats alongside madmom — [Beat-Transformer GitHub](https://github.com/zhaojw1998/Beat-Transformer); [ChordMiniApp](https://github.com/ptnghia-j/ChordMiniApp)
- BEAST (ICASSP 2024) is an online/streaming transformer beat+downbeat tracker — [BEAST GitHub](https://github.com/WildHoneyPie/BEAST)
- Essentia `ChordsDetectionBeats` "estimates chords on segments between consecutive beats given their time positions as an additional input" — [Essentia tutorial](https://essentia.upf.edu/tutorial_tonal_chords.html)
- madmom has an open issue requesting beat-aligned chord output (#403), i.e. it does not do this natively — [madmom issue #403](https://github.com/CPJKU/madmom/issues/403)
- Mackenzie 2025 "enhances interpretability by incorporating beat detection into model outputs" — [arXiv 2512.22621](https://arxiv.org/abs/2512.22621)

### Inferences
- Beat This! (pip, PyTorch, MIT, 2026 release, Windows-friendly) plus any .lab-producing chord model is the simplest stack: snap chord boundaries to the nearest beat and group by downbeat to get per-bar chords.
- BeatNet pulls in madmom (and PyAudio) as hard dependencies, inheriting madmom's install problems on Windows; Beat This! only needs madmom optionally.

### Gaps
- Numerical beat/downbeat F-measures for Beat This! vs BeatNet vs madmom on rock datasets were not extracted (the README refers to tables in the paper).
- Whether Beat This! outputs tempo or time-signature explicitly is not stated; downbeats can be used to infer meter.

## Key Question 4: How do these handle key detection and chord simplification (power chords / 7ths -> ukulele-friendly voicings)?

### Takeaway
Key detection is available in madmom (CNN key model), Essentia (KeyExtractor, not on Windows) and commercially from music.ai; no open ACR package does ukulele-oriented simplification, but `mir_eval.chord` and `madmom.evaluation.chords` provide the standard reduction functions (triads/tetrads/majmin) that map 7ths, extensions and inversions down to playable triads.

### Cited Findings
- madmom `CNNKeyRecognitionProcessor` recognises the global key with a CNN, from "Genre-Agnostic Key Classification with Convolutional Neural Networks"; CLI `KeyRecognition` — [madmom key.py](https://github.com/CPJKU/madmom/blob/main/madmom/features/key.py); [madmom bin/KeyRecognition](https://github.com/CPJKU/madmom/blob/main/bin/KeyRecognition)
- Essentia `KeyExtractor` chains FrameCutter, Windowing, Spectrum, SpectralPeaks, HPCP and Key; a practitioner notes there is "no pretrained key model in Essentia" — [Essentia ISMIR 2013 paper](https://www.justinsalamon.com/uploads/4/3/9/4/4394963/bogdanov_essentia_ismir13.pdf); [dev.to BPM/key post](https://dev.to/dipak8080/bpm-detection-from-42-to-85-accuracy-with-a-pretrained-model-20al)
- music.ai Chords returns a `key` string (e.g. "C Major", "A minor") alongside the chord timeline and offers "Simple Pop" vs "Complex Pop" vocabularies with bass detection — [music.ai Chords](https://music.ai/modules/transcription/chords/)
- `mir_eval.chord` provides `root`, `thirds`, `majmin`, `triads`, `sevenths`, `tetrads`, `mirex` comparison levels; `triads()` treats ('A:7','A:maj') as equivalent, i.e. it reduces to root + quality through the 5th — [mir_eval chord docs](https://mir-eval.readthedocs.io/latest/api/chord.html)
- `madmom.evaluation.chords.reduce_to_triads()` and `reduce_to_tetrads()` reduce chord labels to triads/tetrads — [madmom evaluation.chords docs](https://madmom.readthedocs.io/en/v0.16.1/modules/evaluation/chords.html)
- Standard vocabulary reduction discards inversions and added/suppressed notes stepwise, e.g. "D-flat:maj(9)/3 -> D-flat:maj/3 -> D-flat:maj" — [McFee & Bello ISMIR 2017](https://archives.ismir.net/ismir2017/paper/000077.pdf)
- Chordino's vocabulary is governed by its `chord.dict`; editing the dictionary restricts output to whatever chord types you list — [isophonics.net/nnls-chroma](http://www.isophonics.net/nnls-chroma)
- crema outputs inversions (bass) in its 602-class vocabulary; ChordFormer and the ISMIR2019 model decompose chords into root/bass/7th/9th/11th/13th components, so extensions can be dropped at decode time — [crema models](https://crema.readthedocs.io/en/latest/models.html); [arXiv 2502.11840 HTML](https://arxiv.org/html/2502.11840)
- Python music-theory helpers for building chords from names: mingus (triads/sevenths/extended) — [mingus chords tutorial](https://bspaans.github.io/python-mingus/doc/wiki/tutorialChords.html)

### Inferences
- A pipeline step "parse Harte label -> reduce with mir_eval/madmom to triad -> drop bass -> look up ukulele voicing" covers the simplification need; for a majmin-only model (madmom, Omnizart, autochord) the reduction is already implicit, and the only issue left is power chords, which these models will label as major or minor by context — a key estimate (madmom CNN key) can be used to pick the diatonic quality.
- Only madmom offers key detection natively on Windows (via git install); Essentia's key extractor requires WSL.

### Gaps
- No open-source library found that specifically maps chords to ukulele-friendly voicings; this must be written (chord-name -> fingering table).
- No accuracy figures found for madmom's CNN key model versus Essentia's KeyExtractor on rock/pop.

## Key Question 5: Practical issues (madmom numpy/Python breakage, Vamp on Windows, Essentia on Windows)?

### Takeaway
madmom's PyPI release is 7 years old and fails on Python >=3.10 and NumPy >=1.20; the git main branch (0.17.dev0, last commit Aug 2024) fixes both but must be compiled with Cython on Windows. Chordino works on Windows only if you install the Vamp Plugin Pack binaries and point `VAMP_PATH` at them. Essentia has no Windows Python bindings at all (WSL/Docker required). PyTorch-based models (BTC, ISMIR2019, ChordMini, Beat This!) have no Windows-specific blockers.

### Cited Findings
- madmom 0.16.1 imports `MutableSequence` from `collections`, removed in Python 3.10, causing ImportError; fix is `pip install git+https://github.com/CPJKU/madmom` (0.17.dev0), Python <=3.9, or patching `processors.py` to `collections.abc` — [madmom issue #502](https://github.com/CPJKU/madmom/issues/502); [madmom issue #509](https://github.com/CPJKU/madmom/issues/509)
- madmom pip version uses `np.float`, deprecated in NumPy 1.20 and later removed; downgrading NumPy below 1.20 then breaks Cython; installing from GitHub (`setup.py`) resolved it (March 2024); "the main developer doesn't use Windows" — [madmom discussion #536](https://github.com/CPJKU/madmom/discussions/536)
- Last upstream commit 2024-08-25 "CI and NumPy compatibility updates (#540)" — [madmom commits](https://github.com/CPJKU/madmom/commits/main)
- Downstream projects hit the same failure: crepe_notes issue "Fresh install cannot be imported: madmom build/runtime failure" — [crepe_notes issue #15](https://github.com/xavriley/crepe_notes/issues/15); Beat This! issue "madmom dependency requires python<=3.9" — [beat_this issue #9](https://github.com/CPJKU/beat_this/issues/9)
- madmom model files are CC BY-NC-SA 4.0; commercial use needs permission from Gerhard Widmer — [PyPI madmom](https://pypi.org/project/madmom/)
- chord-extractor bundles Chordino only for Linux 64-bit; on Windows "download the Vamp plugin pack installer" and set `VAMP_PATH`; numpy must be pre-installed for the `vamp` dependency's setup.py — [chord-extractor GitHub](https://github.com/ohollo/chord-extractor)
- Chordino provides "readily compiled binaries for Windows and Mac OSX (Intel)" — [isophonics.net/nnls-chroma](http://www.isophonics.net/nnls-chroma)
- Essentia: "Python bindings are not yet supported on Windows"; use MinGW cross-compile or WSL — [Essentia installing](https://essentia.upf.edu/installing.html); PyPI wheels exist only for manylinux and macOS — [PyPI essentia](https://pypi.org/project/essentia/)
- BeatNet on Windows: PyAudio must be installed from a pre-built wheel because pip install may fail — [BeatNet GitHub](https://github.com/mjhydri/BeatNet)
- Basic Pitch supports Windows explicitly; Python 3.7-3.11 (Mac M1 needs 3.10); TensorFlow <=2.15 if the TF backend is used — [PyPI basic-pitch](https://pypi.org/project/basic-pitch/)
- Omnizart is "incompatible for ARM-based MacOS" and depends on the Chordino Vamp plugin for chroma — [PyPI omnizart](https://pypi.org/project/omnizart/); [Omnizart chord docs](https://music-and-culture-technology-lab.github.io/omnizart-doc/chord/api.html)
- autochord has had no release since 2021-10-07 and runs the NNLS-Chroma Vamp plugin plus TensorFlow — [PyPI autochord](https://pypi.org/project/autochord/)

### Inferences
- On Windows 11 the madmom path is: install Visual Studio Build Tools (for the Cython extension compile), `pip install cython numpy`, then `pip install git+https://github.com/CPJKU/madmom`; pin to a Python the Aug-2024 main branch has been tested on (3.9-3.11 most likely). Isolate it in its own venv so its numpy pin does not conflict with PyTorch models.
- The Vamp route (Chordino, autochord, Omnizart) adds a non-Python native dependency that must be installed per machine and located through `VAMP_PATH`; this is manageable but is the main source of "works on my machine" failures.
- Pure-PyTorch models (BTC, ISMIR2019 Chord-CNN-LSTM, ChordMini, Beat This!) are the cleanest fit for Windows: they need only `torch`, `librosa` and a git checkout with checkpoints, and run on CPU for a 4-minute song.

### Gaps
- No source confirms which Python versions madmom main (0.17.dev0) has been tested against after the Aug-2024 NumPy fixes, nor whether it builds with NumPy 2.x.
- No source confirms a successful `pip install vamp` on Windows with recent Python; the `vamp` package needs a C++ build or wheel, which was not verified.
- Flagged as abandoned/dormant (no release >= 3 years): autochord (2021), crema (0.2.0, c. 2022), BTC-ISMIR19 and music-x-lab ISMIR2019 repos (2019 code, still runnable), chord-extractor (26 commits, no recent activity visible), madmom PyPI (2018; git main semi-maintained to Aug 2024).
