# WR-106 — Backtest Pipeline Decision-to-Review State Consistency Boundary

## Summary

`BacktestPipelineResult` now rejects a review state that contradicts
the completed pipeline decision.

## State invariant

The aggregation boundary accepts only:

- `PASS` with `APPROVE` and `READY`;
- `REVIEW` with `CONDITIONAL` and `LIMITED`;
- `REJECT` with `REJECT` and `NOT_READY`.

Any other decision-to-review combination raises:

```text
ValueError("summary decision and review state must match")
```

## Validation precedence

The new invariant runs after the existing nested type, strategy
identity, report/summary decision, and summary/review confidence checks.
Their established exception behavior therefore remains unchanged.

## Compatibility

Valid generated pipeline results, constructor fields, public imports,
serialization, and exports remain unchanged. Only contradictory
manually assembled completed results are rejected.

No shared policy abstraction or generator change was introduced.
