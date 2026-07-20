# WR-067 — Decision External Contract Boundary

## Purpose

Introduce a stable external contract boundary for Decision consumers.

## Responsibility

External contract exposes decision information without exposing
internal domain models.

## Internal Source

DecisionRecord

## External Contract

DecisionResponse

## Contains

- decision_id
- decision_type
- decision_state
- confidence
- created_at

## Design

External contract is immutable.

Mapping happens through a dedicated mapper.

## Forbidden Responsibilities

External Contract must not:

- modify DecisionRecord
- perform lifecycle transitions
- access repositories
- contain business rules

## Result

External consumers depend on stable contracts instead of domain objects.

## Status

Accepted
