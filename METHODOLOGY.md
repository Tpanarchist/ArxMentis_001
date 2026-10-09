# Minimal Causal Architecture Method

ArxMentis now treats capability construction as a minimization problem.

For a capability C, define an experiment by four components:

```text
State        persistent internal distinctions
Law          transition rules available to the system
Environment  externally supplied changes, timing, resets, or observations
Evaluator    the condition that decides whether C was achieved
```

A capability claim is valid only relative to all four.

## Research loop

For each proposed capability:

1. **Specify behavior first.** Define C without naming the mechanism expected
   to implement it.
2. **Expose assistance.** Record every intervention supplied by the harness.
3. **Search before adding.** Determine whether the existing architecture can
   already satisfy C.
4. **Prove lower bounds when small.** Exhaustively enumerate candidate machines
   or encodings whenever the search space permits.
5. **Add the minimum candidate.**
6. **Ablate.** Remove or collapse the candidate structure and verify that C
   disappears.
7. **Minimize behaviorally.** Treat internal states that never change observable
   behavior as equivalent.
8. **Record only earned implications.**

## Complexity accounting

ArxMentis does not equate "few bits" with "simple." Complexity can be moved
between components. Track at least:

```text
K_S  persistent-state complexity
K_L  transition-law complexity
K_E  environment/harness assistance
K_G  evaluator/goal complexity
```

These are bookkeeping categories, not yet a universal scalar metric.

A future scalar complexity measure may use explicit proxies such as reachable
state count, transition-table entries, syntax-tree size, or description length.
Until such a metric is justified, keep the four components separate.

## Current proven lower bounds

### One lost binary distinction

To recover either value of an overwritten binary distinction after visible
state has converged, the internal memory must distinguish at least two cases.

```text
minimum internal states = 2
minimum binary distinctions = 1
```

`formalism.py` proves this by exhaustive encoder/decoder search.

### Arbitrary binary action mapping over two contexts

Two contexts with two possible actions admit four possible mappings:

```text
00  choose action 0 in both contexts
01  choose 0 then 1
10  choose 1 then 0
11  choose action 1 in both contexts
```

A persistent controller that can later reproduce any one of those mappings
must distinguish four learned cases.

```text
minimum controller states = 4
minimum binary distinctions = 2
```

`formalism.py` proves this by exhaustive encoder/decoder search.

This lower bound does not prove that ArxMentis discovered the contexts. The
current implementation is given the context partition externally and uses D1
to select one of two policy bits.

### Fixed STAY/FLIP environment prediction

For the restricted environment class

```text
STAY  next = current
FLIP  next = 1-current
```

exact next-state prediction requires the learned system to distinguish which
of the two laws is active. Exhaustive encoder/decoder search establishes:

```text
minimum model states = 2
minimum binary distinctions = 1
```

The existing M bit already meets this lower bound. No new persistent state or
runtime transition is needed. One observed transition lets
`evaluate_criterion` write the transition parity into M; existing
`memory_dependent_transition` can then advance D2 according to the learned
law before future environment transitions.

This is the first post-pivot example where formal specification and search
show that a proposed new primitive is unnecessary.

## Four-law result

For the complete deterministic binary one-step law class, exhaustive search
establishes:

```text
minimum model states = 4
minimum binary distinctions = 2
```

Existing P0/P1 already meet the capacity lower bound.

The current dedicated contextual-adaptation rule is not itself a complete
model-acquisition rule under the direct interpretation D1=context,
D2=observed successor. In particular, the context-1 / successor-0 case
oscillates.

However, search over the existing transition semantics exposed a derived
operation:

```text
XOR(driver, target)
then plastic(driver, target, selector)
```

which is exactly a gated write:

```text
selector=0 -> preserve target
selector=1 -> target := driver
```

Using a temporary context complement for one slot and the original context for
the other yields a fixed, branch-free two-slot addressed store. The same
construction yields a context-selected read into a prediction bit.

Therefore all four binary deterministic laws can be acquired and predicted
with the existing persistent state and primitive transitions once one
observation from each context is supplied.

This distinguishes three levels that must remain separate:

1. **capacity**: can the retained state represent the model?
2. **acquisition dynamics**: can existing laws write the model from observations?
3. **information availability**: does experience expose enough of the
   environment to identify the model?

## Passive identifiability bound

The third level now becomes the frontier.

From initial state 0, constant-0 and identity produce the same passive
trajectory forever. From initial state 1, identity and constant-1 do the same.

No amount of additional memory or a more elaborate learner can infer a
transition that is never observed when multiple environment laws remain
consistent with the entire history.

## Immediate research frontier

The next question is therefore:

> what is the minimum additional causal structure required for ArxMentis to
> obtain information that passive experience cannot provide?

Candidate sources of that information must be distinguished rather than
collapsed together:

- externally supplied coverage of otherwise unvisited states;
- endogenous intervention that changes the environment into an informative
  state;
- exploration policy that decides when an intervention is useful;
- uncertainty state that distinguishes known from still-underdetermined model
  entries;
- autonomous sequencing that invokes observation, storage, prediction, and
  intervention without the harness choosing each operation.

Do not add all of these. The next experiment should determine which is first
actually necessary.

A strong first target is **intervention without uncertainty reasoning**:
provide a fixed intervention schedule that forces coverage of both binary
contexts, then test whether the already-derived acquisition program learns all
four laws. If that succeeds, intervention/coverage is sufficient while
decision-making about when to intervene remains unearned.

Only after that should the project ask whether ArxMentis can represent its own
model uncertainty and choose an intervention because it would resolve that
uncertainty.
