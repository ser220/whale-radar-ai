# WR-114 Report — Simulation Runner Python 3.9 Optional Strategy Type Contract

## Scope

Corrected one Python 3.9-incompatible public constructor annotation.

## Implementation

- Import `Optional` alongside the existing `Iterable` import.
- Replace `SimulationStrategyAdapter | None` with
  `Optional[SimulationStrategyAdapter]`.
- Preserve the strategy parameter and its `None` default.

## Tests

- Resolve constructor annotations with `typing.get_type_hints()`.
- Require the strategy hint to resolve to
  `Optional[SimulationStrategyAdapter]`.
- Require the strategy default to remain `None`.
- Require the return hint to remain `NoneType`.

## Boundaries

No runtime logic, WR-113 dependency selection, runtime validation,
simulation model, strategy adapter, result, public import, or other
annotation change was introduced.

## Verification

- Changed Python files compile successfully under Python 3.9.6.
- Focused WR-114 type-contract test: 1 passed.
- Complete simulation tests: 12 passed.
- Complete `tests/backtest` suite: 158 passed.
- Deterministic project regression excluding four pre-existing live
  Telegram scripts: 1438 passed, 1 environment warning.
