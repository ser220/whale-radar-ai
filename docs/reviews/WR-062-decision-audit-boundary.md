# WR-062 — Decision Audit Boundary

## Purpose

Introduce immutable audit tracking for Decision Domain events.

## Responsibility

Decision Audit records lifecycle events without modifying decisions.

## Events

Supported events:

- decision_created
- decision_approved
- decision_rejected

## Stored information

Audit event contains:

- event_id
- decision_id
- event_type
- created_at

## Forbidden responsibilities

Audit must not:

- modify DecisionRecord
- approve or reject decisions
- execute trades
- contain business rules

## Design

Audit events are immutable records.

Audit storage is separated from Decision storage.

## Result

Decision Domain gains traceability without coupling.

## Status

Accepted
