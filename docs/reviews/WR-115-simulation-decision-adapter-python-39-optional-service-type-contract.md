# WR-115 — Simulation Decision Adapter Python 3.9 Optional Service Type Contract

## Summary

`SimulationDecisionAdapter.__init__()` now declares its optional
application service with Python 3.9-compatible `typing.Optional`.

## Type contract

The previous postponed `DecisionApplicationService | None` annotation
allowed the module to import, but `typing.get_type_hints()` could not
evaluate it on Python 3.9.

The application service annotation is now:

```python
Optional[DecisionApplicationService]
```

Runtime type introspection resolves successfully while preserving the
existing `None` default and return annotation.

## Compatibility

Constructor parameters, dependency selection, decision creation,
public imports, and runtime behavior remain unchanged. No runtime
validation, dependency, or other annotation change was introduced.
