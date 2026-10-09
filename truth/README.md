# Truth files

What the owner's ear and the published sources have settled about each song, one folder per run, named after its run folder under `runs\` (the run folders themselves are untracked). `youkelele evaluate <run> --truth truth/<run>` scores a run against its folder.

## Formats (spec 9.1)

A tracked folder `truth/<run folder name>/` per song (run folders themselves are untracked), beside the existing `beats.txt` and `chords.lab` convention, holding what the ear and the published sources have settled, as plain text with one record per line and `#` comments:

- `patterns.txt`: `start end verdict [figure]`, bar range (0-based, end exclusive), verdict YES, MOSTLY or NO, and the heard figure where the owner gave one (`D-DU-UDU`, one or two bars).
- `riffs.txt`: `start end label`, label riff, strum, mixed, dyad or bleed.
- `rests.txt`: `start end label`, label rest, play, tail or contested.
- `key.txt`: `tonic mode source` and an optional second line for an alternative the sources allow.
- `credits.txt`: `title` on the first line, `artist` on the second.

## Conventions used in these files

- Fields are separated by whitespace. `#` starts a comment anywhere on a line; blank and comment-only lines carry no record.
- Bars are the grid's 0-based indices (`02_grid/grid.json`), as the validation records use them. Every range is end exclusive: `55 61` covers bars 55 to 60. The records write some ranges with an inclusive end (the 1.7 record's "bars 26-32" lists, the clip tables' "Bars" column); those are converted here and the comment says so where it matters.
- A two-bar figure is two whitespace-separated bar strings, the first being the row the range's first bar should print. Strokes use the printed alphabet: `D` down, `U` up, `x` muted, `-` empty slot.
- A figure is given only where the owner said the clicks fit (verdict YES): the figure is then the printed row the clip clicked, read from the run's `07_score/score.json`. The owner's prose descriptions of a wrong pattern are not turned into figures.
- A pattern range is the clip's own bars where a clip was judged; the regression ranges the pattern review names without a clip are the section ranges it gives.
- `rests.txt`: `rest` is a bar heard (or published) with no guitar on the stem; `tail` is a bar that carries only the previous stroke's decay and rests; `play` is a bar heard playing; `contested` is a bar the records dispute and which no score counts.
- `key.txt`: the source is one word, a URL or a short tag such as `general-knowledge`. A `key.txt` with no record line means the sources settle no key for the song; treat it as absent.
- `credits.txt`: the title and the artist the sheet should print, matched after casefold and tag stripping.
- Every record cites its source in a trailing `#` comment.

## Sources, in order of authority

1. The listening passes: `docs/superpowers/specs/2026-10-05-v1-6-validation.md`, "Listening pass" (cited as "1.6 clip N"), and `docs/superpowers/specs/2026-10-06-v1-7-validation.md`, "Ear clips" (cited as "1.7 clip N"), "Ground truth from published sources" (cited as "1.7 sources: <item>"), "Resting bars" (cited as "1.7 rests") and "Blind song" (cited as "1.7 Badge").
2. `docs/superpowers/research/2026-10-06-v1-7/acdc-ear-truth.md` (cited as "AC/DC clip N").
3. The review truth tables, section C of each, in `research_notes/Weak music measurements research/`: `review_pattern_vote_and_direction.md` ("pattern review C"), `review_riff_versus_strum.md` ("riff review C"), `review_rests_and_activity.md` ("rests review C"), `review_key_and_metadata.md` ("key review C").

## Rules

- A verdict the records give as MOSTLY is MOSTLY.
- A range two records judge differently keeps the later record's verdict, with a comment naming both.
- A range a record leaves ambiguous is omitted, with a comment saying why; nothing is guessed.
- The pattern review's ear-passed regression ranges count as YES.
- No lyrics in any file.
