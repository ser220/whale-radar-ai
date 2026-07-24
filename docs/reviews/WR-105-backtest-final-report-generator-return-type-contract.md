# WR-105 — Backtest Final Report Generator Return Type Contract

## Summary

`ReportGenerator.generate()` now declares its actual return contract:
`BacktestFinalReport`.

The previous annotation referenced `BacktestReport`, which was not
defined in the generator module. Runtime generation succeeded because
annotations were postponed, but `typing.get_type_hints()` raised
`NameError`.

## Compatibility

Only the incorrect return annotation changed. Method arguments, runtime
validation, generated values, public imports, and report behavior remain
unchanged.

Runtime type introspection now resolves the return annotation to
`BacktestFinalReport`.
