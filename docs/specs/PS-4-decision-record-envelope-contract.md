# PS-4 Immutable Compatibility Decision Record Envelope Contract

## Objective

`RealityGapCompatibilityDecisionRecordEnvelope` binds an immutable historical
compatibility decision payload to its immutable decision identity reference.
It is a provenance contract, not a compatibility engine.

## Contract

The frozen record contains exactly:

- `decision_reference`: `RealityGapCompatibilityDecisionReference`;
- `decision_payload`: `RealityGapAttachmentCompatibilityDecision`;
- `envelope_version`: required version text;
- `created_at`: timezone-aware datetime normalized to UTC.

The reference preserves decision identity, revision, and an optional historical
digest. The payload preserves the complete externally supplied compatibility
decision. These records remain separate and independently immutable.

## Validation and serialization

Construction requires the exact typed reference and payload contracts, a
non-empty valid envelope version, and an aware timestamp. `to_dict()`,
`from_dict()`, and `canonical_json()` preserve nested identities, payload fields,
enums, references, and timestamps deterministically. Unknown or incomplete
serialized fields are rejected.

## Boundaries

The envelope does not evaluate compatibility, calculate or verify a digest,
resolve references, query current defaults, or substitute historical data. It
contains no service, API, database, persistence, migration, or runtime
integration behavior.

All pre-existing decision, decision-reference, decision-basis, and association
contracts remain unchanged. The envelope is an additive contract only.
