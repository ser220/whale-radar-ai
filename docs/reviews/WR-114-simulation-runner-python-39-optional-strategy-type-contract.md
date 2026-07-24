# WR-114 — Simulation Runner Python 3.9 Optional Strategy Type Contract

## Summary

`SimulationRunner.__init__()` now declares its optional strategy
dependency with Python 3.9-compatible `typing.Optional`.

## Type contract

The previous postponed `SimulationStrategyAdapter | None` annotation
allowed the module to import, but `typing.get_type_hints()` could not
evaluate it on Python 3.9.

The strategy annotation is now:

```python
Optional[SimulationStrategyAdapter]
```

Runtime type introspection resolves successfully while preserving the
existing `None` default and return annotation.

## Compatibility

Constructor parameters, WR-113 dependency selection, simulation
execution, result construction, public imports, and runtime behavior
remain unchanged. No runtime validation was introduced and no other
annotation was modified.
