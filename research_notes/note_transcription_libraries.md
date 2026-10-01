# Python libraries and models for automatic music transcription (monophonic, polyphonic piano/guitar, guitar tablature), as of 2026-10-01

Scope note: all dates below are as reported by the cited source on 2026-10-01. "Last release" means the latest PyPI version or GitHub state the source showed; where a page did not show a date, this is flagged. Two of the guitar-tab papers (TART, Noise2Fret) are arXiv preprints from Aug/Sep 2026 and have not been peer reviewed.

## Key Question 1: Monophonic pitch tracking (CREPE/torchcrepe, pYIN, SWIPE, PESTO, RMVPE, FCPE, SwiftF0, Praat) — which is best for electric guitar riffs vs. vocals?

### Takeaway
On the only large independent cross-dataset benchmark found (lars76/pitch-benchmark, 19 trackers, 10 corpora, noisy/reverberant variants), SwiftF0 (0.781 pitch F1@50c, CPU-only ONNX, ~180x real time) and RMVPE (0.768, GPU-oriented) lead, with FCPE (0.728) next and CREPE/torchcrepe (~0.69, 0.4x real time on one CPU core) and PESTO (0.680) behind; PESTO's own papers report ~97-98% RPA on MIR-1K/MDB-stem-synth, but MIR-1K is in its training data. No source found that benchmarks these specifically on distorted electric guitar; most published evaluations are vocal-centric (MIR-1K, vocal pitch).

### Cited Findings

Independent benchmark (covers all trackers at once)
- lars76/pitch-benchmark v2.1 compares 19 monophonic trackers (SwiftF0, RMVPE, FCPE, TorchCREPE, CREPE, PESTO, SHS, Praat, RAPT, HarmoF0, SWIPE, SPICE, Harvest, YAAPT, PENN, DIO, BasicPitch, pYIN, REAPER) on 10 corpora, each in 9 audio conditions (clean plus 8 combinations of background sound, reverb, mic filtering); metric is frame-level pitch F1 at +/-50 cents, averaged over the non-clean conditions — [lars76/pitch-benchmark](https://github.com/lars76/pitch-benchmark)
- Top results: SwiftF0 0.781 F1 at 179.6x real time (single core); RMVPE 0.768 at 13.6x; FCPE 0.728 at 27.8x; CREPE/TorchCREPE 0.689-0.691 at 0.4x real time; PESTO 0.680. The author states SwiftF0's lead over RMVPE "is not statistically resolved" — [lars76/pitch-benchmark](https://github.com/lars76/pitch-benchmark)
- Caveat: SwiftF0 and the benchmark are by the same author (Lars Nieradzik), so the benchmark is not fully independent for that entry — [lars76/swift-f0](https://github.com/lars76/swift-f0); [SwiftF0 preprint arXiv:2508.18440](https://arxiv.org/pdf/2508.18440)

SwiftF0 (2025)
- `pip install swift-f0`; Python >=3.8; hard deps only numpy + onnxruntime (no PyTorch, CPU-only inference); 14,386 parameters / 135 KB model; range 46.875-2093.75 Hz (G1-C7); "450 times real time on a laptop CPU"; optional extras for audio I/O, plotting and MIDI export; PyPI version 0.2.0 shown — [swift-f0 PyPI](https://pypi.org/project/swift-f0/0.2.0/); [GitHub README](https://github.com/lars76/swift-f0/blob/main/README.md)
- Preprint: "SwiftF0: Fast and Accurate Monophonic Pitch Detection", Lars Nieradzik, arXiv 2508.18440 (Aug 2025) — [arXiv](https://arxiv.org/pdf/2508.18440)
- Lower bound of G1 (~47 Hz) covers low-E guitar (82 Hz), bass low E (41 Hz) is out of range. License not visible in the fetched pages (gap).

RMVPE (2023)
- "RMVPE: A Robust Model for Vocal Pitch Estimation in Polyphonic Music", arXiv 2306.15412; official PyTorch repo Dream-High/RMVPE, Apache-2.0, only 19 commits; no PyPI package shown; the repo page fetched did not show install instructions, pretrained-weight links, or benchmark numbers (they are in the paper/README not retrieved) — [RMVPE GitHub](https://github.com/Dream-High/RMVPE); [RMVPE paper](https://arxiv.org/pdf/2306.15412)
- Designed for vocals in polyphonic mixtures (i.e., tolerant of accompaniment bleed), which is why it ranks high on the noisy benchmark conditions — [RMVPE paper](https://arxiv.org/pdf/2306.15412)

FCPE (2024 code, 2025 paper)
- `torchfcpe` on PyPI, "official PyTorch implementation of Fast Context-based Pitch Estimation", latest 0.0.4 released 2024-03-06, 40.2 MB wheel (weights bundled) — [torchfcpe PyPI](https://pypi.org/project/torchfcpe/); [libraries.io](https://libraries.io/pypi/torchfcpe)
- Paper: Luo, Zhang, Liu, Li, Liu, submitted 2025-09-18, arXiv 2509.15140 (under review); Lynx-Net with depth-wise separable convolutions on mel spectrogram; 96.79% RPA on MIR-1K ("on par with state of the art"); RTF 0.0062 on one RTX 4090; "2.6x faster than PESTO"; paper license CC BY-NC-SA 4.0 — [FCPE arXiv](https://arxiv.org/abs/2509.15140); [FCPE PDF](https://arxiv.org/pdf/2509.15140)

PESTO (2023 ISMIR, v2 2025 TISMIR)
- `pip install pesto-pitch`; LGPL-3.0; PyTorch + torchaudio required; CLI `pesto file.wav` with outputs .csv (time, frequency, confidence), .npz (timesteps, pitch, confidence, activations) or .png; `-s` step size ms, `--gpu -1` for CPU, `-c` chunking; Python API `pesto.predict(x, sr)` returns timesteps, pitch, confidence, activations; one model `mir-1k_g7`; streaming mode and JIT/ONNX export added (ONNX "twice as fast"); speed claim: 2m51s of audio in ~13 s on an Intel i7-1185G7 CPU (~12x real time) — [SonyCSLParis/pesto](https://github.com/SonyCSLParis/pesto); [pesto-pitch 2.0.0 PyPI](https://pypi.org/project/pesto-pitch/2.0.0/)
- Self-supervised, 130k parameters (170x fewer than CREPE's 22.2M); PESTO v2 reports 97.7% RPA on MIR-1K vs CREPE 97.5%, and 97.0% on MDB-stem-synth; the ISMIR 2023 version reported 96.1% vs CREPE 97.8% on MIR-1K; authors note MIR-1K was used in training RMVPE, CREPE and PESTO so their MIR-1K scores are optimistic; PESTO is claimed more robust to out-of-distribution data than supervised models — [PESTO TISMIR 2025](https://transactions.ismir.net/articles/10.5334/tismir.251); [PESTO v2 arXiv 2508.01488](https://arxiv.org/pdf/2508.01488); [PESTO 2023 arXiv 2309.02265](https://www.alphaxiv.org/abs/2309.02265v1)
- Conflict: PESTO's own papers put it at/above CREPE on MIR-1K, while the lars76 cross-corpus benchmark puts it slightly below CREPE (0.680 vs 0.689); the difference is the test distribution (in-domain MIR-1K vs 10 corpora with noise/reverb) — [TISMIR](https://transactions.ismir.net/articles/10.5334/tismir.251); [lars76/pitch-benchmark](https://github.com/lars76/pitch-benchmark)

CREPE / torchcrepe
- `torchcrepe` (Max Morrison, PyTorch port of CREPE) latest 0.0.24 released 2025-05-16; 10.87M total PyPI downloads, ~204k in the last 30 days (actively used) — [torchcrepe libraries.io](https://libraries.io/pypi/torchcrepe); [pepy](https://pepy.tech/projects/torchcrepe)
- A separate `torchcrepeV2` 0.2.0 package also exists on PyPI — [torchcrepeV2 PyPI](https://pypi.org/project/torchcrepeV2/)
- CREPE is 22.2M parameters (per PESTO paper) and runs at only 0.4x real time on a single CPU core in the benchmark; GPU strongly recommended — [PESTO TISMIR](https://transactions.ismir.net/articles/10.5334/tismir.251); [lars76/pitch-benchmark](https://github.com/lars76/pitch-benchmark)

pYIN (librosa), SWIPE, Praat/parselmouth
- pYIN, SWIPE, Praat, RAPT, YAAPT, DIO/Harvest (WORLD) all appear in the lars76 benchmark as classical DSP trackers, all below the neural trackers on the aggregate noisy-condition F1 (exact per-algorithm values beyond the top 3 and CREPE were not shown in the fetched summary; see repo README table) — [lars76/pitch-benchmark](https://github.com/lars76/pitch-benchmark)
- librosa.pyin documentation page could not be fetched (HTTP 404 at the "latest" URL tried); pYIN is in librosa as `librosa.pyin` and returns f0, voiced_flag, voiced_probs (not verified from a fetched page this session — treat as a gap).

Basic Pitch as a monophonic tracker
- Basic Pitch appears in the lars76 benchmark as one of the 19 trackers; it ranks below the dedicated monophonic trackers on the F1@50c metric (exact value not shown in fetched summary) — [lars76/pitch-benchmark](https://github.com/lars76/pitch-benchmark)

### Inferences
- For isolated vocals or a clean guitar/ukulele stem on a Windows machine without a GPU: SwiftF0 (onnxruntime only, no torch, fastest, top-ranked) is the pragmatic first choice; PESTO is the strongest alternative with a permissive-enough LGPL license and CPU speed ~12x real time; both expose per-frame f0 + confidence that can be segmented into notes.
- For vocals in a Demucs stem with residual bleed, RMVPE (trained for vocals in polyphonic mixes) and FCPE are the most noise-robust per the benchmark; both need PyTorch and RMVPE has no pip package.
- For distorted electric guitar riffs, no tracker has been benchmarked specifically; distortion adds strong harmonics that octave-confuse any f0 tracker, so expect lower accuracy than the vocal numbers above and verify on your own material. Monophonic trackers will fail on double-stops/power chords (two or more simultaneous pitches); use a polyphonic model (Q2) for those passages.
- CREPE remains widely used but is dominated on both accuracy and speed by 2024-2025 models; keep torchcrepe only for compatibility with existing pipelines.

### Gaps
- No source found that evaluates any of these trackers on distorted electric guitar or on ukulele; guitar-specific pitch accuracy is unknown.
- SwiftF0 license, pesto-pitch exact Python-version constraints, and RMVPE install/weights/benchmarks could not be read from fetched pages (PyPI page for pesto-pitch failed to load; RMVPE README not retrieved).
- Per-tracker numbers for pYIN, SWIPE, Praat in the lars76 benchmark were not captured beyond "below the neural trackers"; read the README table for exact values.
- Praat/parselmouth maintenance status and version were not checked.

## Key Question 2: Polyphonic / multi-instrument transcription (Basic Pitch, Onsets and Frames, Bytedance piano transcription, MT3 / YourMT3+, Transkun, Timbre-Trap, 2024-2026 models)

### Takeaway
For piano, Transkun v2 (MIT, `pip install transkun`, 2024) reports the best MAESTRO v3 numbers found (note onset F1 0.953, onset+offset F1 0.984, +velocity 0.935, pedal F1 0.864); Bytedance's Kong et al. (Apache-2.0, `pip install piano_transcription_inference`, 96.72% onset F1 but repo archived Dec 2025) is the proven fallback. For guitar/ukulele/vocals/mixed stems, YourMT3+ (GPL-3.0, 2024, 91.65% onset F1 on GuitarSet, direct vocal transcription) is the strongest open multi-instrument model but is research code with no pip package; Spotify Basic Pitch (Apache-2.0, pip, CPU, Windows) is the easiest to deploy but is much less accurate (80.1% note F1 on GuitarSet, 70.9% on MAESTRO) and last released Aug 2024.

### Cited Findings

Spotify Basic Pitch (2022)
- `pip install basic-pitch`; Apache-2.0 (Spotify AB 2022); Python 3.7-3.11 on macOS, Windows, Ubuntu (Mac M1 limited to 3.10); backends TensorFlow, CoreML, TFLite, ONNX with automatic fallback, TF not installed by default except Python 3.11+; input MP3/OGG/WAV/FLAC/M4A, downmixed to mono, resampled to 22,050 Hz; outputs MIDI with pitch bends, raw predictions (NPZ), note events (CSV), rendered WAV; min/max frequency filters — [spotify/basic-pitch](https://github.com/spotify/basic-pitch)
- Latest PyPI release 0.4.0 on 2024-08-16; no release since (libraries.io flags it as receiving low maintainer attention) — [basic-pitch PyPI](https://pypi.org/project/basic-pitch/); [libraries.io](https://libraries.io/pypi/basic-pitch)
- Paper (ICASSP 2022, "A Lightweight Instrument-Agnostic Model for Polyphonic Note Transcription and Multipitch Estimation"): 16,782 parameters; trained on MAESTRO, Slakh, GuitarSet, iKala, MedleyDB; note F1: MAESTRO 70.9%, GuitarSet 80.1%, Slakh 64.2%, MedleyDB 62.1%, iKala (vocals) 73.5%, Phenicx 55.8%; vs Onsets & Frames on piano 70.9% vs 95.2%; vs Vocano on vocals 73.5% vs 75.1%; peak memory 951 MB, 24 s for a 7:45 file — [ar5iv 2203.09893](https://ar5iv.labs.arxiv.org/html/2203.09893); [arXiv abstract](https://arxiv.org/abs/2203.09893)

Google Magenta Onsets and Frames (2018) and MT3 (2021/2022)
- Onsets and Frames repo README states the repository "is currently inactive and serves only as a supplement to the papers"; TensorFlow 1-era code; supports velocity; also ported to Magenta.js for browser use — [magenta/magenta O&F README](https://github.com/magenta/magenta/blob/main/magenta/models/onsets_frames_transcription/README.md); [magenta oaf-js](https://magenta.tensorflow.org/oaf-js)
- Search summary states the main magenta/magenta repository was archived on 2026-01-06 — [magenta/magenta issue #2003](https://github.com/magenta/magenta/issues/2003) (archival date reported in search aggregate; verify on the repo page)
- MT3 (magenta/mt3): Apache-2.0; T5X/JAX framework; Colab notebook provided for inference; README says "For now, we do not (easily) support training"; no Windows notes; the fetched page did not show archived status or a last-commit date — [magenta/mt3](https://github.com/magenta/mt3). A search aggregate claimed commits in 2026 (dates 2026-03-09, 2026-07-09, 2026-09-29), but these appear to be copybara bot sync commits and were not verified on the page — treat as unconfirmed.
- Magenta discuss thread: MT3 scores better than Onsets and Frames on MAESTRO but does not output velocity; O&F "might generalize better outside of the MAESTRO dataset" (forum opinion, not a measured result) — [magenta-discuss](https://groups.google.com/a/tensorflow.org/g/magenta-discuss/c/BfCi0xr9Dq4)

Bytedance / Kong et al. high-resolution piano transcription (2020)
- Paper "High-resolution Piano Transcription with Pedals by Regressing Onset and Offset Times" (Kong, Li, Song, Wan, Wang; arXiv 2010.01815, Oct 2020, rev. Jul 2021): MAESTRO onset F1 96.72% vs Onsets and Frames 94.80%; pedal onset F1 91.86% — [arXiv 2010.01815](https://arxiv.org/abs/2010.01815)
- Training repo bytedance/piano_transcription: Apache-2.0; archived (read-only) on 2025-12-08; CRNN "Regress_onset_offset_frame_velocity_CRNN"; training needs 29 GB GPU memory (V100, batch 12), ~1 week for 300k iterations; MAESTRO v2 training; frame AP 0.9285, onset MAE 0.097 s, offset MAE 0.135 s, velocity MAE 0.027 — [bytedance/piano_transcription](https://github.com/bytedance/piano_transcription)
- Inference package `pip install piano_transcription_inference`, latest 0.0.6, author Qiuqiang Kong, Python >=3.6, developed with Python 3.7 / PyTorch 1.4 ("should work with other versions, but not fully tested"); outputs MIDI with onsets, offsets, velocity and pedal — [piano-transcription-inference PyPI](https://pypi.org/project/piano-transcription-inference/); [qiuqiangkong/piano_transcription_inference](https://github.com/qiuqiangkong/piano_transcription_inference)
- A Windows/mac GUI wrapper exists: azuwis/pianotrans — [pianotrans](https://github.com/azuwis/pianotrans)

Transkun (2021 neural semi-CRF; v2 ISMIR 2024)
- `pip3 install transkun`; MIT; PyPI 2.0.1 released 2024-09-28; Python >=3.6; CLI `transkun input.mp3 output.mid [--device cuda]`; segment/hop options for long files; outputs MIDI incl. velocity and pedal; README "under construction"; one shipped checkpoint (trained with augmentation, without pedal extension) — [transkun PyPI](https://pypi.org/project/transkun/); [Yujia-Yan/Transkun](https://github.com/yujia-yan/transkun)
- MAESTRO v3 results from the GitHub README: Transkun V2 / V2 Aug / V2 No Ext — note onset F1 0.953 / 0.9505 / 0.8441; note onset+offset F1 0.9832 / 0.984 / 0.9833; onset+offset+velocity F1 0.9349 / 0.9314 / 0.8149; pedal activation F1 0.8642 / 0.8453 / 0.8444 (note: the README's row labels as extracted look inconsistent — the "onset+offset" row exceeding the "onset" row is implausible; the exact row ordering should be checked against the README before quoting) — [Yujia-Yan/Transkun](https://github.com/yujia-yan/transkun)
- Paper: "Scoring Time Intervals using Non-Hierarchical Transformer for Automatic Piano Transcription", ISMIR 2024 (arXiv 2404.09466v6, Nov 2024) — [arXiv 2404.09466](https://arxiv.org/pdf/2404.09466)
- Search aggregate attributes to MIREX 2024: "TransKun V2 Aug achieved 90.81% holistic note F1 (SOTA) and 96.48% summary onset F1 (SOTA)" — [sota2 MAESTRO leaderboard](https://www.sota2.com/research/sota/automatic-piano-transcription-on-maestro-v3-0-0-test) (secondary aggregator; not verified against MIREX page)
- Transkun is offered as a hosted algorithm on mvsep.com, indicating it is used in production — [mvsep Transkun](https://mvsep.com/algorithms/106)
- A 2026 paper used a transcription layer certified at F1 = 0.9791 on the MAESTRO v3 test set (model not named in abstract) — [arXiv 2605.06685](https://arxiv.org/pdf/2605.06685)

YourMT3+ (MLSP 2024)
- GitHub mimbres/YourMT3: GPL-3.0; 247 stars, 30 commits; "pre-release code"; Hugging Face Spaces demo with free GPU (Aug 2024) and Colab demo; README on fetched page does not give pip install, checkpoint links, VRAM, or Windows notes (they may be in subpages/issues); YouTube input in the demo blocked since Nov 2024 — [mimbres/YourMT3](https://github.com/mimbres/YourMT3)
- Paper (Chang, Benetos, Kirchhoff, Dixon; arXiv 2407.04822; IEEE MLSP 2024): PerceiverTF encoder with spectral cross-attention + mixture of experts, multi-channel T5 decoder; 45.8M parameters (YPTF.MoE+Multi), 2.5% more than MT3; input 2.048 s segments at 16 kHz mono; note onset F1: MAESTRO 96.98% (MT3 94.86%), GuitarSet 91.65% (MT3 89.10%), Slakh2100 onset F1 84.56% (MT3 75.20%) and multi-instrument F1 74.84% (57.69%), URMP multi F1 67.98% (59.0%), MIR-ST500 vocals 71.60% with separation vs 71.07% without ("direct vocal transcription capabilities, eliminating the need for voice separation pre-processors"), ENST-Drums 87-89%, MusicNet strings 91.32% / winds 83.46%; on RWC-Pop non-main instruments score below 10%; inference "approximately six minutes of piano music within 40 seconds" on an NVIDIA T4, "36x real-time" in float16 on newer GPUs — [YourMT3+ arXiv HTML](https://arxiv.org/html/2407.04822v1); [MLSP PDF](http://eecs.qmul.ac.uk/~simond/pub/2024/ChangEtAl-MLSP-2024.pdf)

Timbre-Trap (Sony, ICASSP 2024)
- GitHub sony/timbre-trap: MIT; install by cloning and `pip install -e`; pretrained base weights via a Hugging Face Space; `model.transcribe(audio)` API; NSGT-based invertible CQT + 2D autoencoder; dataset wrappers for URMP, Bach10 etc.; 60 commits; no benchmark table on the fetched page; authors Cwitkowitz, Cheuk, Choi, Martinez-Ramirez, Toyama, Liao, Mitsufuji — [sony/timbre-trap](https://github.com/sony/timbre-trap); [arXiv 2309.15717](https://arxiv.org/html/2309.15717v2)
- Output is multi-pitch estimation (frame-level pitch salience), not note events with velocity; it targets low-resource/instrument-agnostic MPE.

Other 2024-2026 multi-instrument work (not packaged tools)
- MR-MT3 "Memory Retaining Multi-Track Music Transcription to Mitigate Instrument Leakage" (arXiv 2403.10024, 2024) — [arXiv](https://arxiv.org/html/2403.10024v1)
- "Timbre-Adaptive Transcription: A Lightweight Architecture with Associative Memory for Dynamic Instrument Separation" (arXiv 2509.12712, Sep 2025) — [arXiv](https://arxiv.org/html/2509.12712v1)
- "A Lightweight Two-Branch Architecture for Multi-Instrument Transcription via Note-Level Contrastive Clustering" (TISMIR 2025) — [TISMIR](https://transactions.ismir.net/articles/10.5334/tismir.300)
- "Toward Fully Self-Supervised Multi-Pitch Estimation" (Cwitkowitz, arXiv 2402.15569, 2024) — [arXiv](https://arxiv.org/html/2402.15569v1)

### Inferences
- Piano stems: Transkun v2 is the current best-accuracy pip-installable choice (MIT, MIDI with velocity + pedal, CPU or CUDA); Kong/Bytedance is a close, longer-proven second and has a Windows GUI, but its training repo is archived and inference code targets PyTorch 1.x.
- Guitar/ukulele/vocal stems where note events (not tab) are needed: YourMT3+ gives roughly +11 points note F1 over Basic Pitch on GuitarSet (91.65 vs 80.1, different papers/eval protocols so not strictly comparable) but costs a GPU, GPL-3.0 licensing, and research-grade setup; its MIR-ST500 numbers show source separation adds only ~0.5 point for vocals, suggesting separation is optional for that model. Basic Pitch remains the "works on Windows CPU in one pip install" option and its pitch-bend output is useful for bends/vibrato.
- Onsets and Frames and MT3 should be considered legacy: inactive repos, TF1/JAX stacks that are painful on Windows; Colab is the realistic way to run MT3.
- Timbre-Trap is a research framework for multi-pitch salience rather than a note/MIDI tool; not a fit for a tab pipeline without extra note segmentation.

### Gaps
- YourMT3+ install procedure, checkpoint download, VRAM needs, and Windows viability were not readable from the fetched README; must be checked in the repo (likely requires Linux/WSL for the training stack, inference via HF Space is the easy path).
- Transkun README benchmark rows need verification (extraction produced implausible row ordering); Transkun inference speed and PyTorch version constraint not stated.
- MIREX 2024 Transkun numbers come from an aggregator (sota2.com), not the MIREX results page.
- MT3 repo current commit dates and archived status unverified; magenta/magenta archival date (2026-01-06) comes from a search summary.
- No Windows-specific confirmation for piano_transcription_inference beyond the existence of the pianotrans GUI.

## Key Question 3: Guitar-specific / tablature transcription (TabCNN, FretNet, GOAT, TART, Noise2Fret, Fretting-Transformer, Fretiq) and robustness on distorted electric guitar

### Takeaway
Open audio-to-tab models remain research code: TabCNN (ISMIR 2019) and FretNet (Yousician/Rochester, 2023, code released) score ~0.72-0.73 tablature F1 on acoustic GuitarSet, and TabCNN drops to 0.45 tab F1 on real effected electric guitar (EGSet12) unless trained with effects-augmented data (0.56). 2025-2026 work (GOAT dataset with amp-augmented DI electric guitar, Noise2Fret diffusion model 0.795 tab F1 on GOAT, TART modular pipeline 54% end-to-end tab F1, Fretting-Transformer for MIDI-to-tab with tuning/capo conditioning) is improving fast, but nothing is pip-installable and none has been shown to work on distorted guitar inside a full rock mix.

### Cited Findings

TabCNN (2019) and FretNet (2023)
- TabCNN (Wiggins & Kim, ISMIR 2019): CNN mapping audio directly to tablature, "simultaneously leveraging physical playability constraints and differences in string timbres implicit in the data" — [ISMIR 2019 paper](https://archives.ismir.net/ismir2019/paper/000033.pdf)
- FretNet ("Continuous-Valued Pitch Contour Streaming for Polyphonic Guitar Tablature Transcription", Cwitkowitz, Hirvonen, Klapuri; arXiv 2212.03023v2, 2023-03-14; work done as a Yousician research intern); code at cwitkowitz/guitar-transcription-continuous (uses mir_eval, cluster-based note grouping); GuitarSet results: tablature F1 FretNet 0.727 vs TabCNN 0.717; multipitch F1 0.818 vs 0.820; string-dependent note F1 0.506 vs 0.430; string-agnostic note F1 0.664 vs 0.583; main gain is continuous-pitch (bend/vibrato) resolution — [FretNet arXiv HTML](https://arxiv.org/html/2212.03023); [GitHub](https://github.com/cwitkowitz/guitar-transcription-continuous)

Robustness to electric guitar effects (2024)
- Pedroza, Abreu, Corey, Roman, "Leveraging Real Electric Guitar Tones and Effects to Improve Robustness in Guitar Tablature Transcription Modeling" (arXiv 2405.14679, May 2024, rev. Jul 2024): TabCNN trained on GuitarSet, plus synthetic GuitarSetFX / GuitarProFX (real electric tones through effects); new EGSet12 evaluation set of 12 professional electric guitar performances; on GuitarSet cross-validation, multipitch F1 0.826 -> 0.837 and tab F1 0.748 -> 0.746 (no change); on EGSet12 (out-of-domain electric), tab F1 0.447 -> 0.557 with GuitarSetFX training and multipitch F1 improved >10 points; TDR up >10 points with GuitarProFX; code and evaluation set released on the project website — [ar5iv 2405.14679](https://ar5iv.labs.arxiv.org/html/2405.14679); [arXiv abstract](https://arxiv.org/abs/2405.14679)

GOAT dataset (ISMIR 2025)
- "GOAT: A Large Dataset of Paired Guitar Audio Recordings and Tablatures" (Loth et al., ISMIR 2025, arXiv 2509.22655): 5.9 h of high-quality direct-input electric guitar from many guitars/players, annotated with string/fret and playing techniques; amp-simulation augmentation yields 29.5 h; baseline experiments for guitar MIDI transcription and an AGTT approach using Whisper; the AMP-trained model matches the DI model on some splits and "significantly outperforms" on others; access via Zenodo, helper code on GitHub — [ISMIR 2025 poster](https://ismir2025program.ismir.net/poster_245.html); [JackJamesLoth/GOAT-Dataset](https://github.com/JackJamesLoth/GOAT-Dataset); [arXiv 2509.22655](https://arxiv.org/abs/2509.22655)

Noise2Fret (Aug 2026 preprint)
- "Playability-Aware Audio-to-Tablature Guitar Transcription via Diffusion Models" (Simionato & Bigo, Univ. Bordeaux/CNRS/LaBRI; arXiv 2608.30854v1, 2026-08-31): diffusion model generating tab via a continuous latent of string/fret targets; evaluated on GuitarSet and GOAT; on GOAT: Noise2Fret pitch F1 0.800 / tab F1 0.795 / TDR 0.993 vs TabCNN 0.664 / 0.656 / 0.987 and FretNet 0.669 / 0.662 / 0.989; code at RiccardoVib/Noise2Fret under CC BY-SA 4.0; experiments "restricted to standard-tuned recordings without effects processing" and explicitly exclude "electric timbres" (distorted) — [Noise2Fret arXiv HTML](https://arxiv.org/html/2608.30854v1); [GitHub](https://github.com/RiccardoVib/Noise2Fret)

TART (Sep 2026 preprint)
- "TART: A Modular Tool for Technique-Aware Audio-to-Tablature Guitar Transcription" (arXiv 2609.11904v1, 2026-09-10; CC BY 4.0): four stages — (1) audio-to-MIDI CRNN adapted from Kong et al. (onset/offset/velocity from log-mel), (2) CNN-BiLSTM technique classifier (~160k params; bend, hammer-on/pull-off, harmonics, palm mute, slide, vibrato, picking, plus kick/snare), (3) "AudioFret" T5 encoder-decoder (15M params) conditioned on MIDI + per-note audio embeddings for string/fret, (4) beat-aligned MusicXML tab generator; trained on GAPS, Guitar-TECHS, Leduc, GOAT (DI), SynthTab, DadaGP; evaluated on GuitarSet, EGDB plus new noisy variants; audio-to-MIDI F1@50ms 81.35% average over 4 benchmarks; string-fret tab F1 71.8% with oracle MIDI; end-to-end tab F1 54.08%; +8.5 points string-fret F1 over TabCNN and the original Fretting-Transformer; noise-robust augmentation "preserving onset alignment while simulating realistic recording-condition noise"; no code-availability statement in the fetched text — [TART arXiv HTML](https://arxiv.org/html/2609.11904); [PDF](https://arxiv.org/pdf/2609.11904)

Fretting-Transformer (MIDI-to-tab, ICMC 2025)
- Hamberger, Murgul, Schmidt, Heizmann (Klangio-affiliated authors per name match — unverified), arXiv 2506.14223, 2025-06-17, accepted ICMC 2025: T5 encoder-decoder converting MIDI to guitar tab; trained on DadaGP, GuitarToday, Leduc; "surpasses baseline methods like A* and commercial applications like Guitar Pro"; tuning/capo conditioning improves results; abstract gives no accuracy numbers and no code link — [arXiv 2506.14223](https://arxiv.org/abs/2506.14223)

Other guitar-specific items
- SynthTab (ICASSP 2024, yongyizang/SynthTab): synthesized guitar audio paired with tabs for pretraining GTT models — [GitHub](https://github.com/yongyizang/SynthTab)
- Fretiq (arXiv 2607.18303, Jul 2026): "browser-native electric guitar string classification via engineered spectral features" — the HTML fetch returned 404; only the title is confirmed — [arXiv PDF](https://arxiv.org/pdf/2607.18303)
- Sony: Timbre-Trap (Q2) is Sony's instrument-agnostic MPE work; Cwitkowitz moved from Yousician (FretNet) to Sony. No Yamaha guitar-tab transcription code was found in this session.

Commercial (brief)
- Klangio (Berlin): Guitar2Tabs, Piano2Notes, Sing2Notes, Drum2Notes, Transcription Studio, DAW plugin and a developer API; Guitar2Tabs Pro $6.25/mo billed annually (regular $14.99/mo), 50 transcriptions/month, songs up to 15 min; free tier for short demos — [Guitar2Tabs](https://guitar2tabs.klang.io/); [Songscription comparison](https://www.songscription.ai/blog/best-audio-to-midi-converters)
- AnthemScore: desktop audio-to-sheet-music/MIDI, Windows/Mac/Linux, one-time purchase, 30-day trial — [Songscription AnthemScore alternatives](https://www.songscription.ai/blog/anthemscore-alternatives)
- Melodyne: pitch/time editor with "Save as MIDI"; Essential $99, Studio $699 — [MuseHub guide](https://www.musehub.com/learn/best-music-transcription-software)

### Inferences
- There is no production-ready open-source audio-to-tab library in 2026; TabCNN/FretNet code is runnable but acoustic-only in training, and the two 2026 systems (Noise2Fret, TART) are preprints with CC-licensed code at best.
- The most practical architecture for a tab pipeline today is the TART pattern: a strong audio-to-MIDI note model (Transkun/Kong-style CRNN, YourMT3+, or Basic Pitch) followed by a symbolic MIDI-to-tab fingering step (Fretting-Transformer-style, or a simple playability-cost DP/A*). For ukulele (4 strings, re-entrant tuning) only the symbolic step needs instrument-specific adaptation, which is a strong argument for this two-stage design over end-to-end string/fret models trained on 6-string guitar.
- Distorted electric guitar in rock mixes is the weakest case: TabCNN loses ~30 points tab F1 moving from GuitarSet to clean-ish professional electric recordings (0.748 -> 0.447), and Noise2Fret explicitly excludes effected timbres; expect substantially worse results on Demucs "other" stems containing distorted guitar, and plan for manual correction.

### Gaps
- No paper found that reports tab or note accuracy on distorted electric guitar extracted from full rock mixes; EGSet12 is the closest proxy (real electric performances, solo).
- Fretting-Transformer code availability and numeric accuracy not confirmed; TART code release not confirmed.
- Fretiq content not retrievable (404), so its accuracy and licence are unknown.
- No ukulele-specific transcription dataset or model was found in this session (not searched directly; GuitarSet/GOAT are 6-string guitar).

## Key Question 4: Note-to-MIDI post-processing — onset detection, note segmentation, beat-grid quantization (madmom / BeatNet / Beat This!), pretty_midi / mido / music21

### Takeaway
For beat tracking on Windows in 2025-2026, Beat This! (CPJKU, ISMIR 2024, MIT, `pip install beat-this`, PyTorch >= 2.0, CPU fallback) is the only option that avoids madmom, whose PyPI release (0.16.1) is broken on Python >= 3.10 / NumPy >= 1.24 and has no Windows wheels; BeatNet (CC-BY-4.0) depends on madmom and PyAudio and needs manual wheel installs on Windows. Note-level transcription models (Transkun, Kong, YourMT3+, Basic Pitch) emit MIDI directly, so onset detection is only needed when converting monophonic f0 tracks to notes.

### Cited Findings
- madmom: current PyPI version is limited to Python < 3.10 "because of unresolved issues"; madmom 0.16.1 has compatibility issues with Python >= 3.10 and NumPy >= 1.24 (`MutableSequence` import error, `numpy.float` attribute error); workaround is `pip install git+https://github.com/CPJKU/madmom.git` (dev version 0.17.dev0) or Python 3.9 — [beat_this issue #9](https://github.com/CPJKU/beat_this/issues/9); [madmom installation docs](https://madmom.readthedocs.io/en/latest/installation.html); [madmom issue #478](https://github.com/CPJKU/madmom/issues/478)
- madmom on Windows: "the only working installation is from source, as precompiled Windows packages are not available" — [madmom Windows wiki](https://github-wiki-see.page/m/CPJKU/madmom/wiki/Install-on-Windows); [madmom-users thread](https://groups.google.com/g/madmom-users/c/iOHzcbIp5mg)
- Beat This! (CPJKU/beat_this, ISMIR 2024 "Beat This! Accurate Beat Tracking Without DBN Postprocessing"): `pip install beat-this`; MIT; PyTorch >= 2.0 plus tqdm, einops, soxr, rotary-embedding-torch; FFmpeg for non-WAV input; auto-GPU with CPU fallback (`--gpu=-1`), float16 option; CLI `beat_this audio.file -o out.beats`; batch mode; optional `--dbn` postprocessing needs madmom; outputs beats and downbeats (.beats files readable by Sonic Visualiser); 245 commits; no Windows notes and no release date shown on the fetched page — [CPJKU/beat_this](https://github.com/CPJKU/beat_this)
- BeatNet (mjhydri/BeatNet, ISMIR 2021): CC-BY-4.0; `pip install BeatNet`; Python 3.9+; depends on librosa, madmom (with compatibility workarounds documented), PyAudio (Windows users must download a wheel and install locally); modes streaming / real-time / online / offline; output NumPy array (num_beats, 2) of beat and downbeat times plus tempo and meter; v1.2.0 added official training pipeline; 94 commits — [mjhydri/BeatNet](https://github.com/mjhydri/BeatNet)
- Basic Pitch exposes note-event CSV and MIDI with pitch bends, and tunable min/max frequency; its CLI/API thresholds (onset, frame, minimum note length) are documented in the repo README — [spotify/basic-pitch](https://github.com/spotify/basic-pitch)
- SwiftF0 ships an optional MIDI-export extra, i.e., built-in f0-to-note segmentation — [swift-f0 README](https://github.com/lars76/swift-f0/blob/main/README.md)
- FretNet's released code includes "cluster-based note and pitch contour grouping" for turning continuous pitch streams into notes — [guitar-transcription-continuous](https://github.com/cwitkowitz/guitar-transcription-continuous)
- TART's final stage merges notes and techniques into "beat-aligned MusicXML scores" (an example of beat-grid quantization inside an AMT pipeline) — [TART](https://arxiv.org/html/2609.11904)
- Transkun's CLI offers segment-size/hop-size parameters for long-file processing and writes standard MIDI — [transkun PyPI](https://pypi.org/project/transkun/)

### Inferences
- Pipeline recommendation: (1) model -> MIDI (Transkun / Kong / Basic Pitch / YourMT3+) or f0 -> notes (SwiftF0 MIDI extra, PESTO confidence-gated segmentation); (2) Beat This! for beat/downbeat grid (no madmom needed); (3) pretty_midi/mido to snap onsets to the grid and write MIDI; (4) music21 or a custom A*/DP fingering step for tab/MusicXML. pretty_midi, mido, music21 themselves were not researched this session (see gaps) but are standard pure-Python packages with Windows wheels.
- Avoid madmom-dependent stacks (BeatNet, madmom onset detectors) on Python 3.11+ Windows unless you are willing to build from the git dev branch.

### Gaps
- pretty_midi, mido, music21 versions/maintenance status were not checked (search budget prioritized model research).
- Beat This! accuracy versus madmom/BeatNet numbers were not captured from the fetched README (they are in the ISMIR 2024 paper).
- No dedicated comparison of onset-detection libraries (madmom, librosa.onset, aubio) for guitar was found.

## Key Question 5: Realistic accuracy on Demucs-separated stems vs. clean recordings

### Takeaway
Direct measurements are scarce. The best available data points: YourMT3+ gains only ~0.5 point vocal note F1 from source separation on MIR-ST500 (71.60% vs 71.07%); a singing-transcription study found a dedicated vocal pitch model beat Demucs+CREPE by 3-4 points because the separated stem still contains backing vocals and CREPE jumps between voices; and tab transcription drops ~30 points tab F1 between in-domain acoustic data and out-of-domain real electric recordings even without separation artifacts. Expect note F1 in the 60-75% range on separated vocal/guitar stems versus 90%+ on clean solo-instrument recordings for the best models.

### Cited Findings
- YourMT3+ on MIR-ST500 (pop vocals in mixtures): 71.60% F1 with vocal separation pre-processing vs 71.07% without; the authors present the model as not needing a separation pre-processor — [YourMT3+ arXiv](https://arxiv.org/html/2407.04822v1)
- Search summary of "Pseudo-Label Transfer from Frame-Level to Note-Level in a Teacher-Student Framework for Singing Transcription from Polyphonic Music" (arXiv 2203.13422): JDC pitch estimation "achieves 3 to 4% higher accuracy" than Demucs + CREPE on three metrics; "the separated vocal stem from Demucs includes multiple vocal sources (e.g., chorus ensembles) and CREPE predicts discontinuous pitch contours switching between different voices" (the abstract page fetched did not contain these numbers; they come from the search aggregate of the full paper and should be verified in the PDF) — [arXiv 2203.13422](https://arxiv.org/pdf/2203.13422)
- Best-case clean benchmarks for reference: piano (MAESTRO, solo recordings) onset F1 95-97% (Kong 96.72%, YourMT3+ 96.98%, Transkun ~95%); GuitarSet (solo acoustic, hex-pickup) note onset F1 91.65% (YourMT3+) / 80.1% (Basic Pitch); vocals iKala (clean studio vocals) 73.5% (Basic Pitch); MedleyDB stems 62.1% (Basic Pitch) — [arXiv 2010.01815](https://arxiv.org/abs/2010.01815); [YourMT3+](https://arxiv.org/html/2407.04822v1); [Basic Pitch ar5iv](https://ar5iv.labs.arxiv.org/html/2203.09893)
- Out-of-domain electric guitar (no separation involved): TabCNN tab F1 0.748 on GuitarSet vs 0.447 on EGSet12 real electric performances; effects-augmented training recovers to 0.557 — [ar5iv 2405.14679](https://ar5iv.labs.arxiv.org/html/2405.14679)
- Multi-instrument mixtures without separation: YourMT3+ Slakh2100 multi-instrument F1 74.84%, URMP 67.98%, and "below 10%" for non-main instruments on RWC-Pop (commercial pop) — [YourMT3+](https://arxiv.org/html/2407.04822v1)
- Noise-robustness is now an explicit design goal: TART trains with augmentation that "preserv[es] onset alignment while simulating realistic recording-condition noise" and evaluates on noisy GuitarSet/EGDB variants; its average audio-to-MIDI F1@50ms across four benchmarks is 81.35% — [TART](https://arxiv.org/html/2609.11904)
- Community pipelines (e.g., "coming-undone": Demucs stems -> labelled multi-track MIDI; "stem-score-lab": Demucs + SheetSage2) exist but publish no accuracy numbers; one project notes separation "may reveal a line that is masked in the full mix. It does not establish that a separated transcription is more accurate" and that the Demucs "other" stem "can contain multiple instruments; artifacts and incorrect model voice labels are possible" — [coming-undone](https://github.com/swwallowws/coming-undone); [stem-score-lab](https://github.com/tusharmagar/stem-score-lab)
- The lars76 benchmark's noisy/reverberant conditions (background sound, reverb, mic filtering) are the closest systematic proxy for separation-artifact robustness among monophonic trackers; neural trackers RMVPE/FCPE/SwiftF0 degrade least there — [lars76/pitch-benchmark](https://github.com/lars76/pitch-benchmark)

### Inferences
- For a YouTube -> Demucs -> stem -> notes pipeline, the dominant error sources are (a) separation bleed and multiple voices in the stem (which breaks monophonic trackers more than polyphonic note models), (b) timbre domain shift (distorted/effected guitar is far from GuitarSet/GOAT training data), and (c) reverb from the mix. Realistic expectations: vocals ~70% note F1 with YourMT3+ or Basic Pitch; clean/acoustic guitar 80-90%; distorted lead guitar well below that (probably 45-60% judging from EGSet12 numbers, which are for solo recordings and therefore optimistic).
- Using a polyphonic model (Basic Pitch / YourMT3+) on the stem and then selecting the top melodic voice may be more robust than a monophonic tracker when the stem has harmony vocals or double-stops; conversely, for a genuinely single-line riff with bends, a monophonic tracker (SwiftF0/PESTO) will give better pitch-contour resolution.
- Separation sometimes helps (removes masking) and sometimes hurts (artifacts); the only quantified case (YourMT3+ vocals) shows a marginal net gain, so A/B both paths on your own material.

### Gaps
- No paper found that reports transcription accuracy on Demucs (htdemucs/htdemucs_6s) stems versus the original clean stems for guitar or piano; the MIR-ST500 vocal comparison in YourMT3+ is the only quantified separation-vs-no-separation result located.
- The Demucs+CREPE vs JDC numbers are from a search summary of arXiv 2203.13422 and were not verified in the paper text.
- No data on how Demucs' "guitar" stem (6-stem htdemucs_6s model) affects downstream note or tab accuracy.
