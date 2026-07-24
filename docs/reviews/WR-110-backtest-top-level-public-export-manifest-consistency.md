# WR-110 — Backtest Top-Level Public Export Manifest Consistency Boundary

## Summary

The top-level `app.backtest` export manifest now contains exactly its
30 intended public symbols.

## Manifest correction

- Added `BenchmarkCalculator` beside `BacktestBenchmarkReport`.
- Removed duplicate equity exports.
- Removed duplicate risk exports.
- Preserved every existing unique export and its established order.

All names declared by the root `__all__` resolve to actual
`app.backtest` attributes and occur exactly once.

## Consumer behavior

`from app.backtest import *` now exposes `BenchmarkCalculator`.
Existing explicit imports continue to resolve to the same objects.

## Compatibility

No class, function, constructor, validation, runtime path, or
subpackage export was changed. Pipeline symbols remain public from
`app.backtest.pipeline` and were not promoted into the root package.

The change is additive for wildcard consumers. Removing duplicate
manifest strings does not remove any public object.
