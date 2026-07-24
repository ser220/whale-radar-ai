# WR-117 Report — Decision Application Default Repository State Consistency Boundary

## Scope

Corrected the confirmed default repository split in
`DecisionApplicationService`.

## Production change

When both constructor dependencies are omitted:

- Create one `DecisionRepository`.
- Pass it to the default `DecisionGovernance`.
- Pass it to the default `DecisionQueryService`.

Explicitly injected dependencies retain their existing behavior.

## Test

One focused regression test:

- Creates a default `DecisionApplicationService`.
- Injects it into `SimulationDecisionAdapter`.
- Creates a decision through the adapter.
- Retrieves the decision through the same application service.
- Requires the retrieved response to be present and equal to the created
  response.

## Boundaries

No simulation production code, public signature, annotation, runtime
validation, persistent storage, dependency-selection redesign, or unrelated
behavior was changed.

## Verification

- Python 3.9 `py_compile`: passed.
- Focused WR-117 test: 1 passed, 2 deselected.
- Decision suite: 37 passed.
- Simulation suite: 14 passed.
- Backtest suite: 158 passed.
- Deterministic project regression: 1441 passed, 1 unrelated
  `urllib3` LibreSSL warning.
- `git diff --check`: passed.
