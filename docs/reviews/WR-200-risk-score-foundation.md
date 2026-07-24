# WR-200 — Risk Score Foundation

## Purpose

Introduce the independent immutable domain foundation for a future common
Whale Radar AI risk contract.

## Domain contract

`RiskScore` is a frozen value object containing:

- `total_score`
- `liquidity_score`
- `funding_score`
- `whale_score`
- `flow_score`
- `volatility_score`

Dataclass value equality and hashing make equal score compositions equivalent
domain values.

`RiskLevel` defines the stable values:

- `LOW`
- `MEDIUM`
- `HIGH`
- `EXTREME`

## Boundaries

This slice does not calculate scores or derive a `RiskLevel` from a score.
Thresholds and calculation policy remain outside the foundation.

No existing Intelligence, Decision, Backtest, service, persistence, or
execution path is integrated or modified.

## Compatibility

The foundation uses only Python 3.9-compatible standard-library APIs and adds
an isolated `app.risk` public package.
