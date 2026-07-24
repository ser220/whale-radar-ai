# WR-104 — Backtest AI Review Decision Input Validation Boundary

## Summary

`AIReviewGenerator` now accepts only the explicit decision values
`PASS`, `REVIEW`, and `REJECT`.

Previously, every value other than `PASS` or `REVIEW` entered the
rejection branch. Unknown or malformed input could therefore become a
valid rejection review and lose its original invalid state.

## Validation

`REJECT` is now an explicit branch. Every other unsupported value raises
exactly:

```text
ValueError("invalid decision")
```

Decision values are not trimmed, case-normalized, rewritten, or
inferred.

## Compatibility

The generator signature, valid decision mappings, review contract, and
public imports remain unchanged. Only previously unsupported fallback
input now fails deterministically.
