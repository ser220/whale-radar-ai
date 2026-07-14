# WR-033 Intelligence Correlation Layer Report

## Status

Implemented on `wr-033-intelligence-correlation-layer`; pending Architecture
Review. The contract is isolated and not integrated into production.

## Objective

Create an immutable relationship boundary that explicitly records when fast,
observation and expert artifacts may describe the same underlying market event.
The boundary makes shared provenance visible so future Decision Intelligence
can avoid treating correlated evidence as independent confirmation.

## Architecture

```text
FastObservation references
    + normalized Observation references
    + ExpertOpinion source names
    -> EventCorrelation
    -> future Decision Intelligence
```

WR-033 implements only the `EventCorrelation` contract. It does not implement a
correlator service, inference engine, confidence adjustment, Decision Layer,
signal, alert or production integration.

## Public API

```python
from app.intelligence.correlation import EventCorrelation
```

Fields:

- `correlation_id: str`;
- `created_at: datetime`;
- `asset: str`;
- `time_window: Tuple[datetime, datetime]` (`start`, `end`);
- `related_fast_events: Tuple[str, ...]` containing FastObservation event IDs;
- `related_observations: Tuple[str, ...]` containing normalized observation IDs;
- `related_experts: Tuple[str, ...]` containing expert names;
- `correlation_score: float` (0–100);
- `independence_score: float` (0–100);
- immutable `metadata`.

The model provides `to_dict()` and `from_dict()`. Timestamps are serialized as
ISO-8601 UTC values, and `time_window` is serialized with explicit `start` and
`end` fields.

## Relationship semantics

`correlation_score` is the caller's reviewed assessment that the references
describe the same underlying event. `independence_score` is the caller's
reviewed assessment of how much independent evidence remains after shared
sources or event lineage are considered. Neither score is calculated by the
model or automatically applied to confidence.

A high correlation score and low independence score can tell future Decision
Intelligence not to count a FastObservation and a downstream Trend opinion as
two independent confirmations when both originate from the same structure
break. The relationship does not change either source artifact.

## Deterministic boundary

The model accepts explicit identifiers only:

- fast `event_id` values;
- observation IDs;
- expert names, because current `ExpertOpinion` has no opinion ID;
- one asset and one compatible time window;
- optional frozen metadata for explicit shared event references and correlation
  basis.

It does not accept artifact objects, inspect timestamps, compare assets, search
metadata, infer relationships, deduplicate across providers or calculate
scores. Those responsibilities require a separately reviewed future
orchestration layer. Tests demonstrate extracting stable references from real
`FastObservation` and `ExpertOpinion` values at the caller boundary.

Duplicate references inside a collection are rejected instead of silently
deduplicated, because silent cleanup could hide false double-counting input.

## Validation behavior

- correlation ID and asset are required non-empty strings;
- asset is normalized to uppercase;
- `created_at`, window start and window end must be timezone-aware and are
  normalized to UTC;
- window start must not be after window end;
- correlation and independence scores must be finite real values in the
  inclusive 0–100 range; booleans are rejected;
- related collections accept non-empty string references, preserve order,
  become tuples and reject duplicates;
- metadata must be a mapping and is recursively frozen;
- serialization restores timestamps, collections, scores and metadata without
  loss.

Empty related collections are allowed so a correlation record can be assembled
incrementally by a future immutable replacement workflow; this model itself
remains frozen. All three collections and both scores must be supplied
explicitly; the contract does not invent a default relationship assessment.

## Dependency boundaries

The runtime correlation package imports only Python standard-library modules.
It does not import FastObservation, Observation, ExpertOpinion,
MarketStateEngine, ShadowIntelligenceEngine, Experts, Telegram, FastAPI,
databases, repositories, production pipeline code, exchanges, providers,
networking or adapters.

No third-party dependency is added.

## Files created

- `app/intelligence/correlation/__init__.py`;
- `app/intelligence/correlation/models.py`;
- `test_intelligence_correlation.py`;
- `docs/reports/WR-033_REPORT.md`.

## Files modified

None.

## Production safety

- Production pipeline changed: **NO**
- Telegram changed: **NO**
- Hostinger changed/deployed: **NO**
- Trading signals created: **NO**
- Execution logic created: **NO**
- ExpertOpinion modified: **NO**
- Market direction calculated: **NO**
- External data/provider connected: **NO**
- Dependency added: **NO**

## Verification

```bash
PYTHONPYCACHEPREFIX=/tmp/whale_radar_pycache ./venv/bin/python -m py_compile \
  app/intelligence/correlation/__init__.py \
  app/intelligence/correlation/models.py \
  test_intelligence_correlation.py

./venv/bin/python -m unittest -v test_intelligence_correlation.py
./venv/bin/python -m unittest -v test_fast_intelligence.py
./venv/bin/python -m unittest -v test_shadow_intelligence.py
./venv/bin/python -m unittest -v test_legacy_adapter.py
./venv/bin/python -m unittest -v test_trend_adapter.py
./venv/bin/python -m unittest -v test_intelligence_contracts.py
./venv/bin/python -m unittest -v test_market_state_engine.py
./venv/bin/python test_core.py
./venv/bin/python test_filter.py
./venv/bin/python test_parser.py
```

Also inspect runtime imports, the complete branch diff, unrelated untracked
files and `git diff --check` before commit.

Results:

- Python 3.9 compile check: passed;
- `test_intelligence_correlation.py`: 12 tests passed;
- `test_fast_intelligence.py`: 12 tests passed;
- `test_shadow_intelligence.py`: 10 tests passed;
- `test_legacy_adapter.py`: 11 tests passed;
- `test_trend_adapter.py`: 10 tests passed;
- `test_intelligence_contracts.py`: 14 tests passed;
- `test_market_state_engine.py`: 30 tests passed;
- `test_core.py`, `test_filter.py`, `test_parser.py`: passed;
- correlation runtime dependency inspection: passed;
- no live service, Telegram send, provider call or database test was run.

## Architecture deviations

None. The requested `time_window` is represented as an immutable ordered pair
of UTC datetimes. Related collections store stable string references rather
than artifact objects, preserving isolation and serializability.

## Open questions

1. Which future component owns deterministic `correlation_id` generation and
   immutable replacement/versioning?
2. Should `ExpertOpinion` later receive a stable opinion ID so correlations can
   reference an individual opinion instead of only its expert name?
3. Which deterministic policy calculates correlation and independence scores,
   and how will it be calibrated before affecting Decision Intelligence?
4. Which event types may share lineage across fast and deep paths, and which
   must remain independent despite temporal proximity?
5. Should future typed correlation-basis fields replace generic metadata?

No merge, production integration, deployment, automatic inference or
subsequent WR task is authorized by WR-033.
