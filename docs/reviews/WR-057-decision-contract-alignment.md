# WR-057 — Decision Contract Alignment

## Problem

The current `DecisionRecord` contract does not align with the
`CandidateDecisionInputProjection`.

`CandidateDecisionInputProjection` exposes the canonical references:

- `candidate_reference`
- `intelligence_reference`

`DecisionRecord` currently expects:

- `candidate_id`
- `situation_id`

This forces the future Decision Builder to perform implicit
identifier translation, creating unnecessary coupling between
the Candidate Pipeline and the Decision Domain.

## Decision

The Decision Domain should consume the same canonical references
produced by the Candidate Pipeline.

Rename:

- `candidate_id` → `candidate_reference`
- `situation_id` → `intelligence_reference`

`DecisionRecord` becomes the first immutable Decision object
created directly from `CandidateDecisionInputProjection`
without any identifier transformation.

## Benefits

- Consistent contracts across domain boundaries.
- Simpler Decision Builder implementation.
- No hidden mapping logic.
- Reduced architectural coupling.
- Clear ownership of canonical identifiers.
- Fully immutable decision pipeline.

## Consequences

The future `DecisionBuilder` becomes a pure constructor instead
of an adapter responsible for translating identifiers.

Execution-related identifiers remain the responsibility of the
Execution Domain and are introduced only when an execution
intent is created.

## Status

Accepted
