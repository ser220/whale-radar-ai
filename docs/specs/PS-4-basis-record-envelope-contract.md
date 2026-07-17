# PS-4 Immutable Compatibility Decision Basis Record Envelope Contract

## Objective

`RealityGapCompatibilityDecisionBasisRecordEnvelope` binds an immutable
historical compatibility basis payload to its immutable basis identity
reference. It is a provenance contract, not a compatibility evaluator.

## Contract

The frozen record contains exactly:

- `basis_reference`: `RealityGapCompatibilityDecisionBasisReference`;
- `basis_payload`: `RealityGapCompatibilityDecisionBasis`;
- `envelope_version`: required version text;
- `created_at`: timezone-aware datetime normalized to UTC.

The reference preserves basis identity, revision, and an optional historical
digest. The payload preserves the complete externally supplied explanation
basis, including rule, policy version, basis type, and canonical historical
reference snapshot. These records remain separate and independently immutable.

## Validation and serialization

Construction requires the exact typed reference and payload contracts, a
non-empty valid envelope version, and an aware timestamp. `to_dict()`,
`from_dict()`, and `canonical_json()` preserve nested identities, payload fields,
canonical artifact references, enums, and timestamps deterministically. Unknown
or incomplete serialized fields are rejected.

## Boundaries

The envelope does not evaluate compatibility, calculate or verify a digest,
resolve references, query current defaults, or substitute historical data. It
contains no service, API, database, persistence, migration, or runtime
integration behavior.

All pre-existing basis, basis-reference, decision-reference, decision-record,
and association contracts remain unchanged. The envelope is additive only.
