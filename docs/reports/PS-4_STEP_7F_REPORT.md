# PS-4 Step 7F Report — Immutable Evidence Preparation Boundary

## Summary

Step 7F defines the documentation-only boundary that will turn approved,
sanitized source material into immutable evidence references and explicit
rejection/duplicate audit records. It preserves provenance, availability,
eligibility, uncertainty, identity, deterministic ordering, and anti-hindsight
without interpreting what evidence means.

## Evidence preparation boundary

```text
Approved Source Material
          |
          v
Evidence Preparation Boundary
          |
          v
RealityGapEvidenceReference
          |
          v
Reality Gap Orchestration and Assembly
```

Preparation receives material already admitted by an upstream source boundary;
it performs no provider or Timeline extraction.

## Responsibilities

The future layer validates source/artifact/identity material, normalizes
supplied aware timestamps to UTC, preserves sanitized provenance, applies an
explicit eligibility policy, creates immutable contract-valid evidence,
rejects invalid/duplicate attempts, and produces deterministic output/trace.

It does not score relevance, explain causes, generate candidates, classify
gaps, calculate metrics or severity, correlate sources, learn, persist, notify,
or change production decisions.

## Evidence provenance

The conceptual immutable provenance record contains source namespace/reference,
artifact reference, provider/schema versions, supplied observed/received
timestamps, extraction-method descriptor, preparation version, and primitive
metadata. It describes origin—not reliability. Raw payloads, secrets, clients,
network/environment state, and host identity are forbidden.

## Evidence identity policy

Preparation owns evidence identity. Versioned fixed-order identity material
includes source/artifact/Timeline reference, factor/non-factor marker, observed
time, supplied relation, normalized value/absence state, and provenance/schema
versions. Identity is independent of UUID, database, process, host, environment,
network, locale, receipt/current time, and collection order.

No digest, encoding, ID length, or collision implementation is selected in
Step 7F.

## Eligibility policy

The existing binary `ELIGIBLE`/`INELIGIBLE` decision is retained. The conceptual
reason taxonomy distinguishes valid source, outside window, stale, unsupported,
missing/invalid timestamp, duplicate, invalid artifact, provider error,
incomplete metadata, and unknown.

Eligibility means only that evidence may participate in the approved analysis
boundary. It does not mean that evidence is relevant, explanatory, causal,
correct, confident, or directional.

## Invalid and duplicate handling

Contract-valid ineligible evidence is preserved as an ineligible reference with
an explicit reason. Material missing a required contract field is not repaired
or fabricated; it is retained as a sanitized rejection-attempt record.

Identical canonical identity material represents one evidence identity.
Duplicates remain traceable as duplicate-attempt records referencing the
canonical evidence ID, do not become eligible twice, and are not silently
merged into the canonical item.

## Multi-source policy

Different sources remain separate evidence references. Binance and OKX evidence
is not merged, averaged, voted, ranked, or correlated in preparation.
Corroboration is a future evidence-relationship concern outside this boundary.

## Evidence trace

The conceptual trace records preparation/version identity, counts, ordered
eligibility and identity decisions, deterministic warnings, and a supplied UTC
timestamp. It contains structured audit facts only and no hidden reasoning.

## Failure model

Initial categories are `INVALID_SOURCE`, `INVALID_ARTIFACT`,
`INVALID_TIMESTAMP`, `IDENTITY_CONFLICT`, `POLICY_CONFLICT`,
`UNSUPPORTED_INPUT`, and `INTERNAL_VALIDATION_ERROR`. Failure preserves a
sanitized reason, creates no silent partial valid evidence, and never mutates
previous evidence.

## Version ownership

- evidence identity-policy version: canonical identity meaning;
- eligibility-policy version: decision/reason rules;
- provenance-schema version: origin metadata semantics;
- preparation version: request/result, ordering, duplicate and trace behavior.

Version meaning cannot silently change. Old evidence remains immutable and
readable under its original versions.

## Anti-hindsight

Only approved source material, observation window, and artifact references may
be used. Future Timeline entries, outcomes, learning feedback, historical
similarity, boundary expansion, and mutation of completed evidence are
forbidden.

## Alternatives

- assembler-created evidence: rejected because boundaries mix;
- provider-created domain evidence: rejected because provider assumptions leak;
- raw payload evidence: rejected for security/privacy/reproducibility;
- dedicated immutable Evidence Preparation boundary: selected.

## Production impact

None. Step 7F adds documentation only. No Python/runtime, provider, approved
Reality Gap contract, external dependency, production pipeline, Telegram,
Hostinger, persistence, learning, or Outcome Analysis change.

## Open questions

- Which canonical value normalization and timestamp precision will identity
  policy select?
- Which digest/encoding and collision policy will be approved later?
- Is a future preparation batch atomic, or may valid items survive alongside
  item-level rejection records?
- Which upstream adapter contract guarantees sanitized source material without
  coupling preparation to providers?
- Which stable attempt identity will rejection and duplicate audit records use?

## Recommended Step 7G

Design Candidate generation as a separate consumer of immutable eligible and
auditable ineligible evidence. Define candidate identity, evidence-reference
requirements, dispositions, limitations, and anti-causality language without
implementing classification, metrics, persistence, learning, or production
integration.
