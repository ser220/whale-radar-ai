# WR-082 — Backtest Report Generation

## Purpose

Introduce a unified backtest report boundary.

## Responsibility

Combine backtest session results and performance results into one immutable report.

## Input

- BacktestSessionResult
- BacktestPerformanceReport

## Output

BacktestReport.

Contains:

- session result
- performance report

## Forbidden Responsibilities

Backtest reporting layer must not:

- execute trades
- load market data
- create decisions
- modify strategy logic
- calculate trade lifecycle results

## Flow

BacktestSessionResult

+

BacktestPerformanceReport

↓

BacktestReportGenerator

↓

BacktestReport

## Status

Accepted
