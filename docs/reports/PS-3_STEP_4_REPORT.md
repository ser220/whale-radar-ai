# PS-3 Step 4 — Emerging Situation Engine Report

## Status

Implemented on `ps-3-emerging-situation` from `origin/main` at `0e8423a`.
The layer is deterministic, descriptive, provider-neutral, not merged, and not
deployed. It does not affect Telegram, production decisions, Opportunity,
Priority, Maturity, Early Bird weights, learning, persistence, or execution.

The branch consumes only the merged Step 3 contracts and does not include or
depend on the unmerged PS-3 Step 2 funding branch.

## Public API

`app/intelligence/early_bird/emerging.py` adds:

- `EmergingStage`;
- immutable `EmergingSituation`;
- `EmergingSituationEngine.evaluate()`;
- `format_emerging_situation()`.

The names are exported through `app.intelligence.early_bird`.

## Input boundary

The engine consumes only:

- `EarlyBirdAssessment`;
- `EarlyBirdCandidateBuildResult`;
- `EarlyBirdExplanation`.

It verifies matching asset, candidate ID, assessment ID, Opportunity, Priority,
and Maturity values. Input objects are never mutated. With no explicit
timestamp, the output uses the source assessment's UTC evaluation time, making
identical input deterministic.

The engine calls no scanner, provider, exchange, funding hub, Telegram,
MarketStateEngine, Expert, database, repository, persistence, or network path.

## Model

`EmergingSituation` is a frozen dataclass with:

- normalized uppercase asset and timezone-aware UTC evaluation timestamp;
- bounded Emergence, Horizon, and Detection Confidence scores;
- descriptive `EmergingStage`;
- immutable supporting and limiting factors;
- explicit missing, stale, unsupported, and error groups;
- deterministic reasons and warnings;
- stable assessment and candidate source IDs;
- deeply immutable metadata;
- primitive `to_dict()` / `from_dict()` round trip.

It has no direction, recommendation, signal, trade readiness, entry, target,
stop, execution, or probability-of-profit field.

## Emergence formula

Emergence asks how strongly measured evidence describes a situation that is
forming. Only `AVAILABLE` values can enter the calculation. Structural zero
placeholders for non-available factors are ignored.

First calculate normalized measured strength from:

| Factor | Phase 1 weight |
|---|---:|
| Whale Activity | 25% |
| Funding Divergence | 20% |
| Volume Expansion | 20% |
| Structure Event | 20% |
| Momentum Shift | 15% |

```text
fresh_factor_strength =
    sum(available factor score × factor weight)
    / sum(weights of available emergence factors)
```

An emergence factor is materially active at raw score `>= 25`.

```text
active emergence factor count:
0 -> independence 0
1 -> independence 25
2 -> independence 50
3 -> independence 75
4 or 5 -> independence 100
```

```text
emergence_score =
    55% fresh_factor_strength
  + 20% existing assessment Opportunity
  + 15% existing candidate Freshness
  + 10% emergence independence proxy
```

The score is bounded to `0..100`. If none of the five emergence factors is
`AVAILABLE`, Emergence is exactly zero, stage is `UNKNOWN`, and a warning is
added. Relative Strength, OI, and Liquidity can support detection confidence
or the descriptive supporting list when measured, but do not enter
fresh-factor strength.

## Horizon formula

Horizon asks how much measured development appears to remain. It is not
derived from Opportunity.

```text
horizon_score =
    50% × (100 - existing assessment Maturity)
  + 20% × existing candidate Freshness
  + 20% × early_structure_proxy
  + 10% × incomplete_confirmation_proxy
```

### Early structure proxy

When Structure Event is unavailable, the neutral descriptive proxy is `50`
and the availability limitation remains explicit. When measured:

```text
structure 0..20:
    linear 70 -> 100

structure 20..60:
    linear 100 -> 60

structure 60..100:
    linear 60 -> 0
```

This refines the suggested low-structure band into a continuous function:
initial measured structure raises horizon, moderate structure peaks, and
extreme structure lowers remaining horizon. Direction is never interpreted.

### Incomplete confirmation proxy

Initiating evidence exists when at least one measured Whale, Funding, or
Structure factor has score `>= 25`. Confirmation gaps are considered only for
measured Momentum or Volume below `40`:

```text
measured confirmation gap = (40 - score) / 40 × 100
incomplete_confirmation_proxy = mean(measured gaps)
```

If no initiating evidence exists, or confirmation factors are unavailable,
the proxy is zero. Missing data is never rewarded as early evidence.

Therefore high Opportunity plus high Maturity can produce low Horizon, while
low Opportunity plus fresh initiating evidence and low Maturity can produce
high Horizon.

## Detection Confidence formula

Detection Confidence describes reliability and completeness of the emergence
classification. It is not market confidence.

```text
detection_confidence =
    40% candidate Data Completeness
  + 30% candidate Quality
  + 20% independent factor coverage
  + 10% candidate Freshness
```

The supported expected denominator contains every canonical factor except
`UNSUPPORTED`. Missing, stale, error, weak available, and active available
factors remain in that denominator.

```text
independent factor coverage =
    count(AVAILABLE factors with score >= 25)
    / count(factors not UNSUPPORTED)
    × 100
```

Candidate Quality already aggregates only `AVAILABLE` values under the merged
builder contract, so stale quality does not contribute. The result is bounded
to `0..100`.

## Exact stage policy

Rules are evaluated in this order:

1. `UNKNOWN`
   - no available emergence factor; or
   - Detection Confidence `< 20`.
2. `EXHAUSTED`
   - Maturity `>= 85` and Horizon `< 25`; or
   - an existing over-mature warning and Horizon `< 30`.
3. `MATURE`
   - Maturity `>= 70` and Horizon `< 45`.
4. `EMERGING`
   - Emergence `>= 35`;
   - Horizon `>= 60`;
   - Maturity `< 45`.
5. `BUILDING`
   - Emergence `>= 45`;
   - Horizon `35..<60`;
   - Maturity `35..<70`.
6. `SEED`
   - Emergence `< 35`;
   - Horizon `>= 65`;
   - Maturity `< 35`.
7. Otherwise `UNKNOWN`.

The ordering removes overlap between `EMERGING` and `BUILDING`. `MATURE`
accepts Horizon below 15 as well as 15..44 when the stricter `EXHAUSTED` rule
does not apply; high maturity with little remaining horizon must not fall back
to `UNKNOWN` merely because it crossed the suggested lower Horizon boundary.

Stages are descriptive lifecycle labels only. They are not market direction,
trade readiness, correction completion, or execution state.

## Supporting and limiting factors

Supporting factors must be `AVAILABLE` and materially active (`>= 25`). They
are ordered by the existing Early Bird weighted contribution descending, with
canonical factor order as the stable tie-breaker. Non-available factors can
never appear as support.

Limiting factors may describe:

- weak measured Momentum or Volume;
- high measured Maturity;
- stale evidence;
- low supported completeness;
- low available-factor quality;
- concentration in one measured emergence factor;
- unavailable initiating evidence, with its explicit availability status.

Missing data is described as unavailable, never as measured weakness.

## Reasons and warnings

Reasons describe measured combinations, low measured Maturity, measured
Funding contribution without direction, and independent support. Warnings
preserve deduplicated Explainability warnings and add deterministic warnings
for limited detection confidence, absent emergence factors, concentration,
high maturity with low Horizon, unavailable initiating evidence, stale
evidence, and incomplete supported data.

No reason or warning contains trading or execution advice.

## Examples verified by tests

### Low Opportunity / high Horizon

Opportunity `10`, Maturity `10`, fresh initiating Structure, and measured weak
Volume/Momentum produce Horizon above `75`. Opportunity is not inverted or
used as the Horizon basis.

### High Opportunity / low Horizon

Opportunity `95`, Maturity `90`, extreme Structure, and exhausted Freshness
produce Horizon below `25`. High attention does not hide advanced maturity.

## Formatter

`format_emerging_situation()` produces plain terminal text containing scores,
stage, detection confidence, supporting factors, limiting factors, missing
factors, reasons, and warnings. It contains no Telegram markup or trade
language.

## Files

Created:

- `app/intelligence/early_bird/emerging.py`;
- `test_emerging_situation.py`;
- `docs/reports/PS-3_STEP_4_REPORT.md`.

Modified:

- `app/intelligence/early_bird/__init__.py` for public exports only.

No engine, policy, explanation, scanner, funding, production pipeline,
Telegram, database, repository, API, requirements, or Hostinger file changed.

## Verification

Python: `3.9.6`. No dependency or requirements file changed.

Commands:

```bash
PYTHONPYCACHEPREFIX=/tmp/whale_radar_pycache ./venv/bin/python -m py_compile \
  app/intelligence/early_bird/__init__.py \
  app/intelligence/early_bird/emerging.py \
  test_emerging_situation.py

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
```

Results:

- Python 3.9 compile: passed;
- Emerging Situation focused tests: 38 passed;
- Explainability regressions: 21 passed;
- candle/scanner regressions: 40 passed;
- builder/availability regressions: 66 passed;
- Early Bird foundation regressions: 61 passed;
- MarketSituation/Fast/Correlation regressions: 58 passed;
- Shadow/Contracts/MarketState regressions: 54 passed;
- total unit tests: 338 passed;
- safe core/filter/parser smoke checks: passed;
- dependency boundary: standard library plus the merged local Early Bird
  availability, builder, explanation, and models only;
- provider/network/scanner/Telegram/database/repository/MarketState/Expert
  imports: none;
- Opportunity/Priority/Maturity engine and policy changed: no;
- production pipeline changed: no;
- Hostinger changed or deployed: no.

## Open questions

1. Should future stage review add a separate `DECLINING` descriptive state, or
   is `MATURE` followed by `EXHAUSTED` sufficient?
2. Should a future observation contract provide explicit factor-specific
   freshness rather than using availability plus aggregate candidate
   freshness?
3. Should supporting-factor ordering eventually use dedicated emergence
   weights instead of the existing Opportunity contribution order?
4. Which historical review process should calibrate stage boundaries without
   adding learning or optimizing weights inside this deterministic engine?
