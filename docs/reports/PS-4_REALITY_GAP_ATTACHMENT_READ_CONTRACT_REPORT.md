# PS-4 RealityGapAttachment Read Contract Boundary Report

## Scope

Implemented an immutable read-only consumer boundary for Reality Gap analysis
attachments. The contract exposes only attachment identity, three independently
versioned artifact references, availability, and a UTC creation timestamp.

## Public API

- `AttachmentAvailabilityStatus`
- `AttachmentReadReference`
- `AttachmentReadValidationError`
- `RealityGapAttachmentReadContract`

## Boundaries

The package contains no raw evidence, candidate or projection objects, mapping
details, classification or metrics payloads, runtime services, APIs, storage,
production integration, or third-party dependencies.

## Verification

Focused contract tests cover immutability, exact field exposure, independent
version validation, identity separation, availability states, UTC normalization,
strict deserialization, round-trip behavior, and deterministic canonical JSON.
