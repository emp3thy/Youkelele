# Assumption pass, 1.8: key and credits (A7, A8, A9)

Written 2026-10-08 against main at 27bf2a2, read-only on `runs\`. Scripts in the session scratchpad (`ap_key\a7_sets.py`, `a7_precise.py`, `a8_badge_mode.py`, `a9_titles.py`); they import `youkelele.music.key`, `music.chroma`, `stages.harmony` and `titles` and run the project's own functions on the stored data.

## A7. `SET_VETO_MARGIN` 0.10 fires on Badge and on no other run

Method: for each run, `_chords` on `03_harmony\chords.json` events, `_set_share` at all twelve major tonics (the "major set") and `pair_shares(events, _TONICS)` (each tonic's better relative pair, as spec 7.1 names it). Decided tonic from `chords.json` `key`. Veto printed when best minus decided is at least 0.10.

| run | decided | best major set | best share | decided tonic's share (major set / pair) | gap | veto prints |
|---|---|---|---|---|---|---|
| all-fired-up | G major | G | 1.000 | 1.000 / 1.000 | 0.000 | G |
| chelsea-dagger | G major | G | 0.971 | 0.971 / 0.971 | 0.000 | G |
| cream-badge | D major | G | 0.995 | 0.756 / 0.756 | **0.238** | **G** |
| fame | F major | A# | 0.988 | 0.981 / 0.981 | 0.008 | F |
| mangetout | C major | C (F ties) | 0.995 | 0.995 / 0.995 | 0.000 | C |
| need-you-tonight | F major | F | 0.928 | 0.928 / 0.928 | 0.000 | F |
| pour-some-sugar-on-me | C# minor | E | 0.793 | **0.219** / 0.793 | **0.575 / 0.000** | E / C# |
| summer-of-69 | D major | D | 0.931 | 0.931 / 0.931 | 0.000 | D |
| the-beatles-day-tripper | E major | E | 0.862 | 0.862 / 0.862 | 0.000 | E |
| the-cars-you-might-think | D major | D | 1.000 | 1.000 / 1.000 | 0.000 | D |
| you-shook-me-all-night-long | G major | G | 1.000 | 1.000 / 1.000 | 0.000 | G |

Badge's gap is 0.2383 (spec says 0.239; same figure at the spec's rounding of the parts). The next-largest gap by pair share is Fame, 0.0077 for B flat (spec: 0.007); every other run is 0.000. The lead tonic changes on Badge alone, to G.

Two implementation hazards found, both about which share the veto compares:

1. **The decided tonic's share must be its pair share, not its own major set.** Pour Some Sugar On Me is decided C# minor; the C#-major set holds 0.219 of chord time while the E-major set (its relative) holds 0.793. A veto that compares the best major set with the decided tonic's major set fires at 0.575 and renames the song E. With `pair_shares` (max of X major and the major a minor third up) the gap is 0.000. Spec 7.1 names `pair_shares`, which is right; the implementation must not reach for `_set_share` at the decided tonic.
2. **`pair_shares` over twelve tonics ties every relative pair.** On Badge E and G both read 0.995 (All Fired Up E and G 1.000, Fame G and A# 0.988, mangetout C, D, F and A 0.995). `_winner`'s tie-break is lowest pitch class, so `_winner(pair_shares(...))` names **E** for Badge, not G. "That set's major tonic" must be found explicitly: take the best tonic by `_set_share` over the twelve major sets (G 0.995), or, among the tied pair, the one whose own major set carries the share. Either lead is allowed by A8's sources, but the spec's text and `TonicVotes.set_tonic` should say which is printed.

Verdict: **held** on the band (0.238 against at most 0.008, 0.10 inside the gap; no other lead moves), provided the veto compares pair shares at the decided tonic and names the major tonic of the winning set deliberately rather than through `_winner`'s pitch-class tie-break.

## A8. Badge's mode at G clears `MODE_TIE_MARGIN`

Method: as `HarmonyStage.run` does it: `read_stems` on guitar, bass, piano and other from `01_separate\stems`, `harmonic_chroma`, `bar_energy` and `chorded_energy_reference` on the summed mix over `02_grid\grid.json`, the loud mask (`FILL_MIN_ENERGY` times the reference; all 70 bars pass), `chroma.mean(loud, bars)`. Then `mode_at`, `_profile_fit`, `_mode_of` and `tonic_chord_mode` on the stored events.

| tonic | `mode_at` | margin | Krumhansl corr major / minor | `_profile_fit` | `_mode_of` | `tonic_chord_mode` | under 0.05 |
|---|---|---|---|---|---|---|---|
| G | major | **0.644** | 0.687 / 0.044 | 0.687 | major | major | no |
| E | minor | 0.316 | 0.226 / 0.542 | 0.542 | minor | minor | no |
| D | major | 0.489 | 0.790 / 0.301 | 0.790 | major | major | no |

The D-row margin matches the stored `mode_margin` 0.489, so the rebuilt chroma is the one the stage used. At G the chroma names major by 0.644, twelve times `MODE_TIE_MARGIN`; the chord fallback is not reached and agrees. The veto path prints **G major**, and the hedge of 7.2, computed as `_mode_of("E", ...)`, names **E minor** (margin 0.316, also clear). Nothing hedges on mode. Both leads score 1.0 against one published key: G major from the Hooktheory-style sources, E minor from the others.

Two notes: the stem chroma's own 24-way ranking is D major 0.790, G major 0.687, A major 0.605, B minor 0.549, E minor 0.542, so the chroma alone would still say D; the key at G rests on the chord set, as 7.1 intends. And if A7's hazard 2 is left to `_winner`, the printed lead becomes E minor (or G major) instead of G major (or E minor); either satisfies validation criterion 1.

Verdict: **held**; at G the mode is major by 0.644, no hedge on mode, relative hedge E minor.

## A9. Rung 2 and the channel test on the eleven runs and the test titles

Method: rung 2 as written in 8.2 (equal-prefix fast path on the cleaned artist field or uploader, else split at the earliest of " - ", " – ", ": " when the head has at most four words and `_TAG_RE` finds no tag word in it; the rest cleaned as `clean_title` does); 8.3's channel test on `uploader_id` where known, else `channel` (equal to the uploader on all eleven per spike 3). `uploader_id` is **not stored**: `source_meta.json` holds the five `_METADATA_FIELDS` and `00_ingest\source.json` holds no channel field, so the six handles come from the key review's spike 3 and the other five runs are tested on the uploader name. Rung 1 (`track` and `artists`) cannot be tested on stored data; only Fame carries them per spike 3, and its stored `artist` "David Bowie" gives the same credit by rung 3. Provenance under 8.2's rule: a lower rung (rung 4 always returns the uploader) differs from the chosen artist after casefold and tag stripping.

| run | raw title | uploader | uploader_id | rung | title / artist | provenance | expected | match |
|---|---|---|---|---|---|---|---|---|
| all-fired-up | Pat Benatar - All Fired Up (Official Music Video) | Benatar Giraldo | @PatBenatarVEVO (pass) | 2 split | All Fired Up / Pat Benatar | **yes** | All Fired Up / Pat Benatar | yes |
| chelsea-dagger | The Fratellis - Chelsea Dagger | The Fratellis | @TheFratellisVEVO (pass) | 2 equal | Chelsea Dagger / The Fratellis | no | same | yes |
| cream-badge | Cream - Badge | Gñåf Ütøpìe | @GnafUtopie (fail) | 2 split | Badge / Cream | yes | Badge / Cream | yes |
| fame | Fame (2016 Remaster) | David Bowie | channel (pass) | 3 (1 when `track` kept) | Fame / David Bowie | no | same | yes |
| mangetout | Wet Leg - mangetout (Official Video) | Wet Leg | channel (pass) | 2 equal | mangetout / Wet Leg | no | same | yes |
| need-you-tonight | INXS - Need You Tonight (Official Video) | INXS | channel (pass) | 2 equal | Need You Tonight / INXS | no | same | yes |
| pour-some-sugar-on-me | DEF LEPPARD - "Pour Some Sugar On Me" (Official Music Video) | DEF LEPPARD | channel (pass) | 2 equal | Pour Some Sugar On Me / Def Leppard | no | same | yes |
| summer-of-69 | Bryan Adams - Summer Of 69 (Official Music Video) | Bryan Adams | @bryanadams (pass) | 2 equal | Summer Of 69 / Bryan Adams | no | same | yes |
| the-beatles-day-tripper | The Beatles - Day Tripper (Official Video) | Natan Santos | @goldsongs7948 (fail) | 2 split | Day Tripper / The Beatles | yes | Day Tripper / The Beatles | yes |
| the-cars-you-might-think | The Cars - You Might Think (Official Music Video) | RHINO | @rhino (fail) | 2 split | You Might Think / The Cars | yes | You Might Think / The Cars | yes |
| you-shook-me-all-night-long | AC/DC - You Shook Me All Night Long (Official 4K Video) | AC/DC | channel (**fail**) | 2 equal | You Shook Me All Night Long / AC/DC | no | same | yes |

Eleven of eleven credits match. The channel test passes the three artist handles and fails the three others as 8.3 says. Two things the spec does not say:

- **A fourth provenance line.** All Fired Up's uploader "Benatar Giraldo" differs from the chosen "Pat Benatar", so by 8.2's rule the sheet prints "uploaded by Benatar Giraldo" although @PatBenatarVEVO passes the channel test. The review's criterion "a provenance line on exactly the three" needs either the channel-test pass to suppress the line (3.4's "the names coincide" is not literally true here) or the criterion to say four.
- **AC/DC fails the channel test**: `_long_words` keeps words of three or more letters and "AC/DC" has none. Harmless here (uploader equals artist, nothing prints), but a one-word act with short tokens (U2, ELO, AC/DC) can never pass rung 3.

Rung 2 on `tests\test_titles.py` (KNOWN_TITLES, the parametrised `clean_title` cases, the capitals cases and `test_wider_artist_prefix_rule`): every case is unchanged except these, plus the two dash-inside-title probes from 8.4 and the A9 risk:

| raw | artist field | today | rung 2 | note |
|---|---|---|---|---|
| Of Us - Song | Of Them | Of Us - Song / Of Them | Song / Of Us | expected by 8.4 |
| Pat Benatar - Song | None | Pat Benatar - Song / None | Song / Pat Benatar | not listed in 8.4 or A12; the test's "no artist field" assertions must change |
| Song - Live at Wembley | Other Artist | whole | **Live at Wembley / Song** | 8.4 says it "stays whole"; it does not, the tag word is in the tail |
| Band - Song - Live | Other Artist | whole | Song - Live / Band | correct split at the first separator |
| Live - Song, Live at Wembley - Song | Other Artist | whole | whole | the head exclusion works |

Verdict: **held on the eleven runs and the known titles; the exclusion must widen.** The head-only tag-word rule lets "Song - Live at Wembley" split into artist "Song". The widening that keeps every run and every other test case: a tag word in the tail outside bracket groups (after `_GROUP_RE` removal) also blocks the split. It costs "Band - Song - Live" (kept whole, uploader as artist), which no run shows. The replacement test case in 8.4 should be worded as "Song - Live at Wembley" stays whole under the widened rule, and `test_wider_artist_prefix_rule`'s "Pat Benatar - Song" with no artist field now splits.
