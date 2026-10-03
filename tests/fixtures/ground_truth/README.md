# Ground-truth fixtures

Each folder holds hand-made annotations for one run, named after the run slug. Both files are optional: a missing file gives `n/a` for its metrics in `youkelele evaluate`.

## `beats.txt`

One beat time in seconds per line. A downbeat (the first beat of a bar) is marked by a second whitespace-separated column holding `1`. Other beats may omit the column or carry `0`.

```
0.0	1
0.5
1.0	0
```

## `chords.lab`

Tab-separated `start<TAB>end<TAB>label`, times in seconds, labels in Harte notation (for example `C:maj`, `A:min`, `G:7`, `N` for no chord).

```
0.0	2.0	C:maj
2.0	4.0	G:maj
```

## Contents

- `example/` is a tiny 4-bar, 120 bpm clip (C, G, Am, F) used by the tests.
- The real annotations for the two target songs (Summer of '69 and Pour Some Sugar On Me) are made by hand by the project owner and saved under `<slug>/` here. They are not part of the implementation plan.

Run the report with `youkelele evaluate <slug> --truth tests/fixtures/ground_truth/<slug>`.
