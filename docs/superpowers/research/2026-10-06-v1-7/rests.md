# Spike: a per-bar "holds a strummed instrument" rule without basic-pitch (2026-10-06)

Throwaway scripts: `%TEMP%\youkulele-v17-research\rests\` (`perbar_feats.py <song>`, `analyse.py`, `rule.py`, `others.py`). Calls to mirror: `rms_ratio` at the native rate for the guitar/mix energy ratio per bar; `librosa.stft(n_fft=2048, hop_length=512)` on the guitar stem resampled to 22 050 Hz for the band share; `detect_onsets`, `track_pitch`, `name_notes` for the pitch candidate.

## Recommendation

A bar holds a strummed instrument when its guitar/mix energy ratio is at least 0.05 and the share of its guitar-stem STFT power below 330 Hz (`lo330`) is at least 0.005.

| Candidate | Bell bars and Chelsea Dagger bar 5 (max) | Lowest ear-verified bar | Usable band |
|---|---|---|---|
| `lo330` (STFT power share below 330 Hz) | 0.0002, 0.0003, 0.0006 | 0.040 (Need You Tonight bar 23) | 0.001 to 0.04 |
| `lo330b` (Butterworth low-pass) | 0.0003, 0.0003, 0.002 | 0.025 (Need You Tonight bar 23) | 0.002 to 0.025 |
| `lo262` (below 262 Hz) | 0.0002, 0.0003, 0.0004 | 0.010 (Summer of '69 bar 77) | 0.0004 to 0.010 |

0.005 is the log-midpoint of the `lo330` band. At 0.005, 0.01 and 0.02 every one of the 49 listed near-silent bars rests, all nine Chelsea Dagger empty and bell bars rest, and no bar of an ear-verified section rests. Chelsea Dagger bars 13 to 19 (real power chords) score at least 0.26.

Other bars rested beyond the 49: at 0.005, two (Pour Some Sugar On Me bars 7, by the ratio test alone, and 68); at 0.01, five (adding Need You Tonight 9, Summer of '69 29, Day Tripper 1 which is loud at ratio 0.83 but high-register); at 0.02, thirteen. The ratio floor alone rests 45 of the 49; the band share adds the bell bars 3, 4, 5 and Pour Some Sugar On Me 67.

## Candidates that fail

- **Lowest or median named pitch (pyin, E2 to E6).** The bell bar 3 is named lowest MIDI 40 and median 57.5 (octave errors against a true 75 to 105); bars 4 to 6 have no named notes, so no threshold rests them; at lowest under 62 a Chelsea Dagger power-chord bar rests, at under 60 Need You Tonight's tab bars rest.
- **Spectral centroid.** The bell sits at 1553 to 1800 Hz while ear-verified bars reach 2849 Hz (Need You Tonight 23, All Fired Up 64 to 68, Summer of '69 80); the bands overlap.

## Risks

The `lo330` margin is about eightfold each side, and the ear-verified minimum comes from decaying tails at section ends; a loud bar played high on the neck would rest (Day Tripper bar 1 at the looser 0.01); the feature depends on the stem holding content below 330 Hz, so separation quality moves it; thresholds were fitted to ten songs.
