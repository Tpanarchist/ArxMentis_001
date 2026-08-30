# Arxmentis Genesis Kernel and Self-Revision Capsule

Date: 2026-08-29

Status: Consolidated design for human review

Scope: First executable Arxmentis sub-project

## 1. Outcome

Arxmentis is a persistent pulse machine that attends over governed
transformations, dynamically composes them into cognitive structures, and
reversibly compiles stable cognition into cheaper machinery.

Genesis does not implement that entire vision. It establishes the smallest
causal and constitutional substrate on which the later system can honestly be
built.

Genesis must demonstrate that:

1. Every canonical Unit-State transition is caused by an admitted Signal and
   TransitionProposal.
2. Only the deterministic control plane installs Unit State or changes the
   active runtime head.
3. Atomic Units and recursively nested Formations obey one external contract.
4. State, control history, governance artifacts, and symbolic Memory remain
   distinct.
5. Connections exist only when types, Capabilities, Constraints, scope, and
   information-flow rules permit them.
6. Substitution is justified only inside a declared and evaluated Congruence
   region.
7. A running Design Formation can inspect its exact declared construction,
   synthesize and choose among bounded type-correct structures expressed in
   the same Unit/Formation algebra it is made from, emit a successor absent
   from the initial store, submit it to a separately governed evaluator,
   survive activation and a clean-process restart, and causally use the
   selected change to reach a semantically different design in its next
   episode.

Genesis is a bounded self-hosting demonstration. It is not evidence of
consciousness, a general-purpose self-improver, or an autonomous semantic
authority.

## 2. The falsifiable question

Genesis answers:

> Can a deterministic, recursively composed Formation inspect the
> content-addressed Release and Formation specifications that declare its
> active design path, construct and select a useful typed subgraph from a
> small primitive grammar using runtime evidence, pass an exhaustive
> predecessor-owned evaluation, activate an immutable successor without
> in-place mutation,
> cold-start that successor from canonical persistence alone, and show through
> replay and exact counterfactuals that the changed path caused the next design
> result?

Genesis inspects the exact declared design closure:

- ReleaseImage.
- Root and nested FormationSpecs.
- UnitSpecs, PortSpecs, and RelationSpecs.
- Registered Mechanism and Constraint identities and content digests.
- Capability policy.
- Mutable-surface declaration.

It does not introspect the semantics of Python, SQLite, the host interpreter,
or the kernel implementation. Those remain part of the trusted computing
base.

## 3. Scope and kill-gated delivery

Genesis is one vertical sub-project delivered through four internal kill
gates. Each gate must pass before the next begins.

### 3.1 K0 — Pulse and Commit spine

K0 implements:

- Canonical encoding.
- Record identifiers and content hashes.
- Signal delivery occurrences.
- One immutable State document per Unit incarnation.
- TransitionProposal.
- KernelTransactionBatch.
- SystemControlJournal and branch journals.
- TransitionCommit.
- One deterministic queue.
- SQLite atomicity.
- Ledger reconstruction replay.
- Mechanism re-execution replay for trusted deterministic Mechanisms.

K0 does not implement Formation recursion or Release succession.

### 3.2 K1 — Minimal recursive Formation

K1 adds:

- UnitSpec and Trion runtime projection.
- FormationSpec as a Unit implementation.
- Explicit Formation boundary mechanisms.
- Ports and Relations.
- Closed Capability sets and attenuation.
- A small closed Constraint set.
- Causally active nesting.
- Boundary-summary reconciliation.

Only features exercised by the Capsule enter K1.

### 3.3 K2 — Immutable Release succession

K2 adds:

- ReleaseImage.
- ReleaseAdmissionRecord.
- ReleaseApprovalDecision.
- ActivationAttempt.
- ReleaseActivationRecord.
- BranchInitializationCommit.
- Isolated evaluation and startup branches.
- Exact compatible State copying between incarnations.
- Predecessor-owned startup evaluation.
- Active-head promotion.
- Cold restart.

K2 supports one narrow State-compatible patch family. It does not implement
general migration.

### 3.4 K3 — Genesis Self-Revision Capsule

K3 adds:

- DesignFormation.
- EvaluationAuthority.
- ReleaseGate.
- ApprovalIngress.
- ActivationController.
- One exhaustive finite Congruence evaluator.
- Bounded primitive graph construction in the Unit/Formation algebra.
- G-001 self-revision.
- G-002 causal succession.
- Exact predecessor, inverse-patch, and surgical mediation counterfactuals.
- Metamorphic anti-theater tests.

### 3.5 Explicit non-goals

Genesis excludes:

- OpenAI, DSPy, and external model calls.
- Humans as cognitive Mechanisms.
- Shell, network, browser, or external tool effects.
- Arbitrary user-supplied Python.
- Textual and pygame.
- Obsidian and Markdown synchronization.
- General symbolic Memory objects such as Claims and Beliefs.
- Semantic attention and learned routing.
- General ephemeral Formation planning.
- General materialization and deoptimization.
- Production Self, Mind, or Society boundaries.
- Multiple kernel writers.
- Real-time concurrency.
- Priorities.
- Wall-clock timers.
- General State migration.
- Kernel recompilation.
- Formal proof of arbitrary programs.
- A general graph-rewrite language.
- A general user-facing fork API.
- Executable geometry templates.
- External-effect outbox execution.

## 4. Governing laws

### 4.1 Causal transition law

Every canonical Unit-State transition and governed Release transition has an
explicit admitted causal Signal or constitutionally typed control proposal.

This law applies to modeled control surfaces. It does not claim that Python
stack frames, SQLite page writes, or physical machine operations each have
modeled Signals.

### 4.2 Transition authority law

Only a TransitionCommit may change existing canonical Unit State or install
Unit-authored domain Signal emissions. Initial Unit State may be installed
only by GenesisBootstrapCommit or BranchInitializationCommit.

Genesis reserves EffectIntent fields but requires them to be empty.

### 4.3 Release authority law

Only a ReleaseActivationCommit in the singleton SystemControlJournal may
change the active runtime head.

### 4.4 Proposal law

Mechanisms and Formations propose. They do not gain mutation, approval, or
activation authority by producing a proposal.

### 4.5 State ownership law

Every Unit incarnation owns exactly one canonical State document at a runtime
cut. An ordinary TransitionCommit changes at most one existing Unit
incarnation's State. A BranchInitializationCommit may atomically create the
initial State documents for multiple new incarnations on a new non-active
branch, but may not change existing State or the active runtime head.

### 4.6 Signal boundary law

Units influence other Units only through target-specific Signal delivery
occurrences routed across declared Relations.

### 4.7 Composition law

Every valid Formation is externally a Unit. It accepts and emits the same
Signal envelope, owns State through its boundary Unit, participates in the
same proposal protocol, and receives no privileged mutation path.

### 4.8 Capability monotonicity law

At runtime, effective Capability is the intersection of every applicable
grant and attenuation.

Across ordinary self-revision, the successor authority envelope must be a
subset of the predecessor envelope. Authority expansion requires a separate
external decision and is outside Genesis.

### 4.9 Predecessor-governance law

The active predecessor's immutable evaluator, selector, startup contract,
ReleaseGate, and authority policy govern a candidate. Candidate rules become
prospective only after promotion.

### 4.10 Immutability law

Release images, Signals, State versions, transaction batches, evaluation
contracts, reports, approvals, and activation records are immutable.
Supersession creates linked records.

### 4.11 Replay law

Ledger reconstruction replay reproduces canonical projections from recorded
transaction batches.

Mechanism re-execution replay starts at the acceptance-pinned pre-G-001 cut
with only the Release, verified State, origin Signals, and recorded external
results, invokes every trusted
Mechanism again, and reproduces every generated proposal digest, admission
decision, TransitionCommit, and final runtime head.

Genesis acceptance requires both modes.

### 4.12 Honest opacity law

Genesis guarantees causal completeness across declared control surfaces,
conditional on trusted-kernel integrity. It does not claim that registered
Mechanism source is semantically understood or that ledger records prove
external reality.

### 4.13 Scoped Congruence law

No implementation is globally substitutable by type or name alone.
Congruence always names:

- Applicability region.
- Initial-State relation.
- Input family.
- Observation boundary.
- Output relation.
- Relevant State relation.
- Failure and termination relation.
- Effect relation.
- Evaluator.
- Coverage method.
- Tolerance.

## 5. Canonical identity and encoding

### 5.1 Record identity is not content identity

Genesis separates stable record names from content hashes.

A RecordId is allocated from causally prior data:

    journal_scope_id
    journal_transaction_sequence
    record_kind
    local_index

Every record also has a content_hash.

Back-references use RecordIds. Content hashes verify immutable bodies. This
prevents circular hashes among a TransitionCommit, its new State, and its
emitted Signals.

`journal_scope_id` names either the singleton SystemControlJournal or one
runtime/evaluation branch journal. Runtime records additionally name their
`branch_id` in their bodies.

Hashes are derived envelope fields, never members of the body they verify:

    record_content_hash =
        SHA256(domain_prefix || canonical_encode(record_body))

    batch_body_hash =
        SHA256(batch_body_domain || canonical_encode(batch_body))

    resulting_batch_hash =
        SHA256(batch_chain_domain || prior_batch_hash || batch_body_hash)

`content_hash`, `batch_body_hash`, and `resulting_batch_hash` are excluded
from their own canonical inputs. `prior_batch_hash` occurs exactly once in
the batch-chain calculation. RecordIds may safely occur in hashed bodies
because their allocation does not depend on content hashes.

### 5.2 Canonical encoding profile

Genesis canonical encoding is versioned and has these rules:

- UTF-8.
- Lexicographically sorted object keys by Unicode code point.
- NFC-normalized strings.
- Object keys normalized to NFC before duplicate detection and sorting.
- Duplicate keys after normalization prohibited.
- Explicit type and schema-version tags.
- Defaults materialized before hashing.
- Integers only for canonical numeric fields.
- Floating point, NaN, infinity, and negative zero prohibited.
- Bytes encoded as lowercase hexadecimal.
- Timestamps prohibited from canonical control decisions.
- Lists retain declared order.
- Sets encoded as sorted lists under their schema-defined key.
- SHA-256 with a type-specific domain prefix.
- The exact domain-prefix bytes included in the kernel ABI manifest.
- Pydantic validates data but does not define the wire format.

Changing this profile requires a kernel ABI transition.

## 6. State, history, governance, and Memory

Genesis recognizes four distinct durable roles.

### 6.1 Canonical current control State

State is the current canonical operational value recognized for a Unit
incarnation by the control plane at a particular version.

Canonical means authoritative for runtime control. It does not mean
epistemically true of the world.

Each Unit incarnation owns one State document containing:

- IncarnationId.
- State-schema digest.
- Owner-local State version.
- Complete canonical value.
- Prior State RecordId.
- Creating KernelTransactionBatch RecordId.
- Content hash.

A TransitionProposal supplies a complete replacement State value, not a
generic patch program.

### 6.2 Kernel control State

Kernel control State includes:

- Active runtime head.
- Queue.
- Runtime instance graph.
- Branches.
- Capability contexts.
- Budgets.
- Activation attempts.
- Trion dispositions.

Global fields are represented by the singleton SystemControlJournal; runtime
fields are represented by branch journals. All are rebuildable projections of
canonical transaction batches. Kernel control State is not Unit-owned State.

### 6.3 Immutable control history

KernelTransactionBatches and their annotations record accepted control-plane
history. They are authoritative for what Genesis recorded and committed,
conditional on trusted-kernel integrity.

They do not prove that an external Observation was accurate or that a payload
Claim was true.

### 6.4 Immutable governance artifacts

Release images, evaluation contracts, reports, approvals, and activation
records are durable governance artifacts. They are neither current Unit State
nor symbolic Memory merely because they persist.

### 6.5 Symbolic Memory

Symbolic Memory is a future typed representation of past State,
Observations, Episodes, Referents, Concepts, Claims, Evidence, Beliefs, Goals,
and other durable cognitive content.

The Genesis ledger may later be cited as evidence about control-plane
occurrences. It is not the complete Memory ontology.

The future Obsidian vault will project and ingest symbolic artifacts. A file
edit will enter as an origin Signal and proposal; Markdown will never directly
replace canonical live State.

## 7. Mechanism, Unit, Trion, and Formation

### 7.1 Mechanism

A Mechanism is a trusted deterministic implementation that computes:

    Mechanism(
        complete Unit State at t,
        delivered Signal,
        frozen EnvironmentView
    )
        ->
    TransitionProposal[
        complete replacement State,
        proposed CommitSignalEmissions,
        empty EffectIntents
    ]

Genesis Mechanisms are a closed set of small kernel-shipped Python functions.

Purity, determinism, absence of ambient access, and termination are
construction-time trusted-computing-base obligations verified by review and
tests. Running in one Python process cannot enforce those properties against
malicious code.

A hung Mechanism hangs Genesis and is a trusted-kernel defect. Genesis does
not claim safe preemption or sandboxing.

### 7.2 EnvironmentView

EnvironmentView is immutable and contains:

- Active ReleaseImage digest.
- Target logical and incarnation identities.
- Frozen State RecordId and hash.
- Frozen trace cut:
  - branch_id
  - transaction sequence
  - batch hash
- Authorized TraceQuerySpec and TraceQueryResult digests.
- Authorized specification references.
- Effective Capability digest.
- Remaining structural budgets.

It contains no database handle, file handle, network client, clock, random
source, mutable registry, or live trace query.

The proposal read set cites exact State and trace-cut references.

A TraceQuerySpec is a content-addressed, predecessor-owned deterministic
selection and projection over canonical history. Every TraceQueryResult names:

- TraceQuerySpec digest.
- Frozen journal, branch, and transaction cut.
- Complete selected RecordId set or a deterministic selection proof.
- Derivation-implementation digest.
- Result digest.
- Completeness, omission, and redaction status.

The kernel or an independent verifier can recompute the result from canonical
records. Genesis diagnostic queries return the general typed
request/completion slice for a declared design episode; they may not encode a
target Relation or preselect the suspected duplicate path.

### 7.3 Unit

A UnitSpec declares:

- Logical Unit identity.
- Implementation kind.
- Input and output PortSpecs.
- State schema.
- Mechanism identities.
- Capability requirements and grants.
- Constraints.
- Lifecycle and failure behavior.
- Inspection surface.

A logical_instance_id names a durable architectural position that may survive
compatible Releases.

An incarnation_id names:

    ReleaseImage digest
    logical_instance_id
    UnitSpec digest

State ownership belongs to the incarnation.

### 7.4 Trion

Trion is the canonical small stateful Unit implementation.

Its ternary disposition is a kernel-derived control projection:

- inhibited: ordinary delivery is rejected because the incarnation is
  disabled, quarantined, or failed.
- quiescent: one activation slot is free.
- active: one delivered Signal is awaiting proposal recording or one proposal
  is awaiting admission.

Genesis permits one active activation per Unit incarnation. Ordinary Signals
for an active Unit remain queued.

Disposition at a durable cut is reconstructed from canonical queue, proposal,
failure, and lifecycle records. While the single synchronous scheduler is
inside a trusted Mechanism call, live inspection may additionally report the
guarded invocation as active; no durable cut occurs inside that Python call,
and a crash returns the still-pending delivery to the quiescent projection. A
Unit cannot self-report its disposition.

The trit is operational only. It is not a Claim truth value, authorization
result, or arbitrary internal data restriction.

### 7.5 Formation

A FormationSpec is a UnitSpec whose implementation declares:

- Child UnitSpecs or nested FormationSpecs.
- Internal Relations.
- External-to-internal mappings.
- Internal-to-external mappings.
- Boundary State schema.
- Capability grants.
- Completion policy.
- Cycle and pulse budgets.
- Failure aggregation.
- Inspection aggregation.

Every Formation instance has an explicit boundary Unit and one active
activation at a time in Genesis.

An external Signal is delivered to the boundary Unit. Its boundary Mechanism
proposes:

- Activation and correlation State.
- Internal child-input emissions.

A TransitionCommit installs that State and those emissions.

Child completion Signals return to a declared boundary input. The boundary
Mechanism then proposes terminal State and external output emissions. Another
TransitionCommit emits them.

Every Formation activation has:

- activation_id
- parent correlation
- allowed output cardinality
- child membership
- completion rule
- failure rule
- late-Signal rule
- pulse budget

This makes Formation-as-Unit literal rather than privileged routing syntax.

In Genesis, Relation compatibility is deliberately strict. A RelationSpec
names one source output Port and one target input Port with the same canonical
schema digest, plus its Capability attenuation and scope. There is no implicit
subtyping, coercion, payload rewriting, or adapter insertion. Any
transformation must be an explicit Unit or Formation and therefore appears in
the inspected design and causal trace.

## 8. Signal, emission, delivery, and control records

### 8.1 SignalRecord

Every deliverable Signal is represented by one member of a closed immutable
SignalRecord union:

- OriginSignalRecord: authenticated external or constitutional ingress.
- CommitSignalEmission: Unit-authored output created by a TransitionCommit.
- KernelControlSignal: constitutionally authored control data created by a
  KernelTransactionBatch.

A CommitSignalEmission contains:

- Source incarnation and output Port.
- Schema digest and canonical payload.
- Creating TransitionCommit RecordId.
- Correlation and causal parents.
- ReleaseImage digest.

A KernelControlSignal contains:

- Creating KernelTransactionBatch RecordId.
- Constitutional control rule.
- Schema digest and canonical payload.
- Causal Signal, proposal, and governance RecordIds.
- Target kernel endpoint or authorized Unit control Port.

TransitionProposal is its own immutable typed record. A KernelControlSignal
targeted at the admission controller carries its RecordId and digest as the
control payload. It is not a CommitSignalEmission because no Unit output Port
or TransitionCommit creates it.

### 8.2 SignalDeliveryOccurrence

Fan-out creates one target-specific delivery occurrence per Relation.

Each delivery contains:

- SignalRecord reference and Signal class.
- RelationSpec digest where applicable.
- Target incarnation and input Port, or kernel control endpoint.
- Branch-local enqueue_sequence.
- Causal parents.
- Parent Formation path.
- Source grant context.
- Relation attenuation.
- Target grant.
- Parent Formation grant path.
- Invocation lease where applicable.
- Effective Capability-set digest.
- ReleaseImage digest.

Each delivery has its own lifecycle even when several deliveries share one
emission.

### 8.3 Signal classes

The Signal classes are origin, commit-derived, and control, corresponding to
the three SignalRecord variants. Every control Signal names its creating
transaction, causal input, and constitutional rule. Routing a control Signal
to a Unit still requires an explicitly authorized control Port; targeting a
kernel endpoint does not pretend that the kernel is an ordinary Unit.

### 8.4 TransitionProposal

A TransitionProposal is wrapped as an internal control Signal and contains:

- Target incarnation.
- Expected ReleaseImage.
- Expected complete State RecordId and hash.
- Frozen read set.
- Complete proposed replacement State.
- Proposed output emissions.
- Empty EffectIntent collection.
- Claimed postconditions.
- Basis Signals.
- Mechanism identity.
- Resource accounting.

## 9. KernelTransactionBatch and Commit types

### 9.1 Canonical append-only source

One KernelTransactionBatch is the canonical append-only record for one
journal append performed by one SQLite transaction. Its body contains:

- journal_scope_id: the SystemControlJournal or one branch journal.
- journal-local transaction_sequence.
- prior_batch_hash.
- transaction_kind.
- consumed_record_ids.
- created_records: a fixed-order collection of complete typed canonical
  records.
- declared projection mutations used only as rebuildable checks.
- fixed-order annotations.

`created_records` may contain any registered Genesis core type, including
OriginSignalRecord, CommitSignalEmission, KernelControlSignal,
SignalDeliveryOccurrence, TransitionProposal, StateVersion, BranchCreated,
SnapshotCreated, ReleaseImageStored, ReleaseAdmissionRecord,
ReleaseApprovalDecision, ApprovalRevocation, ActivationAttempt, and
ReleaseActivationRecord.

Current State, queue, instance graph, disposition, branch heads, ingress
buffer, and active runtime head are projections. Complete typed records in the
journals, rather than annotation strings or projection tables, are canonical.

### 9.2 SystemControlJournal and branch journals

Genesis has one singleton SystemControlJournal with its own total transaction
sequence and hash chain. It canonically orders:

- GenesisManifest and branch creation.
- Stored Release and governance artifacts.
- Evaluation and activation attempts.
- Approval decisions and revocations.
- Durable origin ingress buffering and transfer cursors.
- The activation lock.
- ReleaseActivationCommits and the global active runtime head.

Each runtime or evaluation branch has an independent branch journal for its
queue, Unit State, instance graph, budgets, and transition history. A branch
cannot change global System control State. Cross-journal references are by
RecordId and always point to a causally prior committed batch.

Cold boot derives the active head only by verifying and replaying the
SystemControlJournal. A stored active-head projection is never authority.

### 9.3 KernelTransaction

A KernelTransaction is any atomic batch that advances one canonical journal.
It may record ingress, delivery completion, proposal generation, rejection,
failure, branch initialization, governance, or lifecycle activity.

### 9.4 TransitionCommit

A TransitionCommit is a branch KernelTransactionBatch that admits one
TransitionProposal and installs:

- One existing incarnation's replacement State.
- Zero or more CommitSignalEmissions and deliveries.
- Related complete typed control records.

### 9.5 BranchInitializationCommit

A BranchInitializationCommit is the first batch of a newly created inactive
evaluation or activation branch. It references a causally prior BranchCreated
system record and contains:

- Branch purpose: evaluation or activation.
- Governing EvaluationContract or ActivationAttempt.
- Source runtime cut and State root.
- Target ReleaseImage.
- CandidateInitialStatePlan.
- Complete created incarnation map and initial State records.
- Resulting branch State root.

It may atomically create multiple incarnation State records through exact
compatible copy and declared initialization. It may not change existing Unit
State, enqueue live external ingress, or alter the active runtime head. A
crash between BranchCreated and this first batch leaves an incomplete inert
branch that recovery marks failed.

### 9.6 ReleaseActivationCommit

A ReleaseActivationCommit is a SystemControlJournal batch that atomically
compare-and-swaps the expected predecessor active head to a validated,
quiescent staging-branch head. It also binds the durable ingress buffer to the
new head for ordered idempotent transfer. No branch batch may promote itself.

### 9.7 GenesisBootstrapCommit

One explicit GenesisBootstrapCommit is R0's branch-initialization batch. It
creates R0's initial incarnations and State and is caused by the
GenesisManifest and BranchCreated system records. It is the only bootstrap
exception; later initial State uses BranchInitializationCommit.

## 10. Pulse–Proposal–Commit execution

### 10.1 Pulse definition

One Pulse is one scheduler step that processes the ready queue entry with the
smallest branch-local enqueue_sequence under the kernel's closed deterministic
readiness predicate.

A domain Signal delivery Pulse may invoke a Mechanism and atomically record a
Proposal Signal.

A Proposal Signal delivery Pulse performs deterministic admission and either
creates a TransitionCommit or a rejection transaction.

Thus an ordinary Unit-State transition normally spans two visible Pulses:

    delivered domain Signal
        ->
    proposal recorded
        ->
    proposal admitted and State committed

### 10.2 Unified queue order

Every queued delivery, regardless of Signal class, receives one monotonically
increasing branch-local enqueue_sequence.

Within one transaction, the kernel allocates consecutive sequences in:

1. Output Port declaration order.
2. RelationSpec digest order.
3. Target incarnation order.

Proposal Signals and branch-local kernel control Signals receive queue
sequences in their creating branch transactions. An OriginSignalRecord first
receives a System origin_ingress_sequence; a later idempotent branch ingress
transaction assigns its delivery enqueue_sequence in origin order. Normal
scheduling does not overtake assigned activation-ingress transfer.

Readiness is a total kernel predicate, not a Mechanism or policy hook:

- Proposal and kernel-controller deliveries are ready.
- An ordinary delivery to a quiescent target is ready.
- An ordinary delivery to an active target is blocked and remains queued.
- A delivery to an inhibited or missing target is ready for explicit
  rejection handling.

The scheduler selects the lowest-sequence ready entry. A blocked entry keeps
its sequence and becomes preferred immediately when ready. This permits the
later Proposal Signal for the activation that caused the block to reach the
admission controller; strict queue-head blocking would deadlock two queued
deliveries to one Unit. There is no mutable priority, re-enqueue, or
Mechanism-controlled defer.

### 10.3 Crash-safe delivery

For synchronous trusted Mechanisms:

1. Peek the pending queue entry.
2. Capture exact State, trace cut, Release, and Capability context.
3. Invoke the Mechanism without changing canonical database State.
4. In one SQLite transaction:
   - consume the delivery
   - append delivery annotations
   - store and enqueue exactly one Proposal Signal, or
   - store MechanismFailed and an allowed control Signal

If the process crashes during invocation, the queue entry remains pending and
recovery re-invokes the deterministic Mechanism.

Proposal generation has uniqueness key:

    delivery RecordId
    Mechanism digest
    captured State hash
    trace-cut hash

### 10.4 Admission

Proposal admission checks:

1. Schema.
2. Active Release and branch.
3. Target incarnation.
4. Mechanism authorization.
5. Expected State version and hash.
6. Read-set validity.
7. State ownership.
8. Replacement-State schema.
9. Unit Constraints.
10. Formation and Release invariants.
11. Output Signal schemas.
12. Port and Relation compatibility.
13. Pinned Capability-context recomputation.
14. Capability non-amplification.
15. Empty EffectIntent requirement.
16. Resource and queue budgets.

The result is admit or reject.

### 10.5 Rejection

Rejection installs none of the proposal's State, proposed domain Signals, or
EffectIntents.

Kernel-authored rejection records and an allowed ProposalRejected control
Signal remain valid.

Stale State produces StaleProposal. Reconsideration requires a new explicit
Signal.

### 10.6 Control-budget escape

Kernel control Signals use a small separate constitutional control budget.
They are not charged to the exhausted domain activity that caused them.

Control Signals cannot start unbounded domain work. A recipient must open a
fresh bounded activity explicitly.

## 11. Capability and Constraint model

### 11.1 Genesis Capability set

The closed Genesis set includes:

- signal.emit
- state.propose
- trace.read
- formation.instantiate
- release.propose
- release.evaluate
- runtime.inspect
- evaluation.branch

release.activate is not a delegable Unit Capability. Only the kernel
ActivationController path may request a ReleaseActivationCommit.

Release approval is likewise not an ordinary Unit Capability. It is a
nondelegable constitutional-origin authority held only by an externally
configured principal. It cannot appear in a Release, Unit, Formation,
Relation, or invocation-lease grant. ApprovalIngress may issue a challenge and
authenticate and route the returned decision; it cannot create or approve the
decision.

### 11.2 Runtime attenuation

Effective Capability is:

    Release grant
    intersect parent Formation grant
    intersect Unit grant
    intersect Relation attenuation
    intersect invocation lease
    intersect constitutional policy

The exact operands and result digest are pinned on each delivery occurrence.

### 11.3 Succession authority delta

ReleaseGate computes a canonical delta across:

- Release grants.
- Unit and Formation grants.
- Relation attenuation.
- Lease-issuance authority.
- Inspection access.
- Governance access.
- Data-scope access.

Ordinary Genesis succession rejects any increase.

The candidate-controlled delta cannot add or broaden:

- Approval or activation authority.
- Evaluation-authority mutation.
- Capability-policy amendment.
- Production test-ablation authority.

The successor Release necessarily retains the unchanged predecessor-owned
governance siblings and references; their authority is not inherited by the
mutable DesignFormation.

### 11.4 Constraints

Genesis uses a closed set of trusted total predicates with result:

- satisfied
- violated
- indeterminate

Indeterminate authority or safety never admits.

Constraint code is trusted; boundedness is verified by construction and tests,
not enforced against hostile Python.

## 12. Persistence, branches, and recovery

### 12.1 Canonical store

Genesis uses:

    .arx/arxmentis.db

SQLite provides atomic transactions across transaction batches and current
projections.

Genesis pins:

- `PRAGMA foreign_keys = ON`.
- `PRAGMA synchronous = FULL`.
- `PRAGMA journal_mode = DELETE` for the single-writer Genesis store.
- Explicit `BEGIN IMMEDIATE` for writer transactions.

Crash claims are bounded by SQLite and the host filesystem's documented
durability guarantees. Tests cover failure before commit, termination during
a transaction, termination immediately after commit, and simulated I/O
failure.

Human-readable exports are non-authoritative.

### 12.2 Branches

Every runtime record has branch_id.

An evaluation branch references:

- parent branch.
- parent transaction sequence.
- parent batch hash.
- complete snapshot root.
- owning EvaluationContract.
- causally prior BranchCreated system RecordId.

Each branch has independent:

- transaction sequence.
- enqueue sequence.
- queue.
- State.
- instances.
- budgets.
- transaction hash chain.

Evaluation-purpose branches can never become live. Only an
activation-purpose staging branch tied to one valid ActivationAttempt can be
promoted through ActivationController.

Genesis exposes branches only to the predecessor-owned evaluation path.

### 12.3 Snapshot

A verified snapshot contains or hashes:

- ReleaseImage.
- transaction cut and hash.
- complete logical-instance to incarnation map.
- complete State-owner map.
- queue.
- runtime instance graph.
- Capability contexts.
- budgets.
- disposition projections.
- activation status.
- SystemControlJournal cut and hash used with the branch snapshot.

No external outbox exists in Genesis.

### 12.4 Recovery

Recovery:

1. Verifies the SystemControlJournal from GenesisManifest to its head.
2. Derives the active branch and cut from that journal.
3. Verifies every active-branch batch from its branch root to the active cut
   and every branch cut referenced by the active Release's admission and
   activation lineage.
4. Only then verifies and uses a snapshot as a projection accelerator.
5. Applies later KernelTransactionBatches.
6. Rebuilds every current projection.
7. Compares rebuilt and stored projections.
8. Fails closed on mismatch.

`verify-ledger` and acceptance replay verify every branch referenced by any
covered System governance record, including rejected candidates; ordinary
cold boot need not reconstruct unrelated inert branches beyond integrity of
their referenced cuts.

A snapshot never exempts earlier history from verification in Genesis.

A clean-process cold boot receives only:

- Database path.
- Installed kernel package version.
- Boot command.

It receives no R1 object, expected digest, fixture path, or in-memory registry
state from the prior process.

The active ReleaseImage and registries are resolved only from canonical
persistence and the installed trusted registry.

### 12.5 Two replay modes

Ledger reconstruction replay begins at GenesisManifest and
GenesisBootstrapCommit and applies every System and covered branch batch
through the accepted G-002 DesignEpisodeResult. It verifies all projections,
hashes, branch roots, and active-Release transitions.

Mechanism re-execution replay begins at the fixed pre-G-001 cut before the
workload challenge. It is a noncanonical scratch reconstruction that reuses
the recorded logical journal and branch identities, expected sequences, and
therefore deterministic RecordIds. It appends nothing to the canonical
database. Before advancing, it compares every regenerated canonical body and
hash with the original.

It re-invokes trusted Mechanisms and replays authenticated external results,
including workload challenges and approval decisions, as recorded origin
Signals; it does not rerun external authorities. It compares:

- Proposal digests.
- Queue allocation.
- Admission.
- TransitionCommits.
- Final State and Release head.

The replay must cover workload selection, R1 construction and evaluation,
approval ingress, staging, promotion, activation-ingress transfer, G-002, and
R2 production. R1 must be discovered through the replayed
ReleaseActivationCommit, never supplied in the start snapshot.

Each ReplayReport records start and end cuts, System and branch transaction
counts, origin set, active-Release transitions, and the exact causal slice.
A final-state, zero-transition, or suffix-only replay cannot pass Genesis.

## 13. Recursive composition and Congruence

### 13.1 Causally active nesting

Every nesting level counted by Genesis must:

- Receive a boundary Signal.
- Execute at least one child transition.
- Emit a completion or output boundary Signal.
- Contribute to the causal slice of R1 or R2.

Pass-through wrappers do not count.

### 13.2 Boundary summaries

A collapsed Formation projection contains:

- Input boundary Pulse.
- Exact child transaction range.
- Output or failure boundary Pulse.
- Child Pulse and resource totals.

Expansion resolves the same immutable range.

### 13.3 Flattening

Genesis does not compare raw hierarchical and flattened traces.

The Congruence evaluator applies a declared observation projection that:

- Hides boundary-administrative records.
- Maps instance identities through an explicit correspondence.
- Compares external Signal streams.
- Compares declared State projections.
- Compares failure and termination behavior.
- Reports resource counts separately.

### 13.4 Congruence is application-level

The kernel supplies deterministic branches and trace extraction. It does not
decide semantic Congruence.

Genesis includes one predecessor-owned CongruenceEvaluator for the finite
Capsule domain.

Its report distinguishes:

- verified_for_exhaustively_enumerated_region
- no_counterexample_on_evaluated_scenarios
- refuted_by_counterexample
- unsettled

Genesis substitution requires
verified_for_exhaustively_enumerated_region. No statistical or sampled
substitution enters K3.

### 13.5 Genesis applicability guard

The revised evaluation path suppresses only EvaluationSemanticKey traces whose
length, equality pattern, payload schema, terminal-outcome class, and context
family satisfy E0's exact structural applicability predicate. Literal future
key bytes and SeenSetScope labels are opaque alpha-renamings, not unbounded
semantic dimensions.

An out-of-region or indeterminate identity bypasses suppression and follows
the predecessor behavior. It never disappears.

## 14. Release artifacts without digest cycles

### 14.1 ReleaseImage

ReleaseImage is the immutable content-addressed executable definition:

- Kernel ABI.
- Schema bundle.
- Root FormationSpec.
- UnitSpec and Mechanism registry references.
- Constraint registry.
- Capability policy.
- Mutable-surface declaration.
- Startup-contract reference.
- Parent ReleaseImage digest.

The release_image_digest is derived from the body and is not embedded in the
hashed body.

ReleaseImage contains no approval, evaluation result, runtime State root, or
activation status.

### 14.2 CandidateInitialStatePlan

Genesis activation supports:

- Exact schema-and-value copy from mapped predecessor incarnation to a new
  successor incarnation.
- Initialization of newly introduced Unit State.
- Archival of deleted Unit State.

An identity-copy map links:

    old incarnation
        ->
    new incarnation

Even unchanged values receive new State records owned by the successor
incarnations and created by the staging branch's
BranchInitializationCommit. The later ReleaseActivationCommit only promotes
the already initialized and validated branch head.

### 14.3 ReleaseAdmissionRecord

This immutable record references:

- Base ReleaseImage.
- Candidate ReleaseImage.
- Frozen EvaluationContract.
- Exact evaluator, selector, workload-provider, metric-extractor, and
  CongruenceEvaluator digests.
- EvaluationReport.
- CongruenceReport.
- Authority-delta report.
- Manifest-diff proof.
- CandidateInitialStatePlan.
- Predecessor-owned StartupContract.
- Approval-policy identity, source/configuration digest, version, input schema,
  challenge policy, and authority kind expected for automated approval.

### 14.4 ReleaseApprovalDecision

Approval is a typed immutable decision created after the admission reports
exist.

It contains:

- Approving principal.
- Exact nondelegable grant.
- Base and candidate ReleaseImage digests.
- EvaluationContract and report digests.
- Decision: approve, reject, or abstain.
- Conditions and activation scope.
- Expiry as a SystemControlJournal transaction ceiling and one-use challenge,
  never wall-clock time.
- Post-evaluation challenge nonce.
- Ledger positions and causal references proving the reports predate the
  decision.
- Governance cut at which the decision was created.
- For a mechanical fixture, approval-policy identity and digest, exact
  predicate inputs, and predicate result.

Later revocation is a separate immutable ApprovalRevocation system record. An
immutable decision never contains mutable revocation status.

The automated fixture is candidate-agnostic. Its policy is content-addressed
and pinned in R0 before workload selection. It approves only when a fixed
mechanical predicate over immutable reports passes. Its source and
configuration contain no expected Release digest, target identity, or profile
identity.

This demonstrates binding and governance mechanics, not independent semantic
wisdom. A future human decision may provide stronger external judgment.

### 14.5 ActivationAttempt and ReleaseActivationRecord

ActivationAttempt references:

- Predecessor active head and runtime cut.
- Candidate ReleaseImage.
- ReleaseAdmissionRecord.
- ReleaseApprovalDecision.
- CandidateInitialStatePlan.
- StartupContract.
- Staging branch.

ReleaseActivationRecord references:

- Successful attempt.
- Promoted staging-branch head.
- Final candidate State root.
- Promotion transaction.
- Prior active head.
- Exact approval-validity result at attempt creation and at promotion.
- Ingress-buffer assignment and transfer cursor.

It is created inside the successful ReleaseActivationCommit batch. Because
the compare-and-swap and record append are one SQLite transaction, no active
head can exist without its activation record.

Before creating an ActivationAttempt, and again atomically in the
ReleaseActivationCommit, ActivationController recomputes approval validity
from canonical System control State. It requires:

- Decision is `approve`; reject and abstain cannot create an attempt.
- Exact base, candidate, admission, branch, contract, report, and challenge
  matches.
- Approval scope covers this attempt and every condition is satisfied.
- The external nondelegable grant is valid and unconsumed.
- The System-transaction expiry ceiling has not passed.
- No causally later ApprovalRevocation exists.

The promotion transaction consumes the one-use approval. Any mismatch fails
closed.

## 15. Evaluation, approval, and activation authority

### 15.1 Root topology

The root has capability-separated siblings:

    GenesisRootFormation
        DesignFormation
        EvaluationAuthority
            WorkloadProvider
            ScenarioRunner
            BaselineRunner
            CandidateRunner
            CongruenceEvaluator
            CostComparator
            Selector
        ReleaseGate
        ApprovalIngress
        ActivationController

ReleaseGate and EvaluationAuthority are outside the mutable DesignFormation.
ScenarioRunner is the immutable expensive service exercised by design-search
requests. BaselineRunner and CandidateRunner are predecessor-owned harness
roles that execute matched whole-Release branches. A candidate may send typed
requests through declared Ports but cannot mutate any authority implementation
or report.

The authoritative harness instance always belongs to the active predecessor
(R0 for R1 and R1 for a later candidate) and writes its reports to System
governance records. A candidate branch
contains the unchanged ScenarioRunner as part of the behavior being exercised,
but no Unit in that branch can author its own EvaluationReport,
CongruenceReport, selection, or admission decision.

### 15.2 Immutable evaluation authority

EvaluationContract E0 exists in R0 before the DesignProblem that generates a
candidate.

E0 pins:

- Workload family and exhaustive region.
- External challenge schema, challenge-authority identity, profile-generator
  digest, and permitted nonce domain.
- Workload-provider digest.
- Evaluator and runner digests.
- Metric extractor.
- TraceQuerySpec and derivation digests.
- Cost vector and weights.
- Congruence projection.
- Selector.
- Primitive catalog, graph grammar, configuration grammar, canonical
  enumeration order, and hard candidate bound.
- G-002 task generator, candidate grammar, validity oracle, target-path family,
  pulse-budget formula, success margin, and counterfactual procedure.
- Approval fixture policy identity, source/configuration digest, version,
  challenge policy, and fixed predicate.
- Allowed manifest-diff surface.
- Negative tests.
- StartupContract.

DesignFormation may propose extra tests but cannot remove or redefine E0.

Candidate branches can emit observations only. They cannot write evaluator
State, reports, workload data, or selection results.

Metrics come from kernel transaction records, never candidate-emitted counters.

ReleaseGate recomputes report validity from canonical evidence.

### 15.3 Allowed candidate delta

Genesis permits exactly:

- Replacement of one declared mutable Relation with a nested compatible
  Formation.
- Addition of that nested Formation's UnitSpecs and Relations.
- Initialization of its new State.
- Transitive content-hash changes caused by those edits.

Every other ReleaseImage field must equal the candidate's exact active base
Release.

ReleaseGate rejects changes to:

- EvaluationAuthority.
- Selector.
- WorkloadProvider.
- ReleaseGate.
- ApprovalIngress.
- ActivationController.
- Metrics.
- Constraint registry.
- Capability policy.
- StartupContract.
- Kernel instrumentation.

### 15.4 Staged activation

Activation never moves the active head before startup passes.

Lifecycle:

    prepared
        ->
    healthcheck_running
        ->
    healthcheck_passed
        ->
    active

or:

    healthcheck_failed

Procedure:

1. Record ActivationBarrierRequested in the SystemControlJournal for the exact
   ReleaseActivationProposal. From that System cut onward, new origins enter
   only the durable ingress buffer while predecessor dispatch drains work that
   was already queued.
2. Drain R0 until the ReleaseActivationProposal is the only actionable item,
   then consume it. The predecessor policy pins a finite drain-Pulse budget;
   exhaustion aborts the barrier rather than abandoning queued work.
3. Verify the active queue is empty, every Unit and Formation activation is
   quiescent, no Proposal or bounded activity remains, and no earlier attempt
   is unresolved. Acquire the durable System activation lock and pause
   predecessor dispatch.
4. Recompute positive approval validity and create ActivationAttempt and a
   BranchCreated record.
5. Create successor incarnations and State with one
   BranchInitializationCommit on the staging branch.
6. Deliver CandidateStartupContext and run the predecessor-owned bounded
   StartupContract with no effects or live ingress.
7. Require the terminal health result committed, staging queue empty, every
   staging Trion quiescent, and no pending startup control Signal.
8. On failure, mark the attempt failed, release the lock, and idempotently
   transfer buffered origins back to R0 in origin order. R0's head never
   moved.
9. On success, recompute approval validity and use one System
   ReleaseActivationCommit to compare-and-swap the validated staging head into
   the active head and bind the buffer to R1.
10. Create ReleaseActivationRecord in that same System batch, conditional on
    the successful compare-and-swap; there is no post-commit recording gap.
11. Enqueue one distinct operational RuntimeActivated control Signal, then
    idempotently transfer buffered origins in origin sequence before normal
    dispatch resumes.

If barrier validation or the first approval check fails before an
ActivationAttempt exists, one System BarrierAborted record releases the lock
or pending barrier and returns buffered origins to the unchanged predecessor
in origin order.

CandidateStartupContext is staging-only and is never enqueued again after
promotion. RuntimeActivated is a distinct operational Signal.

BufferedOrigin and IngressTransferCursor are canonical System records. Each
branch transfer records an origin-RecordId to delivery-RecordId mapping with a
uniqueness constraint. If a process dies after branch enqueue but before the
System cursor advances, recovery observes the mapping and advances without a
duplicate. The promoted branch remains in `DRAINING_ACTIVATION_INGRESS` until
RuntimeActivated and every assigned origin through the buffer cut are
transferred.

Any unclean termination while an ActivationAttempt is prepared,
healthcheck_running, or healthcheck_passed but not yet promoted marks that
attempt failed on recovery. The predecessor remains active; retry requires a
new proposal, approval check, and attempt. Genesis never resumes a partially
executed startup branch. A crash after the ReleaseActivationCommit instead
recovers R1 as active and resumes only the idempotent activation-ingress drain.

## 16. Genesis Self-Revision Capsule

### 16.1 What Genesis claims

The Capsule is a bounded executable demonstration of reflexive construction
and causal succession.

The same algebra plays four roles:

1. UnitSpec, FormationSpec, PortSpec, and RelationSpec are the executable
   object language of R0.
2. Trace records and SelfLens references point to those exact same spec nodes,
   rather than to a second descriptive model.
3. CandidatePatch and the bounded graph grammar construct new typed
   Formations with the same composition and Capability laws.
4. CandidateCompiler produces an ordinary ReleaseImage that the unchanged
   kernel executes through the same Pulse–Proposal–Commit protocol.

There is no shadow architecture model and no separate privileged design
language. The design is being used to design itself: executable Formation
structure is both the thing inspected and the medium of the proposed change.
Governance remains deliberately non-reflexive in Genesis; the candidate
cannot rewrite the evaluator, gate, approval policy, or kernel.

Human design supplies a small generic primitive catalog, a bounded typed graph
grammar, and finite prospective task families. It does not supply a
deduplication Formation, a quota Formation, a target Relation, or a candidate
Release. The test asks whether DesignFormation constructs the useful
composition and locates it from its own design and evidence. This is not a
claim that an open-ended designer invented the primitives or objective.

### 16.2 DesignFormation topology

    DesignFormation
        Observe
        ProblemFramer
        TraceDiagnoser
        SelfLens
        PatchSynthesizer
            RewriteSearchFormation
                RewriteEnumerator
                CandidateQueue
                MutableScenarioRequestPath
                ScenarioRequestEmitter
        CandidateCompiler

The candidate evaluation Units are not children of DesignFormation.
`MutableScenarioRequestPath` is one of several type- and locally
topology-compatible paths inside DesignFormation. The expensive ScenarioRunner
is behind DesignFormation's output boundary in the unchanged
EvaluationAuthority. Candidate edits occur before that authority boundary and
cannot change or wrap the constitutional evaluator itself.

### 16.3 Workload profiles

E0 pins a finite profile generator and nonce domain. After R0 is
content-addressed and Mechanism implementations are fixed, an external test
authority supplies a fresh authenticated challenge nonce that was unavailable
to DesignFormation before the R0 digest. WorkloadProvider deterministically
expands and records it as one profile:

1. Duplicate evaluation work on one eligible scenario-request path.
2. No duplicate work, for which NoChange must win.
3. Duplicate work at a different type- and locally topology-compatible path
   and nesting depth.

The finite input and State region for each profile is exhaustively enumerable.
Evaluation runs every member.

Every profile contains at least two simultaneous active decoy paths with the
same Port schemas and local graph shape. The duplicate workload moves among
them across challenges. Choosing the first route, deepest route, only route
before ScenarioRunner, or any stable structural signature therefore fails.

The canonical passing G-001 run uses profile 1 or 3, chosen after R0 exists.
Profile 2 is a mandatory negative control. Acceptance expands four fixed-count
challenge seeds: duplicate at path A, duplicate at path B, duplicate-free,
and a semantics-preserving wrapper/flattening variant.

Unit identities, Relation identities, and catalog declaration order are
permuted in metamorphic variants without changing semantics. The challenge
Signal and deterministic expansion are recorded and replayed; temporal
post-freeze ordering alone is not treated as challenge separation.

### 16.4 EvaluationSemanticKey and SeenSetScope

Genesis separates semantic equality from isolation provenance.

EvaluationSemanticKey contains:

- Canonical candidate-spec digest.
- EvaluationContract digest.
- Scenario-bundle digest.
- Relevant initial boundary-State root.
- ScenarioRunner implementation digest.
- Constraint and Capability-context digest.

SeenSetScope contains:

- Evaluation branch identity.
- Search-episode identity.

DedupKey is the pair `(SeenSetScope, EvaluationSemanticKey)`. SeenSet indexes
DedupKey, while Congruence compares ordered EvaluationSemanticKey sequences.
Branch and episode identities remain ledger provenance but cannot make matched
R0 and candidate behavior semantically unequal.

The first occurrence atomically inserts its DedupKey into episode-local State
before emitting a runner request. Later identical requests are suppressed
whether the first request is queued, running, or complete. The Genesis
ScenarioRunner is deterministic for a complete EvaluationSemanticKey and the
boundary contract requires one terminal receipt per unique key, not per
duplicate request. An infrastructure Mechanism defect invalidates the
experiment rather than silently deleting or reusing the key. Cold restart
reconstructs the exact seen-key State.

Mandatory cases:

- Same semantic key and same scope is suppressed after the first insertion,
  including while the first request is in flight.
- Same candidate with a different scenario bundle or initial State is not
  suppressed.
- Two branches or episodes do not leak SeenSet State.
- A new episode begins through SearchEpisodeStarted with a new empty scope.
- Cold restart mid-episode restores exactly that episode's seen keys.

E0 does not enumerate literal future digests. It exhaustively enumerates
bounded input traces by equality-pattern class: trace length, first/duplicate
pattern, terminal outcome, payload family, and allowed context family. Keys
are opaque canonical bytes and ScopedSeenSet may only hash and compare them.
The evaluator also exhaustively checks equivariance under injective renaming
of key bytes, branch identities, and episode identities.

The region certificate records the enumerator digest, exact class cardinality,
hash of the complete member set, and per-member coverage. Every G-002 input
must satisfy the exact E0 structural applicability predicate. An out-of-region
G-002-like input bypasses suppression and is a mandatory negative control.

### 16.5 Candidate space

PatchSynthesizer does not possess or emit a designated filter or R1. It uses a
closed primitive catalog:

- Identity: typed pass-through.
- CanonicalKey: configured canonical field projection and hash.
- ScopedSeenSet: persistent scoped membership annotation.
- Counter: persistent episode-local ordinal annotation.
- Comparator: total equality or bounded-integer predicate.
- Gate: typed pass/reject routing from a Boolean annotation.

The bounded graph grammar enumerates no-op and every canonical single-entry,
single-exit, acyclic, type-correct inserted subgraph with:

- At most four primitive Unit instances.
- At most five internal Relations.
- No implicit adapters, fan-out, cycles, or hidden State.
- Configuration values drawn only from E0's finite field, scope, comparator,
  constant, and Gate-output grammar.
- Placement at every evidence-eligible mutable compatible Relation plus, when
  available, exactly one canonical evidence-free compatible decoy.

EvidenceEligibility is a frozen generic predicate over the recomputed trace
slice: the same RelationSpec must have carried at least two byte-identical
EvaluationSemanticKeys in the episode and at least one corresponding terminal
Scenario receipt must exist. It names no path or topology signature.

This grammar produces competing structurally admissible families, including
identity chains, counter/gate structures, malformed-for-the-objective but
type-correct gates, and the useful key/SeenSet/gate structure. Type checking,
ReleaseGate admission, exhaustive behavioral evaluation, and cost selection
eliminate them; PatchSynthesizer contains no high-level
`EvaluationIdentityFilterFormation` constructor.

The graph grammar, primitive Mechanism digests, configuration grammar,
enumeration order, and numeric bounds are frozen before any challenge. The
implementation contains no:

- Expected R1 or R2 digest.
- G-001 or G-002 conditional branch.
- Fixture-specific Unit or Relation identity.
- Expected target path or topology signature.
- Preassembled candidate Formation or Release.
- Catalog-order assumption.

SelfLens derives candidate locations by traversing the content-addressed active
FormationSpec and joins them to the general TraceQueryResult through typed
instance and Relation references. Target preference must arise from repeated
EvaluationSemanticKey evidence, not from path shape alone. In a mandatory
evidence-ablation control, the same design and topology receive a matched
diagnostic origin stream whose formerly duplicate semantic keys are replaced
by unique keys. The resulting TraceQueryResult is recomputed normally; the
useful key/SeenSet/Gate candidate must not be synthesized.

CandidatePatch is itself a canonical typed design artifact containing:

- Exact base ReleaseImage digest.
- Target Formation path and RelationSpec digest.
- Expected source/target Port and schema digests.
- Expected Capability and Constraint context.
- Canonically generated inserted FormationSpec.
- New-State initialization plan.
- Generator identity and grammar derivation.
- Evidence RecordIds used to establish placement eligibility and canonical
  ordering.
- Exact preconditions.
- Mechanically derived inverse operation.

CandidateCompiler is a pure generic application of CandidatePatch to
ReleaseImage using the ordinary Formation validators. An independent verifier
recomputes the derivation, full Release body, and digest. CandidateCompiler
emits these artifacts only in a `release.propose` Signal; ReleaseGate is the
sole path that stores a candidate ReleaseImage in System governance. Runtime
construction therefore grants no storage, admission, approval, or activation
authority.

Candidate ReleaseImages, CandidatePatches, and inserted FormationSpecs must be
absent from the initial store, fixtures, registries, and origin Signals. The
generic primitive Mechanisms and grammar are necessarily present; absence is
evidence of runtime construction, not by itself evidence against canning.

### 16.6 G-001 flow

1. R0 boots through GenesisBootstrapCommit.
2. External challenge ingress supplies a post-freeze nonce and WorkloadProvider
   expands it under E0.
3. DesignProblem requests reduced exhaustive design-search cost while
   preserving boundary behavior.
4. Observe reads a frozen trace cut from the selected profile's diagnostic
   run.
5. The general TraceQueryResult is independently recomputed from canonical
   history.
6. TraceDiagnoser emits hypotheses from repeated EvaluationSemanticKey
   evidence across active decoys.
7. SelfLens discovers compatible active Relations from the exact declared
   design.
8. PatchSynthesizer exhaustively enumerates the bounded primitive graph grammar
   at the evidence-eligible placement, one compatible decoy, and no-op.
9. CandidateCompiler constructs previously absent CandidatePatches,
   FormationSpecs, and ReleaseImages.
10. ReleaseGate verifies grammar provenance and the exact mutable surface.
11. EvaluationAuthority forks the baseline and every candidate from matched
    snapshots through BranchInitializationCommit.
12. It exhaustively runs the finite equality-pattern and workload region.
13. CongruenceEvaluator compares:
    - ordered first occurrence of each EvaluationSemanticKey
    - one valid terminal Scenario receipt per unique semantic key
    - outputs, failures, and termination
    - final selected design result and evidence references
    - boundary State
14. CostComparator uses a frozen kernel-derived vector:
    - Mechanism invocations
    - TransitionCommits
    - Signal deliveries
    - ScenarioRunner completions by implementation digest
    - peak queue size
    - canonical bytes processed
15. Selector admits only candidates with strict positive frozen total-cost
    improvement and no dimension outside tolerance. If none qualify,
    NoChange wins. Ties use canonical CandidatePatch digest order.
16. The duplicate-free profile must select NoChange.
17. A passing duplicate profile must select the evidence-derived path and the
    key/ScopedSeenSet/Gate composition, not an arbitrary compatible location
    or a host-named template.
18. ReleaseGate creates ReleaseAdmissionRecord.
19. ApprovalIngress issues a post-report one-use challenge.
20. The provenance-pinned candidate-agnostic external fixture emits
    ReleaseApprovalDecision.
21. ActivationController stages and promotes R1.
22. A clean Python process cold-boots from the database alone.

### 16.7 G-002 causal succession

Before G-001 begins, E0 pins the G-002 generator, task family, primitive
grammar, validity oracle, admissible target family, budget formula, success
margin, and counterfactual procedure. None may depend on measured R1
performance.

After R1 promotion and clean-process boot, an external origin supplies only a
fresh allowed nonce and semantic identity permutation. WorkloadProvider
expands it into a prospective G-002 instance with a new target path not named
by any pre-R1 origin Signal. The exact target instance and threshold are not
chosen after comparing R0 and R1.

G-002 asks for a semantically different design: a bounded QuotaFormation at a
declared sandbox PolicySlot that passes the first `q` requests in an episode
and emits a typed QuotaExceeded result thereafter. The valid structure is
constructed from Counter, Comparator, and Gate primitives. It is not another
key/SeenSet deduplication insertion. Its functional oracle and `q` domain are
frozen in E0.

The G-002 edit grammar is restricted to unchanged sandbox PolicySlots present
in both R0 and R1; the inherited G-001 filter location is not a G-002 candidate
site. R0, R1, and the surgical intervention therefore enumerate the same
ordered DesignAlternativeSemanticKey stream. Their difference is the amount
of duplicate evaluation work performed after enumeration.

DesignAlternativeSemanticKey identifies the target logical slot, inserted
FormationSpec digest, configuration, and functional contract while excluding
inherited Release ancestry and evaluation-branch provenance. It lets aligned
R1 and counterfactual runs compare the same proposed design even when their
governance envelopes have different record identities.

The duplicate-heavy work occurs in the search for this quota design, not in
the quota design objective. Under the one prospectively fixed pulse budget:

- R1 suppresses redundant evaluations and reaches and evaluates the later
  unique quota candidate.
- Exact R0 exhausts the same budget earlier.
- An evaluation-only surgical intervention on R1 that forces every SeenSet
  decision to `novel` also exhausts the budget earlier.

R1 must produce a previously absent R2 CandidateReleaseImage containing both
the inherited R1 optimization and the new quota design. Genesis validates R2
but does not admit or activate it. Its terminal governance artifact is a
CandidateValidationReport against the frozen G-002 functional contract, not a
ReleaseAdmissionRecord or claim of Congruence with R1.

Acceptance requires:

- R1 is active by a System-journal-derived persisted ReleaseImage digest.
- R1 inspects its own exact declared spec and general trace slice.
- The R1-only ScopedSeenSet path receives causal Signals, suppresses only
  byte-identical earlier EvaluationSemanticKeys, and emits explicit
  suppression records.
- At least one later unique quota candidate passes the path and completes
  evaluation.
- RewriteEnumerator emits the same ordered DesignAlternativeSemanticKey stream
  in R0, R1, and the surgical intervention; the quota alternative that becomes
  R2 occurs at the same semantic ordinal.
- Every novel candidate passed by R1 is payload-identical to its counterpart;
  first-unique order is unchanged.
- R2 evidence references Scenario terminal Signals descended from the passed
  quota candidate, and Selector consumes those evidence Signals.
- The authority-separated, predecessor-owned EvaluationAuthority validates R2
  against the frozen G-002 functional contract.
- R2, its CandidatePatch, and inserted quota Formation do not exist in R0, R1,
  fixtures, or pre-G-002 records.
- A TraceAlignmentReport accounts for saved duplicate subtraces, filter
  overhead, and every divergence before R2.
- A DesignEpisodeResult records the complete causal slice.

NoChange is valid for negative controls but cannot pass canonical G-002.

### 16.8 DesignEpisodeResult

The terminal artifact contains:

- Active ReleaseImage.
- Exact inspected FormationSpec digest.
- DesignProblem.
- EvaluationContract.
- External challenge and WorkloadProvider expansion.
- TraceQuerySpec and recomputed TraceQueryResult.
- Candidate-generation trace range.
- Primitive-grammar derivation and complete candidate set.
- Evaluation reports and decisions.
- Changed-path causal references.
- TraceAlignmentReport for G-002.
- R2 digest, or evidence-bearing NoChange for noncanonical controls.
- Evaluator identities.
- Cost vector.

### 16.9 Exact counterfactuals

Genesis uses:

1. Exact immutable R0 initialized at SearchEpisodeStarted so every logical
   instance shared with R1 has byte-identical schema-compatible State and
   R1-only instances are absent.
2. An inverse-patch branch mechanically derived from CandidatePatch P1.
3. A mandatory evaluation-only surgical mediation replay that keeps R1's
   ReleaseImage, exact starting State, enumeration order, hash/comparator
   overhead, origin Signals, budgets, and every non-SeenSet route, but forces
   each ScopedSeenSet `seen_before` decision to `false`.

Applying the inverse patch to R1 must reproduce R0's root FormationSpec digest
exactly and leave the introduced State records unreachable and explicitly
archived. Release ancestry, governance records, and self-description still
differ; this branch is therefore a total-effect control, not the mediation
control.

All matched branches receive identical origin Signals, ordering, and budgets.

No test-only runtime topology mutation is permitted.

The surgical intervention is a predecessor-evaluator operation recorded in a
counterfactual branch and is never eligible for promotion. It intervenes only
on the SeenSet output value; the original and replacement values and every
affected downstream RecordId are labeled in the report.

G-002 begins with SearchEpisodeStarted. All episode-local DesignFormation
State outside the tested ScopedSeenSet is proven equal after reset, and the
starting State is reachable under each branch's own Release semantics. Exact
R0 and inverse patch are total-effect controls; only the surgical intervention
carries the mediation claim.

Trace alignment must establish:

- Identical ordered candidate stream before filtering.
- No divergence before the first duplicate decision.
- Every suppressed request matches an earlier key byte-for-byte.
- Identical payload and order for every passed novel request.
- R0 and intervention spend the missing budget only on identified duplicate
  ScenarioRunner subtraces.
- Saved subtrace cost minus measured filter overhead equals the observed cost
  delta within E0's exact accounting tolerance.

### 16.10 Anti-theater source and behavior checks

Acceptance audits the closed trusted Mechanism, grammar, workload generator,
and automated approval-policy source/configuration artifacts for forbidden:

- Expected candidate digests.
- Fixture-specific identities.
- Preassembled candidate manifests.
- Preassembled filter or quota Formation constructors.
- Branches on episode or profile names.
- Host lookup of a known target path.
- Expected target topology signatures or Release digests.

Metamorphic runs rename and permute all nonsemantic identities.

Evaluation-shaped and production-shaped invocations with identical contract
inputs must produce identical proposal digests despite different branch,
correlation, and scenario labels.

A negative fixture preloads a candidate or hard-codes a target and must be
detected. Another uses a post-report expected-R1 check in the approval fixture
and must also be detected.

Source scanning is a hygiene check, not proof that canning is absent. The
normative evidence is post-freeze external challenge generation, simultaneous
structural decoys, the duplicate-free NoChange control, primitive graph
enumeration, diagnostic-evidence ablation, the semantically different
prospectively frozen G-002 task, behavioral metamorphic variants, and surgical
causal mediation.

### 16.11 Hard feasibility bounds

Genesis K3 fixtures are valid only when all of these pre-run bounds hold:

- At most three mutable type-compatible placement Relations, including at
  least one active decoy.
- At most four inserted primitive Units and five internal Relations per graph.
- At most 48 unique canonical CandidatePatches in an episode after exhaustive
  type pruning.
- At most 16 exhaustive workload members per profile.
- Exactly four canonical metamorphic challenge variants.
- At most 2,048 genuine ScenarioRunner completions across the full K3
  acceptance suite.
- At most 250,000 Pulses and 128 MiB of canonical database growth per canonical
  G-001 or G-002 run.

The grammar compiler computes cardinality before execution. Exceeding a bound
fails the fixture; it never silently truncates or prunes candidates after
enumeration in a way that could preserve a preferred answer. The full suite
has a documented ten-minute target on the reference development machine, but
wall time is an engineering target rather than a control-plane decision.

## 17. Congruence and cost acceptance

### 17.1 Evaluated region

E0 declares the complete finite operational region by equality-pattern class
for the revised path. Its RegionCertificate contains the canonical enumerator
digest, class cardinality, complete member-set hash, coverage multiplicity,
and equivariance checks for opaque key and scope renaming.

The evaluator exhausts it. The report may therefore say:

    verified_for_exhaustively_enumerated_region

It may not say globally equivalent.

### 17.2 Boundary equality

R0 and R1 must have:

- Same ordered first-unique EvaluationSemanticKey sequence.
- Same terminal Scenario result for every unique semantic key.
- Same failures and termination.
- Same final selected design result.
- Same externally declared boundary State.
- No Capability or Constraint regression.

Internal ScopedSeenSet State, suppression records, and administrative Pulses
are outside the declared boundary but remain inspectable.

### 17.3 Cost requirement

On a duplicate-heavy profile:

- At least 25 percent fewer genuine ScenarioRunner completions.
- Positive improvement in the frozen total cost function.
- No unmeasured Mechanism class.
- No resource dimension worsens beyond its E0 tolerance.

E0 records numerator, denominator, weights, and tolerances before candidates.

### 17.4 Ablation and predecessor result

Exact R0, inverse-patch, and mandatory surgical SeenSet intervention recover:

- Duplicate completion trajectory.
- Higher cost.
- G-002 budget exhaustion before R2.

If R1's improvement remains, causal mediation is not established.

## 18. Activation and identity acceptance

### 18.1 Incarnation copy

R0 to R1 activation creates new successor incarnation identities and new State
records through exact compatible copy. R1 never owns R0 incarnation State.

### 18.2 Startup contract

R0's ReleaseAdmissionRecord pins a StartupContract:

- CandidateStartupContext input.
- Candidate initial State.
- Expected boundary outputs and State predicates.
- Maximum Pulse and Commit budget.
- Evaluator digest.
- No effects.

Candidate-emitted health is evidence. R0 evaluator decides.

### 18.3 Buffered ingress

During staging, external observations receive origin ingress sequence but no
runtime enqueue sequence.

After promotion:

1. One operational RuntimeActivated control Signal is enqueued first.
2. Buffered origins follow in origin sequence.

CandidateStartupContext was consumed only on the staging branch and is not
re-enqueued. On failed staging, buffered origins return to R0 in the same
origin order. Transfer is cursor-driven and idempotent across crashes.

## 19. Failure model

### 19.1 Malformed ingress

Reject and record without target Unit State.

### 19.2 Routing failure

Create RoutingFailed control record and Signal. Never silently drop.

### 19.3 Mechanism defect

No delivery-completion transaction occurs until the Mechanism returns.
A crash leaves the queue item pending. An exception records MechanismFailed.
A hang is a TCB defect and is not safely recoverable inside the process.

### 19.4 Stale proposal

Reject with exact State mismatch. Reconsideration requires a new Signal.

### 19.5 Constraint or authority failure

Reject. Indeterminate never admits.

### 19.6 Budget exhaustion

Stop the bounded activity and emit BudgetExhausted using the separate control
budget.

### 19.7 Database failure

Fail closed. Never continue on an uncommitted in-memory world.

### 19.8 Ledger or projection corruption

Stop at the first invalid transaction hash or projection mismatch. Do not
truncate or silently repair canonical history.

### 19.9 Startup failure

Mark the staging attempt failed. R0 remains active. Candidate State and reports
remain inspectable.

### 19.10 Congruence counterexample

Mark the report refuted_by_counterexample and reject admission.

### 19.11 Formation failure

Boundary completion policy decides fail-fast or aggregate failure for the
declared activation. Late child Signals become LateResult control Signals and
cannot reopen a completed activation.

### 19.12 Self-revision integrity failures

Genesis negative tests reject or fail acceptance when:

- Candidate changes evaluator, selector, workload, metrics, instrumentation,
  ReleaseGate, startup contract, or capability policy.
- Candidate emits report-shaped data into evaluator State.
- Candidate changes an inactive path.
- SeenSet leaks across branch or episode scope.
- Same candidate under different EvaluationSemanticKey is incorrectly
  suppressed.
- Candidate canonicalization version differs.
- Candidate recognizes evaluation mode.
- R1 boots but G-002 dispatches to R0 Mechanisms.
- Approval references another base, contract, report, branch, or expired
  challenge.
- A reject, abstain, revoked, consumed, out-of-scope, or condition-failing
  approval creates an ActivationAttempt or promotion.
- Approval policy or TraceQueryResult provenance cannot be recomputed.
- Inverse patch does not reconstruct R0.
- R1 reaches quiescence by dropping pending Signals.
- Clean boot resolves R1 from fixture or process memory rather than the
  database.
- Preloaded R1 or target-specific code is detected.
- Candidate enumeration exceeds a hard bound or is silently truncated.
- G-002 task, oracle, or budget was selected after observing R1 performance.
- Surgical mediation changes anything beyond the ScopedSeenSet decision.

## 20. Inspection contract

Genesis inspection reads immutable snapshots or transaction history and emits
no domain Signals.

Every projection identifies:

- Exact branch and transaction cut.
- Source artifact types and RecordIds.
- ReleaseImage.
- Authority class:
  - canonical control State
  - immutable control record
  - governance artifact
  - derived view
- Derivation and schema version.
- Freshness.
- Completeness for its declared surface.
- Fidelity.
- Redacted, unavailable, absent, stale, disconnected, and integrity-failed
  conditions separately.

Passive inspection is read-only.

Pause, stepping, breakpoint installation, active probes, and explanation
requests are governance operations and require typed control Signals in later
interfaces. Genesis's automated harness may stop between transactions without
pretending that this is an unrecorded domain action.

Required inspectable data:

- Active ReleaseImage and kernel ABI.
- SystemControlJournal head, active-head derivation, and branch transaction
  head.
- Unit and Formation instance tree.
- Logical and incarnation identities.
- Trion disposition.
- State versions and permitted values.
- Queue.
- Signal causal ancestry.
- Proposal admission and rejection.
- Capability derivation.
- Constraint results.
- Formation boundary and child ranges.
- Evaluation, Congruence, approval, and activation lineage.
- TraceQuerySpec/result derivation and RegionCertificate coverage.
- Primitive-grammar derivation, CandidatePatch inverse, and TraceAlignmentReport.

## 21. Minimal headless command surface

Genesis provides operations equivalent to:

- initialize
- run-g001
- inspect-trace
- verify-ledger
- approve exact candidate through the configured fixture or operator
- activate
- cold-boot in a clean process
- run-g002
- replay-ledger
- replay-mechanisms
- run-counterfactuals
- run-negative-controls

General interactive breakpoints, arbitrary historical forks, and rich query
commands are deferred.

## 22. Implementation constraints

Genesis uses:

- One pinned Python 3.12 patch release for acceptance.
- Pydantic 2.
- Standard-library SQLite.
- One OS process per runtime.
- One kernel writer.
- Synchronous closed trusted Mechanisms.
- Pytest.
- Hypothesis for property-based testing of canonical encoding, queue order, branch
  isolation, replay, and Formation boundaries.
- A content-addressed runtime manifest pinning interpreter, dependency,
  registry, canonicalization, and SQLite-policy versions.

Genesis does not use:

- Web servers.
- Actor frameworks.
- Task queues.
- Distributed databases.
- Plugin loading.
- Dynamic code download.
- Model SDKs.
- UI frameworks.

## 23. Acceptance matrix

### 23.1 K0

- Every post-bootstrap State version that changes existing State has exactly
  one admitted proposal and causal basis. Every initial State version names a
  GenesisBootstrapCommit or BranchInitializationCommit and its governing
  System record.
- Crash during Mechanism invocation leaves delivery pending.
- Proposal recording and delivery consumption are atomic.
- Rejection installs no proposal delta.
- Lowest-ready deterministic queue ordering is exact and the two-delivery
  active-target deadlock fixture completes.
- Ledger reconstruction replay covers the complete K0 fixture from bootstrap
  to its terminal head.
- Mechanism re-execution replay starts before the K0 fixture's first origin and
  regenerates every nonbootstrap transition.
- Canonical encoding digests are stable.
- System and branch hash chains rebuild all canonical projections.

### 23.2 K1

- Formation boundary changes occur through ordinary TransitionCommits.
- Every counted nesting level is causally active.
- One activation slot prevents overlapping State corruption.
- Capability intersections are pinned and verified.
- Inhibited delivery rejects.
- Boundary summaries reconcile to exact child ranges.
- Observation-projected flattening passes.

### 23.3 K2

- Candidate ReleaseImage contains no digest cycle.
- BranchInitializationCommit creates candidate State before startup without
  moving the active head.
- Approval is positive, postdates reports, binds exact artifacts and scope,
  remains unexpired and unrevoked, and is rechecked atomically at promotion.
- Successor authority does not increase.
- Candidate State belongs to successor incarnations.
- Predecessor and staging quiescence barriers pass.
- Staging failure never moves active head.
- Successful health check promotes in one transaction.
- Clean-process boot recovers from canonical persistence only.
- RuntimeActivated occurs once; buffered ingress is preserved and transferred
  idempotently across crash cuts.

### 23.4 K3

- Externally seeded workload profile is selected after R0 freeze and its
  expansion replays exactly.
- Candidate graph and Release are constructed from the primitive grammar and
  absent from the initial store.
- No fixture-specific Mechanism, grammar, workload, or approval constants.
- No-op wins on duplicate-free control.
- Correct target follows evidence across simultaneous structural decoys.
- Removing duplicate correlations from the diagnostic trace prevents
  synthesis of the useful candidate.
- Exhaustive region Congruence passes.
- Frozen total cost improves.
- Exact R0, inverse patch, and surgical SeenSet intervention remove the
  improvement under aligned traces.
- R1 cold-boots and produces an authority-separated validation of a
  semantically different, nonactivated quota R2 under prospectively frozen
  G-002 rules.
- Every G-002-filtered input satisfies E0 applicability; the out-of-region
  negative control bypasses suppression.
- G-002 evidence and cost mediation causally traverse the R1-only path.
- Metamorphic and anti-theater negative tests pass.
- Every hard feasibility bound is checked without silent candidate pruning.
- Full ledger and Mechanism replay start pre-G-001, derive R1 through the
  activation chain, and cover G-002 and R2 production.

## 24. Deferred roadmap

### 24.1 Symbolic world

Add typed Referent, Observation, Representation, Claim, Evidence, Belief,
Goal, Episode, Experiment, and Decision artifacts. Project to and ingest from
Obsidian through Signals.

### 24.2 Textual machine room

Build read-only recursive inspection, then typed command Signals. Add pulse
rail, State instruments, branch comparison, pause, step, replay, and fork.

### 24.3 Semantic attention

Implement SemanticAttentionFormation as an ordinary replaceable Formation.
Separate descriptor Claims, observed evidence, selection estimates, and
outcomes. Add route leases and bounded ephemeral construction.

### 24.4 External cognitive mechanisms

Add effect adapters for models and humans. Bind outputs to exact
ContextProjections and return completions as origin Signals.

### 24.5 Materialization

Use guarded scoped Congruence to fold stable Formations into cheaper
implementations. Retain original Formations and add shadow, canary,
prediction-error, and unfold protocols.

### 24.6 Self and Society

Add governed identity, Memory, Goal, observation, action, and continuity
boundaries. Preserve member authority and privacy across composition.

### 24.7 Kernel succession

Only later investigate reproducible kernel builds, ABI transitions,
independent conformance, external approval, and a recovery launcher outside
both kernels.

## 25. Final acceptance statement

Genesis is complete only when one human-inspectable and automated causal chain
establishes:

    R0 ReleaseImage created before workload selection
        ->
    externally seeded post-freeze workload challenge delivered
        ->
    R0 inspected its exact declared FormationSpec and independently
    recomputable frozen trace query
        ->
    R0 exhaustively constructed bounded type-correct primitive graphs in its
    own Unit/Formation algebra at evidence-derived and decoy locations
        ->
    previously absent R1 constructed from a provenance-complete patch
        ->
    separate R0 EvaluationAuthority exhausted the finite region
        ->
    exact reports and nonincreasing authority admitted
        ->
    provenance-pinned positive post-report approval bound to a one-use
    challenge and exact artifacts
        ->
    candidate staged without moving the active head
        ->
    predecessor startup contract passed
        ->
    one ReleaseActivationCommit promoted R1
        ->
    every process stopped
        ->
    a clean interpreter recovered R1 from SQLite alone
        ->
    prospectively frozen, externally seeded post-R1 quota-design challenge
    delivered
        ->
    R1-only path enabled a semantically different, causally supported quota R2
    under the predeclared budget
        ->
    exact R0, inverse patch, and surgical SeenSet intervention failed to reach
    R2 with trace-aligned excess work
        ->
    ledger reconstruction and Mechanism re-execution reproduced the
    recorded control-plane transition sequence

Genesis fails if any arrow is supplied by:

- A preloaded candidate.
- A preassembled high-level filter or quota constructor.
- A fixture-specific Python branch.
- A mutable evaluator.
- Candidate-authored metrics.
- A canned pre- or post-report approval policy keyed to an expected candidate.
- A host-selected target trace or topology signature.
- An unrecorded host mutation.
- A tentative active pointer.
- A test-only topology trick.
- A UI-only explanation.

That is the smallest executable Arxmentis worth building.
