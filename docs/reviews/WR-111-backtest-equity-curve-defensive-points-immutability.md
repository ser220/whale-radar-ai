# WR-111 — Backtest Equity Curve Defensive Points Immutability Boundary

## Summary

`BacktestEquityCurve` now takes a defensive tuple snapshot of its
`points` collection during construction.

## Immutability invariant

The frozen curve contract no longer retains a caller-owned mutable
points list. Mutating the source list cannot change an already-created
curve or a downstream contract containing that curve.

The snapshot preserves:

- every point value;
- original ordering;
- duplicate points;
- point object identity;
- empty collections.

No element validation, deep copying, sorting, deduplication, or curve
consistency calculation is introduced.

## Validation

The defensive conversion occurs after the existing scalar checks.
Their established validation messages and precedence remain unchanged.

## Compatibility

The constructor fields, tuple annotation, calculator output, public
imports, evaluation and risk consumers, pipeline, serialization, and
exports remain unchanged. Existing tuple inputs remain valid, while
list inputs are stored as immutable tuples.
