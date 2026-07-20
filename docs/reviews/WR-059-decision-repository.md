# WR-059 — Decision Repository

## Purpose

Introduce a read/write boundary for immutable DecisionRecord storage.

## Responsibility

DecisionRepository stores and retrieves immutable DecisionRecord objects.

## Allowed operations

- save decision record
- get decision record by decision_id
- check existence

## Forbidden operations

Repository must not:

- modify DecisionRecord
- approve or reject decisions
- execute trades
- contain exchange logic
- contain business decision rules

## Design

DecisionRecord remains immutable.

Repository stores references to immutable objects and returns
the same canonical decision representation.

## Result

Decision Domain gains persistence abstraction without coupling
business logic to storage implementation.

## Status

Accepted
