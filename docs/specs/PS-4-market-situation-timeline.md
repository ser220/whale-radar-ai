# PS-4 Step 1: Market Situation Timeline Specification

## Objective

Provide immutable, append-only, in-memory domain contracts that preserve the
lifecycle history of one Market Situation exactly as understood at each point
in time.

## Scope

- `SituationDNA` point-in-time normalized factor snapshot.
- `MarketSituationTimelineEntry` lifecycle and expectation fact record.
- `MarketSituationTimeline` ordered immutable history version.
- `append_timeline_entry()` pure replacement operation.
- deterministic dictionary serialization and deserialization.

## Public API

Exported by `app.intelligence.timeline`:

- `SituationDNA`
- `MarketSituationTimelineEntry`
- `MarketSituationTimeline`
- `append_timeline_entry`

The `stage` and `current_stage` fields use the public Early Bird
`EmergingStage`: `UNKNOWN`, `SEED`, `EMERGING`, `BUILDING`, `MATURE`, and
`EXHAUSTED`.

## Fields and validation

### SituationDNA

Optional 0–100 factors: `whale_activity`, `funding_divergence`,
`volume_expansion`, `structure_event`, `momentum_shift`, `relative_strength`,
`open_interest_change`, and `liquidity_event`. `None` means unavailable; `0.0`
means a measured zero.

Required 0–100 values: `completeness`, `quality`, `freshness`, `opportunity`,
`priority`, `maturity`, `emergence`, `horizon`, and `detection_confidence`.
Booleans and non-finite numbers are rejected. `factor_availability` requires a
string-to-string mapping. Metadata and availability are defensively copied and
deeply frozen. Mapping keys serialize deterministically.

### MarketSituationTimelineEntry

Required fields: `entry_id`, `timeline_id`, UTC-aware `created_at`,
`EmergingStage stage`, `SituationDNA dna`, ordered unique string tuples for
supporting/limiting factors and all four expectation collections, and a
non-empty `transition_reason`. Source assessment, candidate, and situation IDs
are optional but must be non-empty strings when present. Metadata is deeply
frozen. Stage correctness and progression are not evaluated.

### MarketSituationTimeline

Required fields: `timeline_id`, normalized uppercase `asset`, UTC-aware
`created_at` and `updated_at`, ordered entries, `EmergingStage current_stage`,
integer `version >= 1`, and immutable metadata. `updated_at` cannot precede
creation or the final entry. Entry timeline IDs must match, entry IDs must be
unique, and entry timestamps must be non-decreasing. A non-empty timeline uses
the last entry stage. An empty timeline is allowed only with `UNKNOWN`.

## Append and versioning semantics

`append_timeline_entry(timeline, entry, updated_at=...)`:

- accepts only the timeline and entry domain types;
- requires matching timeline IDs and a unique entry ID;
- rejects an entry older than the last entry or timeline creation;
- requires UTC-aware `updated_at >= entry.created_at`;
- returns a new timeline with exactly one appended entry;
- preserves the timeline identity, asset, creation time, metadata, and all
  previous entries;
- increments version by exactly one;
- sets current stage from the new entry;
- performs no stage inference, persistence, orchestration, or side effect.

## Expectation semantics

Expected, observed, missing expected, and unexpected events are independent,
explicit facts. Empty observed events do not imply missing expected events.
Timeline never evaluates expectations or invents explanations after an outcome.

## Serialization

Every model provides `to_dict()` and `from_dict()`. Round-trip preserves UTC
datetimes, `EmergingStage`, `None` versus numeric zero, complete DNA, ordered
immutable collections, deeply immutable metadata, and full entry history.

## Dependency boundaries

Allowed: Python standard library, public Early Bird `EmergingStage`, and local
timeline modules. Forbidden: providers, exchanges, Telegram, FastAPI, database,
repositories, production pipeline, Decision Engine, Trade Readiness,
MarketStateEngine, Experts, scanners, and networking. No third-party dependency
is added.

## Out of scope

Persistence, files, repositories, caches, scheduling, discovery, automatic
transitions, `MarketSituation` modification, outcome evaluation, learning,
similarity, DNA comparison, Telegram, deployment, and production integration.

## Acceptance criteria

- frozen dataclasses and immutable nested collections;
- every specified validation and append invariant is tested;
- expectation categories stay distinct;
- no trade, direction, outcome, or execution fields;
- Python 3.9 compatibility and standard-library-only runtime;
- focused and existing safe regressions pass;
- no production, Telegram, database, API, repository, requirements, deployment,
  or Hostinger changes.

## Verification commands

```bash
PYTHONPYCACHEPREFIX=/tmp/whale_radar_pycache ./venv/bin/python -m py_compile \
  app/intelligence/timeline/__init__.py \
  app/intelligence/timeline/models.py \
  app/intelligence/timeline/timeline.py \
  test_market_timeline.py

./venv/bin/python -m unittest -v test_market_timeline.py
./venv/bin/python -m unittest -v test_emerging_situation.py
./venv/bin/python -m unittest -v test_early_bird_explainability.py
./venv/bin/python -m unittest -v test_early_bird_candle_factors.py
./venv/bin/python -m unittest -v test_early_bird_scanner.py
./venv/bin/python -m unittest -v test_early_bird_candidate_builder.py
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
