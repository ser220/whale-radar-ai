# WR-201A — Risk Component Contract

## Purpose

Add one shared immutable result contract for future independent risk
evaluators.

## Domain contract

`RiskFactor` defines exactly:

- `FUNDING`
- `OPEN_INTEREST`
- `LIQUIDITY`
- `LIQUIDATIONS`
- `CVD`
- `WHALE`
- `FLOW`
- `VOLATILITY`

Every member uses its uppercase member name as its stable string value.

`RiskComponent` is a frozen value object containing exactly:

- `factor: RiskFactor`
- `score: float`
- `level: RiskLevel`
- `reason_code: str`

Dataclass value equality and hashing make components with equal supplied values
equivalent domain values.

## Validation boundary

`reason_code` must be a string and is otherwise preserved unchanged. This
contract introduces no reason-code taxonomy or formatting rules.

The supplied score is preserved unchanged. The contract does not validate a
score range, normalize or clamp a score, derive a level, or validate a
relationship between score and level.

## Architecture boundary

WR-201A adds no evaluator, calculation, threshold, aggregation, service,
metadata payload, persistence, or integration.

`RiskScore` and `RiskLevel` remain unchanged. The isolated `app.risk` package
does not depend on Intelligence or Decision.

## Compatibility

The implementation uses only Python 3.9-compatible standard-library APIs.
