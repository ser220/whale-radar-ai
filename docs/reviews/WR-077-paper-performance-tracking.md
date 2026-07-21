# WR-077 — Paper Performance Tracking

## Purpose

Track performance metrics from paper trades.

## Responsibility

Aggregate closed paper trade results.

## Input

PaperTradeResult collection.

## Output

PerformanceReport.

Contains:

- total trades
- winning trades
- losing trades
- win rate
- total P/L
- average P/L


## Forbidden Responsibilities

Performance layer must not:

- execute trades
- access exchanges
- modify strategy logic
- create decisions


## Flow

PaperTradeResult

↓

PerformanceTracker

↓

PerformanceReport


## Status

Accepted
