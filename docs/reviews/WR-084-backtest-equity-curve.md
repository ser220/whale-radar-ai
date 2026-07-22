# WR-084 — Backtest Equity Curve Engine

## Purpose

Introduce equity curve calculation for historical backtests.

## Responsibility

Track portfolio value changes over time based on completed trades.

## Input

- initial balance
- PaperTradeResult[]

## Output

- BacktestEquityCurve

## Metrics

Initial metrics:

- equity points
- final equity
- cumulative return
- peak equity
- drawdown

## Flow

PaperTradeResult[]

↓

EquityCurveCalculator

↓

BacktestEquityCurve

## Forbidden Responsibilities

Equity layer must not:

- execute trades
- decide entries
- load market data
- modify strategies

## Status

Accepted
