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

## Intervention result

The passive-identifiability bound is not a storage failure. A fixed
intervention schedule is sufficient to expose the missing context.

Starting from context 0, the experiment:

1. records the observed transition from the current context;
2. uses existing copy plus toggle operations to force the environment into the
   complement of the sampled context;
3. records the second transition there.

The same schedule works for all four deterministic binary laws. It does not
branch on the hidden law or successor value.

Therefore the current boundary is now sharper:

- model capacity is sufficient;
- model acquisition laws are sufficient by composition;
- fixed intervention is sufficient to supply missing information;
- choosing **when and why** to intervene is not yet internal.

## Coverage-sensitive intervention result

The first uncertainty-sensitive probe uses the otherwise-free M role as a
one-bit distinction between "still underdetermined" and "resolved" in a
two-candidate environment.

After observing `0 -> 0`, constant-0 and identity remain consistent. Repeating
the same context has zero discriminatory value. A fixed decision program uses
the retained underdetermination state to intervene into context 1 before the
next successor is observed. That observation reduces the candidate set from
two laws to one. Once the retained state is marked resolved, the same decision
program no longer intervenes.

This earns a narrow form of state-dependent information-seeking action. It does
not earn general information-gain reasoning because the useful intervention is
prewired for this experiment.

## Immediate research frontier

Two pieces of external causal structure are now exposed clearly.

### 1. General epistemic choice

Can ArxMentis choose among multiple available interventions when which action
is informative depends on the current candidate-model set, rather than on a
hard-coded one-bit coverage flag?

A valid experiment should require at least two different uncertainty states for
which different interventions are optimal. The system must select before the
revealing observation and the evaluator must score ambiguity reduction, not
task-state reward.

### 2. Endogenous sequencing

The harness still invokes operation programs in the correct order: observe,
store, decide, intervene, predict, evaluate.

Eventually that ordering must itself become part of ArxMentis if the substrate
is to operate without an external experimenter selecting each law invocation.

These questions should remain separate. First determine whether general
epistemic action selection requires new representational state or only a richer
composition of existing laws. Then test whether the resulting program can be
driven by one repeated endogenous transition instead of an externally selected
sequence.
