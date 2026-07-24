# WR-115 Report — Simulation Decision Adapter Python 3.9 Optional Service Type Contract

## Scope

Corrected one Python 3.9-incompatible public constructor annotation.

## Implementation

- Import `Optional` from `typing`.
- Replace `DecisionApplicationService | None` with
  `Optional[DecisionApplicationService]`.
- Preserve the application service parameter and its `None` default.

## Test

- Resolve constructor annotations with `typing.get_type_hints()`.
- Require the application service hint to resolve to
  `Optional[DecisionApplicationService]`.
- Require the application service default to remain `None`.
- Require the return hint to remain `NoneType`.

## Boundaries

No runtime logic, dependency selection, runtime validation, decision
behavior, dependency, public import, or other annotation change was
introduced.

## Verification

- Python 3.9 `py_compile`: passed.
- Focused WR-115 test: 1 passed, 1 deselected.
- Simulation tests: 13 passed.
- Backtest tests: 158 passed.
- Deterministic project regression: 1439 passed, 1 unrelated
  `urllib3` LibreSSL warning.
