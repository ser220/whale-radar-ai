# WR-112 — Backtest Session Service Python 3.9 Optional Runner Type Contract

## Summary

`BacktestSessionService.__init__()` now declares its optional runner
dependency with Python 3.9-compatible `typing.Optional`.

## Type contract

The previous postponed `SimulationRunner | None` annotation allowed the
module to import, but `typing.get_type_hints()` could not evaluate it on
Python 3.9.

The runner annotation is now:

```python
Optional[SimulationRunner]
```

Runtime type introspection resolves successfully while preserving the
existing `None` default and return annotation.

## Compatibility

Constructor parameters, dependency selection, session execution,
timestamps, result construction, public imports, and runtime behavior
remain unchanged. No runtime validation was introduced and no other
annotation was modified.
