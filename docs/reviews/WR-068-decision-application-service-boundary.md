# WR-068 — Decision Application Service Boundary

## Purpose

Introduce application layer between external consumers and Decision Domain.

## Responsibility

DecisionApplicationService coordinates external use cases.

## Command Flow

External Request

↓

DecisionApplicationService

↓

DecisionGovernance

↓

DecisionRecord


## Query Flow

External Request

↓

DecisionApplicationService

↓

DecisionQueryService

↓

DecisionResponse


## Allowed Responsibilities

Application Service may:

- coordinate commands
- coordinate queries
- map external requests


## Forbidden Responsibilities

Application Service must not:

- contain trading logic
- modify DecisionRecord directly
- bypass Governance
- access exchanges


## Result

External systems depend on application boundary only.

## Status

Accepted
