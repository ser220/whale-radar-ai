# WR-064 — Decision Read Model Boundary

## Purpose

Introduce a read-only projection boundary for Decision Domain consumers.

## Responsibility

DecisionReadModel exposes decision information without exposing
domain internals.

## Contains

- decision_id
- decision_type
- decision_state
- confidence
- created_at

## Design

Read model is immutable.

Mapping happens from DecisionRecord into a separate representation.

## Forbidden responsibilities

Read Model must not:

- modify DecisionRecord
- perform lifecycle transitions
- access repositories
- execute decisions

## Result

External consumers receive a stable read-only contract.

## Status

Accepted
