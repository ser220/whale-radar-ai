# WR-036 — Early Bird Foundation, Phase 1 Specification

## Objective

Create a pure deterministic Opportunity Hunter that evaluates normalized facts
for multiple assets and returns ranked, explainable attention assessments
without producing direction, recommendations, trades, or execution advice.

## Inputs

### EarlyBirdCandidate

Required fields:

- identity/provenance: `candidate_id`, uppercase-normalized `asset`, UTC
  `observed_at`, and `source`;
- reliability: `quality` and `data_completeness_score`;
- opportunity facts: `whale_activity_score`,
  `open_interest_change_score`, `funding_divergence_score`,
  `volume_expansion_score`, `relative_strength_score`,
  `liquidity_event_score`, `structure_event_score`, and
  `momentum_shift_score`;
- recency: `freshness_score`;
- stable references: `fast_event_ids`, `observation_ids`;
- immutable serializable `metadata`.

All scores are inclusive `0..100`. The model has no direction,
recommendation, or trade field. Missing providers are represented in
completeness/metadata and are never converted to a signed conclusion.

## Outputs

### EarlyBirdAssessment

Required fields:

- identity: `assessment_id`, `candidate_id`, `asset`, UTC `evaluated_at`;
- axes: `opportunity_score`, `priority_score`, `maturity_score`, `quality`;
- optional positive integer `rank`;
- deterministic `reasons`, `warnings`, immutable `factor_contributions`;
- `source_event_ids`, `source_observation_ids`;
- immutable serializable `metadata`.

The deterministic assessment ID is
`early-bird:{candidate_id}:v{policy_version}`. It is a stable domain reference,
not a persistence key guarantee. Assessment quality is the arithmetic mean of
candidate quality and completeness.

## Public API

```python
EarlyBirdCandidate
EarlyBirdAssessment
EarlyBirdFactor
EarlyBirdPolicy
EarlyBirdEngine.evaluate_candidate(candidate, *, timestamp=None)
EarlyBirdEngine.rank_candidates(candidates, *, limit=None, timestamp=None)
```

The engine accepts list, tuple, generator, or another iterable. Empty input
returns `()`. Duplicate candidate IDs fail. Distinct IDs for the same asset are
allowed and independently ranked, supporting future distinct event windows or
timeframes.

## Exact Opportunity formula

Let each factor score be in `0..100`:

```text
raw_opportunity =
    0.25 * whale_activity
  + 0.15 * open_interest_change
  + 0.10 * funding_divergence
  + 0.15 * volume_expansion
  + 0.15 * relative_strength
  + 0.10 * liquidity_event
  + 0.05 * structure_event
  + 0.05 * momentum_shift

reliability_factor = sqrt((quality / 100) * (completeness / 100))

opportunity_score = clamp(raw_opportunity * reliability_factor, 0, 100)
```

Low quality and incomplete data reduce the magnitude without adding positive,
negative, bullish, or bearish meaning.

## Exact Priority formula

```text
event_urgency =
    0.50 * whale_activity
  + 0.30 * liquidity_event
  + 0.20 * structure_event

effective_quality = (quality + completeness) / 2

priority_score =
    0.45 * opportunity_score
  + 0.25 * freshness
  + 0.20 * event_urgency
  + 0.10 * effective_quality
```

Priority is analysis urgency only. It is not readiness or execution priority.

## Exact Maturity formula

```text
freshness_age = 100 - freshness
age_proxy = freshness_age

if metadata explicitly contains overextension_score:
    validate overextension_score in 0..100
    age_proxy = (freshness_age + overextension_score) / 2

maturity_score =
    0.30 * structure_event
  + 0.25 * momentum_shift
  + 0.20 * volume_expansion
  + 0.15 * open_interest_change
  + 0.10 * age_proxy
```

Maturity is observable development progress. It is not trade readiness,
correction completion, probability of profit, confidence, or market-cycle
maturity. Overextension is never inferred; it is used only when explicitly
supplied as a normalized metadata value.

All engine scores are clamped to `0..100` and rounded to six decimal places.

## Policy defaults and exact thresholds

- `minimum_quality_threshold = 50`;
- `minimum_completeness_threshold = 60`;
- `stale_freshness_threshold = 30`;
- `over_mature_threshold = 85`;
- `material_factor_threshold = 35`;
- `independent_factor_threshold = 35`;
- `dominant_factor_share_threshold = 0.70`;
- `minimum_independent_factors = 2`;
- `reason_limit = 5`;
- `warning_limit = 7`;
- `maximum_results = 20`;
- `policy_version = 1`.

All factor/component weights are frozen policy fields. Each weight group must
sum to `1` within absolute tolerance `1e-9`. Thresholds and limits are
validated; booleans are rejected.

Thresholds generate explanations or warnings. Phase 1 does not exclude a
candidate for low quality, incompleteness, staleness, or maturity.

## Ranking

Assessments sort stably by:

1. priority descending;
2. opportunity descending;
3. maturity ascending;
4. asset ascending;
5. candidate ID ascending.

Maturity favors earlier cases only after equal priority and opportunity. The
engine evaluates a batch at one shared timestamp, applies `maximum_results`,
then assigns contiguous ranks starting at `1`. Explicit limits below the policy
maximum are honored; higher limits are capped. A limit must be an integer at
least `1`, with booleans rejected.

## Reasons

Factors with score at least `35` are material. They sort by weighted raw
contribution descending and factor name as a deterministic tie-break. Up to
five human-readable reasons are returned. The strongest whale contribution
uses:

> Unusual whale activity is the strongest opportunity factor.

Other fixed messages explain OI participation, funding divergence, volume,
relative strength, liquidity, structure, and momentum. When Maturity and
structure are below `35`, an early-development explanation is appended when
the reason limit permits it. No Telegram markup or recommendation language is
used.

## Warnings

Warnings are emitted in this fixed order and capped by `warning_limit`:

1. quality below `50`;
2. completeness below `60`;
3. freshness below `30`;
4. maturity at least `85`;
5. the largest raw weighted contribution is at least `70%` of non-zero raw
   opportunity;
6. whale activity equals zero;
7. fewer than two factors score at least `35`.

Warnings are explanatory and do not automatically exclude candidates.

## Factor contributions

`factor_contributions` maps each `EarlyBirdFactor` value to:

```text
score
weight
weighted_contribution = score * weight
```

Assessment metadata records raw opportunity, reliability factor, event
urgency, effective quality, candidate source, policy version, and the optional
explicit overextension value.

## Validation

- Models and policy are frozen dataclasses.
- Required strings are trimmed and non-empty; assets normalize uppercase.
- All score values are finite real numbers in `0..100`; booleans fail.
- Rank and integer policy limits are at least `1`; booleans fail.
- Naive timestamps fail; aware timestamps normalize to UTC.
- Stable reference collections preserve order and reject duplicates, sets, and
  non-string values.
- Metadata and contribution mappings require string keys, serializable
  primitives, finite numeric values, and recursively frozen collections.
- Raw providers, artifact objects, direction, recommendation, and trade fields
  are not accepted.

## Serialization

Both contracts implement `to_dict()` and `from_dict()`. UTC times serialize as
ISO-8601; tuples serialize as lists; immutable mappings become dictionaries;
enums use public values. Deserialization validates and freezes values again. A
same-type round trip preserves value equality and deterministic ordering.

## Dependency boundaries

The runtime package may import only the Python standard library and local
`app.intelligence.early_bird` modules. It must not import providers, exchanges,
Telegram, FastAPI, databases, repositories, the production pipeline, Experts,
MarketStateEngine, ShadowIntelligenceEngine, MarketSituation objects,
networking, pandas, numpy, or TA libraries.

## MarketSituation compatibility

WR-036 creates and persists no MarketSituation. Assessment IDs and source
artifact IDs are stable references a future reviewed orchestrator may attach
to a replacement MarketSituation version. No automatic embedding or database
write occurs.

## Acceptance criteria

- All specified contracts, policy defaults, formulas, ranking, reasons,
  warnings, exports, documentation, and tests exist.
- Python 3.9 compilation and focused tests pass.
- MarketSituation, Fast, Correlation, Shadow, contracts, MarketState, and safe
  smoke regressions pass.
- Import audit confirms standard-library/local-only runtime dependencies.
- Complete diff contains no production pipeline, Telegram, database, API,
  requirements, Hostinger, deployment, secret, or unrelated change.

## Verification commands

```bash
PYTHONPYCACHEPREFIX=/tmp/whale_radar_pycache ./venv/bin/python -m py_compile \
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

rg '^(from|import) ' app/intelligence/early_bird --glob '*.py'
git diff --check
git status --short
```
