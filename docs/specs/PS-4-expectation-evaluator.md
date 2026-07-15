# PS-4 Step 6 — Market Situation Expectation Evaluator Specification

## Objective and scope

Compare one immutable `SituationExpectation` with later entries in the same
immutable `MarketSituationTimeline` and return a deterministic evaluation.
Scope includes models, enums, policy, seven structural rule handlers,
window/coverage semantics, unexpected events, formatters, read-only demo,
tests, and documentation.

Out of scope: generation-rule changes, production/Telegram integration, trade
decisions, persistence, learning, calibration, providers, deployment, and
rewriting Timeline history.

## Public API

- `ExpectationEvaluationStatus`
- `RealityGapType`
- frozen `ExpectationEvaluationPolicy`
- frozen `SituationExpectationEvaluation`
- `SituationExpectationEvaluator.evaluate()`
- `deterministic_evaluation_id()`
- `format_expectation_evaluation()` and `format_expectation_evaluations()`

## Status semantics

- `PENDING`: window open and no conclusive structural evidence.
- `FULFILLED`: measured evidence satisfies fulfillment.
- `MISSING`: closed window with sufficient measured coverage proving
  non-occurrence.
- `CONTRADICTED`: measured evidence satisfies contradiction.
- `EXPIRED`: closed window without enough measurable evidence.
- `INDETERMINATE`: conflicting evidence or an unusable historical contract
  when later evidence exists.

Reality gaps are `NONE`, `MISSING_EXPECTED_EVENT`, `UNEXPECTED_EVENT`,
`CONTRADICTORY_EVENT`, `BOTH`, and `UNKNOWN`.

## Validation and serialization

IDs, reason, and asset are required; asset normalizes uppercase. Versions are
integers at least 1 and evaluated version cannot regress. Booleans are rejected
as numbers. Timestamps are timezone-aware UTC and window end cannot precede
start. Surprise is 0..100. Collections are ordered, duplicate-free tuples;
snapshots and metadata are deeply frozen. `to_dict()`/`from_dict()` round-trip
enums, timestamps, collections, and mappings. No trade, direction, execution,
or profit-probability fields exist.

## Input and evidence window

Timeline ID/asset must match, Timeline version cannot precede source version,
and the exact source entry/snapshot must remain present. Evidence uses only
entries after the source entry, within `window_start..window_end`, and no later
than `evaluated_at`. Entries after evaluation or window close are ignored.
Open windows remain `PENDING` unless fulfillment/contradiction is conclusive.

## Authoritative evaluation contract

Contract version `"1"` stores common identity/version/window fields and exact
rule parameters. Later policy changes cannot affect old expectations. Missing
or incomplete contract never falls back to current defaults: while open it is
`PENDING`; after close it is `INDETERMINATE` with later evidence and `EXPIRED`
without evidence. Descriptive text is never parsed.

## Rule evaluators

1. Volume confirmation: AVAILABLE volume meeting threshold fulfills; measured
   non-attainment may be missing; unavailable volume expires; stored
   structure/maturity deterioration contradicts.
2. Momentum confirmation: equivalent measured momentum rules; collapse of all
   stored initiating factors contradicts.
3. Factor persistence: adequately measured continued strength fulfills;
   measured collapse contradicts; unavailable evidence expires.
4. Factor appearance: MISSING-to-AVAILABLE fulfills; repeated explicit MISSING
   can prove non-occurrence; ERROR/STALE/UNSUPPORTED expires.
5. Stage advance: exact next stage fulfills; stored incompatible stage,
   including unrecorded two-stage jump, contradicts; sufficient unchanged stage
   is missing after close.
6. Stage persistence: required stage through sufficient later entries fulfills;
   stage change contradicts; no evidence expires after close.
7. Invalidation risk: EXHAUSTED, high-maturity/low-horizon, or stored support
   contraction fulfills; measured emergence/horizon/support strengthening
   contradicts. It is not a price prediction.

Simultaneous fulfillment and contradiction is `INDETERMINATE`.

## Coverage and unavailable evidence

Confirmation coverage is measured target entries divided by eligible later
entries and must meet the stored minimum (default 0.60) for `MISSING`.
Persistence, appearance, and stage rules use stored minimum later-entry counts.
Unavailable evidence reduces coverage; it does not become measured zero.

## Unexpected events

Policy version 1 reports: unrelated MISSING factor appearance; stage movement
greater than one lifecycle step; strong initiating factor becoming unavailable;
Emergence dropping at least 20 while Horizon remains at least 60; and maturity
rising at least 35 without fulfillment. Events are sorted and deduplicated.

## Surprise Score formula

Let `U = min(20, 10 * unexpected_event_count)`:

- `PENDING = 0`
- `FULFILLED = U`
- `MISSING = min(100, 50 + 20 * (1 - coverage_ratio) + U)`
- `CONTRADICTED = min(100, 70 + 0.20 * contradiction_severity + U)`
- `EXPIRED = min(100, 25 + U)`
- `INDETERMINATE = min(100, 40 + 0.20 * max(contradiction_severity, 50) + U)`

Surprise means departure from the structured expectation, not volatility,
profitability, direction, or trade risk.

## Acceptance criteria

All seven handlers/statuses are deterministic; provider absence never becomes
`MISSING`; historical contract absence never invokes current defaults; inputs
remain unchanged; source snapshot is preserved; formatter has no trade advice;
demo is import-safe/read-only; Python 3.9 compile, focused/full regressions,
dependency/scope audits, and safe smoke tests pass.

## Verification commands

```bash
PYTHONPYCACHEPREFIX=/tmp/whale_radar_pycache ./venv/bin/python -m py_compile \
  app/intelligence/timeline/expectations.py \
  app/intelligence/timeline/expectation_evaluation.py \
  app/intelligence/timeline/__init__.py \
  run_expectation_evaluation_demo.py \
  test_situation_expectations.py test_expectation_evaluation.py

./venv/bin/python -m unittest -v test_expectation_evaluation.py
./venv/bin/python -m unittest -v test_situation_expectations.py
./venv/bin/python -m unittest discover -v
./venv/bin/python test_core.py
./venv/bin/python test_filter.py
./venv/bin/python test_parser.py
./venv/bin/python run_expectation_evaluation_demo.py --limit 5 --interval-seconds 60
```
