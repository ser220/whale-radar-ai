# WR-109 Report — Backtest Pipeline Export Manager Explicit Optional Dependency Injection Boundary

## Scope

Removed truthiness-based writer replacement from the existing backtest
pipeline export manager.

## Implementation

- Preserve an injected regular JSON writer whenever it is not `None`.
- Preserve an injected timestamped JSON writer whenever it is not
  `None`.
- Instantiate existing defaults only for `None`.
- Keep constructor and public export method signatures unchanged.

## Tests

- Prove a falsy regular JSON writer is invoked through `export_json()`.
- Prove a falsy timestamped writer is invoked through
  `export_timestamped_json()`.
- Verify original result and requested path identity at each writer.
- Verify each public method returns its injected writer's exact result.
- Preserve explicit `None` to default-writer behavior.

## Boundaries

No runtime type validation, writer, serializer, orchestrator, shared
policy, filesystem behavior, or public API change was introduced.

## Verification

- Changed Python files compile successfully under Python 3.9.6.
- Focused WR-109 dependency-selection tests: 2 passed.
- Complete export-manager tests: 4 passed.
- Complete `tests/backtest/pipeline` suite: 89 passed.
- Deterministic project regression excluding four pre-existing live
  Telegram scripts: 1423 passed, 1 environment warning.
