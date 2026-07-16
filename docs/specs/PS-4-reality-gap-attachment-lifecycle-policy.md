# PS-4 RealityGapAttachment Lifecycle Policy Specification

## Objective

Define an immutable, deterministic contract boundary for the lifecycle of
Reality Gap attachment revisions while preserving historical truth.

## Scope

- lifecycle states;
- allowed state transitions;
- attachment revision semantics;
- supersession semantics;
- historical reference preservation;
- compatibility boundaries;
- focused contract validation and serialization.

## Out of scope

- transition services or orchestration;
- attachment mutation;
- database, repository, API, scheduler, migration, or persistence logic;
- artifact resolution or current-version lookup;
- production and Telegram integration.

## Public API

- `AttachmentLifecycleState`
  - `CREATED`
  - `ACTIVE`
  - `SUPERSEDED`
  - `ARCHIVED`
- `AttachmentRevisionAxis`
  - `ATTACHMENT`
  - `ANALYSIS`
  - `CLASSIFICATION`
  - `METRICS`
- `AttachmentLifecycleTransition`
- `AttachmentLifecycleValidationError`
- `RealityGapAttachmentLifecyclePolicy`
- `canonical_lifecycle_transitions()`
- `canonical_revision_axes()`

## Transition policy

Only these transitions are valid:

1. `CREATED -> ACTIVE`
2. `ACTIVE -> SUPERSEDED`
3. `SUPERSEDED -> ARCHIVED`

Backward transitions, skipped states, repeated states, and transitions from
`ARCHIVED` are invalid.

## Contract fields

`RealityGapAttachmentLifecyclePolicy` contains:

- `lifecycle_state`;
- `policy_version`;
- `revision_policy_identifier`;
- `allowed_transitions`;
- `independent_revision_axes`;
- `immutable_historical_attachments`;
- `preserve_historical_references`;
- `allow_current_default_substitution`.

The last three fields are invariants and validate only as `True`, `True`, and
`False`, respectively.

## Revision rules

- attachment revision is independent of every referenced artifact version;
- Analysis, Classification, and Metrics versions remain independent from one
  another;
- policy version is not an attachment or artifact version;
- revision policy identity is not an attachment or artifact version;
- a future superseding revision must not alter the predecessor.

## Historical rules

- an existing attachment is never modified after creation;
- superseded attachments remain valid historical records;
- exact referenced identities and versions remain attached to the historical
  revision;
- no current default, current policy, or latest artifact may replace a
  historical reference;
- archival does not delete or rewrite the attachment.

## Serialization

- `to_dict()` uses fixed public field names and enum values;
- `from_dict()` rejects missing and unknown fields;
- `canonical_json()` uses sorted keys, compact separators, UTF-8-compatible
  text, and deterministic ordered collections;
- round-trip serialization preserves states, transitions, axes, and invariants.

## Compatibility

The policy is additive and does not change the existing seven-field
`RealityGapAttachmentReadContract`. Lifecycle state and read availability are
separate concepts. No automatic mapping is introduced.

## Acceptance criteria

- contracts are frozen dataclasses;
- collections are immutable tuples;
- the canonical transition graph is enforced;
- historical integrity invariants cannot be disabled;
- focused tests cover valid/invalid transitions, immutability, historical
  preservation, independent revisions, and serialization;
- Python 3.9 compilation succeeds;
- no production, runtime service, API, persistence, or external dependency is
  added.
