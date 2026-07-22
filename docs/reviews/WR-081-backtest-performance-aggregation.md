# WR-081 — Backtest Performance Aggregation

## Purpose

Introduce backtest-level performance aggregation.

## Responsibility

Aggregate paper trade results into a backtest performance report.

## Input

PaperTradeResult collection.

## Output

BacktestPerformanceReport.

Contains:

- total trades
- winning trades
- losing trades
- win rate
- total P/L
- average P/L
- profit factor

## Forbidden Responsibilities

Backtest performance layer must not:

- execute trades
- access exchanges
- modify strategy logic
- create decisions

## Flow

PaperTradeResult Collection

↓

BacktestPerformanceAggregator

↓

BacktestPerformanceReport

↓

Backtest Session Result

## Status

Accepted
