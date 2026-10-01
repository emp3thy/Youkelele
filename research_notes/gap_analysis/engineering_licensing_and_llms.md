# Engineering, licensing and LLM post-processing for an audio-to-ukulele-tab pipeline (Python, Windows 11, consumer NVIDIA GPU)

Research date: 2026-10-01. Hobby / open-source intent assumed. Nothing in the legal sections is legal advice; it is a summary of public sources with uncertainty flagged.

Method note: web search budget ran out part-way through; later findings came from direct fetches of primary pages (PyPI, GitHub, vendor docs, arXiv, gov.uk, Wikipedia). Several planned lookups could not be made and are listed as gaps.

## Key Question 1: Setting up and keeping stable a Python ML audio stack on Windows 11 with a consumer NVIDIA GPU

### Takeaway
As of late Sept 2026 PyTorch ships Windows CUDA wheels for cu126 / cu130 / cu132 on Python 3.10-3.14, but the MIR libraries the pipeline needs lag badly (Basic Pitch officially tops out at Python 3.11; madmom's PyPI release is from 2018 and needs a Cython source build; Essentia has no Windows wheels at all), so Python 3.11 in a uv-managed venv with explicit PyTorch index pins is the pragmatic sweet spot, and the biggest Windows-specific hazards are torchaudio's TorchCodec migration, onnxruntime-gpu CUDA-major mismatches, and the yt-dlp Deno requirement.

### Cited Findings

PyTorch / CUDA wheels
- The PyTorch "previous versions" page lists v2.13.0 with wheel variants CUDA 12.6 (`cu126`), CUDA 13.0 (`cu130`), CUDA 13.2 (`cu132`), CPU, plus Linux-only ROCm 7.1/7.2; v2.12.x offered the same cu126/cu130/cu132 set. Install form: `pip install torch==2.13.0 torchvision==0.28.0 --index-url https://download.pytorch.org/whl/cu130` — [PyTorch previous versions](https://pytorch.org/get-started/previous-versions/)
- PyPI shows torch 2.14.1 released 30 Sep 2026, `Requires-Python >=3.10`, with wheels for CPython 3.10, 3.11, 3.12, 3.13 and 3.14 (incl. free-threaded) and Windows x86-64 wheels for all supported Pythons — [torch on PyPI](https://pypi.org/project/torch/)
- cu128 was the common Windows variant in the 2.7 era (e.g. `torch-2.7.0+cu128-cp310-cp310-win_amd64.whl`); forum reports of CUDA 12.9 toolkit users hitting "missing wheel files / CUDA not enabled" show the toolkit version need not match the wheel tag — [PyTorch forums](https://discuss.pytorch.org/t/issues-installing-pytorch-2-7-0-and-torchvision-0-17-0-with-cuda-12-9-on-windows-11-missing-wheel-files-and-cuda-not-enabled/219527)
- uv's PyTorch guide: declare an explicit index (`[[tool.uv.index]] name="pytorch-cu130" url="https://download.pytorch.org/whl/cu130" explicit=true`) and route `torch`/`torchvision` to it with a marker `sys_platform == 'linux' or sys_platform == 'win32'` because "PyTorch doesn't publish CUDA builds for macOS"; `uv pip install torch --torch-backend=auto` (or `UV_TORCH_BACKEND=auto`) queries the installed CUDA driver and picks the most compatible index, defaulting to CPU when no GPU is found; valid backends include cpu, cu118, cu126, cu128, cu130, rocm6.4, xpu — [uv PyTorch guide](https://docs.astral.sh/uv/guides/integration/pytorch/); [pydevtools how-to](https://pydevtools.com/handbook/how-to/how-to-install-pytorch-with-uv/)
- uv has an open issue (#16522) requesting automatic CPU/GPU wheel-variant selection for packages beyond PyTorch, i.e. the auto-selection is torch-specific today — [astral-sh/uv issue](https://github.com/astral-sh/uv/issues/16522)

onnxruntime-gpu
- ONNX Runtime CUDA EP table: 1.27.x-1.30.x build against CUDA 13.0 / cuDNN 9.x ("compatible with PyTorch CUDA 13.x"); 1.21.x-1.26.x require CUDA 12.8+ / cuDNN 9.x; 1.19-1.20 CUDA 12.x / cuDNN 9.x, compatible with PyTorch >= 2.4. "Starting with version 1.27, GPU packages published to PyPI (onnxruntime-gpu) are built with CUDA 13.0 by default." The docs say onnxruntime-gpu works with PyTorch's bundled CUDA/cuDNN DLLs if both use the same CUDA major and cuDNN major; load order matters — either import torch before creating an InferenceSession, or call `onnxruntime.preload_dlls()` (available since 1.21.0) — [ONNX Runtime CUDA EP](https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html)

torchaudio / TorchCodec (Demucs, Beat This, WhisperX all touch audio I/O)
- torchaudio 2.8.0 deprecated most "Drop" APIs, introduced `load_with_torchcodec()`/`save_with_torchcodec()`, and noted "TorchCodec lacked Windows support at that time"; 2.9.0 removed most deprecated APIs and made `torchaudio.load()`/`save()` rely on TorchCodec underneath; 2.10.0 completed the migration while preserving `lfilter`, `RNNTLoss`, `CUCTC`, `forced_align`, `overdrive` — [pytorch/audio releases](https://github.com/pytorch/audio/releases). Caution: the release dates returned by the fetch (2.8.0 "Aug 2024", 2.9.0 "Oct 2023", 2.10.0 "Jan 2025") are internally inconsistent and likely garbled; the sequence (2.8 -> 2.9 -> 2.10, roughly Aug 2025 -> Oct 2025 -> Jan 2026) is the reliable part. Verify dates before quoting.
- Demucs' own Windows doc (stale but still canonical) says: install Anaconda with Python 3.8+, `conda install -c conda-forge ffmpeg`, "the version of torchaudio should no greater than 2.1", NVIDIA GPU with >2 GiB, "Demucs is not supported on 32bits systems", and gives an `mkl_intel_thread.dll` fix (`conda install -c defaults intel-openmp -f`, `set CONDA_DLL_SEARCH_MODIFICATION_ENABLE=1`) — [demucs docs/windows.md](https://github.com/facebookresearch/demucs/blob/main/docs/windows.md)
- Demucs on Windows relies on ffmpeg because torchaudio support there is limited; GPU needs ~3 GB VRAM minimum and ~7 GB with default args; mitigations: `--segment 8`, `-d cpu`, `PYTORCH_NO_CUDA_MEMORY_CACHING=1`, `PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128` — [demucs PyPI](https://pypi.org/project/demucs/); [demucs issue #356](https://github.com/facebookresearch/demucs/issues/356); [demucs issue #231](https://github.com/facebookresearch/demucs/issues/231)
- A community-maintained Windows note states "the official Windows docs warn that torchaudio must not exceed version 2.1 when using GPU acceleration. The current default torchaudio is well past that, and left alone, pip installs a version Demucs can't talk to" — [stemsplit Demucs setup guide](https://stemsplit.io/blog/demucs-local-setup-guide) (secondary source; treat as anecdotal)

NumPy 2.x and the MIR libraries
- librosa 0.11.0 (released 11 Mar 2025) added NumPy 2.0 support; before that a Windows 10 user on librosa 0.10.2 + numpy 2.0.0 hit "a module that was compiled using NumPy 1.x cannot be run in NumPy 2.0.0" — [librosa changelog](https://librosa.org/doc/0.11.0/changelog.html); [librosa issue #1848](https://github.com/librosa/librosa/issues/1848); [librosa issue #1831](https://github.com/librosa/librosa/issues/1831)
- Basic Pitch: latest PyPI release 0.4.0 (16 Aug 2024), Apache-2.0, Python 3.8-3.11 supported; ships TensorFlow, CoreML, TFLite and ONNX model formats with load priority TF > CoreML > TFLite > ONNX; platform defaults: macOS CoreML, Linux TFLite, **Windows ONNX**; on Python >= 3.11 TensorFlow becomes the default install; `pip install basic-pitch[tf]` adds TF — [basic-pitch on PyPI](https://pypi.org/project/basic-pitch/)
- madmom: latest PyPI release 0.16.1 (14 Nov 2018), classifiers Python 2.7/3.5/3.6/3.7, depends on NumPy, SciPy, Cython (compile step), optional pyfftw; no Windows binary wheels, so `pip install madmom` is a source build needing a compiler — [madmom on PyPI](https://pypi.org/project/madmom/). The GitHub README says Python 2.7 or 3.5+, dependencies NumPy/SciPy/Cython/Mido, "Please do not try to install from the .zip files provided by GitHub" (use pip or a recursive git clone so the models submodule is included), and ffmpeg is needed for anything other than 44.1 kHz/16-bit WAV — [CPJKU/madmom README](https://raw.githubusercontent.com/CPJKU/madmom/main/README.rst)
- Essentia: latest PyPI 2.1b6.dev1438 (19 May 2026), AGPL-3.0-only, wheels for Linux x86-64 (glibc 2.17+) and macOS 15+ (x86-64/ARM64) only, "No Windows wheels available" — [essentia on PyPI](https://pypi.org/project/essentia/)

ffmpeg, yt-dlp, Deno
- yt-dlp 2025.11.12 (released 12 Nov 2025) made an external JavaScript runtime necessary for full YouTube support; supported runtimes and minimums: Deno >= 2.0.0 (recommended, the only one enabled by default), Node >= 20.0.0, QuickJS >= 2023-12-9, QuickJS-ng (all), Bun >= 1.0.31; the `yt-dlp-ejs` component is bundled in official executables; YouTube without a JS runtime is "deprecated" with limited formats; package maintainers should treat the runtimes as optional deps — [yt-dlp issue #15012](https://github.com/yt-dlp/yt-dlp/issues/15012); background in [yt-dlp issue #14404](https://github.com/yt-dlp/yt-dlp/issues/14404) and [GIGAZINE](https://gigazine.net/gsc_news/en/20251113-yt-dlp-required-deno-javascript-runtime/)
- The yt-dlp announcement gives no Windows-specific (winget/choco) install guidance for Deno — [yt-dlp issue #15012](https://github.com/yt-dlp/yt-dlp/issues/15012)
- Demucs' Windows doc recommends `conda install -c conda-forge ffmpeg`; Beat This! needs "ffmpeg or compatible torchaudio backend" for non-WAV input; madmom needs ffmpeg for non-44.1k/16-bit WAV; WhisperX says "You may also need to install ffmpeg, rust etc." — [demucs windows.md](https://github.com/facebookresearch/demucs/blob/main/docs/windows.md); [CPJKU/beat_this](https://github.com/CPJKU/beat_this); [whisperX](https://github.com/m-bain/whisperX)

Other per-tool Windows notes
- WhisperX: BSD-2-Clause; states CUDA 12.8 required for GPU, provides Linux and Windows install notes, ships a `CUDNN_TROUBLESHOOTING.md`, uses faster-whisper/CTranslate2, recommends `pip install whisperx` or uv — [whisperX](https://github.com/m-bain/whisperX)
- Beat This!: PyTorch >= 2.0, extra deps tqdm/einops/soxr/rotary-embedding-torch; "will fall back to CPU if PyTorch does not have CUDA access", `--gpu=-1` forces CPU, `--float16` helps on recent GPUs; checkpoints are stripped PyTorch Lightning files auto-downloaded at inference — [CPJKU/beat_this](https://github.com/CPJKU/beat_this)
- python-audio-separator: MIT; Windows AMD/Intel GPUs via experimental DirectML (`pip install "audio-separator[dml]"`, `--use_directml`); NVIDIA via standard CUDA install; supports MDX (ONNX), VR (PTH), Demucs (YAML) and MDXC/RoFormer incl. BS-RoFormer / Mel-Band RoFormer (CKPT/YAML); default model `model_bs_roformer_ep_317_sdr_12.9755.ckpt` — [python-audio-separator](https://github.com/nomadkaraoke/python-audio-separator)
- Sheet Sage quickstart: "ensure you are running Linux" with Docker; Jukebox path needs a GPU with >= 12 GB — [chrisdonahue/sheetsage](https://github.com/chrisdonahue/sheetsage)
- chord-extractor (Chordino wrapper) docs assume Ubuntu; on non-Linux-64 you must install the Vamp plugin pack yourself — [ohollo/chord-extractor](https://github.com/ohollo/chord-extractor)

WSL2 vs native vs Docker Desktop
- NVIDIA WSL guide: install the NVIDIA driver on Windows only (it is stubbed into WSL2 as `libcuda.so`); "Do not install any Linux GPU driver within WSL2"; Windows 11 needs no Insider enrolment; kernel 5.10.16.3+ recommended; Pascal or newer GeForce/Quadro in WDDM mode; limitations: no Unified Memory ("Full Managed Memory Support is not available"), limited pinned memory, no concurrent CPU/GPU access; NVIDIA Container Toolkit v2.6.0+ works inside WSL2 but only `--gpus all` (no per-device filtering) — [NVIDIA CUDA on WSL user guide](https://docs.nvidia.com/cuda/wsl-user-guide/index.html)
- Docker Desktop GPU support on Windows requires an NVIDIA GPU, current Win10/11, WSL2-paravirtualization-capable driver, up-to-date WSL2 kernel (`wsl --update`), WSL2 backend enabled; flag is `--gpus=all`; GPU passthrough "only available on Windows with the WSL 2 backend" — [Docker Desktop GPU docs](https://docs.docker.com/desktop/features/gpu/)

### Inferences
- Python version: torch needs >= 3.10, Basic Pitch officially <= 3.11, madmom's PyPI metadata stops at 3.7 (git main builds on newer with Cython and a compiler). 3.11 is the only version inside every stated range; 3.12/3.13 work for torch/librosa/Beat This but push Basic Pitch into its TensorFlow default path on Windows, which is heavier and less tested there.
- CUDA wheel pick for a consumer card in Oct 2026: cu126 if the driver is older, cu130 for current drivers; cu128 is no longer in the 2.12+ matrix. Keep onnxruntime-gpu's CUDA major aligned with torch (ORT >= 1.27 defaults to CUDA 13; use the CUDA-12 variant if you pin torch cu126) and call `preload_dlls()` or import torch first.
- Expect to patch or vendor madmom (Cython build, old numpy idioms) or replace it with Beat This! for beats; expect Essentia to be unavailable natively on Windows (use WSL2 or skip).
- Native Windows is viable for torch/ONNX models; WSL2 is the escape hatch for Linux-only wheels (Essentia, Sheet Sage, Chordino binaries) with the documented unified-memory/pinned-memory caveats; Docker Desktop simply rides on WSL2.
- Pin everything with uv (`uv lock`) using explicit PyTorch indexes with platform markers; avoid `--torch-backend=auto` in the lockfile path because it resolves per-machine.

### Gaps
- Could not search GitHub issue trackers for Windows-labelled bugs in Demucs / audio-separator / Basic Pitch / Beat This! / WhisperX (search budget exhausted); only README-level evidence was gathered.
- No primary source retrieved on madmom's numpy 2.x / Python 3.12 build status (the GitHub repo fetch timed out; only the README was retrieved via raw.githubusercontent).
- No benchmark found comparing native Windows vs WSL2 PyTorch throughput for audio models.
- Deno-on-Windows install specifics (winget package, PATH detection by yt-dlp) not confirmed from a primary source.

## Key Question 2: Packaging and orchestrating a multi-model pipeline with caching

### Takeaway
A plain staged pipeline with content-addressed artefacts (hash of normalised audio -> stems -> beats -> chords -> notes -> tab) is well served by either Snakemake's experimental between-workflow cache (hashes inputs, params and software env) or Prefect 3's `INPUTS`/`TASK_SOURCE` cache policies; JAMS is the established JSON format for beat/chord/segment annotations, and GPU memory is best managed by running each model stage in sequence (or a subprocess) with Demucs' segment/CPU fallbacks for small cards.

### Cited Findings
- Snakemake between-workflow caching: "hashing all steps, parameters, software stacks (in terms of conda environments or containers), and raw input required up to a certain job" (Merkle-tree style); cache dir via `SNAKEMAKE_OUTPUT_CACHE`; rules opt in with `cache: True` (or `"omit-software"`); rules must take parameters via `params` (not raw config/wildcards in shell), multi-output rules need `multiext` or explicit naming; cache files are world-readable; feature is "experimental" — [Snakemake caching docs](https://snakemake.readthedocs.io/en/stable/executing/caching.html)
- Prefect 3 caching: default cache key = task inputs + task source + flow run ID; policies `INPUTS`, `TASK_SOURCE`, `FLOW_PARAMETERS`, `NO_CACHE`, composable (`TASK_SOURCE + INPUTS`), subtractable per parameter; cache records live with results in `~/.prefect/storage/`; requires result persistence (`PREFECT_RESULTS_PERSIST_BY_DEFAULT`); `cache_expiration` takes a timedelta; docs do not state whether input hashing is content- or reference-based — [Prefect caching concepts](https://docs.prefect.io/v3/concepts/caching)
- JAMS (JSON Annotated Music Specification, ISMIR 2014) stores multiple annotations per file with schemas for beats, chords, segments, tags, etc.; chord observations are range objects with onset, duration, value (e.g. "C:major") and confidence; beats are event objects; ships Python validation and a translation layer to mir_eval; current library is jams 0.3.5 — [JAMS paper](https://archives.ismir.net/ismir2014/paper/000355.pdf); [jams docs](https://jams.readthedocs.io/); [jams on PyPI/libraries.io](https://libraries.io/pypi/jams)
- Demucs GPU memory: ~3 GB minimum, ~7 GB default args; reduce with `--segment` (e.g. 8), fall back with `-d cpu`, or set `PYTORCH_NO_CUDA_MEMORY_CACHING=1` / `PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128` — [demucs PyPI](https://pypi.org/project/demucs/); [demucs issue #356](https://github.com/facebookresearch/demucs/issues/356)
- A third-party DAW project reports Demucs "crashes on CUDA out-of-memory instead of falling back to CPU", i.e. the fallback must be implemented by the caller — [gantasmo/theDAW issue #205](https://github.com/gantasmo/theDAW/issues/205)
- Beat This! auto-falls back to CPU and exposes `--gpu=-1`; Transkun defaults to CPU with `--device cuda` opt-in — [CPJKU/beat_this](https://github.com/CPJKU/beat_this); [Yujia-Yan/Transkun](https://github.com/Yujia-Yan/Transkun)
- Beat This! checkpoints are auto-downloaded at inference (stripped Lightning checkpoints, several seed/fold variants) — reproducibility therefore needs the checkpoint name/hash pinned — [CPJKU/beat_this](https://github.com/CPJKU/beat_this)
- onnxruntime-gpu and torch can coexist in one process if CUDA/cuDNN majors match and DLL load order is handled (`preload_dlls()` or import torch first) — [ONNX Runtime CUDA EP](https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html)
- Sheet Sage emits lead sheets as PDF + LilyPond + MIDI ("audio-aligned melody and harmony") — a reference for a symbolic intermediate — [chrisdonahue/sheetsage](https://github.com/chrisdonahue/sheetsage)
- ChordSheetJS parses/serialises ChordPro, chords-over-words and Ultimate Guitar formats, transposes by semitone, normalises B#/E#/Cb/Fb, switches sharp/flat modifiers, and converts between symbol, solfege, Roman-numeral and Nashville styles — [ChordSheetJS](https://github.com/martijnversluis/ChordSheetJS)
- alphaTab renders Guitar Pro 3-7, alphaTex and MusicXML in browser JS, Node, .NET and Android; its README does not mention ukulele explicitly — [CoderLine/alphaTab](https://github.com/CoderLine/alphaTab)

### Inferences
- Content-addressing: hash the decoded, resampled PCM (not the container) so re-downloads with different codecs hit the cache; key each stage on (input hash, model id + checkpoint hash, params, code version). Both Snakemake and Prefect already do most of this if parameters are declared explicitly.
- For a hobby CLI, a Typer front-end over a hand-rolled stage runner with a hashed artefact directory is the lowest-friction option; Snakemake/Prefect add value mainly for reruns at scale. (Typer/Hydra/pydantic-settings themselves were not researched here; see gaps.)
- Loading Demucs, a RoFormer, Beat This!, Basic Pitch (ONNX) and a Whisper model in one process on an 8 GB card is risky; sequential load/unload with `torch.cuda.empty_cache()` or per-stage subprocesses is the safer pattern, and it also isolates GPL subprocesses (see Q3).
- CPU-only laptops: every listed model has a CPU path; Demucs/RoFormer separation is the slow stage, so cache stems aggressively and allow a "skip separation" mode.

### Gaps
- No sources were retrieved on Dagster, Hamilton, doit, Hydra, pydantic-settings or Typer specifically (search budget exhausted before these queries ran).
- No published guidance found on multi-model VRAM budgeting for this exact combination.
- MusicXML/MIDI ukulele-tab conventions (string/fret encoding) not researched.

## Key Question 3: Licensing matrix for redistribution (code vs weights; what an MIT/Apache project can depend on)

### Takeaway
Code licences are mostly permissive (Demucs MIT, Basic Pitch Apache-2.0, Beat This! MIT incl. weights, Transkun MIT, Whisper MIT, WhisperX BSD-2, audio-separator MIT, alphaTab MPL-2.0), but the weights are where restrictions bite: madmom and Sheet Sage weights are CC BY-NC-SA, popular BS-RoFormer community checkpoints have no licence at all, and Chordino/chord-extractor, ChordSheetJS, YourMT3+, LilyPond and MuseScore are GPL/AGPL-family, so an MIT project should treat NC-weighted and GPL components as optional, user-installed, subprocess-invoked extras rather than vendored dependencies.

### Cited Findings

Licence facts (code / weights)
- madmom: source code BSD; "All model and data files are distributed under ... Creative Commons Attribution-NonCommercial-ShareAlike 4.0"; "Pickled madmom Processors using any of the files included in this repository inherit the above license"; commercial use requires contacting Gerhard Widmer — [CPJKU/madmom_models](https://github.com/CPJKU/madmom_models); [madmom README](https://raw.githubusercontent.com/CPJKU/madmom/main/README.rst)
- Sheet Sage: code MIT; models CC BY-NC-SA 3.0, "trained on user contributions to HookTheory"; depends on madmom, Melisma and optionally Jukebox, each with its own terms — [chrisdonahue/sheetsage](https://github.com/chrisdonahue/sheetsage)
- Beat This!: code and model weights MIT — [CPJKU/beat_this](https://github.com/CPJKU/beat_this)
- Transkun (piano): MIT for code and weights — [Yujia-Yan/Transkun](https://github.com/Yujia-Yan/Transkun)
- Basic Pitch: Apache-2.0, Copyright 2022 Spotify AB — [basic-pitch on PyPI](https://pypi.org/project/basic-pitch/)
- YourMT3 / YourMT3+: GPL-3.0 — [mimbres/YourMT3](https://github.com/mimbres/yourmt3) (as summarised by search; confirm in repo LICENSE)
- chord-extractor: GPL-2.0; wraps Chordino, a C++ Vamp plugin from the NNLS-Chroma project — [ohollo/chord-extractor](https://github.com/ohollo/chord-extractor)
- ChordSheetJS: GPL-2.0 — [ChordSheetJS](https://github.com/martijnversluis/ChordSheetJS)
- alphaTab: MPL-2.0 — [CoderLine/alphaTab](https://github.com/CoderLine/alphaTab)
- Essentia: AGPL-3.0-only — [essentia on PyPI](https://pypi.org/project/essentia/)
- WhisperX: BSD-2-Clause — [whisperX](https://github.com/m-bain/whisperX)
- python-audio-separator: MIT, with a request to credit UVR; "almost all of the code in this repo was copied from Ultimate Vocal Remover GUI" and models are "trained as part of the UVR project" — [python-audio-separator](https://github.com/nomadkaraoke/python-audio-separator)
- BS-RoFormer-SW community checkpoint (6-stem: bass/drums/other/vocals/guitar/piano): licence "Unknown. The original trainer is unknown and no license was stated with the checkpoint"; the HF re-host is a float16 safetensors conversion only; architecture code (lucidrains/BS-RoFormer, ZFTurbo/Music-Source-Separation-Training) is MIT — [lumabeat/bs-roformer-sw on Hugging Face](https://huggingface.co/lumabeat/bs-roformer-sw)
- Demucs is MIT and Whisper is MIT per the task brief; not independently re-verified here (gap).

NC / CC guidance
- Creative Commons "recommend[s] against using Creative Commons licenses for software" and points to FSF/OSI-approved software licences instead — [CC FAQ](https://creativecommons.org/faq/)
- The CC FAQ frames NC as a question about the nature of the use ("Does my use violate the NonCommercial clause"), not the identity of the user; the fetched excerpt did not include the full answer — [CC FAQ](https://creativecommons.org/faq/)

### Inferences
- Vendoring/distributing MIT or Apache code + MIT weights (Demucs, Beat This!, Transkun, Basic Pitch, Whisper/WhisperX, audio-separator code) inside an MIT/Apache repo is unproblematic, subject to keeping notices.
- madmom and Sheet Sage weights: CC BY-NC-SA attaches to the weights (and to pickled processors), not to your code. A hobby project is almost certainly non-commercial use, but ShareAlike means anything you derive from the weights (fine-tunes, pickles) must also be CC BY-NC-SA, and downstream users who commercialise are not covered. Safest pattern: do not redistribute the weights; let madmom's own pip install fetch them; mark the stage optional. (Not legal advice.)
- GPL code (chord-extractor/Chordino, ChordSheetJS, YourMT3+, LilyPond, MuseScore): invoking an unmodified GPL program as a separate process via its CLI and exchanging files is widely regarded as keeping the two programs separate works, whereas importing the GPL Python/JS module into your process is the classic "derivative work" risk. For an MIT project: call LilyPond/MuseScore/Chordino as subprocesses or make them user-installed optional extras; avoid bundling ChordSheetJS into an MIT front-end (write a small ChordPro emitter instead). AGPL Essentia adds network-use obligations and should be avoided in anything served over a network. (Interpretation, not legal advice; the FSF/GPL FAQ was not fetched this session.)
- Unknown-provenance RoFormer checkpoints: no licence = no permission to redistribute; the project can point users at the Hugging Face URL and download on first run, but should not re-host or vendor the file, and should disclose the status in README.
- MPL-2.0 (alphaTab) is file-level copyleft and combines cleanly with MIT as long as modified alphaTab files stay MPL.

### Gaps
- Could not fetch the GNU GPL FAQ or OSI pages this session; the subprocess-vs-import distinction above is stated from general knowledge and should be cited before publication.
- Demucs, Whisper, LilyPond and MuseScore licences were not independently re-verified (budget).
- Did not verify YourMT3+ model weight licence separately from its code licence.
- Did not check whether UVR's model zoo carries a stated licence for individual MDX/VR checkpoints.

## Key Question 4: Legal issues with publishing or sharing generated tabs/chord sheets (and downloading YouTube audio)

### Takeaway
Publishers (NMPA/MPA) have treated tabs and chord charts as unauthorised derivative works since the 1990s, shut down OLGA and MXtabs by takedown letter without any court ruling, and later licensed Ultimate Guitar; in the UK there is no general private-copying exception and fair dealing for private study covers only "limited extracts" judged by a fair-minded-person test; YouTube's terms forbid downloading without permission. Publishing the pipeline code is unproblematic; publishing generated tabs of in-copyright songs carries the same exposure the tab sites faced.

### Cited Findings
- OLGA (founded 1992 at UNLV; ~22,000 files and 20+ mirrors by 1997): 1996 EMI Publishing complaint led UNLV to remove it; 1998 Harry Fox Agency complaint shut it down; in June 2006 the NMPA and MPA sent a takedown letter stating OLGA "makes available tablature versions of copyrighted musical compositions" controlled by their members, after which all 34,000 tabs were removed and the site ceased — [Wikipedia: On-line Guitar Archive](https://en.wikipedia.org/wiki/On-line_Guitar_Archive)
- MPA issued a statement on 10 Mar 2006 about actively pursuing tab sites; NMPA/MPA position: "U.S. copyright law forbids the distribution of transcriptions or even arrangements that are somewhat similar to the copyright work", so even inaccurate tabs infringe; "there's no specific court precedent dealing with copyright issues around guitar tablature" — [Wikipedia: Ultimate Guitar](https://en.wikipedia.org/wiki/Ultimate_Guitar); [Computerworld, 24 Jan 2007](https://www.computerworld.com/article/1679484/publishers-no-heroes-to-aspiring-guitarists-in-ip-fight.html)
- NMPA general counsel Jacqueline Charlesworth, Jan 2007: "We're not interested in pursuing people who are writing chords on a napkin"; publishers' stated harm is that tab sites "take away revenue from companies that have paid copyright owners for the right to print sheet music" — [Computerworld](https://www.computerworld.com/article/1679484/publishers-no-heroes-to-aspiring-guitarists-in-ip-fight.html)
- Ultimate Guitar: after Taborama and MXtabs closed (2004-2005) under MPA pressure, UG argued it was outside MPA reach because it was headquartered in Russia; on 10 Apr 2010 it signed a Harry Fox Agency licence covering lyrics display, title search and "tablature display with download and print capabilities" for 44,000+ publishers, and now has agreements with Sony, EMI, Peermusic, Alfred, Hal Leonard, Faber and Music Sales; UG is now part of Muse Group — [Wikipedia: Ultimate Guitar](https://en.wikipedia.org/wiki/Ultimate_Guitar)
- A Fordham IPLJ article titled roughly "Why the Courts Can't Save Online Guitar Tablature..." exists but returned HTTP 403 and could not be read — [Fordham IPLJ](https://ir.lawnet.fordham.edu/cgi/viewcontent.cgi?article=1685&context=iplj)
- UK IPO guidance: you may copy "limited extracts of works when the use is non-commercial research or private study" subject to fair dealing; copying an entire work would generally not qualify; a separate text-and-data-mining exception exists for non-commercial research with lawful access; the page describes no general personal-copying exception; the fair dealing test is "How would a fair-minded and honest person have dealt with the work?", considering whether the use substitutes for the original and harms revenue, and whether the amount taken was "reasonable and appropriate" — [gov.uk Exceptions to copyright](https://www.gov.uk/guidance/exceptions-to-copyright)
- YouTube Terms of Service prohibit users from "access, reproduce, download, distribute, transmit, broadcast, display, sell, license, alter, modify or otherwise use any part of the Service or any Content except" with permission or as allowed by law; prohibit accessing "the Service using any automated means (such as robots, botnets or scrapers)" except public search engines per robots.txt, with written permission, or as permitted by law; and prohibit circumventing features that "prevent or restrict the copying or other use of Content" — [YouTube Terms](https://www.youtube.com/t/terms)
- Ultimate Guitar still blocks some tabs at publisher request (forum thread "Blocked tabs") — [UG forum](https://www.ultimate-guitar.com/forum/showthread.php?t=1420282) (secondary; not fetched in full)

### Inferences
- Publishing code: no issue; the code contains no musical works.
- Publishing generated tabs/chord sheets of in-copyright songs: this is exactly what OLGA/MXtabs did and were taken down for; US fair-use and UK fair-dealing arguments for a public repository are weak because the whole work is reproduced and the output substitutes for licensed sheet music. Chord-only charts have been argued to be less protectable, but the publishers' stated position covers "even arrangements that are somewhat similar", and there is no court precedent either way. (Not legal advice.)
- Keeping tabs local, or publishing only tabs of public-domain or self-written/CC-licensed material (and test fixtures built from such), avoids the issue. Example outputs in the README should use public-domain songs.
- Downloading from YouTube with yt-dlp breaches YouTube's ToS regardless of copyright status; the ToS carve-out "as permitted by applicable law" is the only hook, and UK law has no private-copying exception. A project can ship the yt-dlp integration (yt-dlp itself is widely distributed) but should default to local files and make YouTube input the user's responsibility.
- UK private study: converting a legally owned recording into a tab for your own practice is plausibly fair dealing for private study, but "limited extracts" and the no-personal-copy rule mean this is uncertain; US fair use is more flexible for personal, non-distributed use.

### Gaps
- Chordify and Moises licensing arrangements with publishers could not be verified (Wikipedia page 404, chordify.net/terms 403, search budget exhausted). The task brief asserts they take a licensing approach; treat as unverified.
- Fordham IPLJ legal analysis unreadable (403); no scholarly fair-use analysis of tablature was captured.
- No EFF commentary retrieved.
- UK CDPA s.29/s.30 statutory text and the 2014-2015 personal-copying exception history (introduced then quashed) not fetched; gov.uk guidance only.

## Key Question 5: Can LLMs usefully post-process symbolic music data, and when not to use them

### Takeaway
Benchmarks from 2024-2026 consistently show frontier LLMs reason well over symbolic input (Gemini 2.5 Pro near-ceiling on MIDI chord-quality and transposition tasks) but perform poorly when asked to perceive the same things from audio (13-52% chord-quality accuracy from audio vs 97-100% from MIDI), and tool-grounded (music21) agents beat LLM-only prompting on compositional analysis; so LLMs belong after the signal-processing models, for chord normalisation, ukulele-friendly substitutions, section labelling and strum-pattern selection via structured outputs, and not for pitch/beat/chord estimation from audio.

### Cited Findings

Symbolic vs audio competence
- "Evaluating Multimodal Large Language Models on Core Music Perception Tasks" (arXiv 2510.22455, Oct 2025) tested Gemini 2.5 Pro, Gemini 2.5 Flash and Qwen2.5-Omni on syncopation scoring (20 excerpts), transposition detection (20 pairs) and chord-quality ID (44 excerpts; major/minor/dominant/diminished). Chord ID: MIDI 97-100% (Pro), 50-100% (Flash), 22-100% (Qwen); audio 13-52% (Pro), 6-47% (Flash), 6-34% (Qwen). Transposition: MIDI 100% (Pro) vs audio 80-95%. Syncopation: MIDI 95-100% (Pro) vs audio 20-65%. Conclusion: "models perform near ceiling on MIDI but show accuracy drops on audio ... current systems reason well over symbols (MIDI) but do not yet 'listen' reliably from audio"; no human baseline — [arXiv 2510.22455](https://arxiv.org/html/2510.22455v1)
- MuChoMusic (arXiv 2408.01337, Aug 2024): 1,187 multiple-choice questions over 644 tracks; five open-source audio LLMs; finds "an over-reliance on the language modality, pointing to a need for better multimodal integration" — [arXiv 2408.01337](https://arxiv.org/abs/2408.01337)
- ChatMusician (arXiv 2402.16153, Feb 2024) introduced MusicTheoryBench, a "college-level music understanding benchmark"; ChatMusician "surpasses LLaMA2 and GPT-3.5 on zero-shot setting by a noticeable margin"; the abstract gives no numeric GPT-4 score — [arXiv 2402.16153](https://arxiv.org/abs/2402.16153)
- CSyMR (arXiv 2601.11556, Dec 2025, rev. Feb 2026): 126 MCQs requiring chained score analyses; a ReAct-style agent with deterministic music21 operators beats LLM-only prompting by "5-7% absolute accuracy", largest on analysis-heavy categories — [arXiv 2601.11556](https://arxiv.org/abs/2601.11556)
- LilyBench (arXiv 2606.08722, Jun 2026): four open-weight LLMs; zero-shot executable LilyPond generation "is achievable"; understanding tasks show "strong performance on composer and genre recognition" while "structural understanding tasks remain challenging" — [arXiv 2606.08722](https://arxiv.org/abs/2606.08722)
- "Music I Care About" / MusICA-MetaBench (arXiv 2607.06015, Jul 2026): automated multimodal (audio, notation images, MIDI/MusicXML) music-perception benchmarking from user-supplied data, validated against text-only and white-noise baselines; no per-model numbers in the abstract — [arXiv 2607.06015](https://arxiv.org/abs/2607.06015)
- WildScore (EMNLP 2025) benchmarks MLLMs on in-the-wild symbolic score reasoning; ABC-Eval and a "Musical Score Understanding Benchmark" also exist (titles only from search) — [WildScore](https://aclanthology.org/2025.emnlp-main.853.pdf)

Audio-native LLM input and cost
- Gemini audio: "32 tokens per second of audio (1 minute = 1,920 tokens)", up to 9.5 hours per prompt, 13 formats incl. WAV/MP3/FLAC/M4A/Opus; audio is downsampled to 16 kbps and mixed to mono; docs use `gemini-3.8-flash` as the example model and say Gemini "understands non-speech sounds" — [Gemini audio docs](https://ai.google.dev/gemini-api/docs/audio)
- Gemini audio-input prices per 1M tokens: Gemini 3.8 Flash $3.00 in / $12.00 out; Gemini 2.5 Flash $1.00 in / $2.50 out; Gemini 2.5 Flash-Lite $0.30 / $0.40; Gemini 3.1 Flash-Lite $0.50 / $1.50 — [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing)
- OpenAI audio token prices: gpt-realtime-2.1 / gpt-realtime-2 and gpt-audio / gpt-audio-1.5: $32 per 1M audio input tokens, $64 output; mini variants $10 / $20; transcription gpt-4o-transcribe $0.006/min, gpt-4o-mini-transcribe $0.003/min, Whisper $0.006/min — [OpenAI pricing](https://developers.openai.com/api/docs/pricing)
- Claude: the Files API content-block table lists PDF, plain text, images (jpeg/png/gif/webp) and `container_upload` for code execution; no audio content block exists, so Claude cannot "listen" to audio directly (audio files could only be processed as data inside the code-execution sandbox) — [Claude Files API docs](https://platform.claude.com/docs/en/build-with-claude/files.md)
- Claude structured outputs (GA on Opus 4.5+/5/5.5, Sonnet 4.5+/5/5.5, Haiku 4.5+, Fable 5/5.1): `output_config.format` with `type: "json_schema"` uses constrained decoding and guarantees valid JSON; supports enum/const/anyOf/allOf/$ref, nested objects with `additionalProperties: false`; does not support recursive schemas, numeric min/max, string length limits; enum casing not guaranteed (compare case-insensitively); grammar cached 24 h; Python `client.messages.parse(..., output_format=PydanticModel)` returns `parsed_output` — [Claude structured outputs docs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs.md)
- Current Claude model IDs/pricing per the bundled API reference (cached 2026-09-25): claude-opus-5-5 $4/$20 per MTok, claude-sonnet-5-5 $2/$10, claude-haiku-4-5 $1/$5, claude-fable-5-1 $10/$50 — claude-api skill reference (local, cached; verify at https://platform.claude.com/docs/en/about-claude/pricing.md)

MCP / agentic tooling
- music21-mcp-server (brightlikethelight): "production-ready" MCP server with 16 tools for key, harmony, melody, rhythm, form analysis, counterpoint checking, motif extraction over MIDI/MusicXML; 120 tests; also exposes HTTP API, CLI and Python library — [brightlikethelight/music21-mcp-server](https://github.com/brightlikethelight/music21-mcp-server)
- cclawton/music21-mcp: "Symbolic MIDI analysis and editing tools exposed through MCP, built on music21" — [cclawton/music21-mcp](https://github.com/cclawton/music21-mcp)
- MuseScore MCP servers (JordanSucher/musescore-mcp; ghchen99) drive MuseScore over a WebSocket plugin: note/rest insertion, cursor navigation, tuplets, lyrics, time signatures, measure management — [JordanSucher/musescore-mcp](https://github.com/JordanSucher/musescore-mcp); [MuseScore MCP by George Chen](https://www.pulsemcp.com/servers/ghchen99-musescore)
- mcp-score (u4pak): natural language to MusicXML notation with live MuseScore integration — [u4pak/mcp-score](https://github.com/u4pak/mcp-score)
- ableton-mcp (ahujasid): Ableton Live session control, ~2,900 stars — [ChatForest MCP music roundup](https://chatforest.com/reviews/music-audio-production-mcp-servers/) (secondary)
- No librosa-specific MCP server surfaced in search results.

### Inferences
- Cost per song via audio-native LLM: a 3.5-minute track is ~6,720 Gemini audio tokens, i.e. about $0.007 input on Gemini 2.5 Flash, $0.002 on 2.5 Flash-Lite, ~$0.02 on Gemini 3.8 Flash (output extra). OpenAI gpt-audio at $32/1M audio tokens is an order of magnitude pricier but its audio tokens-per-minute rate was not retrieved, so no per-song figure. These are cheap enough for "describe the groove / genre / section feel" prompts but, per 2510.22455, not accurate enough for chord or beat estimation.
- Good LLM jobs (symbolic in, JSON out, verifiable): normalise chord spellings (Bb vs A#, slash chords, enharmonics relative to key); choose ukulele-playable substitutions (e.g. drop extensions, re-voice barre chords) from a provided chord vocabulary; label verse/chorus/bridge from lyric repetition plus chord-progression repetition; pick a strum pattern from a fixed vocabulary given tempo, meter and a drum-groove description; write performance notes. All of these fit Claude structured outputs with enums and `additionalProperties: false`, and can be validated deterministically (music21 for chord parsing, your own playability rules for fingerings).
- Bad LLM jobs: f0/pitch estimation, onset/beat timing, chord recognition from audio, tempo. The MIDI-vs-audio gap in 2510.22455 and MuChoMusic's language-over-reliance finding both point the same way. Keep Demucs/Beat This!/Basic Pitch/chord models for these.
- Hybrid pattern supported by CSyMR: give the LLM deterministic tools (music21 operators, your chord/beat JSON) rather than raw notation and let it reason over tool outputs; the music21 MCP servers are a ready-made way to do this from Claude Code or any MCP client.
- Keep LLM prompts deterministic for caching and reproducibility: fixed system prompt + fixed vocabularies first, song JSON last; log model id and schema hash alongside the output as part of the content-addressed cache key.

### Gaps
- No published accuracy numbers found for GPT-4o-audio, Qwen2-Audio/Qwen3-Omni or Audio Flamingo on chord recognition specifically (only Qwen2.5-Omni via 2510.22455); AHELM (arXiv 2508.21376) was surfaced but not fetched.
- MusicTheoryBench numeric GPT-4 scores and ZIQI-Eval details not retrieved (abstract-level only / search budget).
- No paper found that evaluates LLMs on chord-simplification, section labelling or strum-pattern selection as tasks; the "good jobs" list above is inference from the symbolic-reasoning results, not measured.
- OpenAI audio tokens-per-minute (needed for per-song cost) not retrieved.
- A "ChordSheet LLM" paper named in the brief was not found.
