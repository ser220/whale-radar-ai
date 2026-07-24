# WR-109 — Backtest Pipeline Export Manager Explicit Optional Dependency Injection Boundary

## Summary

`BacktestPipelineExportManager` now distinguishes omitted writers from
explicitly injected writers using `is not None`.

## Dependency selection

An injected regular or timestamped JSON writer is preserved even when
that object is falsy. A default writer is created only when the
corresponding constructor argument is exactly `None`.

This prevents valid injected writers from being silently replaced
through truthiness fallback.

## Verification boundary

Focused tests invoke falsy writer subclasses through `export_json()` and
`export_timestamped_json()`. They verify that each writer receives the
original pipeline result and requested path, and that each manager
method returns the exact path supplied by its injected writer.

Explicit `None` arguments continue to select the existing default
writers through the same public methods.

## Compatibility

Constructor and export method signatures, public writer attributes,
default filesystem behavior, return types, serialization, and exports
remain unchanged. No runtime dependency type validation was
introduced.

No writer, serializer, or orchestrator implementation was modified.
