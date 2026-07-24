# WR-113 Report — Simulation Runner Explicit Optional Strategy Dependency Injection Boundary

## Scope

Removed truthiness-based strategy replacement from the existing
simulation runner.

## Implementation

- Preserve an injected strategy whenever it is not `None`.
- Instantiate the existing default strategy only for `None`.
- Keep constructor parameters, default value, and annotation unchanged.
- Preserve `run()` and `SimulationResult` behavior.

## Tests

- Prove a falsy strategy is invoked through `SimulationRunner.run()`.
- Verify each original snapshot reaches the injected strategy.
- Verify processed and generated-trade counts reflect public execution.
- Preserve explicit `None` to default-strategy behavior.
- Retain existing truthy-strategy and invalid-snapshot coverage.

## Boundaries

No runtime type validation, annotation, strategy adapter, snapshot,
session, backtest, shared policy, or public API change was introduced.

## Verification

- Changed Python files compile successfully under Python 3.9.6.
- Focused WR-113 dependency-selection tests: 2 passed.
- Complete simulation tests: 11 passed.
- Complete `tests/backtest` suite: 158 passed.
- Deterministic project regression excluding four pre-existing live
  Telegram scripts: 1437 passed, 1 environment warning.
