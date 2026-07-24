# WR-111 Report — Backtest Equity Curve Defensive Points Immutability Boundary

## Scope

Closed the mutable points collection escape in the frozen
`BacktestEquityCurve` contract.

## Implementation

- Snapshot `points` as a tuple after existing scalar validation.
- Preserve point values, ordering, duplicates, empty collections, and
  element identity.
- Preserve existing scalar validation messages and precedence.

## Tests

- Prove list input is stored as an independent tuple.
- Prove source-list mutation cannot change the curve.
- Preserve ordering, duplicates, and element identity.
- Preserve tuple and empty collection inputs.
- Preserve scalar validation behavior and frozen assignment rejection.

## Boundaries

No point element validation, curve consistency calculation, calculator,
evaluation, risk, pipeline, serialization, export, or public API change
was introduced.

## Verification

- Changed Python files compile successfully under Python 3.9.6.
- Focused WR-111 immutability tests: 7 passed.
- Complete equity tests: 11 passed.
- Evaluation and risk compatibility tests: 6 passed.
- Complete `tests/backtest` suite: 157 passed.
- Deterministic project regression excluding four pre-existing live
  Telegram scripts: 1434 passed, 1 environment warning.
