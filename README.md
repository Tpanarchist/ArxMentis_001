# ArxMentis

ArxMentis' persistence primitive is a mutable bit stored beside the program.
Distinction 1 starts at `0` in `.arxmentis-state`; distinction 2 starts at `0`
in `.arxmentis-state-2`. They can be changed and recovered independently.

```powershell
python arxmentis.py read
python arxmentis.py toggle
python arxmentis.py read
python arxmentis.py toggle --distinction 2
python arxmentis.py read --distinction 2
python arxmentis.py step --distinction 2
python arxmentis.py copy --distinction 2
```

The last read for each distinction recovers the value saved by the previous
process. Distinction 1 remains the default. To use a different state file for
the selected distinction, pass `--state-file PATH` to `read` or `toggle`.

Given the persisted values `D1` and `D2`, their relation is derivable without a
relation primitive: `D1 XOR D2` is `0` when they are the same and `1` when they
are different.

`step --distinction 2` makes D2's next state depend on D1: it persists
`D2' = D1 XOR D2` while leaving D1 unchanged. With D2 held at `0`, stepping
once with D1=`0` leaves D2 at `0`; stepping with D1=`1` changes D2 to `1`.
Use `--state-file PATH` to override the target distinction's file; the driver
is read from its default file.

`copy --distinction 2` instead persists `D2' = D1`, leaving D1 unchanged. The
XOR step is bijective over the four possible pair states: each future has one
past. Copy is non-bijective: `(0, 0)` and `(0, 1)` both map to `(0, 0)`, while
`(1, 0)` and `(1, 1)` both map to `(1, 1)`. Repeated copy reaches one of these
fixed points after one transition and stays there.

ArxMentis currently persists only the present pair, not transition history.
After copying from either `(0, 0)` or `(0, 1)`, the stored state is `(0, 0)` in
both cases, so this system cannot distinguish those pasts once they converge.

Order matters when both directions are applied. Starting at `(D1, D2) = (1, 0)`,
stepping D2 and then D1 produces `(0, 1)`. Stepping D1 and then D2 produces
`(1, 1)`. The same dependent transitions therefore yield different final
states in a different sequence.

Repeatedly stepping D2 while holding D1=`1`, starting from `(1, 0)`, produces
`D2` values `0, 1, 0, 1, 0`, a period-2 cycle. Repeatedly applying the ordered
round “step D2, then step D1” produces `(1, 0)`, `(0, 1)`, `(1, 1)`, `(1, 0)`.
This is a period-3 cycle measured in complete two-step rounds.

Run the tests with:

```powershell
python -m unittest
```
