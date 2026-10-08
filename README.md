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
```

The last read for each distinction recovers the value saved by the previous
process. Distinction 1 remains the default. To use a different state file for
the selected distinction, pass `--state-file PATH` to either command.

Given the persisted values `D1` and `D2`, their relation is derivable without a
relation primitive: `D1 XOR D2` is `0` when they are the same and `1` when they
are different.

`step --distinction 2` makes D2's next state depend on D1: it persists
`D2' = D1 XOR D2` while leaving D1 unchanged. With D2 held at `0`, stepping
once with D1=`0` leaves D2 at `0`; stepping with D1=`1` changes D2 to `1`.
Use `--state-file PATH` to override the target distinction's file; the driver
is read from its default file.

Run the tests with:

```powershell
python -m unittest
```
