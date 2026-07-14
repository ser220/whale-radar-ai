# WR-028 Legacy Intelligence Adapter Report

## Status

Implemented on `wr-028-legacy-intelligence-adapter`; pending Architecture
Review. The adapter is isolated and is not integrated into production.

## Objective

Represent one already-produced v20 legacy intelligence result as one immutable
`ExpertOpinion`. The legacy system becomes a contributor that can later be
weighted by MarketStateEngine, not a source of truth or a replacement decision
engine.

## Audit findings

`app.engine.intelligence.explain_event()` is the cleanest existing boundary. It
returns one aggregate dictionary after legacy analysis and includes structured
raw blocks alongside presentation text:

| Legacy output field | Producing source | Adapter use |
| --- | --- | --- |
| `probability_raw` | `app.engine.probability_engine` | direction fallback, opinion score fallback, reason |
| `ai_decision_raw` | `app.engine.decision_engine` | primary decision confidence, recommendation, summary, invalidations |
| `market_regime_raw` | `app.engine.market_regime` | canonical state fallback, risk, reason |
| `meta_decision_raw` | `app.engine.meta_decision` | preferred aggregate opinion score |
| `self_confidence_raw` | `app.engine.self_confidence` | preferred confidence/trust value |
| `pattern_confidence_raw` | `app.engine.pattern_confidence` | provenance only in Phase 1 |
| `summary`, `action` | `app.engine.intelligence` | reason and recommendation fallbacks |
| `source_consensus`, `campaign`, `event_memory`, wallet/context fields | their named legacy engines | evidence-reference keys; raw presentation text is not copied into metadata |

The legacy aggregate does not contain a canonical data-quality metric. The
adapter therefore accepts an explicit `quality`, then
`snapshot_quality.overall`, and otherwise uses a documented five-part
recognized-field completeness score. This measures adapter input completeness,
not market truth.

The task requested `reasoning`, but the approved `ExpertOpinion` contract has
`reasons` and `warnings`. The adapter uses those existing fields and stores
evidence-reference names in metadata. The contract was not changed.

## Mapping policy

- `expert_name`: fixed `legacy_intelligence`.
- `direction`: explicit legacy direction, then bullish/bearish probabilities,
  then accumulation/distribution regime, otherwise `NEUTRAL` with warning.
- `state`: explicit canonical state, then regime/bias mapping, otherwise
  `UNKNOWN` with warning.
- `score`: meta final score, dominant probability, AI confidence, then self
  confidence.
- `confidence`: self-confidence trust, AI decision confidence, meta score, then
  dominant probability.
- `quality`: explicit quality, snapshot overall quality, then completeness.
- `reasons`: structured summary, decision summary, regime message, probability
  summary and recommendation.
- `warnings`: invalid/missing fields, clamping and legacy invalidations.
- `metadata`: legacy version, exact source modules represented, generated time,
  recommendation, risk, evidence-reference keys, quality basis and normalized
  probability values.

Legacy values are defensively normalized and clamped to `0–100` before the
strict immutable contract is created. Time must be timezone-aware and is
normalized to UTC. Supplying a timestamp makes output fully deterministic.

## Files created

- `app/intelligence/adapters/__init__.py`
- `app/intelligence/adapters/legacy_adapter.py`
- `test_legacy_adapter.py`
- `docs/reports/WR-028_REPORT.md`

## Files modified

None.

## Dependency boundaries

The adapter imports only Python standard library modules and
`app.intelligence.contracts`. It does not import Telegram, FastAPI, database,
repositories, pipeline, legacy engines, providers, exchange APIs, adapters or
network clients. It performs no I/O and no database write.

## Production safety

- Production pipeline changed: **NO**
- Legacy logic changed/refactored: **NO**
- Telegram changed: **NO**
- Database/schema changed: **NO**
- Hostinger changed/deployed: **NO**
- External dependency added: **NO**
- MarketStateEngine changed: **NO**
- Adapter registered or called by production: **NO**

## Verification

Required before commit:

```bash
PYTHONPYCACHEPREFIX=/tmp/whale_radar_pycache ./venv/bin/python -m py_compile \
  app/intelligence/adapters/__init__.py \
  app/intelligence/adapters/legacy_adapter.py \
  test_legacy_adapter.py

./venv/bin/python -m unittest -v test_legacy_adapter.py
./venv/bin/python -m unittest -v test_intelligence_contracts.py
./venv/bin/python -m unittest -v test_market_state_engine.py
./venv/bin/python test_core.py
./venv/bin/python test_filter.py
./venv/bin/python test_parser.py
```

Also inspect imports, branch diff, unrelated files, `git diff --check`, and
confirm no production pipeline or Telegram file is changed.

Results:

- compile check: passed;
- `test_legacy_adapter.py`: 11 tests passed;
- `test_intelligence_contracts.py`: 14 tests passed;
- `test_market_state_engine.py`: 30 tests passed;
- `test_core.py`, `test_filter.py`, `test_parser.py`: passed;
- no live service, Telegram send, provider call or database test was run.

## Architecture deviations

- `reasoning` maps to existing `ExpertOpinion.reasons`; no new contract field.
- Evidence references are metadata field names, not new Evidence contracts.
- Quality has an explicit fallback formula because v20 does not emit canonical
  source quality.
- No production integration is included, as required.

## Open questions

1. Which caller should later package `score_data.direction` with the aggregate
   `explain_event()` output without changing the legacy function?
2. Should shadow integration assign a configured weight below 1.0 to the broad
   legacy opinion to avoid double-counting future domain Experts?
3. Should a future normalized legacy-output contract replace the current
   mapping boundary after repository/Hostinger parity is restored?
4. What observation period and disagreement thresholds are required before the
   adapter may participate in any production-facing MarketState?

No integration or deployment is authorized by WR-028.
