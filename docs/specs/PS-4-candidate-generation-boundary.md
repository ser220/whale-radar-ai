# PS-4 Step 7G — Immutable Candidate Generation Boundary Specification

## Objective

Define the future immutable boundary that creates evidence-referenced candidate
hypotheses without asserting causal truth, classifying Reality Gaps, ranking
candidates, or calculating confidence/metrics. Step 7G is documentation-only.

## Scope

This specification defines:

- candidate ownership and non-responsibilities;
- deterministic candidate identity material;
- conceptual `CandidateHypothesis` fields and lifecycle;
- supporting, contradicting, and limitation reference semantics;
- immutable candidate version lineage;
- relationship to the future Root Cause Tree/Explanation layer;
- structured trace, anti-hindsight, and failure policies;
- compatibility requirements for existing approved assembly contracts.

## Out of scope

- candidate discovery or generation algorithms;
- automatic root-cause detection or causal inference;
- evidence extraction, preparation, creation, mutation, or eligibility changes;
- Reality Gap classification, dimensions, severity, or final explanation;
- candidate relevance, confidence, score, rank, weighting, or metric calculation;
- Root Cause Tree construction;
- provider, exchange, API, database, repository, cache, or network access;
- persistence, learning, historical similarity, Outcome Analysis, Telegram,
  production decisions, deployment, or Hostinger changes;
- runtime contracts or modifications to approved Reality Gap contracts.

## Normative terminology

`MUST`, `MUST NOT`, `SHOULD`, and `MAY` define requirements for a future
implementation. No runtime implementation is included in Step 7G.

## Domain principle

A Candidate is an evidence-referenced hypothesis that may explain part of a
Reality Gap. It is never represented as a proven cause, market truth,
explanation certainty, prediction, trading signal, or learning conclusion.

## Conceptual Candidate Layer

The future Candidate Layer MUST:

1. receive an approved immutable evidence catalog and already-prepared
   hypothesis material;
2. validate candidate namespace, category, subject, hypothesis reference,
   identity-policy version, and evidence references;
3. create/validate deterministic candidate identity;
4. require eligible support that existed inside the approved boundary before
   candidate creation;
5. preserve contradiction and limitation references without reinterpretation;
6. create one immutable candidate version per successful request;
7. preserve previous versions and inputs unchanged;
8. expose stable candidate identity to a future explanation layer;
9. emit structured deterministic validation/audit facts.

It MUST NOT discover evidence or hypotheses as an implicit side effect, infer
causes, classify gaps, rank candidates, calculate confidence/metrics/severity,
build a tree, learn, persist, notify, or affect production decisions.

Step 7G defines the boundary only. A future generator algorithm requires a
separate reviewed task.

## Candidate ownership

The Candidate Layer owns `candidate_id` and candidate-version lineage. It does
not own evidence IDs, gap/trace IDs, tree IDs, final dispositions, or
`RealityGapAnalysis` construction.

`candidate_id` identifies one immutable hypothesis lineage. It does not identify
a market event, Timeline, Reality Gap lineage, final explanation, tree
position, recommendation, trade, or outcome.

## Candidate identity policy

Conceptual identity material, in fixed order:

1. candidate identity-policy version;
2. candidate namespace;
3. normalized category;
4. normalized subject;
5. normalized stable hypothesis reference;
6. canonical ordered identity-bearing supporting evidence IDs.

The future policy MUST define field boundaries, text normalization, evidence-ID
ordering, missing markers, and namespace semantics. Supporting IDs in identity
material are sorted canonically and duplicate-free; caller collection/hash order
cannot affect identity.

Identical semantic material under the same policy version MUST produce the same
candidate ID. An identity-bearing field change MUST produce a different ID.
Identity MUST be independent of process, host, environment, database sequence,
random UUID, current time, locale, network, and mutable state.

Step 7G selects no digest, encoding, ID length, or collision implementation.

## Conceptual `CandidateHypothesis`

Fields:

- `candidate_id`;
- positive `candidate_version`;
- `candidate_identity_policy_version`;
- `candidate_policy_version`;
- category;
- normalized subject;
- stable `hypothesis_reference`;
- concise description;
- `CandidateStatus`;
- ordered unique `supporting_evidence_refs`;
- ordered unique `contradicting_evidence_refs`;
- ordered unique `limitation_references`;
- caller-supplied aware UTC `created_at`;
- deeply immutable primitive metadata.

### Contract rules

1. IDs, namespace/policy versions, category, subject, and hypothesis reference
   are required.
2. Version is an integer >= 1; booleans are invalid.
3. Timestamps are caller-supplied and normalize to UTC. No current clock is
   read implicitly.
4. Collections are immutable, deterministic, and duplicate-free.
5. Supporting and contradicting evidence sets are disjoint.
6. Metadata is primitive, deeply immutable, and contains no secrets, payloads,
   clients, mutable artifacts, host, or environment data.
7. Serialization is primitive, deterministic, versioned, and round-trippable.
8. No cause, truth, confidence, score, rank, direction, trade, execution,
   outcome, or learning field is permitted.

## `CandidateStatus`

Initial lifecycle values:

- `CREATED`: valid identity and evidence references exist;
- `SUPPORTED`: eligible evidence is consistent with continued consideration;
- `CHALLENGED`: contradicting evidence exists;
- `REJECTED`: hypothesis is no longer considered valid inside this immutable
  analysis boundary;
- `UNRESOLVED`: available evidence is insufficient for a stronger status.

Status is a declared lifecycle fact, not a truth value or probability.

### Initial transition policy

- version 1 begins as `CREATED`, or as another status only when the prepared
  request explicitly carries the validated transition basis;
- `CREATED` may produce a later `SUPPORTED`, `CHALLENGED`, `UNRESOLVED`, or
  `REJECTED` version;
- `SUPPORTED` may later be `CHALLENGED`, `UNRESOLVED`, or `REJECTED` within the
  same approved boundary;
- `CHALLENGED` may later be `SUPPORTED`, `UNRESOLVED`, or `REJECTED` when new
  approved contradiction/status facts are supplied;
- `UNRESOLVED` may later be `SUPPORTED`, `CHALLENGED`, or `REJECTED`;
- `REJECTED` is terminal for that candidate lineage inside the current analysis
  boundary.

Every transition creates the next immutable version and preserves the prior
record. No automatic transition logic is authorized by Step 7G.

## Status versus `RootCauseDisposition`

`CandidateStatus` belongs to a candidate hypothesis lineage.
`RootCauseDisposition` belongs to one analysis/explanation projection. They are
not equivalent:

- `SUPPORTED` does not automatically mean `ACCEPTED`;
- `CHALLENGED` does not automatically mean `REJECTED`;
- `UNRESOLVED` status does not authorize an automatic analysis disposition;
- disposition requires a future reviewed explanation policy.

Step 7G defines no mapping or classification algorithm.

## Conceptual `CandidateEvidencePolicy`

### Supporting references

- MUST resolve in the approved evidence catalog;
- MUST be `ELIGIBLE` without changing eligibility;
- MUST have existed within the approved evaluation/analysis boundary before the
  candidate creation timestamp;
- MUST be ordered uniquely and contain at least one item;
- MUST NOT be fabricated or inferred from missing data.

### Contradicting references

- MUST resolve and remain unique;
- MAY be eligible or ineligible;
- MUST preserve exact eligibility and rejection/availability facts;
- MUST be disjoint from supporting refs;
- MUST NOT be treated as proof that the hypothesis is impossible.

### Limitation references

- MAY reference missing/unavailable evidence facts, observability gaps,
  sanitized rejected/duplicate preparation attempts, or unresolved questions;
- MUST use stable primitive references;
- MUST NOT invent evidence IDs, values, provider facts, or hidden observations;
- SHOULD be present when status is `UNRESOLVED` or when support is materially
  constrained.

## Support and contradiction semantics

Supporting evidence means only that its recorded facts are consistent with the
hypothesis under the declared candidate policy. It does not prove cause,
relevance magnitude, confidence, rank, or final explanation.

Contradicting evidence means only that its recorded facts are inconsistent with
the hypothesis. It does not prove impossibility. The Candidate Layer records
the declared relationship; it does not evaluate final truth.

## Candidate versioning

`candidate_id` is stable while all identity material is stable.
`candidate_version` is the immutable revision number.

Any allowed non-identity change—status transition, description clarification,
additional contradiction, or limitation—MUST create exactly the next version.
Old versions and evidence references remain unchanged and readable.

An identity-bearing change—namespace, category, subject, hypothesis reference,
or identity-bearing supporting evidence basis—MUST create a new candidate ID at
version 1. Until a later reviewed identity policy says otherwise, adding or
removing identity-bearing support is a new candidate lineage. No record is
edited in place.

## Root Cause Tree relationship

The Candidate Layer creates tree-agnostic hypotheses. The future Explanation
Layer creates `RootCauseTree`; it references candidate IDs and owns roots,
edges, parent/child structure, and analysis-specific disposition. It MUST NOT
mutate a `CandidateHypothesis`. One hypothesis MAY be referenced by multiple
immutable tree structures.

### Approved-contract compatibility constraint

The existing approved assembly `RootCauseCandidate` contains role,
disposition, confidence-related fields, and parent/child linkage, while the
conceptual `CandidateHypothesis` contains candidate version/status and no tree
position. They are separate architectural records.

Before runtime Candidate generation, a separately reviewed mapping must define
how immutable hypothesis identity/version and explanation-layer decisions
produce the assembly projection. That projection may include tree linkage for
existing validator compatibility, but it MUST NOT mutate the source hypothesis.
No such mapper or contract change is implemented or authorized in Step 7G.

## Conceptual `CandidateGenerationTrace`

Fields:

- `generation_id`;
- generation/candidate policy versions;
- candidate identity-policy version;
- input evidence-reference count;
- candidate count;
- ordered validation results;
- ordered warnings;
- caller-supplied aware UTC start/creation timestamps;
- optional structured failure category/reason.

Counts are non-negative and reconcile with output. Ordering follows the
candidate policy. Trace facts are structured and concise; no private reasoning,
chain of thought, causal narrative, confidence calculation, rank, or hidden
interpretation is allowed.

## Deterministic ordering

Recommended future policy:

- identity-bearing supporting evidence IDs: lexical canonical ID order;
- contradiction IDs: lexical canonical ID order;
- limitations: stable reference type, then reference ID;
- candidates in one generation result: `candidate_id`;
- validation results: stable input order;
- warnings: fixed policy precedence, then lexical tie-break.

Caller semantic description text is preserved after documented normalization.
Ordering cannot depend on set/hash iteration, arrival race, or provider order.

## Anti-hindsight requirements

1. Candidate creation sees only approved evidence references.
2. Supporting eligibility is preserved and cannot be upgraded.
3. Future evidence and later Timeline entries/versions are forbidden.
4. Outcome information is forbidden.
5. Learning feedback and historical similarity matching are forbidden.
6. Completed candidate versions are immutable.
7. A later version cannot expand the evidence boundary of the owning historical
   analysis.

## Failure model

Use conceptual `CandidatePreparationFailure`:

- `INVALID_EVIDENCE_REFERENCE`
- `INELIGIBLE_SUPPORTING_EVIDENCE`
- `DUPLICATE_IDENTITY`
- `POLICY_VERSION_CONFLICT`
- `INVALID_HYPOTHESIS_REFERENCE`
- `INVALID_METADATA`

Failure MUST preserve category, concise reason, generation stage, candidate and
identity-policy versions, and sanitized attempt reference. It MUST create no
partial candidate, repair no reference, upgrade no eligibility, and mutate no
existing candidate/version. A failed attempt MAY emit only an immutable audit
trace.

## Acceptance criteria for a future implementation

1. Identical normalized identity material produces identical candidate ID.
2. Identity-bearing changes produce a new ID; allowed state changes produce
   exactly the next immutable version.
3. No ID or output depends on current time, UUID, database, process, host,
   environment, locale, network, or hash order.
4. Every supporting ref resolves and is eligible.
5. Contradiction eligibility remains unchanged and visible.
6. Missing/unavailable input is preserved as a limitation, not fabricated.
7. No candidate field or trace asserts causal truth, confidence, rank,
   classification, metric, direction, trade, outcome, or learning conclusion.
8. Candidate hypotheses are tree-agnostic and unchanged by explanation.
9. Inputs and prior candidate versions remain unchanged.
10. No provider, persistence, Telegram, production, learning, or Outcome
    dependency exists.

## Alternatives

- Assembler-owned generation: rejected because hypothesis and aggregate
  construction mix.
- Tree-owned generation: rejected because hypothesis lifecycle couples to one
  explanation structure.
- Provider-generated causes: rejected because provider assumptions bypass the
  evidence/intelligence boundary.
- Dedicated Candidate Boundary: selected.

## Future phases

- Step 7H defines Reality Gap classification and metrics.
- Step 7I defines Learning and Memory consumption.

Future candidate algorithms require a separate reviewed task after the
hypothesis-to-assembly mapping is approved. Step 7G does not implement or
authorize those phases.

## Verification for Step 7G

```bash
git diff --check
git diff --stat
git diff --name-status
git status --short
```

Only the Step 7G ADR, this specification, and report may be added. No runtime
candidate generator, algorithm, approved Reality Gap contract, classification,
metric, persistence, learning, production, Telegram, Hostinger, or Outcome
Analysis file may change.
