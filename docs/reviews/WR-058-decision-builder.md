# WR-058 — Decision Builder

## Purpose

Introduce the first construction service inside the Decision Domain.

The Decision Builder converts an immutable
`CandidateDecisionInputProjection` into an immutable
`DecisionRecord`.

## Input

The builder consumes:

- `CandidateDecisionInputProjection`
- `DecisionType`
- confidence value
- optional creation time

The canonical references are copied directly:

- `candidate_reference`
- `intelligence_reference`

No identifier translation is allowed.

## Output

The builder returns a validated immutable `DecisionRecord`.

The initial decision state is always:

- `DecisionState.CREATED`

The contract version is supplied by the builder configuration and
defaults to:

- `DecisionContractVersion.V1`

## Identity

The builder is responsible for creating `decision_id`.

Decision identity must be deterministic for the same canonical
input values and identity-policy version.

The identity implementation is kept separate from the builder.

## Responsibilities

The Decision Builder may:

- validate the input projection type
- require an available decision input
- create a deterministic decision identifier
- construct the immutable decision record
- invoke `DecisionPolicy`

The Decision Builder must not:

- approve or reject decisions
- execute trades
- access exchanges
- modify candidate or intelligence records
- introduce exchange-specific fields

## Result

The Decision Domain gains a single canonical entry point:

`CandidateDecisionInputProjection`
→ `DecisionBuilder`
→ `DecisionRecord`

## Status

Accepted
