# ADR: PS-4 Immutable Evidence Preparation Boundary

## Status

Proposed; awaiting Architecture Review.

## Context

PS-4 Step 7E separated Reality Gap creation into Preparation, Orchestration,
and Assembly. The approved assembler consumes already-prepared immutable
`RealityGapEvidenceReference` objects, but it does not define how approved
source material becomes those references.

Without a dedicated preparation boundary, providers could leak mutable payloads
and source-specific assumptions into domain contracts, the assembler could gain
extraction responsibilities, missing data could become an invented zero, or
evidence identity and eligibility could vary by process, host, or database.

Evidence Preparation must answer only:

> What information is available, where did it come from, and is it eligible
> inside the approved analysis boundary?

It must not answer why an event happened. Evidence is a structured observation
reference—not an explanation, cause, interpretation, prediction, confidence,
or trading signal.

## Decision

Adopt a dedicated future conceptual `EvidencePreparationLayer` between approved
source material and immutable Reality Gap evidence references:

```text
Approved external/internal source material
                    |
                    v
       Evidence Preparation Boundary
                    |
                    v
       RealityGapEvidenceReference
                    |
                    v
          Reality Gap Orchestration
```

The layer validates supplied identity material, normalizes supplied timestamps
to UTC, preserves sanitized provenance, makes a deterministic eligibility
decision under an explicit policy, rejects invalid/duplicate material, and
produces immutable deterministic preparation output.

It does not connect to providers or discover source material. It receives only
material already admitted by a future upstream adapter boundary.

## Core evidence semantics

Evidence Preparation preserves source facts and uncertainty:

- missing information remains missing;
- unsupported information remains unsupported;
- invalid information remains invalid;
- measured zero remains distinct from no measurement;
- ineligible evidence remains visible for audit where a valid reference can be
  constructed;
- no unavailable value is inferred or silently defaulted.

Eligibility means only that a reference may participate in the approved
analysis boundary. It does not establish relevance, explanatory value, truth,
cause, confidence, classification, or severity.

## Responsibilities

The future layer is responsible for:

- receiving approved sanitized source material;
- validating evidence identity material;
- normalizing caller-supplied aware timestamps to UTC;
- preserving source and schema provenance;
- applying deterministic eligibility rules;
- creating immutable evidence references when their required contract material
  is valid;
- rejecting invalid or duplicate material without silent loss;
- returning deterministic preparation output and a structured audit trace.

It is explicitly not responsible for relevance scoring, explanation, causal
claims, candidate generation, Reality Gap classification, metrics, severity,
learning, persistence, provider access, correlation, notifications, or
production decisions.

## Conceptual preparation contracts

### `EvidencePreparationRequest`

Contains preparation and identity-policy versions, source namespace/reference,
artifact reference, caller-supplied observation and receipt timestamps,
optional factor name, a sanitized primitive value reference, source metadata,
eligibility context, and primitive metadata.

It contains no raw provider payload, credentials, headers, live clients,
mutable objects, database session, environment data, or host state. Factor name
may be absent only for an explicitly supported non-factor artifact type.

### `EvidencePreparationResult`

Contains immutable ordered prepared evidence, rejected material records,
duplicate-attempt records, a preparation trace, preparation version, and policy
versions. Accepted, ineligible, rejected, and duplicate facts remain auditable.
Inputs are never mutated.

Material that cannot satisfy required `RealityGapEvidenceReference` fields—for
example a missing/invalid timestamp—must not be repaired with fabricated data.
It is retained as a sanitized rejection record referencing the source attempt,
not as a malformed evidence reference.

## Provenance decision

Use a future immutable conceptual `EvidenceProvenance` record with source
namespace/reference, artifact reference, provider/schema versions, supplied
observed/received timestamps, extraction-method descriptor, preparation
version, and primitive metadata.

Provenance describes origin and transformation lineage. It is not a reliability
conclusion. `extraction_method` is a supplied versioned descriptor; Step 7F
does not implement extraction. Secrets, raw payloads, network state, environment
data, and host identity are forbidden.

## Evidence identity decision

The preparation layer owns `evidence_id` under a versioned conceptual
`EvidenceIdentityPolicy`. Fixed-order identity material is:

1. evidence identity-policy version;
2. source namespace;
3. artifact reference;
4. Timeline reference when applicable;
5. normalized factor name when applicable;
6. normalized UTC observation timestamp;
7. caller-approved evidence relation;
8. canonical normalized value representation or explicit absence state;
9. provenance/schema version material.

The same normalized semantic evidence produces the same identity. The identity
is independent of random UUID, database state, process, host, environment,
network, locale, receipt/current time, and collection order.

Step 7F specifies identity material and ownership only. It chooses no hash,
encoding, digest length, or collision implementation.

The relation included in identity material is supplied by the approved
preparation context. Preparation preserves it and does not infer explanatory
relevance.

## Eligibility decision

Use the existing domain decision values `ELIGIBLE` and `INELIGIBLE`. Define a
future reason taxonomy:

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

An eligible reference requires a valid artifact, timestamp, known source,
supported factor/artifact type, inclusion inside the approved time boundary,
unique identity, and provenance sufficient for audit.

An ineligible decision requires an explicit reason and retains a valid evidence
reference where possible. Invalid material that cannot form a valid evidence
contract remains a separate rejection record. No item is silently discarded.

## Duplicate semantics

Two preparation attempts with identical canonical evidence identity material
represent one evidence identity plus a `DUPLICATE` attempt—not two independent
evidence items.

The first deterministic canonical item occupies the identity. Later equivalent
attempts are not merged into it, do not become eligible again, and do not create
a second `RealityGapEvidenceReference` with the same `evidence_id`.
`duplicate_evidence` retains sanitized attempt provenance and the canonical
evidence ID it duplicated. Original and duplicate attempts remain traceable.

Selection of the canonical first item must use approved input order or an
explicit deterministic order declared by policy. Arrival races and hash-map
iteration cannot decide it.

Corroboration is different from duplication. Equivalent facts from distinct
sources retain distinct source material and identities and may later be related
by a correlation/corroboration layer.

## Multi-source decision

Evidence from Binance and OKX remains two evidence references even when both
describe volume for the same asset and timestamp. Preparation does not merge,
average, vote, correlate, or rank sources. Future corroboration belongs outside
Evidence Preparation.

## Preparation trace

Use a future immutable `EvidencePreparationTrace` containing preparation ID and
version, input/accepted/rejected/duplicate counts, ordered eligibility and
identity decisions, warnings, and a caller-supplied UTC creation timestamp.

The trace contains structured facts only, deterministic ordering, and no hidden
reasoning. It does not use the current clock implicitly and does not contain
market interpretation or causal explanation.

## Anti-hindsight decision

Preparation may use only approved source material, the approved observation
window, and approved artifact references. It cannot access future Timeline
entries, future outcomes, learning feedback, historical similarity matching,
or later corrections when constructing an earlier evidence record. Evidence
used by a completed analysis is immutable; corrections create new artifacts or
analysis revisions without rewriting history.

## Failure model

Use future categories:

- `INVALID_SOURCE`
- `INVALID_ARTIFACT`
- `INVALID_TIMESTAMP`
- `IDENTITY_CONFLICT`
- `POLICY_CONFLICT`
- `UNSUPPORTED_INPUT`
- `INTERNAL_VALIDATION_ERROR`

Failure preserves a structured category and concise reason. It creates no
partial valid evidence silently, never mutates previous evidence, and may
produce only an immutable sanitized audit record for the failed attempt.

## Version ownership

The preparation boundary declares:

- `evidence_identity_policy_version` for canonical evidence identity meaning;
- `eligibility_policy_version` for eligibility rules/reason taxonomy;
- `provenance_schema_version` for origin metadata meaning;
- `preparation_version` for preparation contract/ordering behavior.

Version meaning cannot change silently. A changed preparation policy uses a new
version. Existing evidence and its historical policy interpretations remain
immutable and readable.

## Alternatives considered

### A. Let the assembler create evidence

Rejected. This mixes source preparation and identity with aggregate
construction and violates the approved assembler boundary.

### B. Let providers directly create domain evidence references

Rejected. Provider schemas, availability semantics, mutable payloads, and
source-specific assumptions would leak into stable domain contracts.

### C. Store raw provider payloads as evidence

Rejected. Raw payloads introduce privacy/security exposure, unstable schemas,
large mutable artifacts, poor reproducibility, and provider dependencies.

### D. Dedicated Evidence Preparation boundary

Accepted. It provides one deterministic normalization, identity, provenance,
eligibility, duplicate, and audit boundary while keeping analysis semantics
outside.

## Consequences

### Positive

- uncertainty and unavailable states remain explicit;
- provider assumptions stay outside Reality Gap contracts;
- evidence identity and duplicate behavior become reproducible;
- eligible and ineligible material remains auditable;
- preparation can be tested independently from orchestration and assembly;
- no persistence or external-service dependency is required.

### Negative and trade-offs

- future adapters must sanitize and version source material before preparation;
- invalid material needs a separate rejection contract because required
  evidence fields cannot be fabricated;
- canonical input ordering and identity encoding still require later review;
- corroboration must be handled by a separate future relationship layer.

## Future phase boundary

- Step 7G: Root Cause Candidate generation;
- Step 7H: Reality Gap classification and metrics;
- Step 7I: Memory/Learning consumption.

Step 7F does not implement or authorize these phases.
