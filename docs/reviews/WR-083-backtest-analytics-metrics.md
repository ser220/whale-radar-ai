# WR-083 — Backtest Analytics Metrics

## Purpose

Introduce analytics layer for evaluating backtest quality.

## Responsibility

Calculate analytical metrics from completed backtest performance results.

## Input

- BacktestPerformanceReport

## Output

- BacktestAnalyticsReport

## Metrics

Initial metrics:

- total return
- average trade
- gross profit
- gross loss
- best trade
- worst trade
- risk reward ratio

## Forbidden Responsibilities

Analytics layer must not:

- execute trades
- load market data
- modify strategies
- calculate lifecycle results

## Flow

BacktestPerformanceReport

↓

BacktestAnalyticsCalculator

↓

BacktestAnalyticsReport

## Status

Accepted
