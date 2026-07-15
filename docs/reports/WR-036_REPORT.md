# WR-036 Early Bird Foundation Report

## Status

Implemented on `wr-036-early-bird-foundation`; pending Architecture Review.
No merge, production integration, or deployment is included.

## Base

- `origin/main` at `af579b6`;
- Python 3.9.6;
- existing standard-library `unittest` framework;
- no new or changed dependency.

## Candidate model

`EarlyBirdCandidate` is an immutable provider-neutral input containing asset,
time, source, quality, eight opportunity factor magnitudes, freshness,
completeness, stable Fast/Observation IDs, and serializable metadata. All
scores are `0..100`, timestamps normalize to UTC, assets normalize uppercase,
and mutable input is defensively frozen.

There is no direction, recommendation, signal, or trade field. Missing source
data is represented through completeness and metadata.

## Assessment model

`EarlyBirdAssessment` is an immutable explainable output containing stable
identity, Opportunity, Priority, Maturity, effective quality, optional rank,
deterministic reasons/warnings, factor contributions, source references, and
scoring metadata. It supports lossless dictionary round trips and contains no
trade or execution semantics.

## Opportunity formula

Raw factor weights: whale `25%`, OI `15%`, funding `10%`, volume `15%`,
relative strength `15%`, liquidity `10%`, structure `5%`, momentum `5%`.

```text
reliability = sqrt((quality / 100) * (completeness / 100))
opportunity = raw_weighted_opportunity * reliability
```

This degrades unreliable/incomplete inputs without adding signed meaning.

## Priority formula

Event urgency is `50%` whale, `30%` liquidity, `20%` structure. Effective
quality is the mean of quality and completeness.

```text
priority = 45% opportunity + 25% freshness
         + 20% event urgency + 10% effective quality
```

Priority means urgency for deeper analysis only.

## Maturity formula

```text
maturity = 30% structure + 25% momentum + 20% volume
         + 15% OI + 10% age_proxy
```

Age is `100 - freshness`. If normalized metadata explicitly includes a valid
`overextension_score`, age proxy is their mean. Maturity is development
progress, not trade readiness, correction completion, profit probability,
confidence, or market-cycle maturity.

## Ranking

Deterministic order is priority descending, opportunity descending, maturity
ascending, asset, and candidate ID. Ranks are assigned after sorting and result
limiting. List, tuple, and generator inputs are supported; duplicate candidate
IDs fail; distinct IDs for the same asset are allowed.

## Files created

- `app/intelligence/early_bird/__init__.py`
- `app/intelligence/early_bird/enums.py`
- `app/intelligence/early_bird/models.py`
- `app/intelligence/early_bird/policy.py`
- `app/intelligence/early_bird/engine.py`
- `app/intelligence/early_bird/README.md`
- `test_early_bird.py`
- `docs/architecture/adr/ADR-WR-036-early-bird-foundation.md`
- `docs/specs/WR-036-early-bird-foundation.md`
- `docs/reports/WR-036_REPORT.md`

## Architecture deviations

None. Additional policy thresholds for material factors, independent-factor
counting, and dominance are explicit because the required deterministic reason
and warning behavior needs exact values. They remain frozen and documented.

## Production safety

- Production pipeline changed: **NO**
- Telegram/API/database changed: **NO**
- Hostinger changed/deployed: **NO**
- Requirements changed: **NO**
- External provider/network connected: **NO**
- Third-party dependency added: **NO**
- MarketSituation created or persisted: **NO**
- Trading direction or instruction added: **NO**

## Verification

Commands executed with `PYTHONPYCACHEPREFIX=/tmp/whale_radar_pycache` where
applicable:

```bash
./venv/bin/python -m py_compile \
  app/intelligence/early_bird/__init__.py \
  app/intelligence/early_bird/enums.py \
  app/intelligence/early_bird/models.py \
  app/intelligence/early_bird/policy.py \
  app/intelligence/early_bird/engine.py \
  test_early_bird.py

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
```

Results:

- Python 3.9 compile: passed;
- Early Bird focused suite: 61 passed;
- MarketSituation regression: 34 passed;
- Fast Intelligence regression: 12 passed;
- Correlation regression: 12 passed;
- Shadow Intelligence regression: 10 passed;
- intelligence contracts regression: 14 passed;
- MarketStateEngine regression: 30 passed;
- safe `test_core.py`, `test_filter.py`, and `test_parser.py`: passed;
- dependency-boundary AST/import audit: passed;
- no live network, provider, Telegram send, database mutation, or deployment
  command was run.

## Open questions

1. Which future normalized builder owns candidate IDs, deduplication windows,
   and per-provider completeness accounting?
2. Should future multi-timeframe candidates expose timeframe as a first-class
   contract field rather than metadata?
3. How will outcome review calibrate policy weights without turning Early Bird
   into a directional predictor?
4. Which future MarketSituation timeline event references an Early Bird
   assessment?
5. How should a future read-only UI group multiple candidate IDs for the same
   asset and explain event windows?

## Next action

Complete verification, commit and push the feature branch, then await
Architecture Review. Do not merge or begin another WR task automatically.
