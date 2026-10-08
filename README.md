# ArxMentis

ArxMentis' first persistence primitive is one mutable bit stored in
`.arxmentis-state` beside the program. The state starts at `0`; toggling it
writes the changed value so a later process can recover it.

```powershell
python arxmentis.py read
python arxmentis.py toggle
python arxmentis.py read
```

The last command reads the value saved by the previous process. To use a
different state file, pass `--state-file PATH` to either command.

Run the tests with:

```powershell
python -m unittest
```
