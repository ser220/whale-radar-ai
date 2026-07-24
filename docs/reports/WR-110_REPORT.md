# WR-110 Report — Backtest Top-Level Public Export Manifest Consistency Boundary

## Scope

Corrected only the root `app.backtest.__all__` public export manifest.

## Implementation

- Add the previously omitted `BenchmarkCalculator`.
- Remove repeated `BacktestEquityCurve`, `EquityCurveCalculator`, and
  `EquityPoint` entries.
- Remove repeated `BacktestRiskReport` and `RiskMetricsCalculator`
  entries.
- Preserve all 30 intended exports and their existing order.

## Tests

- Require the exact expected 30-symbol manifest.
- Require every export to occur exactly once.
- Require every exported name to resolve on `app.backtest`.
- Verify wildcard import exposes `BenchmarkCalculator`.
- Verify all explicit imports retain object identity.

## Boundaries

No subpackage initializer, runtime implementation, pipeline API,
contract, validation, or behavior change was introduced.

## Verification

- Changed Python files compile successfully under Python 3.9.6.
- Focused WR-110 manifest tests: 3 passed.
- Complete public API tests: 4 passed.
- Complete `tests/backtest` suite: 150 passed.
- Deterministic project regression excluding four pre-existing live
  Telegram scripts: 1427 passed, 1 environment warning.
