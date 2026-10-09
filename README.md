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
python arxmentis.py read-memory
python arxmentis.py memory-step --distinction 2
python arxmentis.py plastic-step --distinction 2
python arxmentis.py evaluate
python arxmentis.py adapt --distinction 2
python arxmentis.py read-policy
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

`copy --distinction 2` first retains the old D2 value in the persistent bit
`.arxmentis-memory` (M), then persists `D2' = D1`, leaving D1 unchanged. Read M
with `read-memory`. The XOR step is bijective over the four possible pair
states: each future has one past. Copy remains non-bijective over `(D1, D2)`:
`(0, 0)` and `(0, 1)` both map to `(0, 0)`, while `(1, 0)` and `(1, 1)` both
map to `(1, 1)`. Repeated copy reaches one of these fixed points after one
transition and stays there.

The retained bit distinguishes converging histories: copying from `(0, 0)`
leaves the present pair `(0, 0)` and M=`0`; copying from `(0, 1)` also leaves
the present pair `(0, 0)`, but M=`1`. This retains the overwritten value, not
a general transition log.

`memory-step --distinction 2` makes M affect the next state by persisting
`D2' = D2 XOR M` while leaving D1 and M unchanged. With the present pair fixed
at `(0, 0)`, M=`0` leaves D2 at `0`, while M=`1` changes D2 to `1`. Thus the
retained past can affect a later transition even when the present pair is
identical.

`plastic-step --distinction 2` selects between existing transition rules using
M: M=`0` applies the XOR step (`D2' = D1 XOR D2`); M=`1` applies copy
(`D2' = D1`). Copy can update M by retaining the overwritten D2 value, so a
past state can change which rule a later plastic step uses.

`evaluate` provisionally uses equality as its criterion. It derives
`E = D1 XOR D2`, considers E=`0` satisfied and E=`1` not satisfied, then writes
E to M. Run `evaluate` before `plastic-step` to feed the outcome into the next
rule selection. `plastic-step` leaves M unchanged so it remains available
until the next evaluation or copy.

`adapt --distinction 2` implements the action-evaluate-update cycle with a
separate persistent policy bit P in `.arxmentis-policy`: P=`0` selects XOR and
P=`1` selects copy. It applies P's transition, evaluates equality and stores
the result E in M, then uses win-stay/lose-shift: keep P when E=`0`, otherwise
flip P. Read or flip P with `read-policy` or `toggle-policy`. Unlike the
standalone `plastic-step`, `adapt` does not use M to choose the current action;
M records the outcome while P preserves the policy.

The test suite enumerates all 16 initial configurations `(D1, D2, M, P)` while
holding D1 fixed. Under repeated `adapt` cycles, each reaches a fixed state
with D1=D2 and E=0.

The perturbation test starts at each stable environment state, flips only D1,
and continues `adapt` without resetting D2, M, or P. Both directions return to
D1=D2 and M=0: changing D1 from 0 to 1 takes three cycles and shifts P from XOR
to copy; changing D1 from 1 to 0 takes one cycle and retains copy. No state is
reset after the perturbation. This demonstrates recovery for this one-bit
perturbation under the current criterion and policy rule.

An alternating perturbation test runs `0 -> 1 -> 0 -> 1 -> 0 -> 1 -> 0 -> 1`
without resetting D2, M, or P. It records recovery times of
`3, 1, 1, 1, 1, 1, 1, 1` cycles: after the first exposure changes P from XOR
to copy, the persistent policy supports one-cycle recovery for each subsequent
environment change. This is an operational test of improved performance after
experience for this perturbation sequence; it does not add a new transition
rule or state bit.

A policy-isolation test first acquires P=`1` by solving the same `0 -> 1`
perturbation, then preserves only P and resets D1, D2, and M to `(0, 0, 0)`.
Against a naive XOR-policy control with identical task state, the experienced
COPY policy recovers in one cycle instead of three. This isolates the
performance advantage to persistent policy state for this task.

Before adding context-specific policies, the test suite also checks that the
actions have different value under different contexts. Starting both trials
with D2=`1` and using D2=`0` as the provisional success condition, COPY succeeds
when D1=`0`, while XOR succeeds when D1=`1`. This establishes that the
environment contains a context-dependent choice; it does not change the
existing equality criterion in `adapt` or add policy state.

`adapt-context` tests retained context-to-action associations. The existing
`.arxmentis-policy` is P0, and the additional `.arxmentis-policy-1` stores P1;
each uses `0` for XOR and `1` for COPY. D1 selects which policy acts and learns,
with D2=`0` as the success criterion for this command. The two-bit policy can
represent all four mappings from the two contexts to the two actions; one
global policy bit can represent only two. The interference regression trains
P0 to COPY and P1 to XOR in turn, then returns to each context and confirms its
learned action is still selected after training the other.

The anticipation probe starts from `(D1, D2)=(0, 0)`, toggles D2 before each
environment flip, then evaluates equality only after D1 flips. Across eight
alternating transitions, each preparation temporarily makes D1 and D2 differ,
but the environmental change restores equality before evaluation (`E=0`).
This demonstrates that the existing `toggle_state` operation can mechanically
produce anticipatory regulation under a perfectly alternating environment. It
does not show that ArxMentis predicts the environment or learns when to toggle:
the action and environmental schedule are externally imposed.

The delayed-credit test uses P=`0` for no-op and P=`1` for toggle. At each
episode boundary it restores D2 to the current D1 but preserves P, then applies
the selected action, flips D1, and only then evaluates equality and updates P
with win-stay/lose-shift. P=`0` first produces a later error and switches to
P=`1`. The toggle action then temporarily breaks equality before the
environment flip restores it; the delayed evaluation succeeds and retains
P=`1`. Across eight episodes, outcomes are `1, 0, 0, 0, 0, 0, 0, 0` and the
policy updates are `(0 -> 1)` followed by seven `(1 -> 1)` updates. This
demonstrates delayed credit assignment using existing persistent state and
operations under the imposed alternating schedule; the episode reset and
environment timing remain externally controlled, so this does not establish
that ArxMentis predicts the environment.

`predict-next` commits an explicit alternating-environment prediction by
writing `1 - D1` to the existing M bit before D1 changes. The prediction test
repeats this for eight transitions, verifies M contains the claim while D1 is
still at its observed value, then externally toggles D1 and compares the
previously committed prediction with the new observation. The sequence is
`D1: 0,1,0,1,0,1,0,1`, predictions `1,0,1,0,1,0,1,0`, and all eight match.
M is reused as the prediction register and is not an additional persistent bit.
This verifies a committed, accurate prediction under the assumed alternating
rule; the rule is encoded by the predictor and supplied by the experiment, so
this does not show that ArxMentis learned the environmental pattern.

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
