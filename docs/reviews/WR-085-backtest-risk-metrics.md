# WR-085 — Backtest Risk Metrics Layer

## Purpose

Introduce risk analysis layer for historical backtests.

## Responsibility

Calculate portfolio risk metrics from equity curve.

## Input

BacktestEquityCurve

## Output

BacktestRiskReport

## Metrics

Initial metrics:

- maximum drawdown
- maximum drawdown percentage
- recovery factor
- risk score

## Flow

BacktestEquityCurve

↓

RiskMetricsCalculator

↓

BacktestRiskReport

## Forbidden Responsibilities

Risk layer must not:

- execute trades
- generate signals
- modify strategies
- access market data

## Status

Accepted
