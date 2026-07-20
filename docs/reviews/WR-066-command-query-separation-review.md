# WR-066 — Decision Command Query Separation Review

## Purpose

Formalize separation between Decision command operations and query
operations.

## Command Side

Responsible component:

DecisionGovernance

Responsibilities:

- create decisions
- approve decisions
- reject decisions
- persist state changes
- emit audit events

Command side uses:

- DecisionBuilder
- DecisionRepository
- DecisionLifecycle
- DecisionAudit


## Query Side

Responsible component:

DecisionQueryService

Responsibilities:

- retrieve decisions
- expose read-only representations
- provide stable consumer contract

Query side uses:

- DecisionRepository
- DecisionReadModelMapper
- DecisionReadModel


## Forbidden Coupling

Command side must not:

- return internal domain objects to external consumers
- expose repository internals

Query side must not:

- modify decisions
- execute lifecycle transitions
- create audit events


## Architectural Result

Decision Domain follows CQRS-style separation:

Command path:

DecisionGovernance
        |
        v
DecisionRecord


Query path:

DecisionQueryService
        |
        v
DecisionReadModel


## Status

Accepted
