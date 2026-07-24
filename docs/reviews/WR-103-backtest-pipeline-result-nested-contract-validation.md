# WR-103 — Backtest Pipeline Result Nested Contract Validation Boundary

## Summary

`BacktestPipelineResult` now validates the identity of each nested
contract before reading fields for cross-contract consistency checks.

## Validation

The aggregation boundary requires:

- `report` to be a `BacktestFinalReport`;
- `summary` to be a `BacktestAISummary`;
- `review` to be a `BacktestAIReview`.

Invalid values raise a field-specific `TypeError` instead of producing
an incidental attribute error or entering the pipeline through duck
typing.

Validation uses `isinstance()`, so supported subclasses remain
compatible.

## Compatibility

The frozen dataclass fields, constructor signature, public import,
serialization schema, and existing relational invariants remain
unchanged. No orchestration or export behavior was modified.
