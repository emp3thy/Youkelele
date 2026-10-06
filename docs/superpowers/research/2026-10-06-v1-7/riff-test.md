# Spike: widening the riff test; sections with no instrument (2026-10-06)

Throwaway scripts: `%TEMP%\youkulele-v17-research\riffs\` (`extract.py`, `aggregate.py`, `hb.py`, `noinst.py`, `perbar.py`, `doorbell.py`, `rules.py`, `show.py`; `bp_notes.py` needs basic-pitch under Python 3.11). Recomputed 1.6 features match `strums.json`.

## Feature table (guitar stem)

ent = median per-onset chroma entropy; single = single-pitch-class share; pcs = pitch-change share; rep2 = consecutive named pitches within 2 semitones; root = share of named pitches on the chord root; bp1 = share of onsets where basic-pitch strikes one note; ROS = high single note over a low chord; ratio = guitar/mix energy.

| Section | Ear | 1.6 flag | ent | single | pcs | rep2 | root | bp1 | ROS | ratio |
|---|---|---|---|---|---|---|---|---|---|---|
| Day Tripper 0-11 | riff | no | .86 | .49 | .78 | .41 | .35 | .57 | .04 | .62 |
| Day Tripper 52-58 | riff over strum | no | .71 | .53 | .29 | .92 | .76 | .28 | .03 | .35 |
| All Fired Up 61-90 | riff | no | .73 | .72 | .29 | .71 | .95 | .23 | .12 | .26 |
| Wet Leg 58-65 | riff | yes | .80 | .50 | .61 | .61 | .10 | .16 | .11 | .23 |
| Need You Tonight 13-24 | riff (tab verified) | yes | .54 | .78 | .60 | .96 | .25 | .70 | .09 | .16 |
| Summer of '69 111-121 | riff | no | .90 | .04 | .60 | .80 | .11 | .12 | .21 | .34 |
| The Cars 52-68 | riff | yes | .72 | .61 | .60 | .63 | .48 | .35 | .15 | .34 |
| The Cars 11-19 | strum | no | .67 | .64 | .11 | .91 | .90 | .20 | .11 | .36 |
| All Fired Up 33-49 | strum | no | .66 | .61 | .08 | .92 | .94 | .30 | .23 | .29 |
| Chelsea Dagger 0-20 | no guitar (bars 0-12) | no | .81 | .25 | .32 | .79 | .54 | .25 | .20 | .26 |

Features that do not separate: basic-pitch polyphony (median 1 to 2 everywhere), the register split, onset spectral flatness, attack sharpness. Root share marks the strums (0.86 to 0.94) but also All Fired Up 61-90 (0.95) and Day Tripper 52-58 (0.76).

## Rules

- **Rule A.** Keep the chroma gate (entropy at most 0.82, single share at least 0.45); lower `PITCH_CHANGE_MIN` from 0.40 to 0.26. Band 0.24 to 0.29: All Fired Up 55-61 (a strum, "mostly fits") at 0.238 below; the two recovered riffs at 0.289 and 0.292 above. Catches All Fired Up 61-90 and Day Tripper 52-58.
- **Rule B.** Chroma-free: pitch-change share at least 0.55, root share at most 0.40 (band 0.36 to 0.41), named share at least 0.50. The only rule that catches Day Tripper 0-11 and Summer of '69's outro, which fail the chroma gate on entropy. Depends on the chord labels. Pitch-change share alone is useless across songs (strummed Chelsea Dagger, Pour Some Sugar On Me and Summer of '69 sections reach 0.3 to 0.7).
- **Riff over strum**: no reliable flag. High-band pitch naming (stem high-passed at 400 Hz) names 44% of the high onsets in Day Tripper 52-58 against at most 8% elsewhere in that song, but Need You Tonight 0-13 and 48-56 and Summer of '69 4-19 score as high. One positive example; not adopted.

Blind check over all sections of nine songs (`rules.py`): Rule A adds five flags (All Fired Up 61-90 and Day Tripper 52-58 wanted; Summer of '69 0-4 and The Cars 0-11 unheard) and removes none. Rule B adds eleven: Summer of '69 111-121 and Day Tripper 0-11 wanted; Day Tripper 11-15, 26-30, 30-35, 35-46, 46-52, 58-63, 63-68, 78-95 plausible (the riff runs through the song) but unheard; Wet Leg 33-42 and The Cars 72-76 unheard.

## Sections with no instrument

Chelsea Dagger 0-20 against the other 85 members: energy ratio 0.258 (rank 25 of 85, passes the 10% rule), spectral flatness −29.6 dB (52 of 85), harmonic share 0.81 (44 of 85), 3.45 onsets per bar (16 of 85). Nothing isolates it at section level. Per bar it is three things: bars 0-12 near silence in the guitar stem (ratio 0.00 to 0.07, bar 8 excepted), bars 3-4 a bell at MIDI 75 to 105 (ratio 0.86 to 0.88), bars 13-19 G2-D3-G3 power chords at ratio 0.23 to 0.31. The owner's clip covered bars 0-8 only; bars 12-20 need a listen.

Proposed per-bar rule (measured with basic-pitch; a librosa-only register feature is the subject of the rests spike): a bar holds a strummed instrument when its guitar/mix ratio is at least 0.05 and its lowest note is below MIDI 64. The 0.05 floor cannot rise: Need You Tonight's verified tab bars sit at 0.069 to 0.09. The 64 threshold has a band 64 to 75 (highest lowest-note among 939 bars at ratio 0.10 or more is 63; the bell bars are 75 and 87). Resting bars: Need You Tonight 0-7 and 84-85; Wet Leg 18-25 and 109-112; Pour Some Sugar On Me 0, 8-10, 15-18, 77-79; Chelsea Dagger 0-6, 10, 11; single bars in All Fired Up (114), Pour Some Sugar On Me (66, 67), Summer of '69 (0, 120), Day Tripper (94), The Cars (62); 49 in all. A section-level share cut is not recommended: at 0.5 it also flips Wet Leg 18-33 and Need You Tonight 0-13, which share the guitar-enters-late shape.

## Risks

Every band rests on one or two examples per side; All Fired Up 55-61's ear label is weak and pins Rule A's low edge; Rule B trusts the chord roots with a 0.05-wide band; two Rule A flags and four Rule B flags are untested by ear.
