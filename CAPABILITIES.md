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

### Learned fixed binary transition model and prediction

**Claim:** after one observed transition from an unknown fixed binary environment
law, existing state can retain which law is active and predict later states
before the environment transitions.

The environment class is deliberately small:

- STAY: `D1' = D1`
- FLIP: `D1' = 1 - D1`

Protocol:

1. D2 initially holds the previous D1 value.
2. The environment performs one transition under an unknown fixed law.
3. Existing `evaluate_criterion` writes `M = D1 XOR D2`.
4. Therefore M=0 identifies STAY and M=1 identifies FLIP.
5. Existing `memory_dependent_transition` uses M to advance D2.
6. After synchronization, advancing D2 once before each environment transition
   produces the next-state prediction.

The regression covers both initial D1 values and both laws, then predicts eight
future transitions exactly.

- State: D1, D2, M.
- Law: existing equality evaluation and memory-dependent transition.
- Environment: the harness selects a fixed hidden STAY or FLIP law, initializes
  D2 to the first observed D1, and controls transition timing.
- Evaluator: after each prediction is committed, the harness advances D1 and
  checks whether D2 equals the realized environment state.

**Minimality result:** exhaustive search proves that one model state cannot
represent both STAY and FLIP for exact next-state prediction. Two model states,
equivalent to one binary distinction, are sufficient and necessary. Existing M
already supplies that capacity.

**What is earned:** a learned persistent environment-model distinction and
next-state prediction for this two-law class. The prediction is present in D2
before the next environment transition.

**What is not earned:** autonomous observation timing, discovery of the
environment class, prediction over arbitrary binary laws, or a general learned
world model. The harness still supplies the experiment clock and restricts the
possible environment laws.

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


## Post-pivot findings

### Derived gated write

Existing XOR and plastic transitions compose into a conditional store.

Apply XOR from driver d into target t, then apply plastic transition with
selector s. Exhaustive testing over all eight input triples gives:

```text
s=0 -> t remains its previous value
s=1 -> t becomes d
```

No new primitive is introduced. This derived gated write is enough to address
one of two retained slots when combined with a temporary context complement.

### Complete deterministic binary model class

A binary deterministic one-step environment has four possible transition laws:
`00`, `01`, `10`, and `11`, where the two bits are the successors of
current states 0 and 1.

Exhaustive encoder/decoder search establishes a capacity lower bound of four
learned model states, equivalent to two binary distinctions. Existing P0 and
P1 already supply exactly that capacity.

A fixed composition of existing toggle, XOR, and plastic transitions can store
an observed successor into the context-selected model bit. Another fixed
composition can load the selected model entry into D2 before the environment
moves. Starting both model entries wrong, the regression learns and predicts
all four laws after receiving one observation from each current-state context.

This establishes exact tabular model acquisition and next-state prediction for
the full deterministic binary one-step law class without adding persistent
state or a primitive transition.

The harness still supplies observation timing, one sample from each context,
and execution of the fixed composition.

### Passive identifiability limit

Complete four-law identification cannot be guaranteed from every single passive
trajectory, regardless of memory size.

Starting from 0, constant-0 and identity both generate `0,0,0,...` forever.
Starting from 1, identity and constant-1 both generate `1,1,1,...` forever.

The formalism now computes transient/cycle trajectory signatures and groups
laws that are observationally equivalent from a given initial state.

Therefore this boundary cannot be solved by adding memory. Complete
identification requires informative context coverage from the environment, an
external experimenter, or an intervention mechanism that reaches an otherwise
unobserved state.


### Fixed intervention resolves passive non-identifiability

A second regression replaces externally handed context coverage with a fixed
intervention schedule.

The system starts in context 0, records that transition, then uses existing
copy plus toggle operations to force the environment into the complement of the
sampled context. It records the second transition there. The schedule is the
same for all four environment laws and does not branch on the hidden law or on
the observed successor.

Across all four deterministic binary laws, the sampled contexts are exactly
`[0, 1]` and the retained model becomes exact.

This establishes that **intervention/coverage is sufficient** to overcome the
passive identifiability limit in this environment class. It does not establish
that ArxMentis decides when intervention is needed; the harness still invokes
the fixed schedule.


### Coverage-sensitive information-seeking intervention

A narrow active-learning probe now uses the otherwise-free memory slot as a
one-bit underdetermination/coverage state.

The environment is restricted to the two laws that remain indistinguishable
after observing `0 -> 0`: constant-0 and identity.

After that passive observation:

- two candidate laws remain consistent;
- repeating the same context leaves both candidates consistent;
- the retained uncertainty/coverage bit causes a fixed decision program to
  intervene into context 1 before the revealing successor is observed;
- the context-1 observation reduces the externally evaluated candidate set
  from two laws to one;
- the learned P0/P1 table then equals the hidden law;
- after the uncertainty/coverage bit is marked complete, running the same
  decision program no longer intervenes.

The action choice therefore depends on retained epistemic state and is made
before the revealing observation.

This is not general expected-information-gain reasoning. The mapping from the
one-bit uncertainty state to the useful intervention is built into the fixed
program, and the harness still sequences observation, storage, and evaluation.
