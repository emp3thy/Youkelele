# Verification pass: papers, libraries and package metadata

Compiled 2026-10-03. Scope: items flagged "Unverified"/"Gaps" in `reports/YouTube to ukulele tab pipeline.md`, `reports/Ukulele tab pipeline gap analysis.md` and the research notes, restricted to academic papers, library/repo facts and package metadata. Product/help pages, tab sites and forums were left to the other agent. All URLs accessed 2026-10-03. PDFs were downloaded and text-extracted with pypdf; GitHub/PyPI facts come from the public JSON APIs. Status tags: CONFIRMED (prior claim holds), CHANGED (prior claim or assumption must be revised), ADDS (new fact where there was only a gap), STILL UNKNOWN.

Sections 2, 4, 5, 6, 9, 10, 12 and the F-K items of section 13 were researched by delegated sub-tasks and merged here; sections 4-6 are reconstructed from that sub-task's hand-back report after its longer notes file was lost in a merge step (all numbers and URLs preserved).

## Status summary

| # | Target | Status | One line |
|---|---|---|---|
| 1a | BTC results table | CONFIRMED | Table 1 extracted: BTC 83.8/82.7 (maj-min root/majmin), LV tetrads 65.5; CNN+CRF marginally best |
| 1b | Chord-CNN-LSTM (Jiang 2019) | ADDS | 301-class frame acc 0.7719; MIREX 2018 per-dataset WCSR recovered; Fig-4 bars not textual |
| 1c | ChordMini numbers | CHANGED | DAFx26 paper reports only relative gains (97-99% of teacher, then surpasses); code MIT |
| 1d | crema PyPI/licence | CHANGED | PyPI 0.2.0 (2022-04-21), licence ISC not BSD-2; TF>=2 / keras>=2.6 |
| 1e | madmom main Python/NumPy | CHANGED | main: py3.10-3.12, NumPy 2 fixes merged 2024-08; Cython>=3.1 build breaks (numpy.math); PRs #548/#559 unmerged; no PyPI release |
| 1f | vamp wheels Windows py3.11/3.12 | CHANGED | No wheels since 2015 (cp27 only), no conda-forge; build sdist against Vamp SDK |
| 2 | YourMT3+ install/VRAM/Windows | CHANGED | Code only in Apache-2.0 HF Space (GitHub repo is a GPL-3 placeholder); Py>=3.9/torch>=2.2; no VRAM figure; no Windows statements |
| 2 | Transkun benchmark | CONFIRMED | MAESTRO V3: onset F1 0.9832, +offset 0.9349, +vel 0.9296; MIT; pip 2.0.1 |
| 2 | Harmonica (Sep 2026) | CHANGED | arXiv 2609.04640: instrument-agnostic note AMT, 26.3K-param nano beats Basic Pitch by 14.6 pp; no code yet |
| 2 | Fretiq | CHANGED | arXiv 2607.18303: monophonic string classifier (87.8% held-out), not tab transcription; MIT |
| 2 | Timbre-Trap | CONFIRMED | Dormant since 2024-05, MIT, weights tt-orig.pt on HF; no v2 |
| 3a | PyGuitarPro GP6/7/8 | CHANGED | Not supported, maintainer declined; PRs #58/#62/#63 closed unmerged; kaizenman gpif-support fork exists |
| 3b | music21 tab export / UkeleleFretBoard | CONFIRMED | #778 open, PR #1169 unmerged (to be closed 2026-09); UkeleleFretBoard exists (G4 C4 E4 A4) |
| 4 | Cemgil & Kappen / Cemgil-Desain | CHANGED | arXiv id is 1106.4863; ~5% edit-distance error on 12-pianist Beatles MIDI |
| 4 | Raphael 2001 | CONFIRMED | Markov rhythm+tempo model; no headline accuracy |
| 4 | Friberg & Sundberg 1995 | CONFIRMED | 6 ms below 240 ms IOI, 2.5% above (Crossref abstract) |
| 4 | Nakamura HMM/MRF | CHANGED | Both TASLP 2017; code as anonymous GitHub-Pages zips, no licence |
| 4 | MDPI time-signature survey | ADDS | Sensors 2021: 6/8 at 41-45%, 3-vs-4-vs-6 ~28% error |
| 4 | Wachter et al. code | CONFIRMED | No code or weights |
| 4 | GM2 ukulele patch | CONFIRMED | PC 25, bank MSB 121 LSB 1 |
| 5 | Weiss/Schreiber/Mueller 2020 | CHANGED | SWD only; CNN 73% neither-split, 96% version-split; code key-cnn |
| 5 | Ding & Weiss EUSIPCO 2024 | CHANGED | "Towards Robust Local Key Estimation..." OctaveNet 77.75% neither-split; no code |
| 5 | Papadopoulos & Peeters 2012 | CONFIRMED | 2-bar windows; 80.22% key label acc (DAFx 2009 numbers) |
| 5 | Cho & Bello 2014 | STILL UNKNOWN | No open PDF; only qualitative claims via citing papers |
| 6 | Hockman & Fujinaga / Gkiokas / Seyerlehner | CONFIRMED | 99.4% fast/slow; 75.93% ballroom Acc1; 78.51% ballroom |
| 6 | Bock 2020 | CHANGED | Authors Bock & Davies (no Knees); abstract and tempo accuracies recovered |
| 6 | Dittmar 2015 / Marchand & Peeters 2015 | CONFIRMED | Onset-based swing ratios correlate only 0.66; LLACF better; GTZAN-rhythm released |
| 7a | BS-RoFormer-SW provenance/licence | CHANGED | "SW = shared weights", group-trained, unnamed authors, no licence; original HF host deleted |
| 7b | APSIPA 2025 numbers | ADDS | +0.20 WCSR triads (75.52 -> 75.72) on 485 songs; boosting bass alone hurts |
| 7c | Ko UW-Madison | CONFIRMED | Page live; trained-on-stems model worse; plots only |
| 7d | Transcription F1 on Demucs guitar stems | STILL UNKNOWN | No paper found |
| 8a | Jam-ALT WER table | ADDS | Whisper v3 35.5 all / 37.7 EN; +HTDemucs worsens; AudioShake 26.0/22.1 |
| 8b | Whisper turbo singing WER | ADDS (low confidence) | Non-reviewed 12-song report: turbo 22.8% on Demucs vocals |
| 8c | Wang & Jang repo / MIR-ST500 | CONFIRMED | YouTube links + yt-dlp script; cached audio by email |
| 8d | SVT F1 on English | STILL UNKNOWN | STARS/VocalParse report Chinese only |
| 9 | Murgul ISMIR 2025 / Lukoianov WASPAA 2025 code | CONFIRMED | Nothing released (Murgul); 8 excerpts + downbeat script only (Yousician) |
| 9 | Phithak 2015 | CHANGED | Phithak, Angskun & Angskun, Information 18(2) 2015; 10 songs, 82.6% F; features unknown |
| 10 | Piano-to-guitar / LooPy / SymPAC / Arranger | CHANGED | None is a guitar arranger; only SMC 2024 Sakai et al. lead-sheet-to-fingerstyle |
| 10 | Mitsou 2024 class list | ADDS | 9 techniques, 549 recordings; Zenodo CC BY 4.0 vs article CC BY-NC-ND |
| 11a | GPL FAQ subprocess vs linking | CONFIRMED | #MereAggregation / #GPLPlugins quoted |
| 11b | allin1 NATTEN Windows | CONFIRMED | Build from source; PR #39 pure-PyTorch replacement pending |
| 11c | Beat This! madmom | CONFIRMED | madmom only for optional --dbn |
| 11d | audio-separator Windows CUDA | CONFIRMED | CUDA 11.8/12.2; ORT CUDA-lib mismatch main failure |
| 11e | Demucs torchaudio/TorchCodec | CHANGED | Demucs 4.1.0 (2026-07-11) dropped torchaudio for inference (sphn, Windows wheels) |
| 11f | Essentia Windows wheels | CONFIRMED | None, ever |
| 12 | SynthTab / GOAT licences | CONFIRMED | CC BY-NC 4.0 both; GOAT request-only Zenodo restricted (5.1 TB) |
| 12 | Ukulele audio datasets 2025-26 | ADDS | None new; HF Basic-Chord-Ukulele-Data (1,960 clips, CC BY-NC) is the only chord set |
| 12 | FreePats ukulele | CONFIRMED | CC0 1.0; tenor Flight Fireball, C4-C6, 2026-08-11 |
| 13 | Omnizart pins | CHANGED | Revived 0.6.3 (2026-05-31), Py 3.8-3.14; Windows still unsupported |
| 13 | Pati & Lerch | CHANGED | AES Semantic Audio 2017; F 67.3%, 60 songs |
| 13 | Camacho 2022 / Deng & Kwok 2016 | CHANGED | Camacho 90.38% MajMin+Bass (manual boundaries); Deng inversions ~20% WCSR |
| 13 | DrumFormer | STILL UNKNOWN | No such model; only a Voxengo plug-in |
| 13 | Sayegh 1989 | CONFIRMED | Layered Viterbi cost model via citing papers |
| 13 | librosa.pyin / Tony pYIN | CONFIRMED | 0.11.0 doc URL works; Tony HMM parameters recovered |
| 13 | CASD (Koops 2019) agreement | ADDS | Pairwise WCSR root 0.76, majmin 0.73, sevenths 0.60; alpha <= 0.667 except root |

---

## 1. Chord recognition papers and packages

### 1a. BTC (Park et al., ISMIR 2019) exact results table — CONFIRMED / ADDS

Previously unverified: the chord-recognition note said "BTC paper's exact per-metric numbers on Isophonics/RWC/USPop could not be extracted (PDF parsing failed twice)".

Found (from the arXiv PDF, Table 1, "WCSR scores averaged over the same 5 folds", std-devs in parentheses) — [arXiv 1907.02698 PDF](https://arxiv.org/pdf/1907.02698):

| Model | maj-min Root | maj-min Maj-min | LV Root | LV Thirds | LV Triads | LV Sevenths | LV Tetrads | LV Maj-min | LV MIREX |
|---|---|---|---|---|---|---|---|---|---|
| CNN | 83.6 (1.3) | 81.8 (1.2) | 83.5 (1.4) | 80.4 (1.2) | 75.5 (0.6) | 71.5 (1.9) | 65.2 (1.0) | 81.9 (1.4) | 79.8 (0.7) |
| CNN+CRF | 84.0 (1.3) | 83.1 (1.4) | 83.7 (1.5) | 81.1 (1.4) | 76.3 (0.8) | 71.3 (1.9) | 65.7 (1.6) | 82.1 (1.5) | 81.8 (1.1) |
| CRNN | 83.4 (0.8) | 82.3 (0.9) | 82.9 (1.1) | 80.1 (1.0) | 75.3 (0.7) | 71.3 (1.9) | 65.2 (0.9) | 81.5 (1.3) | 79.9 (0.8) |
| CRNN+CRF | 83.3 (0.8) | 82.3 (1.0) | 82.7 (1.2) | 79.7 (0.9) | 74.8 (0.5) | 69.5 (2.0) | 63.9 (1.0) | 80.7 (1.4) | 80.2 (1.0) |
| BTC | 83.8 (1.0) | 82.7 (1.0) | 83.5 (1.2) | 80.8 (1.0) | 75.9 (0.5) | 71.8 (1.7) | 65.5 (0.9) | 82.3 (1.2) | 80.8 (0.9) |
| BTC+CRF | 83.9 (1.0) | 83.1 (1.1) | 83.5 (1.2) | 80.7 (1.1) | 75.7 (0.5) | 70.7 (2.0) | 64.8 (1.1) | 81.7 (1.4) | 81.4 (0.9) |

- Data: 221 Isophonics songs (171 Beatles, 12 Carole King, 20 Queen, 18 Zweieck) + 65 Robbie Williams + 185 UsPop2002 = 471 songs; 5-fold CV; audio "collected from online music service providers (e.g. Melon)" and labels manually shifted to match. Features: CQT, 6 octaves from C1, 24 bins/octave, hop 2048 at 22,050 Hz, 10 s windows with 5 s overlap; pitch augmentation -5..+6 semitones. Vocabularies: maj-min (25 classes) and large vocabulary (170 classes: 14 qualities x 12 roots + X + N). Metric: WCSR via mir_eval — same source.
- Paper's own reading: "Among the models without a CRF decoder, BTC showed the best performance for all metrics. Including models with a CRF decoder, CNN+CRF obtained the best result in most of the metrics." — same source.

Report impact: confirms the report's "BTC ~ 83-84% root, ~82-83% maj-min, ~65% tetrads on 5-fold Isophonics+RW+USPop" framing; adds the exact table and the caveat that CNN+CRF is marginally better on most metrics.

### 1b. Chord-CNN-LSTM (Jiang, Chen, Li, Xia, ISMIR 2019) results — ADDS (partly STILL UNKNOWN)

Previously unverified: results of "Large-vocabulary chord transcription via chord structure decomposition" were not extracted.

Found:
- Paper: Junyan Jiang, Ke Chen, Wei Li, Gus Xia, ISMIR 2019 pp. 644-651 — [ISMIR archive PDF](http://archives.ismir.net/ismir2019/paper/000078.pdf); [webis anthology entry](https://ir.webis.de/anthology/2019.ismir_conference-2019.78).
- Setup: 1,217 songs (Isophonics + Billboard + MARL, Humphrey & Bello collection), 5-fold CV with 60/20/20 splits as in the CGRU paper; CQT at 22,050 Hz, hop 512, C1-C7, 36 bins/octave (252 bins); pitch-shift augmentation -5..+6 — same PDF.
- Small-vocabulary comparison (Root, Thirds, Maj-Min, Triads, Sevenths, Tetrads, MIREX) against ACE18, CGRU, KHMM, DNN and Chordino is given only as a bar chart (Figure 4, "Comparison of median weighted recall scores", y-axis 0.35-0.90); the text states "Our system outperforms the baseline systems in all metrics". Exact bar values are not in the extractable text — same PDF.
- Large-vocabulary numbers that ARE in the text (Table 2, 301-class vocabulary: 25 qualities x 12 roots + N): no re-weighting: frame-wise acc 0.7719, class-wise acc 0.3475; re-weighting (gamma, w_max) = (0.3,10): 0.7609 / 0.3745; (0.5,10): 0.7459 / 0.4022; (0.7,20): 0.7146 / 0.3738; (1.0,20): 0.6577 / 0.3832 — same PDF.
- MIREX 2018 figures for the same authors' submission (JLCX1/JLCX2, "Junyan Jiang, Ke Chen, Wei Li, Guangyu Xia"): Isophonics2009 JLCX1 Root 86.75, MajMin 86.25, MajMinBass 84.44, Sevenths 75.87, SeventhsBass 74.39; Billboard2012 JLCX2 83.60 / 83.31 / 82.01 / 71.26 / 70.11; Billboard2013 JLCX2 79.38 / 77.92 / 76.74 / 64.22 / 63.20; RWC-Popular JLCX1 87.11 / 86.71 / 84.93 / 73.78 / 72.17; USPOP2002 JLCX1 85.66 / 84.89 / 82.95 / 75.08 / 73.35 — [MIREX 2018 ACE results](https://music-ir.org/mirex/wiki/2018:Audio_Chord_Estimation_Results).
- Code and pretrained weights: official repo `music-x-lab/ISMIR2019-Large-Vocabulary-Chord-Recognition`, CLI `python3 chord_recognition.py audio out.lab [chord_dict]` with dictionaries `submission` (default), `ismir2017`, `full`; re-weighted models on Google Drive — [repo README](https://github.com/music-x-lab/ISMIR2019-Large-Vocabulary-Chord-Recognition).

Report impact: adds concrete numbers (MIREX 2018 per-dataset WCSR, 301-class frame accuracy 77.2%); the small-vocab Figure-4 bars remain unreadable from text (STILL UNKNOWN for exact values).

### 1c. ChordMini paper numbers — CHANGED (numbers are relative, not absolute)

Previously unverified: "ChordMini paper numbers".

Found:
- Paper: "Enhancing Automatic Chord Recognition via Pseudo-Labeling and Knowledge Distillation", Nghia Phan, Rong Jin, Gang Liu, Xiao Dong; arXiv 2602.19778, v1 23 Feb 2026, v5 3 Jul 2026, "Accepted to DAFx26". Abstract numbers: BTC teacher pseudo-labels "over 1,000 hours of diverse unlabeled audio"; students trained only on pseudo-labels reach "about 99% of the teacher's performance" (BTC student) and "about 97%" (2E1D); after Stage 2 fine-tuning with selective distillation the BTC student "consistently surpasses both the traditional supervised learning baseline and the original pre-trained teacher model" — [arXiv abs 2602.19778](https://arxiv.org/abs/2602.19778). The abstract gives no absolute WCSR.
- Code: `ptnghia-j/ChordMini` ("Code for paper: Enhancing Automatic Chord Recognition via Pseudo-Labeling and Knowledge Distillation"), MIT, last push 2026-06-11, 24 stars; the app `ptnghia-j/ChordMiniApp`, MIT, 403 stars, last push 2026-07-30 — [GitHub search API](https://api.github.com/search/repositories?q=ChordMini+user:ptnghia-j); [ChordMiniApp](https://github.com/ptnghia-j/ChordMiniApp).
- The app uses "Beat-Transformer, Chord-CNN-LSTM, and BTC models with intelligent fallback strategies" — [Devpost project story](https://devpost.com/software/chord-mini).

Report impact: changes wording: ChordMini's published gains are relative to its BTC teacher (97-99% then "surpasses"), not an absolute accuracy figure; cite the DAFx26 acceptance.

### 1d. crema PyPI / licence status — CHANGED (licence is ISC on PyPI, not BSD-2)

Previously unverified: "crema's release date, Python/TensorFlow version pins and Windows installability could not be verified"; the table said "BSD-2-Clause".

Found — [PyPI JSON crema](https://pypi.org/pypi/crema/json):
- Latest 0.2.0 uploaded 2022-04-21 (0.1.0: 2017-10-12). `license` field: "ISC". `requires_python`: empty. Dependencies: six, librosa>=0.8, jams>=0.3, scikit-learn>=0.18, keras>=2.6, tensorflow>=2.0, mir-eval>=0.5, pumpp>=0.6, h5py>=2.7 (extras: training = pescador>=2.0.1, muda).
- No wheel-platform restriction (pure Python), so Windows installability hinges on TensorFlow (which ships Windows CPU wheels) and on pumpp/jams compatibility with current librosa; no newer release since 2022.

Report impact: changes licence label to ISC (BSD-equivalent permissive); confirms unmaintained since April 2022 and TF2/Keras dependency.

### 1e. madmom main-branch Python/NumPy support and NumPy 2 — CHANGED (partly)

Previously unverified: "madmom's NumPy 2 and Python 3.12 build status is unknown".

Found:
- PyPI release is still 0.16.1 (sdist only, uploaded 2018-11-14; no Python/NumPy pins in metadata) — [PyPI JSON madmom](https://pypi.org/pypi/madmom/json). Beat This! README: "the current version on PyPI only supports Python<3.10 and numpy<1.20" — [Beat This! README](https://github.com/CPJKU/beat_this).
- main branch (version string `0.17.dev0`): `install_requires` = numpy>=1.13.4, scipy>=1.13, mido>=1.2.6; classifiers list Python 3.10, 3.11, 3.12; licence "BSD, CC BY-NC-SA" — [setup.py](https://raw.githubusercontent.com/CPJKU/madmom/main/setup.py). `pyproject.toml` build-system requires setuptools, wheel, cython>=0.25, **numpy>2** — [pyproject.toml](https://raw.githubusercontent.com/CPJKU/madmom/main/pyproject.toml). CI matrix: Python 3.9-3.12 on ubuntu-latest — [ci.yml](https://raw.githubusercontent.com/CPJKU/madmom/main/.github/workflows/ci.yml).
- Last commit 2024-08-25 "CI and NumPy compatibility updates (#540)" (by jpauwels): "made some changes to fix compatibility with NumPy 2 ... removing Python 3.8 ... added Python 3.11 and 3.12" — [commits API](https://api.github.com/repos/CPJKU/madmom/commits?per_page=12); [PR #540](https://github.com/CPJKU/madmom/pull/540).
- Open breakage since: issue #547 "Cant import madmom" (2025-05-10) — `pip install madmom` fails compiling `beats_crf.pyx`: "'numpy/math.pxd' not found" — [issue 547](https://github.com/CPJKU/madmom/issues/547). PR #548 (2025-05-12, still open) "replace deprecated numpy.math use with libc.math": "builds now fail due to numpy missing from Cython 3.1 wheels" — [PR 548](https://github.com/CPJKU/madmom/pull/548). PR #559 (2026-05-09, open) "Python 3.14 / NumPy 2.4+ compatibility": fixes `distutils.extension` import ("Python 3.12 removed distutils") and a `VisibleDeprecationWarning` when unpickling the shipped models ("NumPy 2.4 emits VisibleDeprecationWarning (and NumPy 3.x is expected to make this an error) when np.dtype is constructed with an int align argument") — [PR 559](https://github.com/CPJKU/madmom/pull/559). Issue #553 "Can we get a new release?" (2025-06-24) has no comments — [issue 553](https://github.com/CPJKU/madmom/issues/553). Repo last pushed 2026-03-20, 1,719 stars — [repo API](https://api.github.com/repos/CPJKU/madmom).

Report impact: changes the engineering note: `pip install git+https://github.com/CPJKU/madmom` runs on Python 3.10-3.12 with NumPy 2.x (as of PR #540), but building from source currently fails with Cython 3.1+ unless PR #548/#559 patches are applied (pin `cython<3.1` or patch `numpy.math` to `libc.math`); Python 3.13/3.14 and NumPy 2.4 need PR #559. No PyPI release in sight.

### 1f. `pip install vamp` wheels for Windows / Python 3.11-3.12 — CHANGED (no wheels)

Previously unverified: whether Vamp host bindings install on Windows Python 3.11/3.12.

Found:
- PyPI `vamp` 1.1.0, MIT, uploaded 2015-07-08; the only files are `vamp-1.1.0-cp27-none-win32.whl`, `vamp-1.1.0-cp27-none-macosx_10_10_x86_64.whl` and the sdist; releases 1.0.0-1.1.0 only; no `requires_python` — [PyPI JSON vamp](https://pypi.org/pypi/vamp/json). The package is "a native-code extension ('vampyhost') that provides a low-level wrapper for the Vamp plugin SDK" — same page.
- Upstream `c4dm/vampy-host` last pushed 2023-08-12; setup.py still `version = '1.1.0'`, classifiers list Python 2 and 3 — [repo API](https://api.github.com/repos/c4dm/vampy-host); [setup.py](https://raw.githubusercontent.com/c4dm/vampy-host/master/setup.py).
- No conda-forge package named `vamp` or `vamphost` exists — [anaconda.org API vamp](https://api.anaconda.org/package/conda-forge/vamp), [vamphost](https://api.anaconda.org/package/conda-forge/vamphost) (both return no package).

Report impact: changes: on Windows with Python 3.11/3.12 `pip install vamp` must compile the 2015 sdist against the Vamp SDK with MSVC (no binary wheels, no conda package); treat Chordino-via-vamp as a build-from-source dependency or avoid it.

---

## 2. Note transcription tools: YourMT3+, Transkun, Harmonica, Fretiq, Timbre-Trap

(Verified by a delegated sub-task; items A-E are target 2, items F-K are target 13.)

### A. YourMT3+ (mimbres/YourMT3) — CHANGED
Previously unverified: install instructions (pip/conda, Python, torch), inference VRAM, Windows notes/issues, checkpoint download/licence, Hugging Face Space.
Found:
- The GitHub repo contains only `LICENSE` and `README.md` (no code); repo licence is GPL-3.0; 247 stars; last push 2024-11-29. The README's "Code" link points to an issue comment, labelled "(pre-release)". — [GitHub API](https://api.github.com/repos/mimbres/YourMT3), [README](https://raw.githubusercontent.com/mimbres/YourMT3/main/README.md), [contents](https://api.github.com/repos/mimbres/YourMT3/contents/)
- Official install instructions (author comment, 2024-07-29): "Assuming you have any environments Python>=3.9 and PyTorch>=2.2 installed... `git lfs install` / `git clone https://huggingface.co/spaces/mimbres/YourMT3` / `cd YourMT3` / `pip install -r requirements.txt` / `apt-get install sox # only required for GuitarSet preprocessing...`"; "Model checkpoints are located in `amt/logs/2024/.../checkpoints`". No pip package or conda env: "it would be most convenient to make it a command-line tool with a PyPI package, but that's unlikely to happen anytime soon." — [issue #2 comment](https://github.com/mimbres/YourMT3/issues/2#issuecomment-2255643217), [issue #5](https://github.com/mimbres/YourMT3/issues/5)
- HF Space `requirements.txt` pins only `transformers==4.45.1` and `numpy==1.26.4`; torch/torchaudio unpinned with `--extra-index-url https://download.pytorch.org/whl/cu113`; `lightning>=2.2.1`. A user reported failures with "python3.10 and torch 2.4.1" because "the specific version of each module is not offered"; the author's fix for a Colab crash was `pip install transformers==4.45.1`. — [HF requirements.txt](https://huggingface.co/spaces/mimbres/YourMT3/raw/main/requirements.txt), [issue #15](https://github.com/mimbres/YourMT3/issues/15)
- Inference VRAM: not stated anywhere in README or issues. The only hardware figures are for training: "`-bsz 10 10` ... Suitable for GPUs with 3-40GB of memory, such as RTX4090 or A100 (40GB)" and a user OOM on an RTX 4090 24 GB with the MoE config (author: "if you run into OOM errors, try `-bsz 9 9`"). The HF Space runs on "Zero" (ZeroGPU) with `precision = '16'` for inference ("FP Precision | BF16-mixed for training, FP16 for inference"); the author recommends `bsz=8` style batched decoding and notes "The output sequence maxes at 1,024 tokens". — [issue #2 comments](https://github.com/mimbres/YourMT3/issues/2#issuecomment-2342031869), [HF app.py](https://huggingface.co/spaces/mimbres/YourMT3/raw/main/app.py), [issue #17](https://github.com/mimbres/YourMT3/issues/17)
- Windows: GitHub issue search for "windows" in mimbres/YourMT3 returns `total_count: 0`; no Windows notes in README. Install instructions use `apt-get` and `aws s3 cp` (Linux-oriented). — [search API](https://api.github.com/search/issues?q=repo:mimbres/YourMT3+windows)
- Checkpoint licence: asked in issue #12 "Weights license"; author reply: "Apache 2.0! This is `Your` MT3". HF Space metadata: `license: apache-2.0`, `sdk: gradio`, `sdk_version: 4.39.0`. Checkpoints named in app.py include `mc13_256_g4_all_v7_mt3f_sqr_rms_moe_wf4_n8k2_silu_rope_rp_b80_ps2@model.ckpt` (YPTF.MoE+Multi). — [issue #12](https://github.com/mimbres/YourMT3/issues/12), [HF README](https://huggingface.co/spaces/mimbres/YourMT3/raw/main/README.md)
- Newer code: "The code used in the 2025 AMT Challenge (https://arxiv.org/abs/2603.27528) is availalble here: https://github.com/mimbres/AMT-challenge" (Apache-2.0, 4 stars, pushed 2025-10-26); best model selected by setting `default_mode_name="YPTF.MoE+Multi (noPS)"` on line 54 of `cfg_local.py`. — [issue #2 comment 2026-04-28](https://github.com/mimbres/YourMT3/issues/2#issuecomment-4334105214), [AMT-challenge API](https://api.github.com/repos/mimbres/AMT-challenge)
- Space page: "Running on Zero", 124 likes. — [HF Space](https://huggingface.co/spaces/mimbres/YourMT3)
Report impact: changes — code is not on GitHub (GPL-3.0 placeholder repo); code+weights live in the Apache-2.0 HF Space; Python>=3.9/PyTorch>=2.2, no inference-VRAM figure, no Windows support statements, no PyPI package.

### B. Transkun (Yujia-Yan/Transkun) — CONFIRMED (with exact numbers)
Previously unverified: README benchmark table, PyPI version/Python requirement, licence, Windows mentions.
Found:
- README "Model Cards" table, Maestro V3 rows (F1): Transkun V2: Note Onset F1 0.9832, Note Onset+Offset F1 0.9349, Onset+Offset+vel. F1 0.9296 (frame activation F1 0.953). Transkun V2 Aug: Onset 0.984, Onset+Offset 0.9314, +vel 0.9264. Transkun V2 No Ext (Maestro V3 No Ext): Onset 0.9833, Onset+Offset 0.8149, +vel 0.8109. "The default checkpoint shipped with the code/pip package is Transkun V2 No Pedal Ext." — [README](https://raw.githubusercontent.com/Yujia-Yan/Transkun/main/README.md)
- PyPI: version 2.0.1 (uploaded 2024-09-28), `requires_python >=3.6`, classifier "License :: OSI Approved :: MIT License", "Operating System :: OS Independent"; deps: ncls, pretty-midi, scipy, torchaudio, torch, mir-eval, pydub, seaborn, matplotlib, tensorboard, tqdm, torch-optimizer, sox, soxr, moduleconf (all unpinned). — [PyPI JSON](https://pypi.org/pypi/transkun/json), [setup.py](https://raw.githubusercontent.com/Yujia-Yan/Transkun/main/setup.py)
- Repo: MIT licence, 450 stars, last push 2024-11-22, 23 open issues. — [GitHub API](https://api.github.com/repos/Yujia-Yan/Transkun)
- Windows mentions (5 issues match): #4 "Metadata conflit when installing transkun package" ("on W10", open, 2022); #29 "Update request. (audioop library)": "on Windows, the installation is quite complicated. Since there is an audioop library, which was added in Python version 3.11 and removed in 3.13 ... replace 'audioop' with 'audioop-lts'" (open, 2025-07-10); #20 maintainer comment: "it says ffmpeg is not found ... Regarding windows path, you should be able to drag a file into the command line". README itself has no Windows note. — [issue search](https://api.github.com/search/issues?q=repo:Yujia-Yan/Transkun+windows), [#29](https://github.com/Yujia-Yan/Transkun/issues/29), [#4](https://github.com/Yujia-Yan/Transkun/issues/4)
Report impact: confirms — MAESTRO note-onset F1 0.983, note-with-offset 0.935, with velocity 0.930 (V2); MIT; pip `transkun` 2.0.1, Python >=3.6; Windows installs work but pydub/audioop friction on Python 3.13.

### C. "Harmonica" (Sep 2026) — CHANGED (exists; it is instrument-agnostic note transcription, not chord/harmony)
Previously unverified: existence/identity.
Found:
- arXiv:2609.04640, "Harmonica: Accurate and Lightweight Instrument-Agnostic Music Transcription", Longshen Ou, Héctor Martel, Joe Hennessy-Priest, Taemin Cho; submitted 4 Sep 2026; "Submission Venue: ICASSP 2027". Abstract: "a family of instrument-agnostic music transcription models built around multi-depth harmonic convolution ... the nano variant has only 26.3K parameters and runs at 1,622.5 times real time, yet achieves a frame F1 of 0.796 on the development set, 14.6 percentage points higher than Basic Pitch." — [arXiv abs](https://arxiv.org/abs/2609.04640)
- Table 1 (from PDF): #Param / xRT / MAESTRO OnP-Frm / GuitarSet OnP-Frm / EGDB OnP-Frm / GOAT OnP-Frm: nano 26.3K / 1622.5x / .880 .831 / .863 .852 / .805 .725 / .686 .738; medium 679K / 848.5x / .951 .902 / .896 .881 / .869 .764 / .720 .796; x-large 15.1M / 123.0x / .968 .922 / .909 .898 / .881 .773 / .750 .809. Baselines: YourMT3+ 48.5M / 45.6x / .957 .769 / .889 .835 / .827 .725 / .680 .703; Transkun 14.1M / 59.2x / .926 .874 / .873 .878 / .820 .726 / .638 .745; Basic Pitch 16.8K / 392.7x / .578 .577 / .776 .827 / .718 .658 / .553 .647; MT3 44.7M; PerceiverTF 3.5M; HPPNet-sp 1.2M; TriAD 635K. Timbre-Trap is not among the baselines. — [arXiv PDF](https://arxiv.org/pdf/2609.04640)
- Training data 1,385.5 h (MAESTRO, GuitarSet, GAPS, EGDB, GOAT, URMP-stem, Slakh-stem); test 145.0 h incl. MAPS. Code: no GitHub link; footnote "Transcription examples and additional details on experiments and on-device deployment are available at www.oulongshen.xyz/amt." GitHub search for "Harmonica music transcription" finds no release repo. — [arXiv HTML](https://arxiv.org/html/2609.04640), [GitHub search](https://api.github.com/search/repositories?q=Harmonica+music+transcription)
Report impact: changes — Harmonica is a multi-pitch/note AMT model (Sep 2026, ICASSP 2027 submission), not chord recognition; no public code yet; relevant as a tiny, fast Basic Pitch replacement.

### D. Fretiq — CHANGED (found; it is string classification, not tablature transcription)
Previously unverified: identity, accuracy, licence (earlier 404).
Found:
- arXiv:2607.18303 v2, "Fretiq: Browser-Native Electric Guitar String Classification via Engineered Spectral Features and Held-Out Free-Play Evaluation", Aadi Garg, published 2026-07-17, updated 2026-10-03; "17 pages, 7 tables, preliminary single-instrument system paper". Abstract: "a preliminary single-instrument, single-player browser-based string classification system using a 26-dimensional feature representation of frequency band energies, spectral statistics, and 13 Mel-Frequency Cepstral Coefficients. Across five seeds, a shuffled frame-level validation split yields 97.25 +/- 0.32 percent accuracy ... A recording-session-held-out evaluation yields 86.53 +/- 1.23 percent accuracy, closely matching an independently collected free-play evaluation (87.8 percent) ... showing shuffled validation substantially overestimates real generalization here." Pitch is from "the McLeod Pitch Method"; monophonic only. — [arXiv API](http://export.arxiv.org/api/query?id_list=2607.18303), [arXiv abs](https://arxiv.org/abs/2607.18303)
- Code: github.com/agarg0/fretiq (5 stars, created 2026-04-19, pushed 2026-08-10), README: "**97.1%** shuffled frame-level validation accuracy (322,215 frames, 6 strings, balanced)", "**87.8%** held-out free-play accuracy (103,000 frames, recorded after training)", "## License / MIT" (no LICENSE file in tree; GitHub API licence = null); requires "Chrome browser (Web Audio API + TensorFlow.js WebGL backend)" and `tensorflow-cpu==2.13.0`; training data "gitignored and not included". — [repo API](https://api.github.com/repos/agarg0/fretiq), [README](https://raw.githubusercontent.com/agarg0/fretiq/main/README.md)
Report impact: changes — Fretiq is a single-player monophonic string classifier (~87% held-out), not a tab transcriber; MIT per README; limited relevance to ukulele tab beyond the string-disambiguation idea.

### E. Timbre-Trap (sony/timbre-trap) — CONFIRMED (no follow-up found)
Previously unverified: repo status, weights, follow-ups.
Found:
- GitHub API: 44 stars, 1 fork, MIT licence, created 2023-09-12, last push 2024-05-05 (last commit 7afe7e9b "Merge pull request #6 ... A few post-publication improvements", 2024-05-05); 1 open issue (#7 "How to convert transcription output to MIDI", 2024-10-07). — [repo API](https://api.github.com/repos/sony/timbre-trap), [commits](https://api.github.com/repos/sony/timbre-trap/commits?per_page=3), [issues](https://api.github.com/repos/sony/timbre-trap/issues?state=all&per_page=20)
- Weights released: README: "Weights for the base model from our paper are available for download within our dedicated Hugging Face Space"; HF Space `cwitkowitz/timbre-trap` files include `models/tt-orig.pt` (space last modified 2026-01-15). Install: `pip install -r timbre-trap/requirements.txt` then `pip install -e timbre-trap/`; model config `sample_rate=22050, n_octaves=9, bins_per_octave=60, secs_per_block=3`. — [README](https://raw.githubusercontent.com/sony/timbre-trap/main/README.md), [HF Space API](https://huggingface.co/api/spaces/cwitkowitz/timbre-trap)
- Follow-ups: arXiv author query for Cwitkowitz lists, newest first: 2506.23371 "Investigating an Overfitting and Degeneration Phenomenon in Self-Supervised Multi-Pitch Estimation" (2025-06-29), 2503.02977 "HARP 2.0" (2025-03), 2402.15569 "Toward Fully Self-Supervised Multi-Pitch Estimation" (2024-02), then 2309.15717 Timbre-Trap. No paper titled "Timbre-Trap v2" or an explicit Timbre-Trap extension exists on arXiv; a web search also found none. — [arXiv API](http://export.arxiv.org/api/query?search_query=au:Cwitkowitz&sortBy=submittedDate&sortOrder=descending&max_results=15)
Report impact: confirms — dormant since May 2024, MIT, weights (tt-orig.pt) public; successor work is self-supervised MPE (2024-2025), not Timbre-Trap v2.

---

## 3. PyGuitarPro and music21 tablature

### 3a. Does PyGuitarPro 0.11 read GP6/7/8? — CHANGED (No, and the maintainer declined)

Previously unverified: "Could not confirm from a release note or changelog whether PyGuitarPro 0.11 reads GP6/7/8; the two 2026 issues are closed but the README was not updated."

Found:
- Repo description and README: "Read, write and manipulate GP3, GP4 and GP5 files." (370 stars, last push 2026-06-02) — [repo API](https://api.github.com/repos/Perlence/PyGuitarPro); [README](https://raw.githubusercontent.com/Perlence/PyGuitarPro/master/README.rst). Source tree contains only `src/guitarpro/gp3.py`, `gp4.py`, `gp5.py`, `io.py`, `iobase.py`, `models.py`, `utils.py` — no gpx/gpif module — [git tree API](https://api.github.com/repos/Perlence/PyGuitarPro/git/trees/master?recursive=1).
- Changelog 0.11 (2026-05-03): "Remove the unused MeasureClef enum", "Implemented reading and writing the track clef #57", "Fixed reading and writing accentuated note effects #56". 0.10.2 (2026-04-18) dropped Python 3.9. PyPI 0.11 requires Python >=3.10 — [CHANGES.rst](https://raw.githubusercontent.com/Perlence/PyGuitarPro/master/CHANGES.rst); [PyPI JSON](https://pypi.org/pypi/PyGuitarPro/json).
- The two 2026 "issues" are pull requests, both closed unmerged: PR #58 "Add GP6/7/8 (GPIF) support" by kaizenman (opened 2026-04-25 as draft: "Reader for GP6/7/8 (97 commits) ... 1847/1847 tests pass"), maintainer reply 2026-04-26: "Sorry, but I don't plan to introduce support for Guitar Pro 6 and later." — [PR 58](https://github.com/Perlence/PyGuitarPro/pull/58). PR #62 "Add reading and writing of GP6 (.gpx) and GP7 (.gp) files" by knoguchi (2026-06-26; BCFZ/BCFS container + gpif.py), closed same day by the author ("just saw #58 for the same purpose and closed"); PR #63 "Translate GP6/GP7 note effects" closed as stacked on #62 — [PR 62](https://github.com/Perlence/PyGuitarPro/pull/62); [PR 63](https://github.com/Perlence/PyGuitarPro/pull/63). Earlier issue #45 (2024-11-27), closed "not_planned": "no, I don't plan to add support for Guitar Pro versions 6 and above"; maintainer notes GP7 `.gp` "is a plain ZIP archive ... `score.gpif` ... XML" — [issue 45](https://github.com/Perlence/PyGuitarPro/issues/45).
- Fork with the GPIF reader: `kaizenman/PyGuitarPro`, branch `gpif-support`, last push 2026-04-25 — [fork API](https://api.github.com/repos/kaizenman/PyGuitarPro/branches).

Report impact: changes the gap-analysis table row "High for GP3-5 and MIDI; GP6-8 unverified" to: GP6-8 are not supported by PyGuitarPro and will not be; use the kaizenman `gpif-support` fork, alphaTab (which reads GP3-8), or unzip `.gp` and parse `score.gpif` XML directly.

### 3b. music21 MusicXML tab export status (issue #778 / PR #1169) and `tablature.UkeleleFretBoard` — CONFIRMED / CHANGED

Previously unverified: "Current status of music21 tab-staff MusicXML export (post-PR 1169) is unverified."

Found:
- Issue #778 "Support Staff-Tuning tags in musicxml with sensible default" (opened 2021-01-14) is still OPEN; the reporter found that music21's tab MusicXML is "displayed correctly in MuseScore if" tuning information is added; maintainer: "we're not fully supporting fretboards yet" — [issue 778](https://github.com/cuthbertLab/music21/issues/778).
- PR #1169 "Handling Staff-tuning in MusicXML (fixes #778)" (opened 2021-11-18 by louisbigo) is still OPEN and unmerged; maintainer comment 2026-09-29: "planning on closing this as abandoned ... and something to reimplement later? ... we were pretty close, but i would need to review from scratch again." — [PR 1169](https://github.com/cuthbertLab/music21/pull/1169).
- Closed related issues: #1534 "tablatures: Export Fret and String articulations inside chords" (2023), #1673 "allow multiple {Fret/String}Indications for chord" (2023), #912 stem problem on tab export (2021) — [issue search](https://api.github.com/search/issues?q=repo:cuthbertLab/music21+tablature+musicxml).
- `music21.tablature.UkeleleFretBoard` exists on master: "A four-string fretboard tuned to G C E A", `numStrings = 4`, `tuning = [G4, C4, E4, A4]` (i.e. re-entrant high-G), alongside `GuitarFretBoard`, `BassGuitarFretBoard`, `MandolinFretBoard`, `ChordWithFretBoard` — [tablature.py](https://raw.githubusercontent.com/cuthbertLab/music21/master/music21/tablature.py). Current PyPI music21 is 10.5.0 (2026-06-17), requires Python >=3.11 — [PyPI JSON music21](https://pypi.org/pypi/music21/json).

Report impact: confirms that music21 still cannot emit `<staff-tuning>` in MusicXML (PR unmerged, about to be closed), so a tab staff exported from music21 lacks tuning and renders wrongly in MuseScore unless post-processed; confirms `UkeleleFretBoard` exists (chord-diagram object, high-G tuning) but it is not a tab-export path.

---

## 4. Rhythm quantisation and timing JND

(Sections 4, 5 and 6 were verified by a delegated sub-task; this text is reconstructed from its hand-back report after the longer notes file was lost in a merge step. All facts and URLs below are from that report.)

### 4a. Cemgil & Kappen 2003; Cemgil, Desain & Kappen 2000 — CONFIRMED (model) / CHANGED (identifier, numbers)

Previously unverified: primary source, model, accuracy ("the JAIR URL I tried resolved" elsewhere).

Found:
- "Monte Carlo methods for tempo tracking and rhythm quantization", JAIR 18 (2003) 45-81, DOI 10.1613/jair.1121; the arXiv mirror is 1106.4863 (NOT cs/0105005, which is a WordNet paper) — [JAIR PDF](https://jair.org/index.php/jair/article/download/10322/24658/19036); [arXiv 1106.4863](https://arxiv.org/abs/1106.4863); [cs/0105005 is unrelated](https://arxiv.org/abs/cs/0105005).
- Abstract: the model is "equivalent to a switching state space model. The switch variables correspond to discrete note locations as in a musical score. The continuous hidden variables denote the tempo"; MCMC (Gibbs, simulated annealing, iterative improvement) is compared with particle filters, with "better results with sequential methods" — JAIR PDF.
- Data: "12 pianists ... two Beatles songs, Michelle and Yesterday" (4 pro jazz, 4 pro classical, 4 amateur; 3 tempi x 3 repetitions, piano MIDI). Result: edit-distance "errors are around 5% for all models"; "Conditioned on the score, the tempo tracking model is a linear dynamical system" (Kalman) — JAIR PDF.
- Cemgil, Desain, Kappen, "Rhythm quantization for transcription", CMJ 24(2):60-76 (2000): "Expressive deviations are modelled by a probabilistic performance model from which the corresponding optimal quantizer is derived by Bayes theorem ... many different quantization schemata can be derived in this framework by proposing suitable prior and likelihood distributions"; prior over grid "code vectors" from a subdivision schema with a depth/complexity measure; trained on a psychoacoustic experiment — [cdk-2.pdf](https://www.mcg.uva.nl/mmm-2003/papers/cdk-2/cdk-2.pdf).
- No code release found.

Report impact: changes the arXiv identifier; adds the citable "~5% edit-distance error" on 12-pianist Beatles MIDI.

### 4b. Raphael 2001 "Automated rhythm transcription" — CONFIRMED

Found — [ISMIR 2001 PDF](https://archives.ismir.net/ismir2001/paper/000016.pdf): abstract: "given a sequence of musical note onset times, performs simultaneous identification of the notated rhythm and the variable tempo ... stochastic model for the interconnected evolution of a rhythm process, a tempo process, and an observable process ... globally optimal identification". The score-position process is "a time-homogeneous Markov chain ... transition probability matrix R(s_{n-1}, s_n)" over (measure, position) pairs; dynamic-programming decoding. No percentage accuracy: Schumann Romance (129 onsets from audio) gives a "perfect parse after correcting 7 or fewer errors" (perplexities 2-8); Chopin Mazurka Op. 6 No. 3 MIDI "1334 notes", learned Perp(R) = 2.02 vs 15 uniform; results as error-count plots only. No code.

Report impact: confirms the HMM/Markov rhythm model; no headline accuracy figure exists to quote.

### 4c. Friberg & Sundberg 1995 JND; Hirsh et al. 1990 — CONFIRMED

Found:
- Crossref abstract of JASA 98(5):2524-2531, DOI 10.1121/1.413218: "Thirty listeners ... fourth tone in a sequence of six ... interonset time ... between 100 and 1000 ms. The absolute jnd was found to be approximately constant at 6 ms for tone interonset intervals shorter than about 240 ms and the relative jnd constant at 2.5% of the tone interonsets above 240 ms. Subjects' musical training did not affect these values." — [Crossref record](https://api.crossref.org/works/10.1121/1.413218) (the JASA page returns 403 to scripts).
- Caution: the "~10 ms / ~5%" figures circulating online come from Friberg & Sundberg 1993 (DOI 10.1121/1.407650), a different experiment — [record](https://synapsesocial.com/papers/W1984276876).
- Repp (AUDITORY list, 2007) cites it as "A good review" and notes "a discontinuity at 200-300 ms" — [auditory.org posting 341](https://auditory.org/postings/2007/341.html).
- Hirsh, Monahan, Grant & Singh 1990, Perception & Psychophysics 47(3):215-226: thresholds "6%-8% at an IOI of 200 msec, 11%-12% at an IOI of 100 msec, and almost 20% at an IOI of 50 msec" — [USUHS record](https://scholar.usuhs.edu/en/publications/studies-in-auditory-timing-1-simple-patterns/).

Report impact: confirms the 6 ms / 2.5% / 240 ms numbers exactly and supplies the citation.

### 4d. Nakamura rhythm transcription HMM (TASLP 2017) and MRF note values — CHANGED (year, code location)

Found:
- Nakamura, Yoshii, Sagayama, "Rhythm transcription of polyphonic piano music based on merged-output HMM for multiple voices", TASLP 25(4):794-806, 2017 — [arXiv 1701.08343 PDF](https://arxiv.org/pdf/1701.08343). Data: 30 polyrhythmic + 30 non-polyrhythmic classical piano MIDI performances (some from PEDB). Table I, difference in rhythm-correction rate vs the proposed model (lower is better): polyrhythmic — note HMM +12.2+/-2.8, metrical HMM +13.1+/-3.1, 2D PCFG +23.8+/-3.9, Melisma v1 +17.7+/-3.7, Melisma v2 +21.4+/-3.3, Connectionist +38.7+/-3.2; non-polyrhythmic — note HMM -0.82+/-0.50, metrical HMM -0.79+/-0.61, Melisma v2 -0.09+/-1.33, Connectionist +30.6+/-2.95. Candidate note values: all normal/dotted/triplet from whole to 32nd; tempo grid of 50 values, 40-200 BPM.
- Code: "We make public the source codes for the best models found (the proposed model and other two HMMs) as well as the evaluation tool" -> RT.zip (64 KB) + manual at [anonymous4721029.github.io/algorithms.html](https://anonymous4721029.github.io/algorithms.html) ([demo](https://anonymous4721029.github.io/demo.html)); no licence or platform stated. github.com/eita-nakamura holds only homepage/test repos — [GitHub](https://github.com/eita-nakamura); [homepage](https://eita-nakamura.github.io/).
- Nakamura, Yoshii, Dixon, "Note value recognition for piano transcription using Markov random fields", TASLP 25(9):1846-1858, 2017 (not 2018) — [arXiv 1703.08144 PDF](https://arxiv.org/pdf/1703.08144): "reduces the average error rate by around 40 percent compared to existing/simple methods"; the score model matters more than the performance model; 148 piano pieces (3.4M notes) for the context model, 180 performances (60 phrases x 3 players); Melisma processed only 115/180 and emitted 30.0% zero note values. Code NVR.zip (99 KB: metrical-HMM onset quantiser, MRF note-value recogniser, evaluation tool, Kalman tempo tracker) at [anonymous574868.github.io/codes.html](https://anonymous574868.github.io/codes.html) ([demo](https://anonymous574868.github.io/demo.html)).

Report impact: changes the year of the MRF paper (2017) and the code location (anonymous GitHub-Pages zips, no licence); confirms the ~12-point advantage on polyrhythmic data.

### 4e. MDPI time-signature detection survey — CONFIRMED (identity) / ADDS (numbers)

Found: Abimbola, Kostrzewa, Kasprowski, "Time Signature Detection: A Survey", Sensors 21(19):6494, 2021, DOI 10.3390/s21196494, covering >110 publications — [PMC8512143](https://pmc.ncbi.nlm.nih.gov/articles/PMC8512143/) (full text; the MDPI page returns 403 to scripts: [MDPI](https://www.mdpi.com/1424-8220/21/19/6494/htm)). Summary tables: classical methods 73.5%-95.5% (e.g. 2004 SSM on Greek music 95.5%; 2014 RSSM on MIDI 93%; 2020 ACMUS-MIR 75.06%); deep learning 72%-93% (2019 TCN 93%; 2019 CRNN on Beatles 72%). Per-metre: bambuco (Estefan 2020) 3/4 madmom 76.05% / multiBT 42.79%; 6/8 madmom 41.13% / multiBT 45.15%; Varewyck 2013 duple/triple error ~10% but 3-vs-4-vs-6 error ~28%; Pikrakis 2004 "2/4 confused with 4/4 or 5/4; 7/8 with 3/4 or 4/4". Conclusion: the task is "a difficult one"; >70% of studies assume a constant bar structure; ASM/RSSM/BSSM/ACF methods "work better on MIDI files than on digital audio files".

Report impact: adds — there is no clean 3/4 vs 4/4 vs 6/8 benchmark; compound 6/8 sits around 41-45% and 3/4/6 discrimination has ~28% error.

### 4f. Wachter et al. rhythm quantisation code — CONFIRMED (no code)

Found: arXiv 2604.22290 (ICSM 2025), T5-based; 97.3% onset F1 / 83.3% note-value accuracy on ASAP; the full text has no code URL (only guitar-pro.com, the MUSTER GitHub, MusicXML, MuseScore, Finale). Table IV: Leduc->Leduc 92.1%/90.2%; ASAP->Leduc 87.2%/71.3%. Pre-quantisation grid = 32nd-note triplets; Table III 3/4 with 3/4+4/4 training 97.9%/80.4% — [PDF](https://arxiv.org/pdf/2604.22290). Companion arXiv 2508.19262 (AES AIMLA 2025): same numbers, MUSTER onset error 12.30, no code mentioned — [HTML](https://arxiv.org/html/2508.19262v1). Authors at Klangio GmbH / KIT.

Report impact: confirms no public code or weights.

### 4g. GM2 Ukulele patch — CONFIRMED

Found: General MIDI Level 2 table: Ukulele = program 25 (1-based; 24 zero-based), Bank MSB 121, LSB 1, Guitar family, a variation of Nylon-string Guitar; selected by "setting cc#0 (Bank Select MSB) to 121 and using cc#32 (Bank Select LSB) to select the variation bank before a Program Change" — [Wikipedia GM Level 2](https://en.wikipedia.org/wiki/General_MIDI_Level_2); corroborated by the Dream soundbank list — [GMBK5X128](https://www.docs.dream.fr/pdf/Serie5000/Soundbanks/GMBK5X128.pdf).

Report impact: confirms; the MIDI-export path can tag ukulele tracks with bank 121/1, program 25.

---

## 5. Local key estimation

### 5a. Weiss, Schreiber, Müller, TASLP 2020 — CHANGED (details) / CONFIRMED (venue)

Previously unverified: "the three core LKE papers were unreadable, so their windows and accuracies are unknown".

Found:
- "Local Key Estimation in Music Recordings: A Case Study Across Songs, Versions, and Annotators", TASLP 28:2919-2932, DOI 10.1109/TASLP.2020.3030485; nine recorded versions of Schubert's Winterreise, three annotators, HMM vs CNN; the version split scores much higher, and errors coincide with annotator disagreement and musically related keys — [FAU CRIS](https://cris.fau.de/converis/portal/publication/245893090?lang=de_DE); [IEEE 9222034 (paywalled)](https://ieeexplore.ieee.org/document/9222034). No Beatles data; inputs are CQT at 0.19 s frames (HCQT/window ablations not confirmed).
- Numbers from the ICASSP 2020 companion paper (same methods and data): neither-split CNN 73% / HMM 71%; song split HMM 69% / CNN 72%; version split HMM 76% / CNN 96% (the "cover song effect"); per-song SD 14.4% vs per-version 5.2% (CNN) — [ICASSP 2020 PDF](https://www.audiolabs-erlangen.com/content/05_fau/professor/00_mueller/03_publications/2020_SchreiberWM_LocalKey_ICASSP_PrintedVersion.pdf).
- Released: annotations and trained CNNs at github.com/hendriks73/key-cnn; SWD dataset on Zenodo 5139893; error visualisations at [schubert-localkey](https://audiolabs-erlangen.de/resources/MIR/schubert-localkey); thesis chapter 9 — [Schreiber PhD](https://www.audiolabs-erlangen.com/content/05_fau/professor/00_mueller/01_group/2020_Schreiber_TempoKeyEstimation_ThesisPhD.pdf).

Report impact: changes: the paper is Schubert-only (not pop), and its 96% figure is a version-split artefact; the realistic song-split CNN figure is 72-73%.

### 5b. Ding & Weiss, EUSIPCO 2024 — CHANGED (exact title) / ADDS

Found: "Towards Robust Local Key Estimation with a Musically Inspired Neural Network", EUSIPCO 2024 pp. 26-30 — [EURASIP PDF 0000026](https://eurasip.org/Proceedings/Eusipco/Eusipco2024/pdfs/0000026.pdf). OctaveNet: CQT (24 bins/octave, 6 octaves) rearranged two ways into conv + recurrent branches with fusion; 20 s segments, 0.2 s hop; SWD, Annotation 3 only. Table I (recall %, Version / Song / Neither split; parameter count): HMM 76 / 67 / 71; CNN (293,296) 95 / 71 / 73; CRNN (361,392) 98.03 / 77.32 / 76.49; TONet (611,528) 92.34 / 74.28 / 72.37; TONet-RNN (722,760) 98.17 / 74.87 / 74.85; OctaveNet (149,720) 96.23 / 80.00 / 77.75. No code mentioned.

Report impact: adds the best current SWD numbers (OctaveNet 80.0% song split) and the fact that no code is released.

### 5c. Papadopoulos & Peeters 2012 — CONFIRMED (method); numbers from the DAFx 2009 version

Found: TASLP 20(4):1297-1312, DOI 10.1109/TASL.2011.2175385; local key from the chord progression with harmonic and metrical dependency; analysis window "expressed in relationship with the tempo period"; two databases — [IP Paris portal](https://researchportal.ip-paris.fr/en/publications/local-key-estimation-from-an-audio-signal-relying-on-harmonic-and/); [HAL (blocked)](https://hal.archives-ouvertes.fr/hal-00655781). DAFx 2009 version: five Mozart sonata first movements; 2-bar windows with 1-bar overlap aligned on downbeats; key-label accuracy 80.22% (chordgram) / 74.11% (chord progression), chords 61.43%; downbeat-aligned 80.21% vs misaligned 76.43%; 2-bar windows best among 2/4/8/16 bars, accuracy falling with longer windows; segmentation F 0.52-0.55 at 1-bar tolerance — [DAFx 2009 PDF](https://www.dafx.de/paper-archive/2009/papers/paper_82.pdf).

Report impact: confirms the 2-bar, downbeat-aligned window recommendation with numbers (classical data only).

### 5d. Cho & Bello 2014 — STILL UNKNOWN (exact numbers)

Found: "On the relative importance of individual components of chord recognition systems", TASLP 22(2):477-492, DOI 10.1109/TASLP.2013.2295926; no open PDF (NYU, ResearchGate, Semantic Scholar all failed) — [Crossref](https://api.crossref.org/works?query.bibliographic=On+the+relative+importance+of+individual+components+of+chord+recognition+systems+Cho+Bello&rows=2). Qualitative claims via citing papers: Korzeniowski & Widmer 2016: "Cho and Bello conclude that appropriate features largely redeem the benefits of complex chord models"; pre-filtering "blur[s] chord boundaries ... and can impair results when combined with more complex" models; log-compressed whitened chroma best — [arXiv 1612.05065](https://arxiv.org/pdf/1612.05065). Humphrey & Bello 2015 cite it for the four-stage pipeline — [ISMIR 2015 #294](https://archives.ismir.net/ismir2015/paper/000294.pdf). FMP notebooks: the HMM "introduces a kind of context-aware postfiltering" — [FMP C5S3](https://audiolabs-erlangen.de/resources/MIR/FMP/C5/C5S3_ChordRec_Beatles.html).

Report impact: no change; the exact smoothing-vs-feature numbers remain unavailable.

---

## 6. Tempo octave and swing

### 6a. Hockman & Fujinaga, "Fast vs slow: learning tempo octaves from user data" (ISMIR 2010) — CONFIRMED

Found — [PDF](https://archives.ismir.net/ismir2010/paper/000041.pdf): fast/slow classification without a beat tracker on Last.fm/YouTube-harvested data; dataset 1 = 397 tracks (109 fast, 288 slow), dataset 2 = 831 tracks; global spectral/MFCC features; k-NN 97.48%, SVM 99.37%, AdaBoost(C4.5) 99.44% on dataset 1; 95.97 / 96.42 / 96.81% on dataset 2; per-genre >93%.

### 6b. Gkiokas, Katsouros, Carayannis (ISMIR 2012) — CONFIRMED

Found — [PDF](https://archives.ismir.net/ismir2012/paper/000301.pdf): triangular tempo-band masks + DCT coding of the periodicity vector; an SVM slow/moderate/fast class masks the periodicity before peak picking; ISMIR 2004 data, 3-fold CV. Accuracy1: 75.93% ballroom / 63.87% songs vs baseline 59.89 / 58.49 (Klapuri 63.18 / 58.49; Seyerlehner SE1 78.51 / 40.86, SE2 73.78 / 60.43); an oracle class gives 88% / 76%.

### 6c. Seyerlehner, Widmer, Schnitzer, "From rhythm patterns to perceived tempo" (ISMIR 2007) — CONFIRMED

Found — [PDF](https://archives.ismir.net/ismir2007/paper/000519.pdf): tempo as k-NN classification on rhythm patterns; +/-4% tolerance; ballroom S1 78.51% / S2 73.78%; songs 40.86% / 60.43% (S2 rank 1); own pop set 68.8% / 74.5%; all joined 64.06% / 68.91%.

### 6d. Böck & Davies, "Deconstruct, analyse, reconstruct" (ISMIR 2020) — CHANGED (authors) / CONFIRMED

Found — [PDF](http://archives.ismir.net/ismir2020/paper/000223.pdf): authors are Böck and Davies (no Knees); abstract: "deconstruct this approach, analyse its constituent parts, and then reconstruct it ... multi-task approach for the simultaneous estimation of tempo, beat, and downbeat ... data augmentation ... up to 6% points"; tempo Acc1/Acc2: ACM Mirum 0.841/0.990, GiantSteps 0.870/0.965, GTZAN 0.830/0.950; code github.com/superbock/ISMIR2020.

Report impact (6a-6d): confirms the tempo-octave classics with exact accuracies; corrects the Böck 2020 author list.

### 6e. Dittmar, Pfleiderer, Müller (ISMIR 2015) and Marchand & Peeters (DAFx 2015) swing — CONFIRMED

Found:
- Dittmar et al., "Automated estimation of ride cymbal swing ratios in jazz recordings" — [PDF](https://www.ismir2015.uma.es/articles/143_Paper.pdf): onset-triple method vs log-lag autocorrelation (LLACF) prototype matching; Weimar Jazz Database (299 solos; 921 swing excerpts, ~50 min; 42 annotated with 834 ride-cymbal onsets); annotator onset F ~0.96 (7.8 ms), automatic onset F ~0.93 (2.5 ms), yet onset-based swing ratios correlate only ~0.66 with ground truth; LLACF is "more reliable". Literature average swing ratios 2.38, 1.75, 2.45, 0.9-1.7.
- Marchand & Peeters, "Swing ratio estimation" — [PDF](https://www.ntnu.edu/documents/1001201110/1266017954/DAFx-15_submission_59.pdf/dca67869-ce69-4b40-b44b-fa8063701621): autocorrelation of the onset-energy function plus rules, 16 s frames; releases GTZAN-rhythm (downbeat/beat/eighth annotations); "91% mean recall" for swing detection; per-genre swing recall with estimated tempo is low (jazz 23.8%, rock 48.2%, country 52.7%) vs noSwing 91.4-100%; jazz rises to 60.2% with annotated tempo; swing ratio "can reach 3.5:1" at slow tempi.

Report impact: adds — estimate swing from the beat-synchronous onset envelope after tempo/beat are fixed; onset-based swing ratios are fragile, and swing detection with estimated tempo is unreliable on rock.

---

## 7. Source separation

### 7a. BS-RoFormer-SW checkpoint provenance and licence — CHANGED (origin now partly known; licence absent)

Previously unverified: "The training provenance and license of the BS-Roformer-SW 6-stem checkpoint are unknown ... could not confirm an official UVR/Anjok07 release note or license text."

Found:
- MVSEP news item dated 15 Sep 2025: "a high-quality model based on the BS Roformer architecture, which separates tracks into 6 stems: bass, drums, guitar, piano, vocals, and other", default for first-time users; SDR vocals 11.30, instrum 17.50, bass 14.62, drums 14.11, guitar 9.05, piano 7.83, other 8.71; no author and no licence stated — [MVSEP news 64](https://mvsep.com/news/64?lang=en).
- The original host `jarredou/BS-ROFO-SW-Fixed` now returns HTTP 401/"Invalid username or password" (account/model gone) — [HF model API](https://huggingface.co/api/models/jarredou/BS-ROFO-SW-Fixed). Rehosts: `lumabeat/bs-roformer-sw` card: `license: other / license_name: unknown`; "Source checkpoint: BS-Roformer-SW.ckpt, SHA-256 24e7d35e...916e (699 MB), re-hosted by jarredou ... (no longer available)"; architecture dim 256, depth 12, 8 heads, 62 bands, n_fft 2048 hop 512, stems bass/drums/other/vocals/guitar/piano — [lumabeat card](https://huggingface.co/lumabeat/bs-roformer-sw). `Blakus/bs_roformer_sw_6stem` and `elicwhite/bs-roformer-sw-6stem-onnx` label themselves `license: mit` (self-asserted by re-uploaders; elicwhite is an ONNX export of the jarredou file) — [Blakus card](https://huggingface.co/Blakus/bs_roformer_sw_6stem); [elicwhite card](https://huggingface.co/elicwhite/bs-roformer-sw-6stem-onnx). `enerjazzer/BS-ROFO-SW-Fixed` declares "license: unknown" (per the issue below).
- Provenance thread (2026-08-17, cross-posted to ZFTurbo/MSST #248, openmirlab/bs-roformer-infer #3, elicwhite/bs-roformer-web #2): community member lucellent: "SW stands for 'shared weights'. It wasn't trained by a single person, nor Mvsep or any of the uploaders of the ckpt ... I'm sure the model itself doesn't have commercial license or maybe any kind of other license"; also "the SW model is absolutely free on Mvsep" — [MSST issue 248](https://github.com/ZFTurbo/Music-Source-Separation-Training/issues/248). ZFTurbo's own pretrained-model table does not list an SW model — [MSST docs/pretrained_models.md](https://raw.githubusercontent.com/ZFTurbo/Music-Source-Separation-Training/main/docs/pretrained_models.md).
- UVR: it is not shipped by UVR; users import the jarredou ckpt via "the latest Roformer patches" (UVR issue #2016, 2025-10-28, deton24) — [UVR issue 2016](https://github.com/Anjok07/ultimatevocalremovergui/issues/2016).

Report impact: changes the report's licence caveat from "unknown" to "no licence; collectively trained 'shared weights' checkpoint whose authors are unnamed; the MIT labels on some rehosts are not from the trainers". For a distributable product, treat as non-redistributable and keep htdemucs_6s (MIT) or a licensed RoFormer as the fallback.

### 7b. APSIPA 2025 Mitoma & Furuya numbers — ADDS

Previously unverified: "Exact accuracy numbers from the APSIPA 2025 paper could not be extracted".

Found — Ayumu Mitoma, Ken'ichi Furuya (Oita Univ.), "Accuracy Improvement of Automatic Chord Recognition with Source Separation Preprocessing", APSIPA ASC 2025, p. 290 — [APSIPA 2025 P307 PDF](https://webdev.apsipa.org/proceedings/2025/papers/APSIPA2025_P307.pdf):
- Method: HTDemucs 4-stem separation; "vocals, bass, and other are classified as pitched instruments, so volume adjustment is performed on these sources" by "doubling the amplitude"; stems re-mixed and fed to BTC (large vocabulary). Evaluation: 485 songs (225 Isophonics, 65 Robbie Williams, 195 uspop2002), WCSR.
- Table I (per-stem doubling, triads / root / maj-min / tetrads, %): Conventional 75.52 / 82.51 / 81.59 / 67.44; vocals x2 74.75 / 81.81 / 80.82 / 66.48; bass x2 75.06 / 82.21 / 81.09 / 66.83; other x2 75.67 / 82.66 / 81.78 / 67.45.
- Table II (final proposed setting from a manual preliminary search): Proposed 75.72 / 82.72 / 81.84 / 67.59 vs Conventional 75.52 / 82.51 / 81.59 / 67.44, i.e. +0.20 / +0.21 / +0.25 / +0.15 points.
- Table III (triads, 1,136,742 frames): 13,675 frames fixed, 11,390 frames broken, net 2,285 frames (0.20%); "sign test ... statistically significant". Boosting vocals or bass alone *hurts*.

Report impact: changes emphasis: the "re-mix with pitched stems boosted" gain is real but tiny (+0.2 WCSR points on 485 songs); boosting bass alone reduced accuracy, which weakens any "bass-anchor by re-mixing" argument.

### 7c. Ko (UW-Madison) stems-hurt-ACR source — CONFIRMED

Previously: cited as an undated project page without numbers.

Found: page live: Daniel Ko, "Automatic Chord Recognition by Music Source Separation", University of Wisconsin-Madison; Demucs (early 2020 release) 4-stem; "The other and bass tracks were combined into a single audio track using the amix filter in by ffmpeg"; 1,217-song Humphrey & Bello set, 60/20/20 split, Jiang et al. architecture, mir_eval Root/Thirds/Maj-Min/Triads/Sevenths/Tetrads/MIREX; result: "on average across all metrics, the Demucs model performed worse than the model that was trained using the original dataset"; results are plots only (no numbers in text) — [ko28.github.io/chord-transcription](https://ko28.github.io/chord-transcription/).

Report impact: confirms (still a course project with no numeric table; note it trained *on* stems, so it tests a distribution shift, not stems fed to a mix-trained model).

### 7d. 2025-2026 paper quantifying transcription accuracy on Demucs guitar stems — STILL UNKNOWN

Searches (4 queries) found no paper that measures note-level F1 of a transcriber on Demucs guitar stems versus clean guitar. Closest evidence: Lukoianov & Klapuri (arXiv 2510.05756) report strum-detection on the HTDemucs "other" stem and note guitar SNR in stems is "barely above 0 dB" — [arXiv 2510.05756](https://arxiv.org/html/2510.05756v1); a Dec 2024 student pipeline paper "Source Separation & Automatic Transcription for Music" (Derby et al.) reports no stem-vs-mix F1 — [arXiv 2412.06703](https://arxiv.org/abs/2412.06703). tabforge's self-reported 0.41 polyphonic F1 in a full mix remains the only number.

Report impact: no change; gap stands.

---

## 8. Transcription

### 8a. Jam-ALT per-system WER table (Cífka et al.) — ADDS

Previously unverified: "Jam-ALT line-break F1 numbers for Whisper ... were not retrievable"; Whisper singing WER uncited.

Found — Jam-ALT (arXiv 2311.13987, Table 1; WER case-insensitive, averages over 5 seeds; "+sep" = HTDemucs vocals) — [arXiv 2311.13987 PDF](https://arxiv.org/pdf/2311.13987):

| System | All WER | All line-break F1 (FL) | English WER | English FL |
|---|---|---|---|---|
| Whisper large-v2 | 35.7 | 69.3 | 43.8 | 63.0 |
| Whisper large-v2 +sep | 44.0 | 61.2 | 32.3 | 53.8 |
| Whisper large-v3 | 35.5 | 73.5 | 37.7 | 71.5 |
| Whisper large-v3 +sep | 47.9 | 65.7 | 43.0 | 66.8 |
| LyricWhiz | — | — | 24.6 | 74.0 |
| AudioShake (in-house) | 26.0 | 82.3 | 22.1 | 80.7 |

- ISMIR 2024 version ("Lyrics Transcription for Humans", arXiv 2408.06370, Table 1, adds a language hint "+lang" and OWSM v3.1): Whisper v2 37.8 -> +lang 27.9 -> +demucs 44.5 -> +demucs+lang 33.5; Whisper v3 35.5 -> +lang 32.6 -> +demucs 48.0 -> +demucs+lang 46.6; English: v2 43.8 / +lang 39.7 / +demucs 33.3; v3 37.7 / +lang 36.4 / +demucs 43.0; OWSM v3.1+lang 69.3; AudioShake v3 16.1 (English 17.3). Text: "the WER increases from 27.9 to 32.6 when comparing Whisper v2 [to v3]" and HTDemucs separation generally worsened Whisper except v2 on English — [arXiv 2408.06370 PDF](https://arxiv.org/pdf/2408.06370).

Report impact: adds the per-system table; confirms that vocal separation does not reliably help Whisper on Jam-ALT and that large-v3 is not better than v2 on lyrics.

### 8b. Whisper large-v3 / turbo singing WER — ADDS (with caveat)

Found: the only turbo-on-singing figure located is a non-peer-reviewed benchmark report dated 10 June 2026 ("Which Setup Works Best for Automatic Lyrics Transcription? A Practical Multilingual Benchmark on Apple Silicon", authored "Claude (Anthropic) for Swaroop G N"), on 12 CC songs from JamendoLyrics MultiLang with MLX on an Apple M5: WER mix / Demucs-vocals: large-v3 24.3 / 22.1; large-v3-turbo 27.1 / 22.8; large-v2 32.6 / 32.4; English vocals: large-v3 22.6, turbo 26.0; `condition_on_previous_text=True` "+28 WER points" — [lyrics-bench report](https://lyrics-bench.onrender.com/papers/paper.html). Treat as anecdotal (12 songs, tuned decoding, not reviewed); the peer-reviewed Jam-ALT numbers above are the citable ones. No Distil-Whisper or Parakeet singing WER was found.

Report impact: adds a provisional turbo figure (approx. 23-27% WER on 12 songs) with an explicit low-confidence flag.

### 8c. Wang & Jang EfficientNet SVT repo and MIR-ST500 access — CONFIRMED / ADDS

Previously unverified: repo README and dataset download instructions could not be fetched.

Found — [york135/singing_transcription_ICASSP2021 README](https://github.com/york135/singing_transcription_ICASSP2021) (default branch `master`, 71 stars, last push 2026-03-05, no licence file reported by the API):
- Paper: Jun-You Wang, Jyh-Shing Roger Jang, "On the Preparation and Validation of a Large-scale Dataset of Singing Transcription", ICASSP 2021.
- MIR-ST500: 500 pop songs; "we provide the label of notes (vocal part) and the corresponding Youtube URL"; `python get_youtube.py MIR-ST500_20210206/MIR-ST500_link.json train test` downloads #1-400 train / #401-500 test; "2026.03.05 ... get_youtube.py has been updated. Now it uses yt-dlp"; for missing audio "send an e-mail to me (junyouwang135@gmail.com) and provide with your name and affiliation. Then, I will decide whether to give you the access or not."
- Inference: `python do_everything.py input output.mid -p model/1005_e_4 -s -on 0.4 -off 0.5` with Spleeter for vocal separation; pre-trained EfficientNet-b0 in `AST/model`; README warns a post-processing bug means results "may not be able to reproduce the exactly same result". Songs are Chinese pop (search snippet: "500 Chinese pop songs (about 30 hours)") — [search result summary](https://arxiv.org/pdf/2304.12082).

Report impact: confirms access terms (YouTube links + email for cached audio) and that the repo is Spleeter/TF-era code.

### 8d. SVT note F1 on English datasets — STILL UNKNOWN (negative result sharpened)

- STARS (arXiv 2507.06670) evaluates on GTSinger (Chinese and English subsets) plus a 30-hour Chinese set, but "We conduct the comparison using only Chinese data"; Table 2 (Chinese): VOCANO COnPOff 50.2 / RPA 76.6; ROSVOT 70.2 / 83.8; STARS 71.0 / 86.7; no English-only numbers — [arXiv 2507.06670](https://arxiv.org/html/2507.06670v1).
- VocalParse (arXiv 2605.04613, May 2026; code Apache-2.0 at `pymaster17/VocalParse`, built on Qwen3-ASR) trains on GTSinger + M4Singer and validates on Opencpop; no English-only note F1 in abstract or README — [arXiv 2605.04613](https://arxiv.org/abs/2605.04613); [VocalParse README](https://github.com/pymaster17/VocalParse).

Report impact: confirms the gap: no English-pop note-level F1 exists for the modern SVT models.

---

## 9. Strumming

### A1. Murgul, Schimper, Heizmann — ISMIR 2025 strumming CRNN (arXiv 2508.07973)
Previously unverified: whether any code or dataset has been released.
Found:
- Title "Joint Transcription of Acoustic Guitar Strumming Directions and Chords"; authors Sebastian Murgul, Johannes Schimper, Michael Heizmann; comments "Accepted to the 26th International Society for Music Information Retrieval Conference (ISMIR), 2025"; the arXiv abstract page lists no code/data links [Source](https://arxiv.org/abs/2508.07973)
- Affiliation line in the PDF: "1 Klangio GmbH, Karlsruhe, Germany". The PDF text contains no availability statement at all: the only URLs in the body/footnotes are guitar-pro.com, amplesound.net (the synthesis sample library), a Waveshare ESP32 product page, two lesson blogs, and the Pedalboard Zenodo DOI. No GitHub/Zenodo/"available upon request" wording for the 90-min real or 4-h synthetic datasets [Source](https://arxiv.org/pdf/2508.07973)
- Data details from the PDF: "28 different strumming patterns in 4/4 time signature", tempos 60/80/100 BPM, three guitarists; synthetic set "generates approximately 1000 examples totaling 4 h of audio, which are randomly split into 90 % training, 5 % validation, and 5 % testing sets", built from "51 chord progressions in functional notation and 36 strumming patterns defined on a 16th-note grid" [Source](https://arxiv.org/pdf/2508.07973)
- ISMIR proceedings deposit on Zenodo (DOI 10.5281/zenodo.17811416, CC BY 4.0) contains only "000055.pdf (292.1 kB)"; no dataset or code files [Source](https://zenodo.org/records/17811416)
- GitHub search for repositories matching "strumming" created after 2025-01-01 returns only hobby/web apps (StrumLoop, strum-trainer, strumvg, chord-strum-counter, etc.); nothing from Klangio or the authors [Source](https://api.github.com/search/repositories?q=strumming+created:>2025-01-01&sort=updated&per_page=30)
- Murgul's KIT page lists the paper plus "A Multimodal Approach to Acoustic Guitar Strumming" (ISMIR 2022 LBD) and "Exploring Procedural Data Generation for Automatic Acoustic Guitar Fingerpicking Transcription" (AIMC 2025) but "No GitHub repositories or Zenodo dataset links" [Source](https://www.iiit.kit.edu/murgul.php)
- Related new work found incidentally: Pennese, Giacomelli, Rinaldi, "A Kolmogorov Arnold Network NAS Framework for Strumming Pattern Recognition in Technology-Enhanced Pop/Rock Music Education", 2025 IEEE 6th International Symposium on the Internet of Sounds (IS2), DOI 10.1109/IS264627.2025.11284580; builds "a dataset of annotated audio samples from YouTube" for the Strummin' Gym platform [Source](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1109/IS264627.2025.11284580?fields=title,authors,year,venue,abstract,externalIds)
Report impact: confirms — no code or data released; the paper contains no availability statement, so "closed" should be stated as an absence rather than quoted. Adds the IS2 2025 KAN strumming paper as a second recent closed-data strumming classifier.

### A2. Lukoianov & Klapuri (Yousician) — WASPAA 2025 (arXiv 2510.05756)
Previously unverified: authors, venue, code/dataset release.
Found:
- Title "Transcribing Rhythmic Patterns of the Guitar Track in Polyphonic Music"; authors Aleksandr Lukoianov, Anssi Klapuri; "Accepted to WASPAA 2025"; arXiv licence CC BY-NC-ND 4.0 [Source](https://arxiv.org/abs/2510.05756)
- PDF affiliation "Yousician, Helsinki, Finland". Data statement: "The dataset that we use in this paper comprises 931 proprietary recordings of 410 popular songs. Each song appears in up to four difficulty levels for the guitar part: simplified, intermediate, advanced, and original." and "Example tracks from the dataset are publicly available at GitHub. 1" (footnote 1 = https://github.com/YousicianGit/rhythmic-pattern-transcription). On code: "Full description is beyond the scope of this paper, therefore we publish our Python implementation as open source. 1" (this refers to the bar-line/downbeat post-processing step) [Source](https://arxiv.org/pdf/2510.05756)
- GitHub repo YousicianGit/rhythmic-pattern-transcription: description "Companion resources for the paper ...", created 2025-07-14, last push 2025-10-08, 14 stars, size 2,111 KB, no licence specified [Source](https://api.github.com/repos/YousicianGit/rhythmic-pattern-transcription)
- README: contains a `downbeat.py` script plus "8 audio excerpts (2 per difficulty level: simplified, intermediate, advanced, original) from the test split, each 10 seconds long" with full-mix and isolated-guitar audio; "No model weights, training data, or annotations appear to be included"; no licence [Source](https://github.com/YousicianGit/rhythmic-pattern-transcription)
Report impact: confirms (authors/venue) and changes slightly — dataset is explicitly "proprietary"; only 8 ten-second example excerpts and one post-processing script are public, no model weights.

### A3. Phithak et al. 2015 — Thai ukulele strumming classifier
Previously unverified: exact authors, title, venue, features, classifier, dataset size, F-measure.
Found:
- Journal version: Phithak, Thawatphong; Angskun, Jitimon; Angskun, Thara. "A Machine Learning-based Approach for Strumming Pattern Recognition from Ukulele Songs". Information (International Information Institute, Tokyo), vol. 18, no. 2, pp. 705-718, February 2015 [Source](https://www.proquest.com/openview/e55f121cf94bb00eb34e7ec8ba34ec7b/1?pq-origsite=gscholar&cbl=936334)
- Search-engine summary of the ResearchGate record: approach "focuses on predicting strumming types (d-, du, -u, and xu patterns) and achieved an 82.6% F-measure for the strumming type predictor"; "experiments used 10 ukulele songs" [Source](https://www.researchgate.net/publication/282060679_A_machine_learning-based_approach_for_strumming_pattern_recognition_from_ukulele_songs) (page itself returns 403 to fetchers; figures come from the search snippet)
- Earlier conference version: same authors, "Strumming pattern recognition from Ukulele songs", WIT Transactions on Information and Communication Technologies (ICIE 2013 proceedings, published 2014), DOI 10.2495/ICIE130101 [Source](https://api.crossref.org/works?query=strumming+pattern+recognition+ukulele+songs&rows=5) and [Source](https://api.openalex.org/works?search=strumming%20pattern%20recognition%20ukulele&per_page=5)
- Feature set and classifier: still unknown (ProQuest preview, ResearchGate and WIT Press pages all blocked or did not render the abstract after 4 attempts).
Report impact: changes — correct spelling is Phithak (not Phithakkitnukoon), co-authors Jitimon and Thara Angskun; two versions exist (ICIE 2013 / WIT 2014 and Information 2015); 10 songs and 82.6 % F-measure confirmed via snippet only; features/classifier remain unverified.

---

## 10. Arrangement

### B1. Piano/lead-sheet-to-guitar arrangement papers 2023-2026 (Sony?, Arranger, LooPy, SymPAC)
Previously unverified: existence and scope of the candidate papers.
Found:
- No Sony CSL / Sony AI piano-to-guitar arrangement paper surfaced in three targeted searches; results were MIDI-to-Tab (Edwards et al., ISMIR 2024), TART (arXiv 2510.02597), rhythm-guitar tab continuation (TISMIR 368), GTR-CTRL, GuitarFlow [Source](https://arxiv.org/abs/2408.05024?context=cs) [Source](https://transactions.ismir.net/articles/368) — still unknown whether such a Sony paper exists.
- Arranger: Hao-Wen Dong et al., "Towards Automatic Instrumentation by Learning to Separate Parts in Symbolic Multitrack Music", ISMIR 2021; repo salu133445/arranger, MIT licence, 60 stars, created 2021-01-14, last push 2023-06-26, homepage https://salu133445.github.io/arranger/. It assigns parts/instruments in symbolic multitrack music; it is not a fretted-instrument tablature arranger [Source](https://api.github.com/repos/salu133445/arranger)
- LooPy: "LooPy: A Research-Friendly Mix Framework for Music Information Retrieval on Electronic Dance Music", arXiv 2305.01051 (submitted to ACM MM 2023); a Python package that renders EDM tracks from melody/chords. Not guitar-related [Source](https://arxiv.org/abs/2305.01051v1)
- SymPAC: "SymPAC: Scalable Symbolic Music Generation With Prompts And Constraints", arXiv 2409.03055, ISMIR 2024; trains symbolic generation from auto-transcribed audio with prompt bars and FSM-constrained decoding. General multitrack symbolic generation, no guitar/fret arrangement [Source](https://arxiv.org/pdf/2409.03055) [Source](https://ismir2024program.ismir.net/poster_366.html)
- Closest actual lead-sheet-to-guitar arrangement work: Shunsuke Sakai, Hinata Segawa, Tetsuro Kitahara (Nihon University), "Tablature Generation from Lead Sheets for Finger-Style Solo Guitar", SMC 2024, paper id 55, CC BY 3.0. Viterbi search over fingering states with initial/transition/emission costs; "We manually made a dataset that include 3658 typical forms"; evaluated on 8 pieces by one classical-guitar expert. No code link in the paper [Source](https://smcnetwork.org/smc2024/papers/SMC2024_paper_id55.pdf)
- Related MIDI-to-tab (not arrangement) work: Hamberger, Murgul, Schmidt, Heizmann, "Fretting-Transformer: Encoder-Decoder Model for MIDI to Tablature Transcription", ICMC 2025, arXiv 2506.14223, no code link on the abstract page [Source](https://arxiv.org/abs/2506.14223); Kaliakatsos-Papakostas et al., "A Machine Learning Approach for MIDI to Guitar Tablature Conversion", SMC 2022 pp. 192-199, arXiv 2510.10619 [Source](https://arxiv.org/abs/2510.10619)
Report impact: changes — Arranger/LooPy/SymPAC are not guitar arrangers; the only verified lead-sheet-to-fretted-instrument arrangement paper is Sakai/Segawa/Kitahara SMC 2024 (rule/Viterbi, no code). Sony candidate: still unknown.

### B2. Mitsou et al. 2024, Data in Brief 52, DOI 10.1016/j.dib.2023.109842
Previously unverified: technique class list and sample counts.
Found:
- Authors Alexandros Mitsou, Antonia Petrogianni, Eleni Amvrosia Vakalaki, Christos Nikou, Theodoros Psallidas, Theodoros Giannakopoulos. Classes and recordings (avg duration s): Alternate picking 81 (6.3), Legato 81 (5.2), Tapping 81 (5), Sweep picking 36 (5.7), Vibrato 54 (8.9), Hammer-on 54 (28.7), Pull-off 54 (23.4), Slide 54 (23.7), Bend 54 (3.3); total 549 video (MP4) + audio (WAV) samples. Three guitars (River West Guitars, Carvin DC-400, Palm Bay Cyclone P7-XR, humbuckers), three Eleven Rack amp sims (SL100, Plexiglass, DC-Modern) [Source](https://pmc.ncbi.nlm.nih.gov/articles/PMC10698518/)
- Data repository: Zenodo "magcil/guitar_style_dataset: Initial Release", DOI 10.5281/zenodo.10075352, one zip of 14.3 GB, published 2023-11-06, licence shown on Zenodo as CC BY 4.0 (the PMC article page states CC BY-NC-ND 4.0) [Source](https://zenodo.org/records/10075352)
Report impact: adds — full class list and counts; note the licence discrepancy (Zenodo record CC BY 4.0 vs article CC BY-NC-ND 4.0).

### B3. Ukulele chord-melody arrangement / ukulele difficulty-model papers (2015-2026)
Previously unverified: whether any exist.
Found:
- Four English searches and one Japanese search (IPSJ) found no ukulele-specific arrangement or difficulty-model paper. Nearest guitar work: Song2Guitar (Ariga, Fukayama, Goto, ISMIR 2017, difficulty-aware guitar solo covers) [Source](https://archives.ismir.net/ismir2017/paper/000041.pdf); the SMC 2024 lead-sheet solo-guitar paper above; the IPSJ search returned only piano/wind-ensemble difficulty-aware arrangement reports [Source](https://ipsj.ixsq.nii.ac.jp/record/212835/files/IPSJ-MUS21132011.pdf)
- Non-ML ukulele notation work exists: Mauro Padellini, "Linear Tablature for Ukulele Transcription" (Zenodo 10.5281/zenodo.7545428, 2023) and "Information Preserving in Ukulele Transcription" (10.5281/zenodo.6525197, 2021), both CC BY 4.0 PDFs [Source](https://zenodo.org/api/records?q=ukulele&size=25&sort=newest); Giovanni Albini, "Graph-Theoretic Ukulele Strumming Patterns", ICGG 2024, DOI 10.1007/978-3-031-71008-7_30 [Source](https://api.crossref.org/works?query=strumming+pattern+recognition+ukulele+songs&rows=5)
Report impact: confirms — no computational ukulele arrangement/difficulty paper found (absence, not proof).

---

## 11. Engineering

### 11a. GPL FAQ on subprocess invocation vs linking — CONFIRMED (now cited)

Previously unverified: "Could not fetch the GNU GPL FAQ ... the subprocess-vs-import distinction above is stated from general knowledge".

Found — [GNU GPL FAQ](https://www.gnu.org/licenses/gpl-faq.en.html):
- #MereAggregation: "Where's the line between two separate programs, and one program with two parts? This is a legal question, which ultimately judges will decide. We believe that a proper criterion depends both on the mechanism of communication (exec, pipes, rpc, function calls within a shared address space, etc.) and the semantics of the communication ... If modules are designed to run linked together in a shared address space, that almost surely means combining them into one program. By contrast, pipes, sockets and command-line arguments are communication mechanisms normally used between two separate programs. So when they are used for communication, the modules normally are separate programs. But if the semantics of the communication are intimate enough, exchanging complex internal data structures, that too could be a basis to consider the two parts as combined into a larger program."
- #GPLPlugins: "If the main program uses fork and exec to invoke plug-ins, and they establish intimate communication by sharing complex data structures, or shipping complex data structures back and forth, that can make them one single combined program. A main program that uses simple fork and exec to invoke plug-ins and does not establish intimate communication between them results in the plug-ins being a separate program. If the main program dynamically links plug-ins, and they make function calls to each other and share data structures, we believe they form a single combined program".
- #GPLInProprietarySystem: "you must make sure that the free and nonfree programs communicate at arms length, that they are not combined in a way that would make them effectively a single program."

Report impact: confirms the report's separation argument (CLI subprocess with files/simple args = separate programs; Python `import` of a GPL module = combined work) and supplies the citation.

### 11b. allin1 / NATTEN Windows build status — CONFIRMED / ADDS

Found: README: "Install NATTEN (Required for Linux and Windows; macOS will auto-install) ... Windows: Build from source: pip install ninja; git clone https://github.com/SHI-Labs/NATTEN; cd NATTEN; make" — [allin1 README](https://raw.githubusercontent.com/mir-aidj/all-in-one/main/README.md). Open issues: #30 "Incompatibility issues with NATTEN v0.17.5" (2025-05), #27 "Update deprecated Natten modules", #36 "Natten compatibility fix and working Dockerfiles" (2025-08), PR #39 (2026-09-20, open) "Run neighborhood attention in plain PyTorch on CPU and MPS; make NATTEN optional" (re-implements the four NATTEN ops with einsum); PR #37 (closed 2025-10-22) "NATTEN 21 Support & misc fixes ... works with torch 2.7.0, cu128" — [issues API](https://api.github.com/search/issues?q=repo:mir-aidj/all-in-one+windows+OR+natten); [PR 39](https://github.com/mir-aidj/all-in-one/pull/39); [PR 37](https://github.com/mir-aidj/all-in-one/pull/37). No Windows-specific issue exists; all pain is NATTEN version drift.

Report impact: confirms "allin1 on Windows = build NATTEN from source"; adds that a pure-PyTorch NATTEN replacement (PR #39) is pending, which would remove the blocker if merged or if the fork is used.

### 11c. Beat This! DBN dependency on madmom — CONFIRMED

Found: `pyproject.toml` dependencies: numpy>=1.20, torch>=2, torchaudio, einops, rotary-embedding-torch, soxr; licence MIT; madmom is NOT a declared dependency — [pyproject.toml](https://raw.githubusercontent.com/CPJKU/beat_this/main/pyproject.toml). README: "If you want to use the DBN for postprocessing, add `--dbn`. The DBN parameters are the default ones from madmom. This requires installing the madmom package (with pip install git+https://github.com/CPJKU/madmom.git ...)" — [README](https://github.com/CPJKU/beat_this).

Report impact: confirms: Beat This! runs without madmom; only the optional `--dbn` path needs the git-installed madmom (see 1e for its build caveats).

### 11d. audio-separator Windows CUDA install notes — CONFIRMED / ADDS

Found — [python-audio-separator README](https://github.com/nomadkaraoke/python-audio-separator): "Supported CUDA Versions: 11.8 and 12.2"; `pip install "audio-separator[gpu]"`; expected log "ONNXruntime has CUDAExecutionProvider available"; troubleshooting: `pip uninstall torch onnxruntime; pip cache purge; pip install --force-reinstall torch torchvision torchaudio; pip install --force-reinstall onnxruntime-gpu`; "Multiple CUDA library versions may be needed ... ONNX Runtime still needs CUDA 11 libraries" when you see "Failed to load library"; Windows AMD/Intel GPUs via `pip install "audio-separator[dml]"` are "Experimental / community-supported ... not tested in CI or by the maintainer" (CI job runs on a T4 in WDDM mode); "Other platforms continue to support PyTorch 2.3 or newer"; native fp16 and torch.compile verified only for MelBand/BS-RoFormer on MPS and CUDA.

Report impact: confirms pip GPU install path on Windows NVIDIA; adds the CUDA 11.8/12.2 constraint and the ONNX Runtime CUDA-library mismatch as the main failure mode.

### 11e. Demucs torchaudio/TorchCodec Windows status — CHANGED (Demucs 4.1.0 dropped torchaudio for inference)

Previously: concern that torchaudio >= 2.9 routes `load/save` through TorchCodec, which needs FFmpeg shared DLLs on Windows.

Found:
- torchaudio 2.9 docs: torchaudio is in maintenance; `load()`/`save()` are now aliases of `load_with_torchcodec`/`save_with_torchcodec` — [torchaudio 2.9 docs](https://docs.pytorch.org/audio/2.9.0/torchaudio.html). TorchCodec README: supports FFmpeg "[4, 9]"; "You'll need FFmpeg that comes with separate shared libraries. This is especially relevant for Windows users: these are usually called the 'shared' releases"; CPU wheels for Windows; CUDA wheels on Windows need `--index-url` — [torchcodec README](https://raw.githubusercontent.com/pytorch/torchcodec/main/README.md).
- `facebookresearch/demucs` is archived (API `archived: true`, last push 2024-04-24); 4.0.1 pinned `torchaudio>=0.8,<2.1` — [repo API](https://api.github.com/repos/facebookresearch/demucs); [requirements_minimal.txt](https://raw.githubusercontent.com/facebookresearch/demucs/main/requirements_minimal.txt).
- NEW: Demucs **4.1.0** was published on PyPI on 2026-07-11 from `adefossez/demucs` ("This is the officially maintained Demucs now that I (Alexandre Défossez) have left Meta"), requires Python >=3.10, `torch>=2.1`; release notes: "Removed torchaudio for inference: audio decoding now goes through sphn with a fallback on ffmpeg for other formats. Wav files are written directly ... flac encoding goes through ffmpeg ... torchaudio remains a training-only dependency"; "Pretrained models are now hosted on the HuggingFace hub (as safetensors)"; Wiener filter vendored, openunmix dropped — [PyPI demucs 4.1.0](https://pypi.org/pypi/demucs/4.1.0/json); [release notes](https://raw.githubusercontent.com/adefossez/demucs/main/docs/release.md); [adefossez/demucs](https://github.com/adefossez/demucs) (last push 2026-08-31). `sphn` 0.2.1 ships `win_amd64` wheels for cp310-cp314 — [PyPI sphn](https://pypi.org/pypi/sphn/json).

Report impact: changes: the TorchCodec/FFmpeg-DLL concern no longer applies to Demucs inference if `demucs>=4.1.0` is used (decoding via sphn wheels); it still applies to any other code calling `torchaudio.load` on torchaudio >= 2.9 (e.g. Beat This! depends on torchaudio).

### 11f. Essentia Windows wheels in 2026 — CONFIRMED (none)

Found: PyPI `essentia` latest 2.1b6.dev1438 (2026-05-19) ships only `macosx_15_0_arm64`, `macosx_15_0_x86_64` and `manylinux2014_x86_64` wheels (cp314 shown); across the whole release history there is no file containing "win"; `essentia-tensorflow` likewise macOS/Linux only — [PyPI JSON essentia](https://pypi.org/pypi/essentia/json); [PyPI JSON essentia-tensorflow](https://pypi.org/pypi/essentia-tensorflow/json).

Report impact: confirms: Essentia is WSL/Docker-only on Windows.

---

## 12. Datasets and soundfonts

### C1. SynthTab (Zang, Zhong, Cwitkowitz, Duan, ICASSP 2024)
Previously unverified: licence of dataset and code, exact URL.
Found:
- Repo https://github.com/AirLabUR/SynthTab, created 2023-02-04, last push 2024-12-06, 35 stars, homepage https://synthtab.dev/; GitHub API reports licence "Other (NOASSERTION)" [Source](https://api.github.com/repos/AirLabUR/SynthTab)
- README: dataset "released under a CC BY-NC 4.0 license"; downloads via UR Box (rochester.app.box.com/v/SynthTab-Dev and /SynthTab-Full) plus a Baidu Netdisk mirror; "Total file size is close to and less than 2 TB", zips "less than 50 GB" each [Source](https://raw.githubusercontent.com/AirLabUR/SynthTab/main/README.md)
- The repo's LICENSE file is the text of "Creative Commons Attribution 4.0 International" (CC BY 4.0), i.e. the code licence differs from the CC BY-NC 4.0 stated for the data [Source](https://raw.githubusercontent.com/AirLabUR/SynthTab/main/LICENSE)
- Site: ~6,700 hours of audio, 15,211 tracks, 23 timbres (7 acoustic + 16 electric) [Source](https://synthtab.dev/)
Report impact: confirms (data CC BY-NC 4.0) and adds — code LICENSE file is CC BY 4.0; hosting is UR Box, not Zenodo/HF.

### C2. GOAT dataset (Loth et al., ISMIR 2025; used by Noise2Fret)
Previously unverified: access terms, licence, request route.
Found:
- Paper: Jackson Loth, Pedro Sarmento, Saurjya Sarkar, Zixun Guo, Mathieu Barthet, Mark Sandler, "GOAT: A Large Dataset of Paired Guitar Audio Recordings and Tablatures", ISMIR 2025 poster P6-5; 5.9 h DI audio + 29.5 h amp-augmented [Source](https://ismir2025program.ismir.net/poster_245.html)
- PDF: "We distribute the GOAT dataset on the Zenodo platform. The dataset is made available by request to better control its use for research purposes only." and "because we do not exclusively own the copyrights for some of its content, we intend to make the dataset available for research purposes only, upon request." Reamping code: https://github.com/JackJamesLoth/GOAT-Dataset [Source](https://arxiv.org/pdf/2509.22655)
- Zenodo record 15690894: licence CC BY-NC 4.0, access "Restricted", 5.1 TB, version 1 published 2025-09-21; request text asks users to "contact us and include a short description of what you plan to use the dataset for"; "for research purposes only and is not intended for use in any commercial product" [Source](https://zenodo.org/records/15690894)
- GitHub JackJamesLoth/GOAT-Dataset: created 2025-03-28, last push 2025-09-30, 26 stars, no licence set [Source](https://api.github.com/repos/JackJamesLoth/GOAT-Dataset)
- Noise2Fret (arXiv 2608.30854) trains on GuitarSet and GOAT and describes its training data as "publicly available research datasets released under appropriate licenses for academic use"; code at https://github.com/RiccardoVib/Noise2Fret [Source](https://arxiv.org/pdf/2608.30854)
Report impact: confirms — request-only via Zenodo restricted record, CC BY-NC 4.0, research-only; request = Zenodo "request access" with a short use description.

### C3. Ukulele audio datasets (2025-2026 and older)
Previously unverified: whether any exist.
Found:
- Hugging Face: FasaiRakphakdee/Basic-Chord-Ukulele-Data — 1,960 audio clips (1.81-5.83 s), 832 MB, 28 basic chords (major, 7, m, m7 across A-G), metadata includes strumming direction (down/up) and clean vs mic-noise; licence CC BY-NC 4.0; last modified 2024-12-24 [Source](https://huggingface.co/datasets/FasaiRakphakdee/Basic-Chord-Ukulele-Data) [Source](https://huggingface.co/api/datasets?search=ukulele&limit=50). sachet911/ukulelebungkus (2026-06-27) is empty [Source](https://huggingface.co/datasets/sachet911/ukulelebungkus)
- Zenodo keyword "ukulele" (newest 25): no audio datasets; only 3D models, a 2026 soundboard vibroacoustics dataset (10.5281/zenodo.22692775, CC BY 4.0, 72.7 MB MATLAB/measurements), a restricted 2025 folk-punk performance recording, and the Padellini notation PDFs [Source](https://zenodo.org/api/records?q=ukulele&size=25&sort=newest)
- GitHub search "ukulele dataset" created after 2025-01-01: only two churn-clustering repos on the Yousician dataset [Source](https://api.github.com/search/repositories?q=ukulele+dataset+created:>2025-01-01&sort=updated&per_page=30)
- Yousician "Open Data Ukulele": 1,000 anonymised users, 30 days, "over 500K played song exercises", "over 10M evaluated instances", "over 100 different chord voicings"; JSON performance-evaluation data, no audio, no explicit licence; download https://d3mzlbmn9ukddk.cloudfront.net/Media/yousician_ukulele.json.zip [Source](https://yousician.com/open-data)
- Kaggle: web search found no ukulele audio dataset (Kaggle search page not fetchable without JS; only the "5000 chords" metadata DB surfaced) [Source](https://huggingface.co/ffatty/5000-chords)
- Older/general: AudioSet "Ukulele" class = 5,292 videos, 14.7 h (eval 60, balanced train 60, unbalanced 5,172), ~90 % label accuracy [Source](https://research.google.com/audioset/dataset/ukulele.html); OpenMIC-2018 includes "ukulele" as one of its 20 classes (CC BY 4.0, 10-s clips) [Source](https://raw.githubusercontent.com/cosmir/openmic-2018/master/class-map.json) [Source](https://zenodo.org/records/1432913); IRMAS (11 classes, CC BY-NC-SA 4.0) has no ukulele [Source](https://zenodo.org/records/1290750); Medley-solos-DB (8 classes, 21,571 clips, CC BY 4.0) has no ukulele [Source](https://zenodo.org/records/3464194); NSynth instrument families contain no ukulele (known taxonomy; not re-fetched)
- Phithak 2015 used 10 ukulele songs; no public release found (see A3). "UkuleleDB": no such dataset surfaced in any search — still unknown.
Report impact: adds — one small HF chord dataset (1,960 clips, CC BY-NC) and OpenMIC-2018/AudioSet weak labels are the only ukulele audio sources; no 2025-2026 ukulele audio dataset on Zenodo/Kaggle/GitHub.

### C4. FreePats ukulele soundfont
Previously unverified: page URL, licence, provenance.
Found:
- Page: https://freepats.zenvoid.org/GuitarFamily/ukulele.html (linked from the Guitar Family section of the index). Sound set "Ukulele", version 2026-08-11; "Recorded by Mateusz Dąbrowski from a Flight Fireball ukulele (tenor)"; "Published under the terms of the Creative Commons CC0 1.0 public domain dedication"; range C4-C6 plus body-tap and chuck articulations; single session, RØDE Podcaster mic; files Ukulele-SFZ+FLAC-20260811.7z (2.3 MiB), Ukulele-SFZ+WAV-20260811.7z (2.8 MiB), Ukulele-SF2-20260811.7z (1.5 MiB) [Source](https://freepats.zenvoid.org/GuitarFamily/ukulele.html) [Source](https://freepats.zenvoid.org/)
Report impact: confirms — CC0 1.0; adds exact URL, provenance and file sizes (very small bank: two octaves, single dynamic).

### C5. Koops et al. 2019 CASD (JNMR 48(3)) inter-annotator agreement
Previously unverified: quantitative agreement figures.
Found:
- Paper: Koops, de Haas, Burgoyne, Bransen, Kent-Muller, Volk, "Annotator subjectivity in harmony annotations of popular music", JNMR 2019, 48(3); open PDF at UvA [Source](https://pure.uva.nl/ws/files/62264010/Annotator_subjectivity_in_harmony_annotations_of_popular_music.pdf)
- Dataset: 50 Billboard songs, 4 expert annotators; "290 unique chord labels"; per-annotator unique labels 148, 127, 201, 120; intersection "only 56 chord labels"; ~11 % of labels are inversions [Source](https://pure.uva.nl/ws/files/62264010/Annotator_subjectivity_in_harmony_annotations_of_popular_music.pdf)
- Table 3, average pairwise WCSR agreement between annotators (mean, sd): ROOT 0.76 (0.19); MAJMIN 0.73 (0.20); MAJMIN_INV 0.67 (0.24); MIREX 0.74 (0.18); THIRDS 0.74 (0.19); THIRDS_INV 0.67 (0.24); TRIADS 0.71 (0.21); TRIADS_INV 0.65 (0.24); TETRADS 0.57 (0.24); TETRADS_INV 0.52 (0.24); SEVENTHS 0.60 (0.24); SEVENTHS_INV 0.54 (0.25). Root agreement "as low as 0.005" on some songs; inversions cost "around 5 percentage points" on average, "up to 31 percentage points" per song [Source](https://pure.uva.nl/ws/files/62264010/Annotator_subjectivity_in_harmony_annotations_of_popular_music.pdf)
- Table 4, agreement of annotators with the Billboard reference: ROOT 0.77 (0.16); MAJMIN 0.77 (0.16); MAJMIN_INV 0.72 (0.19); MIREX 0.77 (0.13); THIRDS 0.75 (0.16); TRIADS 0.71 (0.18); TETRADS 0.57 (0.22); SEVENTHS 0.63 (0.21); SEVENTHS_INV 0.59 (0.23) [Source](https://pure.uva.nl/ws/files/62264010/Annotator_subjectivity_in_harmony_annotations_of_popular_music.pdf)
- Krippendorff's alpha: "With the exception of root, we find that the average α ≤ 0.667"; means range "from 0.63 (thirds, σ = 0.18) to 0.42 (tetrads_inv, σ = 0.17)" [Source](https://pure.uva.nl/ws/files/62264010/Annotator_subjectivity_in_harmony_annotations_of_popular_music.pdf)
- "Subjectivity ceiling": MIREX 2017 best ACE on Billboard2012 scored 0.86 / 0.86 / 0.83 / 0.63 / 0.61 (root / majmin / majmin_inv / sevenths / sevenths_inv) vs CASD inter-annotator 0.76 / 0.73 / 0.67 / 0.60 / 0.54; abstract: "73 percent overlap on average for the traditional major–minor vocabulary and 54 percent overlap for the most complex chord labels", ACE exceeds the ceiling "by about 10 percent" [Source](https://pure.uva.nl/ws/files/62264010/Annotator_subjectivity_in_harmony_annotations_of_popular_music.pdf)
Report impact: adds — full numeric tables; confirms the 73 %/54 % headline figures.

---

## 13. Other items from the Step-1 gap list (transcription and misc)

### F. Omnizart — CHANGED (unexpected 2026 releases)
Previously unverified: Python/TF pins, last release, Windows statement.
Found:
- PyPI 0.6.3 uploaded 2026-05-31 (0.6.0-0.6.2 on 2026-05-30; previous release 0.5.0 was 2021-12-09). `requires_python >=3.8`; licence MIT; `install_requires` include `tensorflow>=2.5.0; python_version < "3.14"`, `tf-nightly; python_version >= "3.14"`, `tf-keras; python_version >= "3.9" and python_version < "3.14"`, `madmom>=0.16.1`, `vamp>=1.1.0`, `sherpa-onnx>=1.10.0`, `setuptools<82`. pyproject.toml (poetry section): `python = ">=3.8,<3.15"`. — [PyPI JSON](https://pypi.org/pypi/omnizart/json), [pyproject.toml](https://raw.githubusercontent.com/Music-and-Culture-Technology-Lab/omnizart/master/pyproject.toml), [setup.py](https://raw.githubusercontent.com/Music-and-Culture-Technology-Lab/omnizart/main/setup.py), [releases](https://github.com/Music-and-Culture-Technology-Lab/omnizart/releases/tag/v0.6.3)
- Repo: 1983 stars, last push 2026-05-31, not archived. — [repo API](https://api.github.com/repos/Music-and-Culture-Technology-Lab/omnizart)
- Windows: README has no Windows support statement; its only compatibility note is "Currently, Omnizart is **incompatible for ARM-based MacOS** system due to the underlying dependencies." Maintainer issue #6 "Known issues when installing omnizart on Windows" (open since 2020-11-06): madmom needs "VS C++ build tools"; "The module `omnizart chord` relies on `vampy` ... originally compiled for 32-bit python2.7 on Windows ... There is currently no workaround ... the only solution would be to use the provided docker image". Other Windows issues: #57, #73, #78. — [README](https://raw.githubusercontent.com/Music-and-Culture-Technology-Lab/omnizart/main/README.md), [issue #6](https://github.com/Music-and-Culture-Technology-Lab/omnizart/issues/6), [issue search](https://api.github.com/search/issues?q=repo:Music-and-Culture-Technology-Lab/omnizart+windows)
Report impact: changes — Omnizart was revived in May 2026 (0.6.x, Python 3.8-3.14, TF>=2.5 / tf-keras); Windows remains officially unsupported (chord module's vamp dependency), Docker recommended.

### G. librosa.pyin + Tony/pYIN note tracker + Vamp parameters — CONFIRMED (doc URL corrected)
Previously unverified: current signature/returns; Tony HMM description; pYIN plugin parameters.
Found:
- URL note: `https://librosa.org/doc/latest/generated/librosa.pyin.html` and `/doc/main/...` both return HTTP 404 (the index pages exist); the versioned page `https://librosa.org/doc/0.11.0/generated/librosa.pyin.html` returns 200. Current PyPI librosa is 1.0.0 (2026-08-11). — [curl status checks], [PyPI](https://pypi.org/pypi/librosa/json)
- Rendered 0.11.0 signature: `librosa.pyin(y, *, fmin, fmax, sr=22050, frame_length=2048, win_length=<DEPRECATED parameter>, hop_length=None, n_thresholds=100, beta_parameters=(2, 18), boltzmann_parameter=2, resolution=0.1, max_transition_rate=35.92, switch_prob=0.01, no_trough_prob=0.01, fill_na=nan, center=True, pad_mode='constant')`. Returns: "f0: np.ndarray [shape=(…, n_frames)] time series of fundamental frequencies in Hertz. voiced_flag: np.ndarray [shape=(…, n_frames)] time series containing boolean flags indicating whether a frame is voiced or not. voiced_prob: np.ndarray [shape=(…, n_frames)] time series containing the probability that a frame is voiced." — [librosa 0.11.0 docs](https://librosa.org/doc/0.11.0/generated/librosa.pyin.html)
- Main-branch source (1.x) drops `win_length` and adds `transition_min_prob: float | None = 1e-4` ("only transitions with probability at least `transition_min_prob` are considered ... approximate inference, but can significantly reduce computation time"); docstring: "The recommended minimum is ``librosa.note_to_hz('C2')`` (~65 Hz) though lower values may be feasible"; `hop_length` "defaults to ``frame_length // 4``"; `max_transition_rate` "maximum pitch transition rate in octaves per second"; `fill_na` "If ``None``, the unvoiced frames will contain a best guess value." — [librosa/core/pitch.py](https://raw.githubusercontent.com/librosa/librosa/main/librosa/core/pitch.py)
- Tony paper (Mauch, Cannam, Bittner, Fazekas, Salamon, Dai, Bello, Dixon, TENOR 2015; preprint fetched via Wayback because code.soundsoftware.ac.uk refused connections): "The note transcription method takes as an input the pYIN pitch track and outputs discrete notes on a continuous pitch scale, based on Viterbi-decoding of a second, independent hidden Markov model (HMM) ... models pitches from MIDI pitch 35 (B1, ≈61 Hz) to MIDI pitch 85 (C♯6, ≈1109 Hz) at 3 steps per semitone, resulting in n = 207 distinct pitches. Following Ryynänen [21] we represent each pitch by three states representing attack, stable part and silence"; emission Gaussian with "τ = 0.1", "v = 0.5 is the prior likelihood of a frame being voiced", "attack states have a larger standard deviation (σ = 5 semitones) than stable parts (σ = 0.9)"; "3-state left-to-right HMM consisting of Attack, Stable and Silent states ... high self-transition probability (0.9, 0.99 and 0.9999 ...)"; transition heuristic: "(1) a note's pitch has to be either the same as the preceding note or at least 2/3 semitones different; (2) small pitch changes are more likely than larger ones; (3) the maximum pitch difference between two consecutive notes is 13 semitones." Post-processing: amplitude-based onset segmentation (RMS ratio r = a_{i+1}/a_{i-1}, "any rise with 1/r < s is considered part of an onset") and "minimum duration pruning, simply discards notes shorter than a threshold, usually chosen around 100 ms." Results on 38 solo vocal pieces: overall accuracy "0.83–0.85"; "a combination of onset detection and minimum duration pruning leads to COnPOff F values of up to 0.50, compared to 0.38 for the baseline pYIN and 0.45 for the best other algorithm (melotranscript)"; COnPOff tolerances "onset time (±5 ms), pitch (±0.5 semitones) and offset (± 20% of ground truth note duration)". Annotation study: 96 recordings; "The baseline annotation time is 437 seconds, more than 7 minutes. (The mean duration of the pieces is 179 seconds ...)". — [Tony preprint via Wayback](https://web.archive.org/web/2024id_/https://code.soundsoftware.ac.uk/attachments/download/1423/tony-paper_preprint.pdf), [publication record](https://code.soundsoftware.ac.uk/publications/147)
- pYIN Vamp parameters (Tony wiki "PYIN Parameters", pYIN v1.1): `lowampsuppression` "Suppress low amplitude pitch estimates" range 0.0-1.0 default 0.1 (Tony "Penalise Soft Pitches" on = 0.2); `onsetsensitivity` "Onset sensitivity" 0.0-1.0 default 0.7; `prunethresh` "Duration pruning threshold" 0.0-0.2 default 0.1; `precisetime` toggle default Off; `threshdistr` "Yin threshold distribution" 8 options default "Beta (mean 0.15)"; `fixedlag` toggle default On; `outputunvoiced` three-way toggle default Off. Sonic Annotator transform id `vamp:pyin:pyin:smoothedpitchtrack`. (vamp-plugins.org/plugin-doc/pyin.html returns 404.) — [PYIN Parameters wiki via Wayback](https://web.archive.org/web/2024id_/https://code.soundsoftware.ac.uk/projects/tony/wiki/PYIN_Parameters)
Report impact: confirms — signature/returns as assumed; cite the 0.11.0 URL (latest/main 404); Tony's 3-state-per-pitch HMM at 1/3-semitone resolution with 100 ms pruning is documented with exact parameters.

### H. Pati & Lerch 2017 guitar solo detection — CHANGED (venue and metric)
Previously unverified: venue, F-measure, feature set, dataset size.
Found:
- Venue is the AES Conference on Semantic Audio, Erlangen, 2017 June 22-24 (not ICASSP). — [PDF](https://musicinformatics.gatech.edu/wp-content_nondefault/uploads/2017/06/Pati_Lerch_2017_A-Dataset-and-Method-for-Electric-Guitar-Solo-Detection-in-Rock-Music.pdf)
- Dataset: "A total of 60 full-length songs were chosen; 37 songs are taken from the list '100 Best Guitar Solos of All Time' and 23 additional songs ..."; "355 minutes of audio out of which nearly 75% constitutes the non-solo part and 25% constitutes the guitar solo. The median length of a guitar solo segment is around 35 seconds"; named "GSD (Guitar Solo Detection) dataset". — same PDF
- Features: "17 baseline features" = "spectral centroid, ... spectral crest factor, spectral flux and the 2nd–13th MFCCs"; "2 predominant pitch-based features" (fundamental pitch value and pitch confidence); "2 structural segmentation-based features" (number of repetitions of a segment, normalised duration) → "21-dimensional feature vector per input block"; SVM classifier; post-processing with k = 4 s. — same PDF
- Table 1 (all %), columns R1 / B / P / S / BP / BS / BSP / BSP_PP: micro-acc m 74.7 / 78.4 / 67.8 / 63.1 / 79.5 / 79.3 / 80.7 / 82.6; macro-acc M 50.0 / 74.3 / 69.5 / 57.2 / 75.8 / 75.4 / 76.7 / 78.6; precision p – / 54.1 / 43.2 / 33.9 / 56.3 / 56.1 / 57.5 / 63.3; recall r – / 67.0 / 69.8 / 49.6 / 68.9 / 68.3 / 69.9 / 71.8; f-measure f – / 59.8 / 53.4 / 40.3 / 62.0 / 61.6 / 63.1 / 67.3. Abstract: "A macro-accuracy of 78.6% with a solo detection precision of 63.3%". — same PDF
Report impact: changes — best solo-detection F-measure is 67.3% (precision 63.3, recall 71.8) at AES Semantic Audio 2017; 60 songs / 355 min confirmed.

### I. Camacho 2022 and Deng & Kwok 2016 (bass/inversion) — CHANGED (numbers now available)
Previously unverified: whether bass estimation improved inversion accuracy, with numbers.
Found:
- Camacho, "Reconocimiento automático de acordes basado en una clasificación de las clases de altura por su volumen y una estimación del bajo" (English title in dblp: "Automatic Chord Recognition Based on Bass Estimation and Pitch Classes Classification by Volume", CLEI 2022, pp. 1-8). Knowledge-based: classifies pitch classes by total volume into a "word", looks it up in an expert-made dictionary, "Por último, usa la estimación del bajo para seleccionar la acepción correcta" (bass estimate picks the correct sense/inversion). Evaluation on Beatles + Queen with Isophonics annotations but manually entered chord boundaries. Cuadro 1 (% time correct), columns Root / Maj/min / Maj/Min+Bs / Sevenths / Sevenths+Bs: AC 95.20 / 92.98 / 90.38 / 82.43 / 79.45; JLCX1 86.75 / 86.25 / 84.44 / 75.87 / 74.39; FK2 87.38 / 86.80 / 83.43 / 75.55 / 72.60; CM1 78.66 / 75.51 / 72.58 / 54.78 / 52.36. Text: adding bass/inversion cost AC only 2.60 points (92.98 → 90.38) vs 1.81 (JLCX1), 3.37 (FK2); "En todas las evaluaciones, AC estuvo al menos un 5 % por encima de los demás algoritmos." No ablation without the bass estimator is reported, and boundaries were hand-set, so the comparison is not like-for-like. — [UCR Kérwa PDF](https://www.kerwa.ucr.ac.cr/bitstreams/46f1d6d1-e53e-46f8-85ee-9c0b04534508/download), [dblp (Camacho)](https://dblp.org/pid/44/935.html)
- Deng & Kwok, "A Hybrid Gaussian-HMM-Deep-Learning Approach for Automatic Chord Estimation with Very Large Vocabulary", ISMIR 2016. Bass is not estimated separately; the NNLS chromagram is "derived by bass-treble profiling" and the 6-sub-segment notegram input is justified because "the number of sub-segments should at least reflect the temporal order of bass line in order to differentiate root position from inversions." Table 1 WCSR (MajMin / MajMinBass / Sevenths / SeventhsBass): Chordino 74.30 / 71.40 / 52.99 / 50.60; CJ-DBN 70.68 / 66.52 / 58.23 / 54.71; CJKU-BLSTM 72.62 / 70.47 / 59.37 / 57.47. Authors: "compared with Chordino, CJ-DBN has a better chance of bass confusion, but less chance of seventh confusion"; "in both systems, there are much higher chances of making seventh confusion than bass confusion." Per-type WCSR (Table 2): maj/5 Chordino 19.9 vs CJKU-BLSTM 22.4; maj/3 17.1 vs 16.1; min/b3 0.0 vs 3.2; test-set share: M/5 2.0%, M/3 1.0%, m/b3 0.4%, m/5 0.6%, M 63.3%. Bass confusion matrices (Table 3/4): Chordino recognises maj/3 correctly 0.19, maj/5 0.23, min/b3 0.00, min/5 0.00; CJ-DBN maj/3 0.23, maj/5 0.19, min/b3 0.01, min/5 0.06. — [ISMIR 2016 PDF](https://archives.ismir.net/ismir2016/paper/000058.pdf)
- Deng & Kwok 2017 (arXiv:1709.07153) adds: "Of all the systems submitted to MIREX ACE after the new evaluation standard, only one supports chord inversions"; "systems that do not support inversions could achieve relatively higher scores than those that support inversions under SeventhsBass evaluation"; and the DL models show "over-fitting of root position chords and the under-fitting of chord inversions". — [arXiv:1709.07153 PDF](https://arxiv.org/pdf/1709.07153)
Report impact: changes — Camacho's explicit bass estimator yields the smallest root→inversion drop (2.6 pts) and 90.38% Maj/Min+Bass, but with manual boundaries and no ablation; Deng & Kwok show inversion WCSRs stuck near 20% (maj/3, maj/5) and ~0-6% (min inversions) for implicit-bass models, which supports an explicit bass-stem prior.

### J. "DrumFormer" — STILL UNKNOWN (no such model found)
Previously unverified: existence.
Found:
- arXiv API `all:DrumFormer` returns zero entries; GitHub repository search for "DrumFormer" returns `total_count: 0`; three web searches return only the Voxengo "Drumformer" multiband dynamics plug-in and generic ADT papers. Closest transformer ADT work found: "Transformer-based Note level Automatic Drum-Set Transcription" (ResearchGate listing, Transformer + SemiCRF loss, >1000-minute dataset) and Noise-to-Notes (arXiv:2509.21739). — [arXiv API](http://export.arxiv.org/api/query?search_query=all:DrumFormer&max_results=10), [GitHub search](https://api.github.com/search/repositories?q=DrumFormer), [Voxengo Drumformer](https://kvraudio.com/marketplace/drumformer-by-voxengo)
Report impact: changes — drop "DrumFormer" as a drum transcription model name; the only product by that name is an audio plug-in.

### K. Sayegh 1989 optimum path paradigm — CONFIRMED (via citing papers; primary abstract not accessible)
Previously unverified: abstract / cost model description.
Found:
- Bibliographic: S. I. Sayegh, "Fingering for string instruments with the optimum path paradigm," Computer Music Journal, vol. 13, no. 3, pp. 76–84, 1989. — [Bontempi et al. 2024, arXiv:2407.09052 ref [9]](https://www.arxiv.org/pdf/2407.09052), [Hori & Sagayama ISMIR 2016 ref [10]](https://archives.ismir.net/ismir2016/paper/000285.pdf)
- Cost-model description (Bontempi et al. 2024): "Sayegh (1989) [9] tackles the fingering procedure by solving a Shortest Path Problem (SPP) on a weighted and layered directed graph (a so-called Viterbi network) in which each layer corresponds to each note of the sequence and contains nodes corresponding to admissible fingerings of such a note. Since only position and string changes between a note and the consecutive one affect the fingering attributes, the weights of such attributes can be directly associated with arcs between two consecutive layers. Concerning the considered attributes, two broad classes of rules may be identified. The first one relates to ease of execution and the second to the homogeneity of the sound generated." — [arXiv:2407.09052](https://www.arxiv.org/pdf/2407.09052)
- Hori & Sagayama 2016: "Sayegh [10] first formulated fingering decision of string instruments as a problem of path optimization. Radicioni et al. [8] extended Sayegh [10]'s approach by introducing segmentation of musical phrase. Radisavljevic and Driessen [9] introduced a gradient descent search for the coefficients of the cost function for path optimization." — [ISMIR 2016 paper 285](https://archives.ismir.net/ismir2016/paper/000285.pdf)
- The JSTOR/MIT Press abstract page itself was not fetched (JSTOR issue TOC only: https://www.jstor.org/stable/i287633); escholarship PDF link returned HTML.
Report impact: confirms — layered Viterbi/shortest-path over per-note fingering candidates with arc costs for position/string changes (ease of execution + timbral homogeneity); exact weight values remain unavailable without the primary PDF.

### L. Böck et al. — skipped (another agent)
### M. Perlence/PyGuitarPro — skipped (another agent)

---

(Sections 9, 10 and 12 verified by a delegated sub-task.)
