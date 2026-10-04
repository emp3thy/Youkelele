# Close tonic calls with both rules in view, and the power-chord note on the easy sheet

Strand: harmony (key hedge) and score/render (power-chord legend). Measured on the seven run folders under `runs\` from their stored `chords.json`, `score.json` and `sheet.html`. No source file, test or run folder was changed; the scripts are throwaway, in `%TEMP%\youkelele-v15-research\key\` (`chroma_cache.py`, `analyse.py`, `proposal.py`, `sensitivity.py`, `power_note.py`, `perpage.py`, `pssom.py`).

## Summary

1. The hedge today is driven by the score rule's margin or by the mix estimate. The pair rule's winner is computed (`TonicDecision.pair_tonic`) and written to the manifest, but it never reaches the sheet. Need You Tonight prints "(or F major)" only because the mix estimate says F.
2. Proposed rule: after the close-margin test and before the mix test, hedge with the pair rule's winner whenever it is a different tonic from the printed one. It needs no new constant; the pair rule's winner is stored on the key as a new optional field.
3. On the seven songs the printed header changes on none. The five known songs keep their headers exactly; Need You Tonight keeps "C major (or F major)" but the hedge is now there by rule (with the mix neutralised, today prints "C major", the proposal prints "C major (or F major)"). The change bites only when the mix and the pair rule disagree.
4. Power note on the easy sheet: Pour Some Sugar On Me rendered through the project's renderer with one extra line (or three) stays at two pages with page 2 unchanged; the other six songs have no power chord and are byte-identical. Recommended: print a tier-specific line in the easy tier, badge still full-tier only.
5. Weakest point: the chroma tie-break that settles Need You Tonight's pair rule is not stable (first half of the song prefers C by 0.009, second half F by 0.114; sections split 3 to 4), so naming both tonics is the honest header; the files hold no evidence that F is right.

## 1. State of the code

All paths under `src\youkelele\` in the worktree `v1-4`.

| What | Where |
|---|---|
| Constants `KEY_TIE_MARGIN = 0.05`, `PAIR_TIE = 0.02`, `KEY_HEDGE_MARGIN = 0.05`, `MODE_TIE_MARGIN = 0.05` | `music\key.py:60`, `:62`, `:64`, `:66` |
| `TonicDecision` (tonic, margin, runner_up, rule, `pair_tonic`, `pair_margin`) | `music\key.py:97-104` |
| `pair_shares` (larger of the X-major and X-minor relative pairs, half credit for a diatonic root of the wrong quality) | `music\key.py:210-225` |
| `pair_rule`: winner by share; shares within `PAIR_TIE` of the best are tied and decided by `_profile_fit` (better Krumhansl correlation on the stem chroma) | `music\key.py:246-263` |
| `decide_tonic`: score winner; `pair_rule` over every candidate is always computed (`:288`); the pair rule decides only when the score margin is under `KEY_TIE_MARGIN`, over the close candidates (`:289-293`) | `music\key.py:266-294` |
| `key_and_decision` builds the `Key` (without `pair_tonic`), then asks `hedge_tonic` for the other tonic and stores its mode in `hedge_mode` | `music\key.py:336-358` |
| `_close` (margin under `KEY_HEDGE_MARGIN`), `_mix_disagrees` (tonic only; mode ignored), `hedged` | `music\key.py:440-450` |
| `_hedge`: runner-up if close, else the mix tonic if it differs, else None | `music\key.py:453-458` |
| `hedge_text` (mode from `Key.hedge_mode`; old-file fallback), `key_text` | `music\key.py:468-488` |
| `pair_rule_note`: "F by 0.083" or "tie, F by chroma" (manifest only) | `music\key.py:491-498`; written at `stages\harmony.py:143` |
| `Key` schema (no field for the pair rule's winner) | `schemas.py:112-125` |
| `Score.key_hedge = hedge_text(chords.key)` | `music\score_builder.py:209`; field at `schemas.py:272` |
| Printed header: `_key_fact` | `render\html.py:63-69`, used at `:135-139` |
| Power legend: `POWER_LEGEND` | `render\html.py:27` |
| Any use of a chord as a power chord marks the diagram | `music\score_builder.py:127` |
| Easy tier prints plain: `power_badge = score.tier == "full"`, `power_lines` empty otherwise | `render\html.py:92-96`; template `render\templates\sheet.html.j2:59-60` (badge) and `:92-94` (line) |

Docs that state the current behaviour: spec 3.1 "Tie-break and hedge" and section 4 "Power-chord badge" ("The easy tier prints the plain key's chord with no badge and no legend line"); README "Known limitations" bullet on the power-chord mark; validation "What to improve next" items 2 and 5.

Reproduction check: re-running `key_and_decision` over the stored events (Pour Some Sugar On Me's power events restored to plain major; chroma recomputed from the four harmonic stems exactly as `stages\harmony.py` does, energy mask included) reproduced the stored tonic, mode, margin, mode margin, runner-up and `hedge_mode` on all seven songs.

## 2. Part 1: the seven songs, both rules

Candidates are the roots with at least `TONIC_MIN_SHARE` (0.2) of chord time. "Margin" for a sole candidate is its own value (the code's convention), so Fame and All Fired Up are not close calls by construction. Chroma fit is `_profile_fit`, the better Krumhansl correlation at the tonic.

| Song | Score rule (winner, margin over runner-up) | Pair shares | Pair rule (winner, margin) | Chroma fit | Mix tonic | Printed hedge today |
|---|---|---|---|---|---|---|
| Summer of '69 | D 0.472 over A 0.458, 0.014 (under 0.05, so the pair rule decides) | D 0.931, A 0.879 | D, 0.052 (decided by share) | D 0.807, A 0.883 (not used) | D major | none (deciding margin 0.0516, above 0.05 by 0.0016) |
| Chelsea Dagger | G 0.445 over D 0.349, 0.096 | G 0.971, D 0.912 | G, 0.059 | G 0.771, D 0.855 (not used) | D major | "(or D major)" from the mix |
| Pour Some Sugar On Me | C# 0.439 over B 0.293, 0.146 | C# 0.793, B 0.653 | C#, 0.140 | C# 0.719, B 0.659 | C# major (same tonic) | none |
| mangetout | C 0.588 over F 0.379, 0.209 | C 0.995, F 0.995 | tie (0.000), C by chroma | C 0.706, F 0.607 | C major | none |
| Fame | F alone, 1.067 | F 0.981 | F, sole candidate | F 0.516 | F minor (same tonic) | none |
| All Fired Up | G alone, 0.726 | G 1.000 | G, sole candidate | G 0.786 | G major | none |
| Need You Tonight | C 0.745 over F 0.418, 0.327 | F 0.928, C 0.924 | tie (0.0033), F by chroma | F 0.730, C 0.672 | F major | "(or F major)" from the mix |

Where the pair rule's chroma winner equals the mix tonic:

- Need You Tonight: yes, F and F. The two agree, which is why the hedge text is already right, for the wrong reason.
- mangetout: yes, C and C (and the score winner too, so there is nothing to hedge).
- Pour Some Sugar On Me, Fame, All Fired Up, Summer of '69: the pair winner equals the mix tonic (mode aside).
- Chelsea Dagger: no. The pair rule says G (by share), the mix says D, and the chroma fit alone would also say D. The hedge there comes from the mix and is right per the known-song expectation.

The chroma is not an independent tonic cue. Taken over every candidate it would pick the other tonic on two of the known songs (Summer of '69: A over D; Chelsea Dagger: D over G). It is used only inside a pair tie, where it has been right on the one tie with a known answer (mangetout) and cannot be checked on the other (Need You Tonight).

Sensitivity of the two ties to the chroma window (`sensitivity.py`):

| Window | Need You Tonight (C vs F) | mangetout (C vs F) |
|---|---|---|
| Loud bars (as the stage) | F by 0.058 | C by 0.099 |
| Every bar | F by 0.050 | C by 0.106 |
| Loud bars, first half | C by 0.009 | C by 0.016 |
| Loud bars, second half | F by 0.114 | C by 0.188 |
| Per-section winners (7 and 9 sections) | C 3, F 4 | C 6, F 3 |

mangetout's tie-break holds in every whole-song window; Need You Tonight's flips between halves and splits the sections. They are different cases: for mangetout the tie-break and the score agree and the header is right; for Need You Tonight the evidence points both ways, which is what a hedge is for.

## 3. Proposed rule

**Condition (hedge source `pair`).** Evaluate in this order in `_hedge`:

1. `_close(key)` and a runner-up exists: name the runner-up (unchanged).
2. New: `key.pair_tonic` is set and `key.pair_tonic != key.tonic`: name the pair rule's winner.
3. `_mix_disagrees(key)`: name the mix's tonic (unchanged).

In words: the sheet names the pair rule's winner when the score is clear but the pair rule, over every candidate and with its chroma tie-break inside `PAIR_TIE`, picks another tonic. A tie is covered because it is resolved by chroma into a single winner; a tie whose chroma winner is the printed tonic (mangetout: C 0.995, F 0.995, chroma C) is agreement and adds no hedge, which the five-song constraint requires. Stating the condition as "the pair rule ties within `PAIR_TIE`" alone would have wrongly hedged mangetout.

**Constants.** None new. It reuses `PAIR_TIE = 0.02` (inside `pair_rule`) and `KEY_HEDGE_MARGIN = 0.05` (rung 1). A narrower variant, firing only when the disagreement is a tie (`pair_margin < PAIR_TIE`), gives identical headers on all seven songs. I propose the broader form because a clear pair-rule win for another tonic is stronger grounds to hedge than a tie, and no song in the set sits there.

**Bands the constants sit in across the seven songs.**

| Constant | Observed on one side | Observed on the other | Where the threshold sits |
|---|---|---|---|
| `KEY_TIE_MARGIN` 0.05 (score margin of the five two-candidate songs) | 0.014 (Summer of '69) | 0.096 (Chelsea Dagger), 0.146, 0.209, 0.327 | the band 0.014 to 0.096 is empty and 0.05 is inside it |
| `KEY_HEDGE_MARGIN` 0.05 (deciding margin) | 0.0516 (Summer of '69, by the pair rule) | 0.096 to 0.327; sole candidates 0.726 and 1.067 | Summer of '69 is 0.0016 above the threshold: the one fragile point, existing today and not touched by this proposal |
| `PAIR_TIE` 0.02 (pair-share gap) | 0.000 (mangetout), 0.0033 (Need You Tonight) | 0.052 (Summer of '69), 0.059 (Chelsea Dagger), 0.140 (Pour Some Sugar On Me) | the band 0.0033 to 0.052 is empty and 0.02 is inside it |
| New pair-disagreement test | disagrees on Need You Tonight only (F against C) | agrees on the other six, including the tie on mangetout | no threshold; categorical |

**Wording.** Unchanged text form: `C major (or F major)`, the other tonic carrying its own stored mode (`hedge_mode`; the stems hear F as major).

**Code touch points** (proposal only, nothing written):

- `schemas.py:112-125`: add `pair_tonic: str | None = None` to `Key` (older files load unchanged, as `hedge_mode` did).
- `music\key.py:350`: `key_and_decision` sets `pair_tonic=decision.pair_tonic` on the `Key` it builds; the existing `hedge_tonic(key)` call at `:355` then also finds the pair tonic and `hedge_mode` is computed at it.
- `music\key.py:440-458`: add `_pair_disagrees(key)`; give `_hedge` the second rung and the source `Literal["runner_up", "pair", "mix"]`; include it in `hedged`. `hedge_text`'s old-file fallback (`:480`) needs no new branch beyond treating `pair` like `runner_up`, because a file without `pair_tonic` never reaches rung 2.
- `stages\harmony.py:61-64` (`_key_log`): optionally log the hedge's source. The manifest note `tonic_pair_rule` is unchanged.
- Tests to update or extend: `tests\test_key.py` (`test_hedged_when_margin_small_or_mix_disagrees` at `:181`, `test_hedge_names_the_runner_up_for_a_close_margin_and_the_mix_otherwise` at `:197`, `test_key_json_from_version_1_3_loads_without_a_hedge_mode` at `:404`), `tests\test_stage_harmony.py`, `tests\test_score_builder.py`.
- Docs: spec 3.1 "Tie-break and hedge" and the validation items; the README limitation bullet on hedges stays true.
- A score or render re-run from an old `chords.json` keeps today's behaviour; the new hedge appears only after re-running from harmony.

### Expected header changes (`proposal.py`, a prototype outside the source tree on the stored decisions)

| Song | Header today | Header under the proposal | Source of the hedge |
|---|---|---|---|
| Summer of '69 | D major | D major | none |
| Chelsea Dagger | G major (or D major) | G major (or D major) | mix (the pair rule agrees with G, so rung 2 is silent) |
| Pour Some Sugar On Me | C# minor | C# minor | none |
| mangetout | C major | C major | none (pair tie, chroma agrees) |
| Fame | F major | F major | none |
| All Fired Up | G major | G major | none |
| Need You Tonight | C major (or F major) | C major (or F major) | pair rule (was the mix) |

Sheet headers print the shape key under a capo, so the stored `sheet.html` shows "A minor (shapes)" for Pour Some Sugar On Me and "D major (shapes)" for Fame, with the sounding key on its own line; none of them changes.

Isolating the new clause (`proposal.py`, mix replaced by the key's own tonic): six songs print exactly as today; Need You Tonight changes from "C major" to "C major (or F major)". With the mix forced wrong (a tritone away): six songs print the mix's wrong hedge as today (the mix clause is untouched), and Need You Tonight prints "C major (or F major)" in place of "C major (or F# major)". So the proposal stops the one real disagreement depending on the mix.

### Risks

- The pair rule is a diatonic-share measure over the chord stream; where the chord stream is thin (a riff song with few chords) its winner can be the relative-pair twin. Need You Tonight's tie is that shape: in its 12-tonic share list D, F, C and A are the top four (0.928, 0.928, 0.924, 0.924) because the F/Dm and C/Am pairs score within 0.004. Naming F picks the major side of the F/Dm pair, with its mode taken from the stems at F.
- The hedge now triggers on any song whose chroma tie-break lands on the other tonic, and the tie-break is unstable (see the window table). Expect more "(or ...)" than today on riff songs where the mix agrees with the score; that is the intent.
- When rung 2 and the mix name different tonics, the sheet names the pair rule's. The mix has been a coin toss on every source measured (spec section 8), so the ordering is deliberate but untested: no song in the set has that conflict.
- When the pair rule decided the tonic over a narrowed set (Summer of '69's case), `pair_tonic` is still the all-candidate winner; if the two ever differed with a clear deciding margin, the hedge would name the all-candidate winner. No song does this.
- Summer of '69's deciding margin of 0.0516 sits 0.0016 above `KEY_HEDGE_MARGIN`. Unrelated to this proposal, but a small change in the score arithmetic could add an "(or A major)" to the one song whose header is known right.
- The truth for Need You Tonight is not in the files. The proposal does not claim F is right; it makes the sheet say that the two rules disagree.

## 4. Part 2: the power-chord note on the easy sheet

Measured on Pour Some Sugar On Me, the only one of the seven with a power chord (`score.json` marks only the Am diagram; tier easy, capo 4, sounding C# minor): 6 power events, 93.2 s, 39.5 percent of chord time; 25 of 87 grid cells carry the power flag; the one real C# minor event is bar 65, 1.42 s. In the easy tier the Am diagram is printed, the cells say plain Am, and neither the raised 5 nor a legend line appears.

Method: each score was loaded from `score.json`, passed to `render_html`, and printed with the project's `html_to_pdf` into the scratch folder. The unmodified render of all seven reproduces the stored `sheet.html` byte for byte and the stored page counts (3, 3, 2, 3, 3, 4, 2 in the order of the table above). For Pour Some Sugar On Me the line was inserted into the rendered HTML at the position the template uses for `power_lines` (after the legend, passing and no-capo lines, before the sections).

| Variant | Line | Pages | Page 1 lowest text (pt from the bottom; margin is 39.7 pt) | Page 2 |
|---|---|---|---|---|
| Today (c) | none | 2 | 104 | lowest text 209 |
| (a) the full-tier line | "Am is a power chord on the record" | 2 | 86 | unchanged (209) |
| (b) softer, one line | "Am is played as root and fifth on the record." | 2 | not separately recorded; one line | unchanged |
| (b') line with a clause | "Am is a power chord (root and fifth) on the record; the easy sheet prints the minor chord." | 2 | 86 (one line, as (a)) | unchanged |
| Worst case, 3 wrapped lines | the (a) sentence six times | 2 | 73 | unchanged |

One line costs about 18 pt on page 1, which had 64 pt of slack above the margin; page 2 keeps about 170 pt free. No other song prints a power line (their diagrams carry no `power` flag, and the line is gated by `any(d.power ...)` exactly as in the full tier), so their pages cannot change. Page count change: none.

Wording against the README: it says the easy tier "reduces chords to triads and simpler shapes", and its limitations list says the mark and its line "print only in the full tier; the default easy sheet prints the plain minor chord". "Am is a power chord on the record" is true of the record, not of the sheet, and does not contradict "reduces chords to triads". But without the raised 5 the reader sees "Am" in every cell and a line calling it a power chord, with no mark to say which cells; a clause that says what the sheet does about it removes that tension. The line stays true under the any-use rule: Am is a power chord for 39.5 percent of chord time and a real minor for 0.6 percent.

**Recommendation: option (a) in placement and gating, with a short easy-tier clause (b').** Print one line per power name in the easy tier too, under the same `Passing:` and no-capo lines, badge still full-tier only, using a tier-specific constant beside `POWER_LEGEND` (`render\html.py:27`), for example `POWER_LEGEND_EASY = "{name} is a power chord (root and fifth) on the record; this easy sheet prints the triad."`. The line prints when any use is a power chord (same rule, `score_builder.py:127`). Reasons: it costs no page on any song, it answers validation item 2 directly, it matches the README's vocabulary ("triads"), and the clause removes the apparent contradiction without a badge. Option (c) leaves the reader unaware that the riff is root and fifth. Option (b) alone says what the record plays but not why the sheet prints something else.

Code touch points (proposal only): `render\html.py:92-96` (choose the line by tier instead of emptying it), `render\templates\sheet.html.j2:92-94` (unchanged), `tests\test_html.py:372-376` (the easy-tier test currently asserts "power chord" is absent), the README Known limitations bullet, spec section 4's sentence "The easy tier prints the plain key's chord with no badge and no legend line", and the validation records that call the easy sheet's silence "by design".

Risk: "prints the triad" assumes the printed chord is the key's triad. The harmony gate guarantees a minor key (`key.py:413`) and `music\arrange.py:135-137` turns the power chord into the key's minor triad. If the gate were widened to major keys the clause would still be true, which is why it says "the triad" and not "the minor chord".

## 5. Assumptions

| # | Assumption | Status | Evidence | Cost if wrong |
|---|---|---|---|---|
| 1 | The re-run decisions equal the stored ones | Verified | `key_and_decision` over the stored events and recomputed chroma reproduced tonic, mode, margin, mode margin, runner-up and `hedge_mode` on 7 of 7 | The pair and fit figures here would not be the stage's; the hedge conclusions would need re-measuring |
| 2 | Pour Some Sugar On Me's power events must be restored to plain major before re-running | Verified by reading `harmony.py:132-137` (the key is decided before the relabel) | The restored events reproduced the stored key | A wrong tonic for that song; it reproduced |
| 3 | The five known songs' correct headers are D, G (or D), C# minor, C, F | Unverified here; taken from the brief and the validation record | Consistent with the stored sheets | The "must not hedge" check would be checking the wrong thing |
| 4 | Need You Tonight's true tonic is unknown | Unverified, and cannot be verified without listening | The files support C by score and F by pair-rule chroma and mix | If the true tonic is C only, the added hedge is noise on that song; if it is F, the hedge is right and the printed tonic should flip, which is a larger question than this proposal |
| 5 | A hedge on a tie that the chroma resolves to the printed tonic would be wrong | Measured on one song | mangetout is such a tie (C 0.995, F 0.995, chroma C) and its header is known right | If every pair tie were hedged, mangetout would gain a wrong "(or F major)" |
| 6 | The chroma tie-break is stable enough to decide a hedge | Refuted for Need You Tonight, held for mangetout | Need You Tonight: first half C by 0.009, second half F by 0.114, sections 3 to 4; mangetout C in every window | The named tonic could flip if the chroma window changes; in a two-candidate tie the hedge still names the other of the two tied tonics, so the header's content is stable even when the order is not |
| 7 | The bands around `PAIR_TIE` and `KEY_TIE_MARGIN` are empty | Measured on 7 songs only | 0.0033 to 0.052 and 0.014 to 0.096 | A song inside a band would change header unpredictably; seven songs do not bound the real distribution |
| 8 | Summer of '69's margin of 0.0516 is stable | Measured, fragile | 0.0016 above `KEY_HEDGE_MARGIN` | A known-right header gains "(or A major)"; not caused by this proposal |
| 9 | Adding `pair_tonic` to `Key` is backward compatible | Unverified (not run); by analogy | `hedge_mode` was added as an optional field with a fallback and has a test for 1.3 files (`tests\test_key.py:404`) | Old `chords.json` would fail to load; a test catches it |
| 10 | One extra line adds no page on any song | Measured | Pour Some Sugar On Me stays at 2 pages with 1 and with 3 extra lines and page 2 is unchanged; the other six have no power chord | A sheet gains a page; caught by the page-count check |
| 11 | The scratch insertion equals what a template change would print | Unverified | The paragraph was inserted into the rendered HTML at the template's `power_lines` position rather than by editing the template | A difference of a few points; page 1's 64 pt of slack covers several lines |
| 12 | The easy-tier measurement is unaffected by the raised-5 badge | Verified by construction | The easy tier prints no badge; the full tier (badge plus line) was measured at two pages in the 1.4 validation | None for the easy tier |
| 13 | The clause "this easy sheet prints the triad" is accurate | Verified for the current gate | `key.py:413` requires a minor key; `music\arrange.py:135-137` maps the power chord to the key's minor triad | The clause would misdescribe a differently simplified chord if the arrangement changes |
| 14 | Only Pour Some Sugar On Me exercises the power line | Measured | Only its Am diagram has `power` in the seven `score.json` files | A song with power chords in another layout may paginate differently; the headroom figure is per song |
