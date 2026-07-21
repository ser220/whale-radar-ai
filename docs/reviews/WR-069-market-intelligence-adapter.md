# WR-069 — Market Intelligence Adapter

## Purpose

Introduce normalized market intelligence boundary.

## Responsibility

Convert external market data into internal intelligence models.

## Sources

Examples:

- exchange APIs
- TradingView
- derivatives data
- on-chain sources

## Output

Normalized MarketSnapshot.

## Design

External providers must not leak into Decision Domain.

## Forbidden Responsibilities

Adapter must not:

- create trading decisions
- execute orders
- manage risk
- access DecisionGovernance

## Flow

External Data

↓

Market Intelligence Adapter

↓

MarketSnapshot

↓

CandidateDecisionInputProjection


## Status

Accepted
