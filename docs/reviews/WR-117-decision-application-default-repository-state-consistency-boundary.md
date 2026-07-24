# WR-117 — Decision Application Default Repository State Consistency Boundary

## Summary

`DecisionApplicationService` now gives its two default collaborators one
shared in-memory `DecisionRepository`.

## Confirmed root cause

The default constructor previously created `DecisionGovernance()` and
`DecisionQueryService()` independently. Each collaborator consequently
created its own repository. `create_decision()` saved through the governance
repository, while `get_decision()` queried a different, empty repository.

## Corrected default behavior

When both constructor dependencies are omitted, the application service
creates exactly one repository and passes it to both default collaborators.
A decision created through the default command boundary can therefore be
retrieved through the default query boundary of the same service.

## Compatibility

Explicitly injected governance and query dependencies keep their previous
selection behavior. Public constructor and method signatures, annotations,
simulation production code, decision construction, and response mapping are
unchanged.

## Regression coverage

The focused simulation-to-decision test injects a default application service
into `SimulationDecisionAdapter`, creates a decision through the adapter, and
requires the same service to retrieve an equal response.

## Excluded scope

- Dependency-injection redesign
- Partial-injection state-sharing policy
- Runtime dependency validation
- Persistent repositories
- Simulation decision policy
- Public API or annotation changes
