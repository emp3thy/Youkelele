# Spike: lyrics from the vocals stem (2026-10-05, deferred to 1.7)

Throwaway scripts: `%TEMP%\claude\...\scratchpad\spike-lyrics\` (transcribe.py, analyze.py, onset_check.py; results in analysis.txt and metrics.json; word-timestamp JSON under out\). No lyrics are quoted here.

## Question

Can speech recognition on the separated vocals stem give words with timings good enough to place under the right bar, offline, on a CPU-only Windows machine, fast enough for the non-coder install?

## Findings

faster-whisper (CTranslate2, int8) installed on the project's Python 3.12 and ran on the vocals stem of four songs (All Fired Up, Wet Leg "mangetout", Need You Tonight, Summer of '69).

| Model | Wall time per song (CPU, this machine) | Words landing in a sung bar | Base-vs-small same-bar agreement |
|---|---|---|---|
| base | 5 to 11 s | 0.98 to 1.00 | 0.63 to 0.92 |
| small | 17 to 35 s | 0.96 to 1.00 | (reference) |
| medium | 39 to 76 s | 0.95 to 1.00 | small-vs-medium 0.80 to 0.90 |

- Timing is the strong part: on every song and model at least 95% of words fall inside bars where the vocal stem is active, and between the small and medium models 80 to 90% of matched words land in the same bar.
- Words are the weak part. Summer of '69 reads well with a few garbled names; Need You Tonight's repeated choruses transcribe almost identically (self-similarity 0.86 to 0.91); All Fired Up's choruses do not match each other at all (0.00) and Wet Leg's barely (0.12 to 0.20).
- The stem is essential: on the full mix the model produced nothing usable on two of the songs.
- Garbage share (non-words, repeated tokens) was at most 0.01 on every run; low-probability words 4 to 17%.

## Recommendation for 1.7

A lyrics stage after separate: faster-whisper `small`, int8, `word_timestamps=True`, `language="en"`, `vad_filter=True`, on the vocals stem; each word placed in the bar containing its start time; printed on the sheet as "words as the machine heard them" with that caveat in the legend. Model download about 500 MB on first run, cached by the library. Half a minute a song on a current laptop CPU.

Risks: wrong words on songs with dense or effected vocals; a first-run download in the non-coder install; the lyric row's page cost.
