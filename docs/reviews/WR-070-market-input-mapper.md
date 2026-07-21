# WR-070 — Market Intelligence Input Mapper

## Purpose

Connect normalized market intelligence with Decision input boundary.

## Responsibility

Convert MarketSnapshot into CandidateDecisionInputProjection.

## Input

MarketSnapshot

Contains:

- symbol
- price
- volume
- volatility
- timestamp


## Output

CandidateDecisionInputProjection


## Design

Mapper translates data only.

No trading decisions are created.

## Forbidden Responsibilities

Mapper must not:

- execute orders
- calculate final signals
- modify decisions
- access exchanges


## Flow

MarketSnapshot

↓

MarketDecisionInputMapper

↓

CandidateDecisionInputProjection

↓

Decision Engine


## Status

Accepted
