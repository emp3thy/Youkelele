# Spike: a riff or solo over a strum, split into two parts (2026-10-06)

Throwaway scripts: `%TEMP%\youkulele-v17-research\split\` (`bands.py`, `analyse.py`, `extra.py`, `bpfeat.py`, `make_lowband_clips.py`; `bp_notes.py` needs basic-pitch under Python 3.11). Ear truth: the owner's six AC/DC verdicts (`%TEMP%\youkulele-ear-v17\acdc-ear-truth.md`): intro 0-16 riff alternating with a chord stab (mixed clicks fit the riff); chorus 16-34 strum; verse 34-43 riff with backing chords; verse 43-57 strum; instrumental 74-90 solo over strum; verse 90-113 riff over chords.

## Result: not shippable

- **Splitters tried**: Butterworth low/high at 400 Hz and 260 Hz, a 150 to 400 Hz band-pass, librosa HPSS (percussive as low, harmonic as high), basic-pitch notes divided at MIDI 60. Only the basic-pitch split (bp60) separates AC/DC's four two-part sections from its two strums: lone single high notes per bar 1.04 to 4.38 against 0.50, with other songs' strums at or below 0.69. HPSS separates AC/DC but The Cars' strum (5.25) and Need You Tonight (5.64) break it across songs. The frequency splits overlap (74-90 at 0.24 high onsets without a low partner against the strum 43-57 at 0.39).
- **Two-part rule** (bp60 lone high notes per bar at least 1.0 and low chords per bar at least 0.75): marks all four AC/DC two-part sections and none of the five negatives; bands 0.92 to 1.03 and 0.70 to 0.80, both resting on AC/DC alone; misses Day Tripper 52-58 (riff and strum on the same eighths); also marks Fame 61-71, Summer of '69 53-58, All Fired Up 97-104 and AC/DC 57-74 (plausible, unheard). An optional branch (high minus low pitch-change share at least 0.35 on the 400 Hz split) catches Day Tripper on one example.
- **Low-band strum patterns** are denser than the mixed ones (bass bleed and sustain wobble push them toward `DUDUDUDU`) and change two plain strums (AC/DC 16-34, All Fired Up 33-49). Clips with low-band clicks: `lowband_instrumental_74-82.wav`, `lowband_verse3_90-98.wav`, `lowband_verse3_90-98_hpss.wav`.
- **The high-band riff** never passes the 1.6 gate on any splitter (agreement 0.00 to 0.30; at most 0.69 on HPSS unpartnered onsets with support 0.00).
- **One fact to keep**: the mixed pattern equals the 400 Hz high band's pattern in nearly every section, so on a two-part stem the printed strokes follow the higher part. That is why AC/DC's intro clicks fit the riff, and why "riff heard, not transcribed" over the mixed strokes is honest: they are the riff's rhythm.

## Why it waits for 1.8

Every threshold is fitted to one song; the splitter needs TensorFlow on a second Python, which the non-coder install cannot carry; riffs in rhythmic unison with the strum are invisible to coincidence; bass bleed pollutes the low band.
