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

## Immediate research frontier

The next high-value target is a capability for which the harness currently
supplies essential structure. Prediction is a strong candidate:

> after observing an environment sequence, produce a next-state prediction
> better than an appropriate baseline without being told the environment law.

The experiment must distinguish:

- learning a law from merely being initialized with one;
- prediction from externally scheduled anticipatory action;
- stored world-model state from policy state;
- performance due to internal state from performance due to the harness.

Do not add a "model bit" until the capability has been specified and the
existing architecture has failed the corresponding search.
