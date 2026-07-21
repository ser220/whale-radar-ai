# WR-074 — Decision Confidence Aggregation

## Purpose

Aggregate intelligence quality and risk assessment into a unified confidence value.

## Responsibility

Calculate decision confidence only.

## Input

- IntelligenceScore
- RiskAssessment


## Output

DecisionConfidence

Contains:

- confidence value
- confidence level


## Forbidden Responsibilities

Confidence layer must not:

- create trading decisions
- execute orders
- access exchanges
- modify DecisionRecord


## Flow

IntelligenceScore

+

RiskAssessment

↓

ConfidenceAggregator

↓

DecisionConfidence

↓

Decision Application


## Status

Accepted
