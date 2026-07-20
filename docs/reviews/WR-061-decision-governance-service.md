# WR-061 — Decision Governance Service

## Purpose

Introduce the orchestration boundary for the Decision Domain.

## Responsibility

DecisionGovernance coordinates:

- DecisionBuilder
- DecisionRepository
- DecisionLifecycle

## Allowed operations

- create decision
- store decision
- approve decision
- reject decision
- retrieve decision

## Forbidden operations

DecisionGovernance must not:

- generate market signals
- analyze candidates
- execute trades
- access exchanges
- mutate immutable records

## Design

DecisionGovernance is an orchestration layer only.

Business rules remain inside dedicated boundaries.

## Result

Decision Domain gains a single governance entry point.

## Status

Accepted
