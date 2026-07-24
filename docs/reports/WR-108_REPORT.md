# WR-108 Report — Backtest Pipeline Explicit Optional Dependency Injection Boundary

## Scope

Removed truthiness-based dependency replacement from the existing
backtest pipeline orchestrator.

## Implementation

- Preserve an injected summary generator whenever it is not `None`.
- Preserve an injected review generator whenever it is not `None`.
- Instantiate existing defaults only for `None`.
- Keep constructor and `run()` signatures unchanged.

## Tests

- Prove a falsy `AISummaryGenerator` subclass is invoked.
- Prove a falsy `AIReviewGenerator` subclass is invoked.
- Verify both custom outputs through a valid completed pipeline result.
- Preserve explicit `None` to default-generator behavior.

## Boundaries

No runtime type validation, export-manager change, shared policy,
pipeline result, serializer, export, or public API change was
introduced.

## Verification

- Changed Python files compile successfully under Python 3.9.6.
- Focused WR-108 dependency-selection tests: 2 passed.
- Orchestrator tests: 4 passed.
- Complete `tests/backtest/pipeline` suite: 87 passed.
- Deterministic project regression excluding four pre-existing live
  Telegram scripts: 1421 passed, 1 environment warning.
