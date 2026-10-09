# ArxMentis Capability Ledger

This file records what each capability claim requires. A capability is not
credited to ArxMentis if a necessary part of the behavior is supplied by the
experiment harness.

Each claim is described across four sources of causal structure:

- **State**: persistent distinctions retained by ArxMentis.
- **Law**: transition logic implemented by ArxMentis.
- **Environment**: changes or timing supplied from outside ArxMentis.
- **Evaluator**: the condition used to classify an outcome.

The purpose is to prevent capability from being hidden in transition code,
test resets, schedules, or success criteria.

## Current claims

### Persistent distinction

**Claim:** a binary distinction survives process death.

- State: one persistent bit.
- Law: read/write/toggle.
- Environment: process termination and restart.
- Evaluator: recovered value equals the previously written value.

### Retained lost history

**Claim:** two histories that converge to the same visible present can remain
distinguishable.

- State: D1, D2, M.
- Law: copy stores the overwritten D2 in M before replacing D2 with D1.
- Environment: two selected initial histories.
- Evaluator: same final (D1, D2), different M.

**Minimality result:** exhaustive search proves that retaining one arbitrary
lost binary distinction requires at least two internal memory states. One bit
is sufficient and necessary for this capability.

### Adaptive equality regulation

**Claim:** repeated adaptation reaches and maintains D1 = D2 for a fixed D1.

- State: D1, D2, P; M is exposed outcome state but is not required to choose
  the next action inside `adaptive_transition`.
- Law: P selects XOR or COPY; equality error drives win-stay/lose-shift.
- Environment: D1 is held fixed.
- Evaluator: E = D1 XOR D2.

**Important bound:** COPY is a globally successful action for this evaluator,
so this task demonstrates learned policy retention in an easy environment. It
does not establish general policy learning.

### Re-adaptation after perturbation

**Claim:** after D1 changes, the existing adaptive loop can restore D1 = D2
without resetting M or P.

- State: D1, D2, M, P.
- Law: existing adaptive transition.
- Environment: the harness flips D1.
- Evaluator: equality.

The perturbation is externally supplied. ArxMentis does not decide when the
environment changes.

### Persistent performance improvement

**Claim:** prior experience changes persistent policy state and improves later
recovery on the same perturbation class.

- State: persistent P carries the advantage.
- Law: adaptive transition.
- Environment: repeated alternating D1 perturbations.
- Evaluator: recovery cycles to stable equality.

The policy-isolation regression strengthens this claim by resetting D1, D2,
and M while preserving only P.

### Context-conditioned action association

**Claim:** separate learned action choices can be retained for two contexts
without overwriting one another.

- State: D1, D2, M, P0, P1.
- Law: D1 directly selects P0 or P1; the selected policy learns independently.
- Environment: context values and task setup are supplied by the harness.
- Evaluator: D2 = 0 for the contextual command.

**Minimality result:** there are four possible binary action mappings over two
binary contexts. Exhaustive search proves that a persistent controller state
must therefore have at least four distinguishable states to represent all four
mappings exactly. Two bits are sufficient and necessary.

**Limitation:** ArxMentis is given the context partition and the mapping from
D1 to a dedicated policy slot. It does not discover that contexts should have
separate learned storage.

### Anticipatory preparation probe

**Claim:** an existing operation can prepare D2 before a perfectly alternating
environmental flip so that equality holds after the flip.

- State: D1, D2, M.
- Law: toggle.
- Environment: the harness imposes the alternating schedule and triggers both
  preparation and environment transition.
- Evaluator: equality after the flip.

This is mechanical anticipatory regulation under an imposed schedule, not
prediction.

### Delayed credit

**Claim:** a policy choice can receive evaluative credit only after a later
environment transition.

- State: D1, D2, M, P.
- Law: P chooses no-op or toggle; later evaluation updates P.
- Environment: the harness restores the episode boundary state, applies the
  environment flip, and controls evaluation timing.
- Evaluator: equality after the environment transition.

This establishes delayed reinforcement under an imposed episode protocol. It
does not establish autonomous episode formation, prediction, or general
temporal credit assignment.

## Rule for future claims

Before adding a new primitive:

1. State the capability as an observable behavioral condition.
2. List every state, law, environment intervention, and evaluator assumption.
3. Search existing state/laws for a witness.
4. If none exists, establish a lower bound where exhaustive search is feasible.
5. Add the smallest candidate structure.
6. Ablate it.
7. Credit only the behavior that remains after external assistance is made
   explicit.

The research target is not the fewest persistent bits in isolation. It is the
smallest causal architecture that satisfies a capability specification without
hiding the solution in laws, environment control, or evaluation.
