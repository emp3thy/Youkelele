# Riff extraction spike (2026-10-05, throwaway)

Question: can a playable note sequence be extracted from the separated guitar stem on ear-confirmed riff sections, reliably enough to print as ukulele tab?

Answer: partly. A riff prints only when the stem holds one clean line that repeats steadily: Need You Tonight verse (high confidence), Fame instrumental (medium). Four of six ear-confirmed riff sections fail (Fame intro, NYT intro, The Cars Verse 3, All Fired Up 97-104). Without a gate, both strum controls come out as fake one-note tab.

## Per section (pyin unless marked bp = basic-pitch)

| Section (bars) | By ear | Voiced | Distinct notes | MIDI range | Repeat pyin / bp | Dominant sequence (name:eighths) |
|---|---|---|---|---|---|---|
| Fame intro 1-17 | riff | .55 | 17 | 43-81 | .17 / .41 | none stable (consensus support .66) |
| Fame instr 29-35 | riff | .76 | 12 | 41-65 | .52 / .62 (2-bar) | G#3:2 G#3:2 D#4:1.5 D#4:1.5 D#4:1 \| C4:1 D4:1 D#4:1 D4:1 D#4:3 G#3:1 |
| NYT intro 8-13 | riff | .52 | 6 | 48-67 | .10 / .27 | bars 8-11 are C-major chord stabs plus a high G4/D5 line; riff starts bar 12 |
| NYT verse 13-24 | riff | .91 | 9 | 48-64 | .72 / .74 (1-bar) | C4:.5 C4:.5 D4:2 D4:1 C4:1 D4:.5 D#4:1 D4:1 C4:.5 |
| Cars V3 52-60 | riff | .64 | 16 | 43-86 | .26 / .21 | none |
| AFU 97-104 | riff + improv | .85 | 18 | 40-63 | .08 / .13 | none |
| Cars V1 11-19 | strum (control) | .93 | 4 | 40-50 | .32 / .32 | D3 x8 (power-chord root) |
| AFU 33-41 | strum (control) | .94 | 3 | 40-50 | .36 / .46 | G2 ... (power-chord root) |

Repeat = similarity of a bar to the next bar or the bar two later; two notes match on exact MIDI within one sixteenth.

## Negative controls

pyin is fooled on strums: it reports the power-chord root, and on per-note measures strums look MORE note-like than riffs (voiced .93-.94 vs .52-.91; within-note pitch IQR 0-10 cents vs 19-40; harmonic energy share .83-.90 vs .68-.81).

Measures that DO separate (each resting on only the two strum controls):
- pyin pitch-change share (next note differs in pitch): riffs .65-.85, strums .05-.17
- top-note share (fraction of notes at the most common pitch): riffs .17-.39, strums .48-.58
- bp multi-note strike share: riffs .07-.34, strums .49-.50

## Recommended method (constants global, bands stated)

1. `librosa.load(sr=22050, mono)`; `librosa.pyin(fmin=82.4, fmax=1318.5, frame_length=2048, hop_length=256)`; `onset_detect(onset_envelope=onset_strength(hop=256), backtrack=False, units='time')` (backtrack=True put 29-78% of onsets more than a quarter sixteenth off-grid; False 0-40%).
2. One note per onset-to-onset segment: skip first 20 ms and last 10 ms, require >= 50% voiced frames, rounded median MIDI. Snap onsets to the nearest sixteenth (each grid.json beat split in four).
3. Consensus riff over a 1- or 2-bar period: at each slot keep the majority pitch if present in >= 50% of repetitions (removes most octave flips and second-guitar flips).
4. Gate, all three must pass: pitch-change share >= .4 (gap .17-.65, two strum controls); repeat >= .5 (printable .52-.76, rejected .04-.41; edge rests on Fame instrumental alone); consensus support >= .75 (printable .79-.83, others .50-.75).
5. basic-pitch: slightly cleaner Fame rhythm, only tool that sees two voices; does not install on Python 3.12 (tensorflow); works via `uv run --no-project --python 3.11 --with basic-pitch --with "setuptools<81"` (first install ~80 s).

## Rendering as ukulele tab

- NYT: no octave shift; C4-D#4 on the C string frets 0-3: `C0 C0 C2 C2 C0 C2 C3 C2 C0`.
- Fame: shift up one octave; G#3-F4 -> G#4-F5: G1 / A3 / A5 / A6 / A8; 9-semitone span fits.
- General rule: choose the octave shift putting the most notes in MIDI 60-81; move remaining outliers by whole octaves; lowest fret across strings; in re-entrant tuning the G string (G4=67) is a high string.
- Renderer needs a sixteenth grid and 2-bar riffs.

## Fame's two guitars

Instrumental: not separable by register; the emphasis note looks like D#4 on slots 8, 11, 14 (3+3+2), inside the riff's own range. Intro: basic-pitch shows an isolated repeated A5 (13 hits, bars 9, 13, 15, ~6 semitones above the rest), probably the emphasis guitar, possibly vocal bleed; pyin misses it. Register split is not a general method.

## Sketch: Fame instrumental (basic-pitch, highest note per strike, uke one octave up)

```
29 | G#3:.5 G#3:1 G#3:.5 F4:2 D#4:1 D4:.5 D#4:1.5 D#4:1    | G1 G1 G1 A8 A6 A5 A6 A6
30 | C4:1 G3:1 D#4:1 D4:1 D#4:1 D4:1.5 G#4:.5 G#3:.5 G#3:1  | A3 G0 A6 A5 A6 A5 A11 G1 G1
31 | G#3:.5 C5:1.5 G#3:2 D#4:1.5 D#4:1.5 D#4:1              | G1 A3 G1 A6 A6 A6
32 | D#4:.5 C4:1 D4:1 D#4:2 D#4:1.5 D#4:.5 F3:1 G#3:1       | A6 A3 A5 A6 A6 A6 E1 G1
33 | (rest 2) G#3:1 D4:1 D#4:1.5 D#4:2 D#4:.5               | G1 A5 A6 A6 A6
```

## Risks

- Coverage: 2 of 6 ear-confirmed riff sections pass; busy or improvised riffs do not repeat note for note.
- Stem bleed: NYT bars 8-11 are chord stabs inside an ear-confirmed riff section.
- Rhythm jitter: 30% of Fame onsets > a quarter sixteenth off-grid; pyin and basic-pitch disagree by a sixteenth.
- Octave flips between Fame's two guitars and the bass (F2, G#2 outliers).
- Thin evidence: every gate band rests on 2 strum controls and 2 passing riffs.
- Pitch unverified by ear: Fame on G#/D#, NYT on C/D/D#; owner should hear one bar of each.

Scripts: riff_common.py, s1_pyin_extract.py, s2_notes_and_metrics.py, s3_basic_pitch.py, s4_consensus.py, s5_sketch.py. Data: notes_guitar.json, notes_basicpitch.json, metrics_guitar.json, metrics_basicpitch.json, consensus.json, sketch.txt.

## Ear check of the extracted riffs (owner, 2026-10-05, synth_riffs.py)

- Need You Tonight verse: pitches RIGHT ("the tones are right"), rhythm WRONG ("the break is in the wrong place"). The strums stage's own onsets on this section were judged perfect in earlier passes, so rhythm should come from those onsets and pyin should only name the pitch at each onset.
- Fame instrumental: "absolutely miles off. Fame is syncopated: dum dum dum de dum dum de dum de dum de dum dum". The consensus figure is wrong in rhythm and probably in notes. So the medium-confidence case is a FALSE POSITIVE of the proposed gate: the only ear-verified printable riff is NYT verse (repeat .72-.76, support .80). The repeat threshold must sit above Fame's .52-.62, and the gate's evidence is now one passing riff and two strum controls; more songs are needed before the bands are trusted.
