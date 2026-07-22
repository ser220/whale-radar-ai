# WR-078 — Simulation Runner

## Purpose

Introduce historical simulation execution.

## Responsibility

Run AI pipeline against sequential market data.

## Input

Historical market snapshots.

## Output

Paper performance results.

## Forbidden Responsibilities

Simulation layer must not:

- access exchanges
- execute real orders
- modify strategy rules


## Flow

Market History

↓

Simulation Runner

↓

AI Decision Pipeline

↓

Paper Execution

↓

Performance Report


## Status

Accepted
