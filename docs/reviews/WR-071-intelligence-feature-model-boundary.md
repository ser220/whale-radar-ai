# WR-071 — Intelligence Feature Model Boundary

## Purpose

Introduce a separate feature model between market data and decision input.

## Responsibility

Convert normalized market snapshots into intelligence features.

## Input

MarketSnapshot

Contains:

- symbol
- price
- volume
- volatility
- timestamp


## Output

MarketFeatures

Contains derived market characteristics.

Examples:

- trend state
- volatility state
- liquidity state


## Forbidden Responsibilities

Feature layer must not:

- create trading decisions
- execute orders
- access exchanges
- modify DecisionRecord


## Flow

MarketSnapshot

↓

Feature Extraction

↓

MarketFeatures

↓

Decision Input


## Status

Accepted
