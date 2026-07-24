# WR-112 Report — Backtest Session Service Python 3.9 Optional Runner Type Contract

## Scope

Corrected one Python 3.9-incompatible public constructor annotation.

## Implementation

- Import `Optional` alongside the existing `Iterable` import.
- Replace `SimulationRunner | None` with
  `Optional[SimulationRunner]`.
- Preserve the runner parameter and its `None` default.

## Tests

- Resolve constructor annotations with `typing.get_type_hints()`.
- Require the runner hint to resolve to
  `Optional[SimulationRunner]`.
- Require the runner default to remain `None`.
- Require the return hint to remain `NoneType`.
- Preserve existing session execution coverage.

## Boundaries

No runtime logic, runtime validation, session model, timestamps,
configuration, result, public import, or other annotation change was
introduced.

## Verification

- Changed Python files compile successfully under Python 3.9.6.
- Focused WR-112 type-contract test: 1 passed.
- Complete session tests: 5 passed.
- Complete `tests/backtest` suite: 158 passed.
- Deterministic project regression excluding four pre-existing live
  Telegram scripts: 1435 passed, 1 environment warning.
