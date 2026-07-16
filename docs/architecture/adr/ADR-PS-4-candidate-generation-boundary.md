# ADR: PS-4 Immutable Candidate Generation Boundary

## Status

Proposed; awaiting Architecture Review.

## Context

PS-4 Step 7F defined immutable evidence preparation: source material becomes
auditable evidence references whose identity, provenance, availability, and
eligibility are preserved. The next architectural boundary must describe how a
future system may represent possible explanations without turning evidence into
causal truth or coupling hypotheses to the Root Cause Tree.

The approved Reality Gap contracts already include `RootCauseCandidate` and
`RootCauseTree` assembly records. Step 7G does not modify those contracts or
implement a generator. It defines the upstream immutable hypothesis lifecycle,
identity, evidence rules, and separation from the explanation structure.

A Candidate is:

> An evidence-referenced hypothesis that may explain part of a Reality Gap.

It is not a proven cause, market truth, certainty, prediction, trading signal,
or learning conclusion.

## Decision

Adopt a dedicated future Candidate Layer between prepared evidence and the
future Explanation/Root Cause Tree layer:

```text
Evidence Preparation
        |
        v
Immutable Evidence References
        |
        v
Candidate Boundary
        |
        v
Immutable Candidate Hypotheses
        |
        v
Future Explanation / Root Cause Tree Layer
```

The Candidate Layer owns deterministic candidate identity and immutable
hypothesis revisions. It receives an approved evidence catalog and prepared
hypothesis material, validates references, preserves support/contradiction and
limitations, and exposes immutable candidates. Step 7G defines no algorithm for
discovering or generating hypotheses.

## Candidate ownership

The future layer is responsible for:

- receiving approved immutable evidence references;
- validating candidate identity material and policy versions;
- creating one immutable hypothesis record from already-prepared candidate
  material;
- requiring eligible supporting evidence;
- preserving contradicting evidence and limitations without reinterpretation;
- enforcing append-only candidate lifecycle/version rules;
- exposing stable candidate references to the future explanation layer;
- producing structured deterministic validation/audit facts.

It does not extract or create evidence, discover causes, classify Reality Gaps,
rank candidates, calculate confidence/metrics/severity, decide final truth,
build a Root Cause Tree, learn, persist, notify, or affect production decisions.

## Candidate identity ownership

The Candidate Layer owns `candidate_id`. It identifies one immutable hypothesis
lineage—not a market event, Reality Gap lineage, final explanation, tree
position, trade, or outcome.

Candidate identity must be deterministic, reproducible, version-aware, and
independent of runtime process, host, environment, database, random UUID,
current time, locale, network, and collection/hash order.

Conceptual fixed-order identity material is:

1. candidate identity-policy version;
2. candidate namespace;
3. category;
4. normalized subject;
5. normalized hypothesis reference;
6. canonical ordered identity-bearing supporting evidence references.

The same normalized semantic hypothesis and identity-bearing support basis
produces the same candidate ID. A changed category, subject, hypothesis
reference, namespace, or identity-bearing support basis creates a different
candidate lineage.

Step 7G selects no digest, encoding, ID length, or collision implementation.

## Conceptual `CandidateHypothesis`

Define a future immutable record containing:

- `candidate_id`;
- `candidate_version` and candidate-policy version;
- category and normalized subject;
- stable hypothesis reference and concise description;
- `CandidateStatus`;
- ordered supporting and contradicting evidence refs;
- ordered limitation references;
- caller-supplied UTC creation timestamp;
- deeply immutable primitive metadata.

The record is primitive-serializable, deterministically ordered, and contains
no mutable collection, raw evidence object, provider payload, hidden reasoning,
confidence calculation, rank, final explanation, direction, trade, or outcome.

## Candidate status decision

Use the future lifecycle `CandidateStatus`:

- `CREATED`: a valid immutable hypothesis exists and its references resolve;
- `SUPPORTED`: eligible evidence is consistent with continued consideration;
- `CHALLENGED`: contradicting evidence is present;
- `REJECTED`: the hypothesis is no longer considered valid inside the current
  immutable analysis boundary;
- `UNRESOLVED`: available evidence is insufficient for a stronger status.

Status describes lifecycle/audit state only. It is not truth probability.
`SUPPORTED` does not prove the hypothesis, `CHALLENGED` does not make it
impossible, and `REJECTED` does not rewrite historical versions.

`CandidateStatus` is distinct from approved `RootCauseDisposition`.
Disposition belongs to a specific Reality Gap analysis/explanation projection;
status belongs to the candidate hypothesis lineage. No automatic mapping is
authorized by Step 7G—for example, `SUPPORTED` must not silently become
`ACCEPTED`.

## Evidence policy

Supporting references must resolve to existing evidence, must be `ELIGIBLE`,
must predate candidate creation inside the approved boundary, and must be
unique. A candidate requires at least one eligible supporting reference.

Contradicting references must resolve and remain unique/disjoint from support.
They may be eligible or ineligible, but their eligibility remains visible and
cannot be upgraded. Ineligible contradiction may limit interpretation but is
not silently treated as measured truth.

Limitations preserve stable references to missing/unavailable evidence facts,
observability gaps, rejected preparation attempts, or unresolved questions.
They cannot fabricate an evidence ID or hidden value.

The Candidate Layer stores declared relationships only. “Supports” means
consistent with the hypothesis, not proof. “Contradicts” means inconsistent
with the hypothesis, not impossibility. Relevance, rank, confidence, and final
truth are outside this boundary.

## Candidate versioning

`candidate_id` identifies a stable hypothesis lineage.
`candidate_version` identifies one immutable revision of that lineage.

Any allowed change to non-identity state—status, description clarification,
new contradiction, or new limitation—creates exactly the next candidate
version. Previous versions and their evidence refs remain readable and
unchanged.

An identity-bearing change—category, subject, hypothesis reference, namespace,
or identity-bearing supporting evidence basis—creates a new `candidate_id`
rather than rewriting the old hypothesis. A future policy must state whether
additional supporting evidence extends the fixed basis or begins a new lineage;
until resolved, the conservative rule is a new identity.

No version is edited in place. Current time is not used implicitly; timestamps
are supplied as part of the approved boundary and do not define identity.

## Relationship with Root Cause Tree

The Candidate Layer creates tree-agnostic `CandidateHypothesis` records. The
future Explanation Layer creates immutable `RootCauseTree` structures that
reference candidate IDs. A candidate does not own its final parent, children,
root role, or tree position. A tree cannot mutate a hypothesis, and one
hypothesis may appear in different immutable explanatory structures.

### Compatibility with approved assembly contracts

The current approved `RootCauseCandidate` is an analysis/assembly projection:
it includes role, disposition, confidence fields, and parent/child linkage, but
does not include the conceptual candidate version/status fields defined here.
The conceptual `CandidateHypothesis` therefore must not be treated as the same
runtime object.

A future reviewed mapping boundary must project an immutable hypothesis plus
future explanation decisions into the existing assembly record without
mutating the hypothesis. Parent/child linkage in that projection must agree
with `RootCauseTree` validation. Step 7G neither defines nor implements this
mapping and does not modify approved contracts. Runtime Candidate generation is
blocked until that compatibility decision is reviewed.

## Candidate trace

Use a future immutable `CandidateGenerationTrace` containing generation ID,
candidate policy/version, input evidence-reference count, candidate count,
ordered validation results, ordered warnings, and caller-supplied UTC
timestamps.

The trace records structured facts only. It contains no chain of thought,
hidden reasoning, causal narrative, ranking, confidence calculation, or market
interpretation. It cannot create candidate content missing from its input.

## Anti-hindsight decision

Candidate creation may use only approved evidence references, their existing
eligibility, and the approved analysis/evaluation boundary. Future evidence,
outcomes, later Timeline entries/versions, learning feedback, and historical
similarity matching are forbidden. Candidate versions used by a completed
analysis remain immutable.

## Failure model

Use future `CandidatePreparationFailure` categories:

- `INVALID_EVIDENCE_REFERENCE`
- `INELIGIBLE_SUPPORTING_EVIDENCE`
- `DUPLICATE_IDENTITY`
- `POLICY_VERSION_CONFLICT`
- `INVALID_HYPOTHESIS_REFERENCE`
- `INVALID_METADATA`

Failure preserves a concise structured reason, policy versions, and attempt
reference. It creates no partial candidate, never repairs or upgrades evidence,
and cannot mutate an existing candidate/version. A failed attempt may emit only
an immutable audit trace.

## Alternatives considered

### A. Generate candidates inside the assembler

Rejected. Hypothesis identity and lifecycle would mix with aggregate
construction, violating the approved pure assembly boundary.

### B. Generate candidates inside `RootCauseTree`

Rejected. Hypothesis lifecycle would become coupled to one explanatory
structure and prevent reuse across different trees.

### C. Let providers generate causes

Rejected. Provider assumptions and source-specific causal narratives would
leak into the intelligence domain and bypass evidence eligibility.

### D. Dedicated Candidate Boundary

Accepted. It isolates hypothesis identity/lifecycle and evidence relationships
while keeping classification, ranking, explanation, and tree ownership outside.

## Consequences

### Positive

- candidate hypotheses remain explicitly non-causal and auditable;
- stable identity and append-only versions support historical comparison;
- eligible support and contradictory/limitation facts remain distinguishable;
- the same hypothesis can be referenced by multiple explanation structures;
- providers, assembly, tree construction, and candidate lifecycle remain
  independently testable boundaries;
- no runtime, persistence, or external dependency is required by the design.

### Negative and trade-offs

- candidate identity changes conservatively when identity-bearing support
  changes until a later policy decides otherwise;
- a future mapping is required between `CandidateHypothesis` and the approved
  assembly `RootCauseCandidate` projection;
- status-to-disposition semantics require a separate explanation policy;
- no useful candidates appear until a separately reviewed generator exists.

## Future phase boundary

- Step 7H: Reality Gap classification and metrics;
- Step 7I: Memory/Learning consumption.

A future Candidate Generator may implement algorithms only after this boundary
and the assembly-projection compatibility are separately reviewed. Step 7G
does not implement or authorize those phases.
