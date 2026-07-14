# WR-035 — Market Situation Runtime, Phase 1 Specification

## Objective

Define immutable, serializable, infrastructure-free runtime contracts that keep
one market story identifiable and auditable across its explicit lifecycle,
artifact references, confidence changes, expectations, health, outcome, and
future learning.

## Scope

- Add `app.intelligence.situations`.
- Define all WR-035 enums and four frozen dataclasses.
- Validate required values, ordering, uniqueness, percentages, and UTC time.
- Deep-freeze mutable collections.
- Provide lossless `to_dict()` / `from_dict()` round trips.
- Export the public API and document its use and boundaries.
- Add focused standard-library `unittest` coverage.

## Out of scope

Situation repositories or tables, automatic lifecycle/health/confidence logic,
merge/split behavior, deterministic situation ID policy, Early Bird, event
producers, outcome collection, expectation evaluation, similarity, Market DNA,
learning, Decision Stability, Telegram/API presentation, production
integration, and deployment are excluded.

## Enums

- `SituationStage`: `DETECTED`, `OBSERVED`, `ANALYZED`, `CORRELATED`,
  `DECISION_SUPPORT`, `OUTCOME`, `LEARNING`, `MEMORY`.
- `SituationHealth`: `HEALTHY`, `WEAKENING`, `CONTRADICTED`, `INVALIDATED`,
  `UNKNOWN`.
- `TimelineEventType`: `DETECTION`, `OBSERVATION_ATTACHED`,
  `EXPERT_OPINION_ATTACHED`, `CORRELATION_ATTACHED`,
  `MARKET_STATE_ATTACHED`, `DECISION_CONTEXT_ATTACHED`,
  `EXPECTATION_CREATED`, `EXPECTATION_UPDATED`, `EXPECTATION_FULFILLED`,
  `EXPECTATION_MISSING`, `EXPECTATION_CONTRADICTED`, `EXPECTATION_EXPIRED`,
  `HEALTH_CHANGED`, `OUTCOME_RECORDED`, `LEARNING_RECORDED`, `MEMORY_STORED`.
- `ExpectationStatus`: `PENDING`, `FULFILLED`, `MISSING`, `CONTRADICTED`,
  `EXPIRED`, `CANCELLED`.
- `ExpectationViolationType`: `NONE`, `UNEXPECTED_EVENT`,
  `MISSING_EXPECTED_EVENT`, `BOTH`, `UNKNOWN`.

All enums inherit from `str` and `Enum` and serialize by value.

## SituationTimelineEntry

Fields:

- `entry_id: str`;
- `event_type: TimelineEventType`;
- `occurred_at: datetime`;
- `summary: str`;
- `artifact_ids: tuple[str, ...]`;
- `metadata: Mapping[str, Any]`.

ID and summary are trimmed and required. Artifact IDs are ordered string
references; duplicate and unordered inputs are rejected. Raw artifacts are not
accepted. The model records a supplied fact and performs no interpretation.

## ConfidencePoint

Fields:

- `recorded_at: datetime`;
- `value: float` in `0..100`;
- `source: str`;
- `reason: str`;
- `metadata: Mapping[str, Any]`.

Source and reason are required. The value is historical system confidence, not
trade readiness, a recommendation, or execution authorization.

## ExpectationRecord

Fields:

- `expectation_id: str`;
- `created_at`, `window_start`, `window_end: datetime`;
- `description: str`;
- `basis_artifact_ids: tuple[str, ...]`;
- `status: ExpectationStatus`;
- `expected_event_type: str`;
- `observed_event_ids: tuple[str, ...]`;
- `violation_type: ExpectationViolationType`;
- `gap_severity: float` in `0..100`;
- `learning_conclusion: Optional[str]`;
- `metadata: Mapping[str, Any]`.

`window_start <= window_end`, and `created_at <= window_end`. A non-empty
expectation claim requires at least one unique basis artifact ID. Observed event
IDs are references only. The expected event and basis are immutable once the
record exists; a later evaluation belongs in a later situation version.

No status/violation is inferred. A `PENDING` expectation may have zero gap
severity. Missing input data is not the same as `ExpectationStatus.MISSING`.
The caller explicitly supplies whether the structural answer represents:

- what happened that should not have happened (`UNEXPECTED_EVENT`);
- what did not happen that should have happened (`MISSING_EXPECTED_EVENT`);
- both (`BOTH`);
- neither or not yet known (`NONE` / `UNKNOWN`).

## MarketSituation

Fields:

- identity/time: `situation_id`, `asset`, `created_at`, `updated_at`;
- explicit state: `stage`, `health`, `version`;
- artifact references: `fast_event_ids`, `observation_ids`,
  `expert_opinion_ids`, `expert_names`, `correlation_ids`, `market_state_ids`,
  `decision_context_ids`, `outcome_ids`, `learning_record_ids`,
  `memory_reference_ids`;
- histories: `timeline`, `confidence_history`, `expectation_history`;
- extension data: `metadata`.

The situation ID and asset are required; asset is trimmed and uppercase.
Version must be an integer at least `1`, and booleans are rejected.
`updated_at >= created_at`.

All reference collections are ordered tuples of unique, non-empty strings.
Duplicate IDs are rejected rather than silently removed. Timeline entries must
be non-decreasing by `occurred_at` and have unique `entry_id` values.
Confidence points must be non-decreasing by `recorded_at`. Expectations must be
ordered by `(created_at, expectation_id)` and have unique IDs, providing a
deterministic tie-break for equal timestamps.

Only nested contract instances are accepted in histories; serialized mappings
are converted by `from_dict()`. No raw artifact object is embedded. Stage,
health, confidence, and expectation outcomes are always explicit inputs.

## Common validation

- All models are frozen dataclasses.
- Required strings are trimmed and reject blank or non-string values.
- All timestamps reject naive/non-datetime values and normalize aware values
  to `timezone.utc`.
- Percentage-like values are finite real numbers in inclusive `0..100`;
  booleans are rejected.
- Metadata must be a mapping with string keys and is recursively copied and
  frozen. Mapping keys are sorted; list/tuple values become tuples; set values
  become deterministically ordered tuples.
- Ordered reference/history inputs reject sets and invalid element types.
- Models do not calculate market interpretation or trade/execution semantics.

## Serialization

Every model supports `to_dict()` and `from_dict()`:

- enums become public string values and are restored;
- timestamps become UTC ISO-8601 strings and accept aware datetime or ISO input;
- tuples become lists and are restored to immutable tuples;
- frozen metadata becomes plain dictionaries/lists and is frozen again;
- nested history entries serialize through their own public methods;
- a same-type round trip preserves value equality, ordering, enums, and time.

## Versioning

`MarketSituation` is append-oriented and immutable. Phase 1 uses explicit
constructor-only replacement:

1. retain the same `situation_id`;
2. carry all prior history and references forward;
3. add explicitly supplied new records/references;
4. set `version` to the intended later value and supply `updated_at`;
5. construct a new object, leaving the previous version unchanged.

Late evidence creates a new version rather than rewriting prior knowledge.
There are no append helpers, repository, orchestrator, cross-version sequence
checks, deletion behavior, or concurrency policy in WR-035.

## Timeline semantics

Timeline entries describe explicit historical facts using an event type,
timestamp, summary, and artifact references. They do not contain raw artifacts
or infer direction, lifecycle transitions, health, confidence, or outcomes.
New entries are preserved in replacement versions.

## Confidence history semantics

Confidence points record how supplied system confidence changed, including its
source and reason. Ordering is chronological. Confidence does not block early
detection, authorize execution, override production recommendations, or act as
Decision Stability.

## Dependency boundaries

The package may import only Python standard-library modules and its own
`app.intelligence.situations` modules. It must not import FastObservation,
Observation types, ExpertOpinion, EventCorrelation, MarketState, Telegram,
FastAPI, APIs, databases, repositories, providers, source adapters, pipelines,
external services, networking, or third-party dependencies.

## Public API

Exported by `app.intelligence.situations`:

- `SituationStage`, `SituationHealth`, `TimelineEventType`;
- `ExpectationStatus`, `ExpectationViolationType`;
- `SituationTimelineEntry`, `ConfidencePoint`, `ExpectationRecord`;
- `MarketSituation`.

## Acceptance criteria

- All specified files, enums, models, exports, validation, and documentation
  exist and compile under the repository's Python 3.9.6.
- Focused tests cover creation, immutability, UTC, bounds, ordering,
  duplicates, deep freezing, structural expectation gaps, serialization,
  absence of automatic calculations, and dependency isolation.
- Existing fast, shadow, contracts, MarketState, and safe smoke checks pass.
- Correlation tests run only if the correlation feature is present in the
  `origin/main` baseline.
- Complete branch diff contains no production pipeline, Telegram, database,
  API, requirements, Hostinger, dependency, secret, or unrelated file change.

## Verification commands

```bash
PYTHONPYCACHEPREFIX=/tmp/whale_radar_pycache ./venv/bin/python -m py_compile \
  app/intelligence/situations/__init__.py \
  app/intelligence/situations/enums.py \
  app/intelligence/situations/models.py \
  test_market_situation.py

./venv/bin/python -m unittest -v test_market_situation.py
./venv/bin/python -m unittest -v test_fast_intelligence.py
./venv/bin/python -m unittest -v test_shadow_intelligence.py
./venv/bin/python -m unittest -v test_intelligence_contracts.py
./venv/bin/python -m unittest -v test_market_state_engine.py
./venv/bin/python test_core.py
./venv/bin/python test_filter.py
./venv/bin/python test_parser.py

rg '^from |^import ' app/intelligence/situations
git diff --check
git diff --name-status origin/main...HEAD
git status --short
```

`test_intelligence_correlation.py` is conditional because WR-033 is not merged
in the WR-035 baseline `c2028c1`.
