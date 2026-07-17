# PS-4 Immutable Governance Provenance Bundle Contract

## Objective

`RealityGapGovernanceProvenanceBundle` is an immutable aggregation snapshot of
one historical Reality Gap attachment-governance chain. It composes existing
immutable contracts without changing their semantics or introducing runtime
governance behavior.

## Contract

The frozen bundle contains exactly:

- `bundle_id`: required bundle identity;
- `attachment_reference`: canonical `ATTACHMENT` artifact reference;
- `decision_record`: immutable compatibility decision record envelope;
- `basis_record`: immutable compatibility basis record envelope;
- `association`: typed compatibility decision association v2;
- `bundle_version`: required bundle contract version;
- `created_at`: timezone-aware datetime normalized to UTC.

The attachment reference preserves version-only, digest-only, or dual-locator
history. Decision and basis records preserve their independent identities,
versions, optional digests, and complete payloads. Association v2 preserves the
typed attachment, decision, and basis references.

## Validation boundary

The bundle validates structural presence, exact nested contract types, an
`ATTACHMENT` root reference, valid version text, and an aware timestamp. It does
not compare IDs, versions, digests, or timestamps between nested contracts.
Semantic consistency across the nested records belongs to a future, explicit
validation boundary.

## Serialization

`to_dict()`, `from_dict()`, and `canonical_json()` preserve every nested object
losslessly and reject missing, incomplete, or unknown serialized fields.
Canonical JSON is deterministic and does not calculate or verify any digest.

## Non-goals

The bundle does not evaluate compatibility, resolve references, perform an
external lookup, validate cross-record lineage, generate digests, substitute
current defaults, persist records, expose an API, or orchestrate runtime work.
All underlying contracts remain independently immutable and unchanged.
