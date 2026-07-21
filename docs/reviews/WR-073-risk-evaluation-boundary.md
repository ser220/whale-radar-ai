# WR-073 — Risk Evaluation Boundary

## Purpose

Introduce risk assessment between intelligence scoring and decision creation.

## Responsibility

Evaluate market risk conditions.

## Input

- MarketFeatures
- IntelligenceScore


## Output

RiskAssessment

Contains:

- risk level
- risk score
- risk reasons


## Forbidden Responsibilities

Risk layer must not:

- create LONG/SHORT decisions
- execute trades
- access exchanges
- modify DecisionRecord


## Flow

MarketFeatures

+

IntelligenceScore

↓

RiskEvaluator

↓

RiskAssessment

↓

Decision Confidence


## Status

Accepted
