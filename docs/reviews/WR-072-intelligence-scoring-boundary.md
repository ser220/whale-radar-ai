# WR-072 — Intelligence Scoring Boundary

## Purpose

Introduce intelligence quality scoring between features and decision input.

## Responsibility

Convert MarketFeatures into IntelligenceScore.

## Input

MarketFeatures

Contains:

- trend
- volatility state
- liquidity state


## Output

IntelligenceScore

Contains:

- numeric score
- confidence level


## Forbidden Responsibilities

Scoring layer must not:

- create trading decisions
- execute orders
- access exchanges
- modify DecisionRecord


## Flow

MarketFeatures

↓

IntelligenceScorer

↓

IntelligenceScore

↓

Decision Input


## Status

Accepted
