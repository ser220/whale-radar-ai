# WR-116 Report — Decision Query Service Python 3.9 Optional Repository Type Contract

## Scope

Corrected one Python 3.9-incompatible public constructor annotation.
The audit stopped after confirming this first valid issue.

## Implementation

- Import `Optional` from `typing`.
- Replace `DecisionRepository | None` with
  `Optional[DecisionRepository]`.
- Preserve the repository parameter and its `None` default.

## Test

- Resolve constructor annotations with `typing.get_type_hints()`.
- Require the repository hint to resolve to
  `Optional[DecisionRepository]`.
- Require the repository default to remain `None`.
- Require the return hint to remain `NoneType`.

## Boundaries

No runtime logic, dependency selection, runtime validation, query
behavior, dependency, public API, or other annotation change was
introduced.

## Verification

- Python 3.9 `py_compile`: passed.
- Focused WR-116 test: 1 passed.
- Decision suite: 37 passed.
- Simulation suite: 13 passed.
- Backtest suite: 158 passed.
- Deterministic project regression: 1440 passed, 1 unrelated
  `urllib3` LibreSSL warning.
