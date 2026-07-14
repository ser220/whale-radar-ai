# WR-026A — Observation Contracts

## Status

Implementation and local verification complete on the dedicated feature
branch. Architecture Review is required before merge.

## Summary

Added a pure immutable Observation Contracts layer for normalized trend,
momentum, structure, funding, open-interest, and liquidity facts. The layer is
additive and has no production integration, builder, Expert, or WR-026B work.

## Architecture documents

- [ADR-WR-026A](../architecture/adr/ADR-WR-026A-observation-contracts.md)
- [WR-026A specification](../specs/WR-026A-observation-contracts.md)

## Repository baseline

- Branch base: `origin/main` at `3162fb2`
- Repository version: `v0.6-intelligence-foundation`
- Python: 3.9.6
- Test framework: standard-library `unittest` plus safe legacy smoke scripts
- WR-024.5 contracts and WR-025 Market State Engine are present on main.
- Pre-existing `docs/chat_archive/` is untracked, preserved, and excluded.

## Files created

- `app/intelligence/observations/__init__.py`
- `app/intelligence/observations/base.py`
- `app/intelligence/observations/enums.py`
- `app/intelligence/observations/trend.py`
- `app/intelligence/observations/momentum.py`
- `app/intelligence/observations/structure.py`
- `app/intelligence/observations/funding.py`
- `app/intelligence/observations/open_interest.py`
- `app/intelligence/observations/liquidity.py`
- `app/intelligence/observations/README.md`
- `test_observation_contracts.py`
- `docs/architecture/adr/ADR-WR-026A-observation-contracts.md`
- `docs/specs/WR-026A-observation-contracts.md`
- `docs/reports/WR-026A_REPORT.md`

## Files modified

None. Existing intelligence and production modules are unchanged.

## Public API

- Abstract `Observation`
- `StructureBreak`, `TrendBias`, `FundingBias`, `LiquiditySide`, `DataTrend`
- `TrendObservation`, `MomentumObservation`, `StructureObservation`
- `FundingObservation`, `OpenInterestObservation`, `LiquidityObservation`

## Validation behavior

Common identifiers are trimmed and required; asset is uppercased. Version is an
integer at least one. Quality is `0..100`. Timestamps must be aware and normalize
to UTC. Metadata is recursively frozen. All numeric fields reject booleans, NaN,
infinities, and values outside their documented ranges. Structure price ordering
and positive-price invariants are enforced. Contradictory trend flags remain
valid facts and are intentionally not interpreted.

## Serialization behavior

Each concrete observation has `to_dict()` and `from_dict()`. Public dictionaries
contain enum strings, ISO-8601 UTC timestamps, ordinary metadata containers,
the preserved version, and a stable `observation_type`. Per-type loaders reject
mismatched type identifiers and restore immutable value equality.

## Versioning behavior

Version defaults to `1`, rejects values below one, round-trips unchanged, and
does not trigger migration. Future builders and Experts must explicitly support
the versions they exchange.

## Dependency audit

The package uses only Python standard-library modules and internal observation
modules. It does not import infrastructure or other intelligence layers. No
dependency is added to `requirements.txt`.

## Architecture deviations

None. The approved small file layout is used exactly. The common base is
abstract rather than a dataclass so Python 3.9 concrete dataclasses can expose
required schema fields while retaining `version=1`; all concrete values are
frozen dataclasses. No optional top-level `app.intelligence` re-export is added.

## Commands executed

```text
git status --short
git branch --show-current
git remote -v
git log -10 --oneline
git fetch origin
git rev-parse origin/main
git describe --tags --always
./venv/bin/python --version
PYTHONPYCACHEPREFIX=/tmp/whale_radar_pycache ./venv/bin/python -m py_compile ...
./venv/bin/python -m unittest -v test_observation_contracts.py
./venv/bin/python -m unittest -v test_intelligence_contracts.py
./venv/bin/python -m unittest -v test_market_state_engine.py
./venv/bin/python test_core.py
./venv/bin/python test_filter.py
./venv/bin/python test_parser.py
rg -n '^(from|import) ' app/intelligence/observations
git diff --check
git diff --stat origin/main...HEAD
git diff --name-status origin/main...HEAD
git log --oneline origin/main..HEAD
git status --short
```

## Test results

- Python 3.9 compile check: PASS
- Observation contract tests: 46/46 PASS
- WR-024.5 contract regression tests: 14/14 PASS
- WR-025 Market State regression tests: 30/30 PASS
- Safe scorer smoke script: PASS
- Safe filter smoke script: PASS
- Safe parser smoke script: PASS
- Live Telegram/network tests: intentionally excluded

## Production pipeline impact

None. Existing pipeline, Telegram, storage/database, sources, services, and API
files are not modified and do not import the observation package.

## Git information

- Branch: `wr-026a-observation-contracts`
- Commit: recorded after successful verification
- Push: recorded after the feature branch is pushed

## Full branch diff stat

Recorded after the verified commit.

## Full branch file list

Recorded after the verified commit.

## Branch commits

Recorded after the verified commit.

## Breaking changes

None.

## Open questions

No blocking questions. Version consumption policy, builders, multi-timeframe
relationships, and concrete Expert semantics remain deliberately deferred.

## Recommended next step

Architecture Review of the pushed WR-026A feature branch. Do not merge or begin
WR-026B without explicit approval.
