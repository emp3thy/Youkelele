# Spike: stroke duration and onset density (2026-10-06)

Throwaway scripts: `%TEMP%\youkulele-v17-research\strokes\` (`common.py` reproduces the stage's onsets exactly: 1066 of 1066 bars match `bar_onsets`; `durations.py`, `durations2.py`, `ear_eval.py`, `ear_rule.py`, `overfire_dump.py`, `filters.py`, `rise.py`, `bleed.py`, `nyt_cars.py`). Ear truth: the 1.6 listening pass (held, short and changed-pattern clips).

## 1. Per-stroke duration: no rule exists

Per onset: time to the next onset, time for the stem RMS to fall 10 and 20 dB below the stroke's peak (10 ms frames, 5 ms hop), and their ratio; full band, above 2 kHz, below 300 Hz.

| Bar | Ear | ratio (10 dB fall / gap) | share of gap within 10 dB |
|---|---|---|---|
| All Fired Up 132 | cut | 19.7 | 1.00 |
| Summer of '69 95 | rings | 12.1 | 1.00 |
| Chelsea Dagger 61 | cut | 0.91 | 0.91 |
| Wet Leg 18 | cut | 3.70 | 1.00 |
| The Cars 68 | cut | 12.1 | 1.00 |
| Pour Some Sugar On Me 77 | rings | 0.60 | 0.60 |
| Need You Tonight 24 | rings | 0.47 | 0.47 |
| Need You Tonight 31 | cut | 0.38 | 0.38 |
| Need You Tonight 56 | cut | 0.33 | 0.33 |
| Fame 47 | cut | 0.31 | 0.31 |
| Fame 61 | cut | 0.51 | 0.51 |

"Rings" spans ratio 0.47 to 12.1, inside "cut" at 0.31 to 19.7. The best rule in the physical direction scores 8 of 11, the same as drawing no sustain line; the 10-of-11 splits run backwards (a stroke "rings" when it decays faster) and are noise. On distorted songs the level barely falls before the next onset whether the player damps or not. The ear truth also contradicts itself on Need You Tonight 24 (clip 7 "rings", clip 23 "all cut off"). Over 6,496 strokes of nine songs the ratio is continuous (10th percentile 0.43, median 2.56, 90th 30.0) with no gap.

Recommendation: draw no sustain lines.

## 2. Over-firing on Summer of '69 is content, not the detector

| Section | Onsets per bar | Pairs under 60 ms | Weak onsets (under 0.3 of bar max) |
|---|---|---|---|
| 4-19 | 6.33 | 3 of 95 | 8 of 95 |
| 31-41 | 4.50 | 1 of 45 | 1 of 45 |
| 53-58 | 5.20 | 0 | 0 |
| 95-111 | 3.38 | 1 of 54 | 0 |

Gaps between onsets cluster at one eighth slot (209 to 232 ms against a 217 ms slot); no decay-tail retriggers; odd-slot onsets as strong as even. The complained sections look like the passed one (53-58 at 5.2 per bar against 75-83 at 4.5). The ear's "eighth" is the grid's quarter: a second part, or a down-up heard as one.

Filters tried (minimum gap 0.7 slot; strength floors at 0.5 of bar max and 0.8 of bar median; `onset_detect` with `backtrack=False` and `delta` 0.10 or 0.15; attack rise under 3 dB): none reaches the ear's density without changing ear-passed patterns (All Fired Up 33-49 and 128-132, The Cars 68-72, Need You Tonight 13-24, Summer of '69 75-83 and 4-19, Chelsea Dagger 61-71 among them). Changing `delta` re-normalises the envelope and flips the recall gate.

## 3. Under-firing

- Need You Tonight 24-31: the three quarter-note stabs are in the raw onsets (strengths 0.23 to 0.62); the run of nine fast notes fits sixteenths from beat 2.75 to the next bar's 0.75 and the detector finds 29 of 36 (five below the default `delta` 0.07, two with no peak). The printed syncopation comes from those misses plus a grid that cannot express a run crossing the barline.
- The Cars 72-76: the printed sparse half equals the raw onsets exactly; every missing eighth has a peak below `delta`; the struck onsets are weak (0.08 to 0.20); the recall gate never runs because the section counts as dense.

## Risks

Eleven ear bars with three "rings"; strength filters would collapse recall-boosted sections unless gate-added onsets are exempt; Fame's second guitar is not separable by any onset feature measured.
