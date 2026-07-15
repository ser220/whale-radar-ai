# PS-4 Step 5 — Market Situation Expectation Engine Report

## Result

Implemented a deterministic, process-local Expectation Engine that creates
immutable, unevaluated hypotheses from the latest entry of a Market Situation
Timeline. No approved Early Bird, Emerging, Identity, Evolution, or Timeline
formula or contract was changed.

## Expectation model

`SituationExpectation` preserves:

- exact expectation, timeline, timeline-version, source-entry, and asset
  identity;
- UTC creation and evaluation-window timestamps;
- expectation kind and descriptive strength;
- subject and description;
- explicit measured basis;
- explicit fulfillment and contradiction criteria;
- source stage;
- immutable snapshots of all eight factor values and availability states;
- policy version, rule name, source-entry timestamp, and generation semantics.

The model has no evaluation status, outcome, direction, recommendation, or
execution fields. Terminal formatting displays `NOT EVALUATED` as presentation
text only.

## Rules implemented

1. Volume confirmation from material measured structure and weak measured
   volume.
2. Momentum confirmation from material measured structure/volume and weak
   measured momentum.
3. Persistence for strong measured whale, funding, structure, or volume facts.
4. Conservative Funding Divergence appearance after strong measured structure
   and volume, only when funding is `MISSING`.
5. One-step stage advance from SEED to EMERGING or EMERGING to BUILDING.
6. Stage persistence fallback when advance conditions are not met.
7. Descriptive invalidation risk for high maturity, low horizon, concentrated
   measured support, or weakening measured confirmation.

Unavailable values are never treated as weak measurements. Missing whale input
does not generate whale appearance. `UNSUPPORTED` or `ERROR` funding does not
generate appearance.

## Window policy

- default: 60 minutes for confirmation and stage persistence;
- short: 30 minutes for factor persistence and invalidation risk;
- long: 120 minutes for factor appearance and stage advance.

The evaluation window begins at creation. The model enforces
`created_at <= window_start <= window_end`.

## Ordering and identity

Default IDs derive from timeline ID, exact timeline version, rule name, and
subject. Expectations sort by fixed rule order, then subject, then ID. The
maximum of five is applied after sorting. Duplicate generated IDs are rejected.

## Anti-hindsight guarantees

- Generation consumes only the latest entry from one exact Timeline version.
- Default creation time is that Timeline's immutable `updated_at`.
- Creation before the source entry is rejected.
- Source values, availability, entry ID, stage, and policy version are copied.
- Future observations cannot mutate the expectation.
- Policy changes cannot rewrite the stored policy version or structured
  payload.
- Generation and future evaluation are separate responsibilities.
- Step 5 performs no evaluation and stores no evaluation result.

## Live sanitized demo

Command:

```bash
./venv/bin/python run_situation_expectation_demo.py --limit 5 --timeframe 15m
```

Captured at `2026-07-15T16:25:34.132408+00:00`:

| Asset | Expectations | Kinds |
|---|---:|---|
| PEPE | 1 | Stage persistence |
| SUI | 3 | Momentum confirmation, stage persistence, invalidation risk |
| ETH | 2 | Stage persistence, invalidation risk |
| SOL | 4 | Volume confirmation, momentum confirmation, stage persistence, invalidation risk |
| BNB | 4 | Volume confirmation, momentum confirmation, stage persistence, invalidation risk |

Total generated: 14. Assets without valid expectations: none. Every rendered
hypothesis showed `NOT EVALUATED`. No outcome, profitability, prediction
accuracy, or trade claim was made.

## Files changed

- `app/intelligence/timeline/expectations.py`
- `app/intelligence/timeline/__init__.py` (exports only)
- `run_situation_expectation_demo.py`
- `test_situation_expectations.py`
- `docs/architecture/adr/ADR-PS-4-expectation-engine.md`
- `docs/specs/PS-4-expectation-engine.md`
- `docs/reports/PS-4_STEP_5_REPORT.md`

## Verification

- Python 3.9 compile: passed.
- Focused Expectation tests: 40 passed.
- Complete specified unit suite: 490 passed, including the 40 focused tests.
- Safe smoke tests: `test_core.py`, `test_filter.py`, `test_parser.py` passed.
- Runtime dependency audit: passed.
- `git diff --check`: passed.

## Production impact

- Production pipeline changed: **NO**
- Production decisions changed: **NO**
- Telegram changed: **NO**
- Hostinger changed: **NO**
- Deployment: **NO**
- Persistence/database/disk writes: **NONE**
- Expectation evaluation: **NOT IMPLEMENTED**
- Learning: **NOT IMPLEMENTED**
- Third-party dependencies added: **NONE**

## Open questions

1. A separately reviewed evaluator must define how later Timeline entries are
   matched to fulfillment and contradiction criteria without hindsight.
2. Persistence, retention, concurrency, and historical policy registries remain
   future architecture work.
3. Future product review should decide whether simultaneous confirmation and
   invalidation-risk hypotheses need UI grouping; the structured hypotheses are
   intentionally independent.
4. Policy threshold changes require a new policy version and must not rewrite
   version 1 expectations.
