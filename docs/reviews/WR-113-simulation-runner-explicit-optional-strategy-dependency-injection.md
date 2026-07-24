# WR-113 — Simulation Runner Explicit Optional Strategy Dependency Injection Boundary

## Summary

`SimulationRunner` now distinguishes an omitted strategy from an
explicitly injected strategy using `is not None`.

## Dependency selection

An injected strategy is preserved even when that object is falsy. The
default `SimulationStrategyAdapter` is created only when the constructor
argument is exactly `None`.

This prevents a valid strategy from being silently replaced through
truthiness fallback.

## Verification boundary

Focused regression coverage invokes a falsy strategy through
`SimulationRunner.run()`. It verifies that the strategy receives each
original snapshot and that its decisions determine the completed
`SimulationResult`.

Explicit `None` continues to select the existing default strategy.

## Compatibility

Constructor parameters, default value, existing annotation, runner
logic, result contracts, default behavior, truthy strategy behavior,
invalid-snapshot behavior, and public imports remain unchanged.

No runtime type validation or Python 3.9 annotation change was
introduced.
