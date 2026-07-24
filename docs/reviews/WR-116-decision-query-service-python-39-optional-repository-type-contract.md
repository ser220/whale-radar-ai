# WR-116 — Decision Query Service Python 3.9 Optional Repository Type Contract

## Summary

`DecisionQueryService.__init__()` now declares its optional repository
with Python 3.9-compatible `typing.Optional`.

## Type contract

The previous postponed `DecisionRepository | None` annotation allowed
the module to import, but `typing.get_type_hints()` could not evaluate
the constructor annotation on Python 3.9.

The repository annotation is now:

```python
Optional[DecisionRepository]
```

Runtime type introspection resolves successfully while preserving the
existing `None` default and return annotation.

## Compatibility

Constructor parameters, repository selection, query behavior, public
imports, and runtime behavior remain unchanged. No runtime validation,
dependency-selection, dependency, public API, or other annotation
change was introduced.
