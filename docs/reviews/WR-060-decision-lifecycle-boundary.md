# WR-060 — Decision Lifecycle Boundary

## Purpose

Introduce a dedicated lifecycle boundary for DecisionRecord state
transitions.

## Responsibility

DecisionLifecycle controls valid transitions between decision states.

## Allowed transitions

CREATED → APPROVED

CREATED → REJECTED

## Forbidden transitions

APPROVED → CREATED

REJECTED → CREATED

APPROVED → REJECTED

REJECTED → APPROVED

## Design

DecisionRecord remains immutable.

Lifecycle operations create a new DecisionRecord instance with the
new state.

## Forbidden responsibilities

DecisionLifecycle must not:

- execute trades
- access exchanges
- modify repository storage
- calculate confidence
- generate decisions

## Result

Decision Domain gains explicit state governance.

## Status

Accepted
