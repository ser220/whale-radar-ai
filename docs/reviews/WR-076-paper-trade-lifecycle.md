# WR-076 — Paper Trade Lifecycle

## Purpose

Introduce lifecycle management for paper trades.

## Responsibility

Manage simulated trade state changes.

## Input

PaperTrade

## Output

PaperTradeResult

Contains:

- closing price
- profit/loss
- status


## Forbidden Responsibilities

Lifecycle layer must not:

- access exchanges
- execute real orders
- modify trading strategy


## Flow

PaperTrade

↓

Lifecycle Service

↓

Close Result

↓

Performance Tracking


## Status

Accepted
