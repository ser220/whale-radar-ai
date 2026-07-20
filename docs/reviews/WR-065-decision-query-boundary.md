# WR-065 — Decision Query Boundary

## Purpose

Introduce a dedicated read query boundary for Decision Domain.

## Responsibility

DecisionQueryService provides read-only access to decisions.

## Flow

DecisionRepository
        |
        v
DecisionReadModelMapper
        |
        v
DecisionReadModel

## Allowed operations

- get decision
- list decisions by reference

## Forbidden responsibilities

DecisionQueryService must not:

- create decisions
- modify decisions
- approve or reject decisions
- execute trades
- write audit events

## Design

Query side is separated from command side.

## Result

Decision Domain gains CQRS-style read separation.

## Status

Accepted
