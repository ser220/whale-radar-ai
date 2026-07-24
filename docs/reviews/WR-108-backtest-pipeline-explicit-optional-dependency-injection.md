# WR-108 — Backtest Pipeline Explicit Optional Dependency Injection Boundary

## Summary

`BacktestPipelineOrchestrator` now distinguishes an omitted generator
from an explicitly injected generator using `is not None`.

## Dependency selection

An injected summary or review generator is preserved even when that
object is falsy. Default generators are created only when the
corresponding constructor argument is exactly `None`.

This prevents valid injected dependencies from being silently replaced
through truthiness fallback.

## Verification boundary

Focused regression coverage uses falsy `AISummaryGenerator` and
`AIReviewGenerator` subclasses. Both dependencies are invoked, and
their custom values are verified through a completed
`BacktestPipelineResult`.

Explicit `None` arguments continue to select the existing default
generators.

## Compatibility

Constructor and `run()` signatures, default output, pipeline result
validation, public imports, serialization, and exports remain
unchanged. No runtime dependency type validation was introduced.

The export manager remains outside this slice.
