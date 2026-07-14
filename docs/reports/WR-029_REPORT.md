# WR-029 Shadow Intelligence Layer Report

## Status

Implemented on `wr-029-shadow-intelligence-layer`; pending Architecture Review.
The layer is isolated and is not integrated into production.

## Objective

Provide an in-memory shadow boundary where already-produced immutable
`ExpertOpinion` values can be collected and evaluated by the existing
`MarketStateEngine` before any production integration is authorized.

## Architecture

```text
Expert Adapter
    -> ExpertOpinion
    -> ShadowIntelligenceEngine
    -> MarketStateEngine
    -> MarketState
```

`ShadowIntelligenceEngine` is a thin collector and coordinator. It does not
create, interpret, weight by default, or modify opinions. `MarketStateEngine`
remains the only synthesis authority.

The collector:

- accepts only `ExpertOpinion` objects;
- retains the original immutable objects in deterministic registration order;
- rejects duplicate `expert_name` values without replacing prior input;
- returns a tuple snapshot from `get_opinions()`;
- delegates empty, single-expert and multi-expert evaluation to
  `MarketStateEngine.synthesize()`;
- optionally forwards explicit weights and an evaluation timestamp without
  owning their validation or synthesis semantics.

## Legacy integration

The first demonstrated source is the WR-028 `LegacyIntelligenceAdapter`:

```text
already-produced legacy output
    -> LegacyIntelligenceAdapter
    -> ExpertOpinion(expert_name="legacy_intelligence")
    -> ShadowIntelligenceEngine
```

The adapter is invoked by the caller, not by the shadow layer. The shadow
package does not import legacy modules or the Legacy Adapter and therefore does
not create opinions or couple synthesis to v20 implementation details.

## Public API

```python
from app.intelligence.shadow import ShadowIntelligenceEngine

shadow = ShadowIntelligenceEngine()
shadow.add_opinion(opinion)
opinions = shadow.get_opinions()
market_state = shadow.evaluate()
```

`ShadowIntelligenceEngine` may receive an existing `MarketStateEngine` through
its constructor. `evaluate()` also accepts the same optional `weights` and
timezone-aware `timestamp` controls used by `MarketStateEngine.synthesize()`.

## Files created

- `app/intelligence/shadow/__init__.py`
- `app/intelligence/shadow/shadow_engine.py`
- `test_shadow_intelligence.py`
- `docs/reports/WR-029_REPORT.md`

## Files modified

None.

## Dependency boundaries

Runtime imports are limited to the Python standard library, intelligence
contracts and `MarketStateEngine`. The shadow package does not import Telegram,
FastAPI, database or repository modules, production pipeline code, legacy
engines, adapters, providers, exchange APIs or networking.

No third-party dependency is added.

## Production safety

- Production pipeline changed: **NO**
- Adapter integrated into production: **NO**
- Telegram changed: **NO**
- Database/schema changed: **NO**
- Hostinger changed/deployed: **NO**
- External provider connected: **NO**
- External dependency added: **NO**

## Validation and duplicate policy

`add_opinion()` rejects non-`ExpertOpinion` objects with `TypeError`. A second
opinion with the same exact `expert_name` is rejected with `ValueError`; the
original remains registered. Replacement is intentionally absent because a
shadow evaluation must not silently erase expert provenance.

The underlying immutable contract validates opinion contents. The existing
MarketStateEngine validates weights, timestamps and synthesis input, including
empty-input behavior.

## Verification

```bash
PYTHONPYCACHEPREFIX=/tmp/whale_radar_pycache ./venv/bin/python -m py_compile \
  app/intelligence/shadow/__init__.py \
  app/intelligence/shadow/shadow_engine.py \
  test_shadow_intelligence.py

./venv/bin/python -m unittest -v test_shadow_intelligence.py
./venv/bin/python -m unittest -v test_intelligence_contracts.py
./venv/bin/python -m unittest -v test_market_state_engine.py
./venv/bin/python -m unittest -v test_legacy_adapter.py
./venv/bin/python test_core.py
./venv/bin/python test_filter.py
./venv/bin/python test_parser.py
```

Also inspect imports, the complete branch diff, unrelated untracked files and
`git diff --check` before commit.

Results:

- compile check: passed;
- `test_shadow_intelligence.py`: 10 tests passed;
- `test_intelligence_contracts.py`: 14 tests passed;
- `test_market_state_engine.py`: 30 tests passed;
- `test_legacy_adapter.py`: 11 tests passed;
- `test_core.py`, `test_filter.py`, `test_parser.py`: passed;
- shadow runtime dependency inspection: passed;
- no live service, Telegram send, provider call or database test was run.

## Architecture deviations

None. Legacy Adapter use is demonstrated at the caller boundary rather than
embedded in the shadow layer, as required by the rule that the layer does not
create opinions.

## Open questions

1. Should future shadow runs accept a named evaluation/session identifier for
   audit correlation without adding persistence to this layer?
2. What reviewed policy should set the legacy opinion weight when domain
   Experts are evaluated alongside it?
3. Which external orchestration boundary may persist shadow inputs and outputs
   after repository/Hostinger parity and data-governance work are complete?
4. What evaluation period and comparison metrics are required before any
   production-facing integration can be proposed?

No production integration, deployment or external connection is authorized by
WR-029.
