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

## Immediate research frontier

The next useful boundary is a larger environment class rather than another
named feature.

A binary deterministic one-step environment has four possible laws:

```text
current 0 -> next 0, current 1 -> next 0
current 0 -> next 0, current 1 -> next 1
current 0 -> next 1, current 1 -> next 0
current 0 -> next 1, current 1 -> next 1
```

Equivalently: constant-0, identity, negation, and constant-1.

The next experiment should ask:

> after sufficient observations, what is the minimum causal architecture needed
> to predict all four laws exactly without being told which law is active?

Before adding state or a new update rule:

- establish the information lower bound;
- specify which observations make the law identifiable;
- test whether existing P0/P1 or other retained distinctions can be reused as
  model state;
- search whether existing transition laws can perform the required model update;
- account separately for any context scheduling or observation timing supplied
  by the harness.

The key distinction is now between **representational capacity** and
**learnability with the existing laws**. Having enough bits to encode a model
does not mean the current dynamics can acquire that model.
