# WR-063 — Governance Audit Integration

## Purpose

Integrate DecisionAudit into DecisionGovernance lifecycle operations.

## Responsibility

DecisionGovernance records lifecycle events through DecisionAudit.

## Events

Created:

- decision_created

Approved:

- decision_approved

Rejected:

- decision_rejected

## Design

Audit remains an independent boundary.

Governance only emits audit events after successful operations.

## Forbidden responsibilities

Governance must not:

- modify audit events
- modify immutable DecisionRecords
- execute trades
- access exchanges

## Result

Decision lifecycle becomes fully traceable.

## Status

Accepted
