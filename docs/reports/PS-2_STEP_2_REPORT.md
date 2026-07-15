# PS-2 Step 2 — Early Bird Factor Availability Contract Report

## Status

Implemented on `ps-2-factor-availability-contract` from `origin/main` at
`6ea65de`. This change is awaiting Architecture Review and is not merged or
deployed.

## Objective

Add an immutable, provider-neutral contract that distinguishes a measured
Early Bird factor from unavailable input. The contract prevents `MISSING`,
`STALE`, `UNSUPPORTED`, and `ERROR` from silently becoming a meaningful zero
score.

## Public API

Exported through `app.intelligence.early_bird`:

- `FactorAvailability`
  - `AVAILABLE`
  - `MISSING`
  - `STALE`
  - `UNSUPPORTED`
  - `ERROR`
- `EarlyBirdFactorValue`

`EarlyBirdFactorValue` fields:

- `factor_name: str`
- `availability: FactorAvailability`
- `score: Optional[float]`
- `observed_at: Optional[datetime]`
- `source: Optional[str]`
- `quality: Optional[float]`
- `reason: Optional[str]`
- `metadata: Mapping[str, Any]`

## Validation and semantics

- `factor_name` is required and normalized by trimming whitespace.
- `AVAILABLE` requires a score, aware timestamp, and non-empty source.
- Scores and optional quality values are finite numbers in `0..100`;
  booleans are rejected.
- Every non-`AVAILABLE` state rejects a supplied score, including `0`.
- Non-available values may preserve source, timestamp, quality, reason, and
  metadata as provenance without treating stale or failed data as a usable
  measurement.
- Aware timestamps normalize to UTC; naive timestamps are rejected.
- The frozen dataclass and recursively frozen metadata provide defensive
  immutability.
- `to_dict()` and `from_dict()` preserve enum and timestamp semantics.
- The contract contains no direction, trade, recommendation, or execution
  field.

## Integration boundary

`EarlyBirdCandidate`, `EarlyBirdEngine`, policy, scoring, production decisions,
and provider paths are unchanged. A future separately reviewed candidate
builder will consume a collection of `EarlyBirdFactorValue` objects and:

- use scores only from `AVAILABLE` values;
- compute completeness from the approved supported/expected factor set;
- preserve provenance and explicit availability warnings;
- never silently fill an unavailable factor with zero.

The future integration still needs an explicit decision on how the current
numeric-only `EarlyBirdCandidate` represents or receives the availability
mask. This task does not make that integration choice.

## Files

Created:

- `app/intelligence/early_bird/availability.py`
- `test_early_bird_availability.py`
- `docs/reports/PS-2_STEP_2_REPORT.md`

Modified:

- `app/intelligence/early_bird/__init__.py`

## Dependency boundary

The runtime file imports only Python standard-library modules and validation/
serialization helpers from the local Early Bird models module. It imports no
provider, exchange client, Telegram, FastAPI, database, repository, pipeline,
Expert, MarketStateEngine, or networking module. No dependency or requirements
file changed, and no third-party dependency was added.

## Verification

Environment: Python 3.9.6.

Commands:

```bash
PYTHONPYCACHEPREFIX=/tmp/whale_radar_pycache ./venv/bin/python -m py_compile \
  app/intelligence/early_bird/__init__.py \
  app/intelligence/early_bird/availability.py \
  app/intelligence/early_bird/enums.py \
  app/intelligence/early_bird/models.py \
  app/intelligence/early_bird/policy.py \
  app/intelligence/early_bird/engine.py \
  test_early_bird_availability.py \
  test_early_bird.py

./venv/bin/python -m unittest -v test_early_bird_availability.py
./venv/bin/python -m unittest -v test_early_bird.py
./venv/bin/python -m unittest -v test_market_situation.py
./venv/bin/python -m unittest -v test_fast_intelligence.py
./venv/bin/python -m unittest -v test_intelligence_correlation.py
./venv/bin/python -m unittest -v test_shadow_intelligence.py
./venv/bin/python -m unittest -v test_intelligence_contracts.py
./venv/bin/python -m unittest -v test_market_state_engine.py

./venv/bin/python test_core.py
./venv/bin/python test_filter.py
./venv/bin/python test_parser.py

git diff --check
```

Results:

- Python 3.9 compilation: passed.
- Availability contract: 26 passed.
- Existing Early Bird: 61 passed.
- MarketSituation: 34 passed.
- Fast Intelligence: 12 passed.
- Correlation: 12 passed.
- Shadow Intelligence: 10 passed.
- Intelligence contracts: 14 passed.
- MarketStateEngine: 30 passed.
- Safe core/filter/parser smoke checks: passed.
- Dependency-boundary AST audit: passed.
- `git diff --check`: passed.

## Production safety

- Production pipeline changed: **NO**
- Production decision logic changed: **NO**
- Telegram/API/database/repository changed: **NO**
- Live providers or networking added/called: **NO**
- Hostinger changed or deployed: **NO**
- Requirements changed: **NO**
- Third-party dependency added: **NO**
- Full candidate builder implemented: **NO**

## Architecture deviations

None. Non-`AVAILABLE` scores are rejected rather than conditionally accepted
because no justified exception exists in this phase and strict rejection best
preserves the approved semantics.

## Open questions

1. Should the future candidate integration extend `EarlyBirdCandidate` with a
   first-class availability mapping, or keep availability in a separate
   builder result passed alongside it?
2. Which factors belong in the completeness denominator for a specific asset
   when a factor is structurally `UNSUPPORTED`?
3. Should `STALE` quality be retained for provenance only or excluded entirely
   from future aggregate data-quality calculations?
