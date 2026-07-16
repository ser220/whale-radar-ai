# PS-4 Step 7F — Immutable Evidence Preparation Boundary Specification

## Objective

Define the future immutable boundary that transforms approved, sanitized source
material into deterministic `RealityGapEvidenceReference` objects and explicit
rejection/duplicate audit records. Step 7F is documentation-only.

## Scope

This specification defines:

- preparation responsibilities and non-responsibilities;
- conceptual request/result/provenance/trace contracts;
- stable evidence identity material and ownership;
- binary eligibility decisions and reason taxonomy;
- invalid, ineligible, and duplicate handling;
- multi-source separation;
- anti-hindsight, failure, ordering, and version rules;
- acceptance criteria for a future implementation.

## Out of scope

- provider or exchange integrations;
- API, network, database, repository, cache, or external service access;
- automatic Timeline evidence extraction;
- evidence relevance, interpretation, correlation, or corroboration;
- Root Cause Candidate generation;
- Reality Gap classification or severity;
- Surprise, Knowledge Gap, Explanation Confidence, residual, or other metrics;
- persistence, learning, Outcome Analysis, Telegram, production decisions,
  deployment, or Hostinger changes;
- modifications to approved Reality Gap contracts;
- runtime implementation of the conceptual contracts in this specification.

## Normative terminology

`MUST`, `MUST NOT`, `SHOULD`, and `MAY` define requirements for a future
implementation. No runtime implementation is included in Step 7F.

## Domain principle

Evidence is a structured observation reference. It is not an explanation,
cause, interpretation, prediction, confidence statement, recommendation, or
trading signal. Preparation MUST preserve uncertainty and exact availability:
missing remains missing, unsupported remains unsupported, invalid remains
invalid, and measured zero remains distinct from absence.

## Conceptual `EvidencePreparationLayer`

The future layer MUST:

1. receive only approved sanitized source material;
2. validate source, artifact, timestamp, factor/artifact type, and identity
   material;
3. normalize supplied timezone-aware timestamps to UTC;
4. preserve versioned sanitized provenance;
5. apply the declared eligibility policy without interpretation;
6. create deterministic immutable evidence references when required contract
   fields are valid;
7. reject invalid or duplicate attempts explicitly;
8. return immutable deterministically ordered output and structured trace;
9. leave every input unchanged.

It MUST NOT connect to a provider, discover evidence, infer a missing value,
score relevance, explain an event, generate candidates, classify gaps,
calculate metrics/severity, correlate sources, learn, persist, notify, or
modify production decisions.

## Conceptual `EvidencePreparationRequest`

Required conceptual fields:

- `preparation_version`;
- `identity_policy_version`;
- `source_namespace`;
- `source_reference`;
- `artifact_reference`;
- `observed_at`;
- `received_at`;
- optional `factor_name`;
- `raw_value_reference`;
- immutable `source_metadata`;
- immutable `eligibility_context`;
- immutable `metadata`.

### Request rules

1. Version, source, and artifact references are non-empty and normalized by
   explicit policy.
2. `observed_at` and `received_at` are caller-supplied timezone-aware values and
   normalize to UTC. Preparation does not read the current clock.
3. `factor_name` is optional only for an explicitly supported non-factor
   evidence artifact type.
4. `raw_value_reference` is a sanitized primitive reference or canonical
   normalized value representation—not a raw provider payload.
5. Mappings and collections contain primitive serializable data only and are
   deeply immutable.
6. Credentials, tokens, headers, host/environment state, clients, sessions,
   callbacks, mutable domain artifacts, and raw payloads are forbidden.
7. Eligibility context contains the approved time/source/factor boundary only;
   it contains no outcome or learning facts.

## Conceptual `EvidencePreparationResult`

Fields:

- `prepared_evidence`: ordered immutable valid evidence references, including
  eligible and contract-valid ineligible references;
- `rejected_evidence`: ordered immutable sanitized rejection-attempt records;
- `duplicate_evidence`: ordered immutable duplicate-attempt records referencing
  their canonical evidence ID;
- `preparation_trace`;
- `preparation_version`;
- immutable `policy_versions`.

### Result rules

1. The result is immutable and primitive-serializable.
2. Prepared evidence ordering is deterministic under the preparation version.
3. Accepted, ineligible, rejected, and duplicate attempts remain auditable.
4. No input is mutated.
5. No analytical conclusion is added.
6. No malformed `RealityGapEvidenceReference` is constructed to preserve an
   invalid attempt.
7. Equal normalized input and versions produce equal output and canonical
   serialization.

## Conceptual `EvidenceProvenance`

Fields:

- `source_namespace`;
- `source_reference`;
- `artifact_reference`;
- optional `provider_version`;
- `schema_version`;
- `observed_at`;
- `received_at`;
- `extraction_method`;
- `preparation_version`;
- immutable primitive `metadata`.

Provenance MUST describe origin and transformation lineage only. It MUST NOT
claim reliability, relevance, confidence, causality, or explanatory strength.
`extraction_method` is a supplied versioned descriptor; it does not authorize
Step 7F to perform extraction. Timestamps are aware UTC. Secrets, raw payloads,
network state, environment values, and host identifiers are forbidden.

## Conceptual `EvidenceIdentityPolicy`

The preparation layer owns evidence identity. Identity material, in fixed
policy order, is:

1. `evidence_identity_policy_version`;
2. normalized source namespace;
3. normalized artifact reference;
4. Timeline ID/version/entry reference when applicable;
5. normalized factor name or explicit non-factor marker;
6. normalized UTC observed timestamp;
7. caller-approved evidence relation;
8. canonical normalized value or explicit availability/absence representation;
9. provenance/schema version material.

The policy MUST define unambiguous field boundaries, text normalization, value
normalization, and missing markers. It MUST reject ambiguous required material.
Same semantic material MUST produce the same identity. Identity MUST NOT depend
on UUID randomness, database sequence, host, environment, process, locale,
network, received/current time, or collection/hash order.

Step 7F selects no hash, digest, encoding, length, or collision implementation.
That choice requires separate review before runtime.

The relation is supplied by the approved context and preserved. Preparation
MUST NOT infer whether evidence supports an explanation.

## Eligibility contract

Use the existing binary domain decision:

- `ELIGIBLE`
- `INELIGIBLE`

Define conceptual `EvidenceEligibilityReason`:

- `VALID_SOURCE`
- `OUTSIDE_ALLOWED_WINDOW`
- `STALE`
- `UNSUPPORTED_FACTOR`
- `MISSING_TIMESTAMP`
- `INVALID_TIMESTAMP`
- `DUPLICATE`
- `INVALID_ARTIFACT`
- `PROVIDER_ERROR`
- `INCOMPLETE_METADATA`
- `UNKNOWN`

`VALID_SOURCE` is the successful eligibility reason. Other reasons explain why
the preparation attempt is ineligible or rejected. Eligibility means only:

> The evidence is allowed to participate in the approved analysis boundary.

It does not establish correctness, relevance, explanation, cause, confidence,
classification, or severity.

## Deterministic eligibility rules

An evidence reference is `ELIGIBLE` only when all are true:

1. source namespace/reference is known under the supplied policy;
2. artifact reference is valid;
3. observed timestamp is valid and timezone-aware;
4. factor is supported, or artifact type is explicitly supported as non-factor;
5. observation is inside the approved inclusive time boundary;
6. canonical identity is not already occupied in this preparation scope;
7. provenance contains the fields required by its schema version;
8. the reference satisfies the approved immutable evidence contract.

An ineligible or rejected attempt MUST have one explicit reason. Where all
required evidence fields remain valid, preparation SHOULD preserve an
`INELIGIBLE` evidence reference. Where a required field is absent/invalid,
preparation MUST retain a sanitized rejection record rather than invent a
value. No attempt is silently discarded.

Staleness is evaluated only from supplied timestamps and supplied approved
freshness policy. Provider error is a supplied source fact, not a network call
made by preparation. Unsupported is a capability fact, not market neutrality.

## Duplicate semantics

Two attempts are duplicates when their canonical evidence identity material is
identical under the same identity-policy version.

Rules:

1. They represent one evidence identity.
2. The canonical item is selected by declared deterministic input/order policy.
3. A duplicate does not create a second prepared evidence object with the same
   ID and does not contribute twice.
4. Duplicate attempts are not silently merged into or used to mutate the
   canonical item.
5. `duplicate_evidence` preserves sanitized attempt provenance, duplicate
   reason, and canonical evidence ID.
6. The decision is reproducible and independent of arrival races, process
   order, or mapping iteration.
7. Conflicting material that produces an identity collision but is not
   semantically identical is `IDENTITY_CONFLICT`, not `DUPLICATE`.

## Multi-source policy

Different sources remain different evidence references. Binance volume and OKX
volume are not merged even for the same asset/window/factor. Source namespace
and artifact provenance remain part of identity. Preparation performs no
averaging, voting, ranking, correlation, or corroboration.

Multiple-source corroboration is a future evidence-relationship concern outside
this boundary and is not duplicate handling.

## Conceptual rejection and duplicate audit records

A future `RejectedEvidenceAttempt` SHOULD contain preparation-attempt identity,
sanitized source/artifact references when valid, reason, failed validation
field, policy versions, supplied timestamps when valid, and primitive metadata.

A future `DuplicateEvidenceAttempt` SHOULD contain preparation-attempt identity,
canonical evidence ID, sanitized provenance, duplicate reason, input order
reference, and policy versions.

Neither record is a `RealityGapEvidenceReference`, participates in analysis, or
contains raw payloads. Both remain immutable and deterministic. Step 7F does
not implement these contracts.

## Conceptual `EvidencePreparationTrace`

Fields:

- `preparation_id`;
- `preparation_version`;
- `input_count`;
- `accepted_count`;
- `rejected_count`;
- `duplicate_count`;
- ordered `eligibility_decisions`;
- ordered `identity_decisions`;
- ordered warnings;
- caller-supplied UTC `created_at`.

Counts are non-negative and reconcile exactly with result groups. Decisions
reference preparation attempts and canonical evidence IDs. Ordering follows the
declared preparation policy. The trace contains concise structured facts only,
no private reasoning, market interpretation, cause, or hidden chain of thought.

## Deterministic ordering

The future preparation policy MUST define input order before duplicate
selection. Recommended output order:

- prepared evidence: canonical `evidence_id`;
- rejected attempts: stable preparation-attempt reference;
- duplicate attempts: canonical evidence ID, then stable attempt reference;
- trace identity/eligibility decisions: stable input order;
- warnings: fixed policy precedence, then lexical tie-break.

Ordering MUST NOT depend on set/hash iteration or concurrent arrival timing.

## Anti-hindsight requirements

1. Only approved source material may enter preparation.
2. Only the approved observation/evaluation window may be used.
3. Future Timeline entries and later versions are forbidden.
4. Future outcomes are forbidden.
5. Learning feedback and historical similarity matching are forbidden.
6. Preparation cannot mutate old evidence after analysis creation.
7. A later policy correction creates new immutable preparation output and, when
   consumed, a new analysis revision; it never rewrites history.

## Failure model

Use conceptual `EvidencePreparationFailure` categories:

- `INVALID_SOURCE`
- `INVALID_ARTIFACT`
- `INVALID_TIMESTAMP`
- `IDENTITY_CONFLICT`
- `POLICY_CONFLICT`
- `UNSUPPORTED_INPUT`
- `INTERNAL_VALIDATION_ERROR`

Failure MUST preserve category, concise reason, preparation stage, relevant
policy versions, and sanitized attempt reference. It MUST NOT silently create
partial valid evidence or alter previous evidence. A batch MAY retain other
independently valid prepared items only when the future batch policy explicitly
defines item-level rejection; otherwise the operation is atomic. This choice
must be fixed before runtime implementation.

## Version ownership

| Version | Owner/meaning |
|---|---|
| `evidence_identity_policy_version` | Canonical identity material/normalization |
| `eligibility_policy_version` | Eligibility rules and reason taxonomy |
| `provenance_schema_version` | Provenance fields and semantics |
| `preparation_version` | Request/result, ordering, duplicate, and trace behavior |

No version can silently change meaning. A changed policy requires a new version.
Old evidence retains its exact ID, eligibility decision, provenance, and policy
versions. Historical records remain readable.

## Acceptance criteria for a future implementation

1. Identical normalized source material and versions produce equal evidence ID,
   eligibility result, output ordering, trace, and canonical bytes.
2. No result depends on current time, UUID, database, host, environment,
   process, locale, network, provider call, or hash iteration.
3. Missing, unsupported, invalid, and measured zero remain distinct.
4. Invalid required fields are never fabricated.
5. Eligible decisions satisfy every declared rule.
6. Ineligible/rejected/duplicate decisions retain explicit reason and sanitized
   auditability.
7. Duplicate identity contributes at most one prepared evidence reference.
8. Different sources remain distinct.
9. Inputs and prior evidence remain unchanged.
10. No analytical, candidate, classification, metric, persistence, learning,
    production, Telegram, or Outcome dependency exists.

## Alternatives

- Assembler-created evidence: rejected because preparation and construction
  become coupled.
- Provider-created domain evidence: rejected because provider assumptions leak
  into stable contracts.
- Raw provider payload evidence: rejected for security, privacy,
  reproducibility, mutability, and dependency reasons.
- Dedicated preparation boundary: selected.

## Future phases

- Step 7G defines Candidate generation.
- Step 7H defines classification and metrics.
- Step 7I defines Memory/Learning consumption.

Step 7F does not implement or authorize those phases.

## Verification for Step 7F

```bash
git diff --check
git diff --stat
git diff --name-status
git status --short
```

Only the Step 7F ADR, this specification, and report may be added. No runtime,
provider, approved Reality Gap contract, dependency, production, Telegram,
Hostinger, persistence, learning, or Outcome Analysis file may change.
