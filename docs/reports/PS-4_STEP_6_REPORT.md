# PS-4 Step 6 — Market Situation Expectation Evaluator Report

## Result

Implemented an immutable deterministic evaluator that compares a stored
expectation with later entries of the same append-only Timeline. Evaluation is
process-local, descriptive, availability-aware, and isolated from production,
Telegram, providers, persistence, and learning.

## Contract amendment and backward compatibility

The proven Step 5 blocker was the absence of machine-readable rule thresholds.
The approved minimal amendment adds deeply frozen
`metadata.evaluation_contract` version `"1"` to new expectations. Existing
fields, rules, formulas, windows, order, IDs, names, and policy version remain
unchanged. Historical payloads without the contract still deserialize. They
remain `PENDING` while open, then become `INDETERMINATE` with later evidence or
`EXPIRED` without evidence; current defaults are never substituted.

## Model and public API

Public exports include six statuses, six reality-gap types,
`ExpectationEvaluationPolicy`, `SituationExpectationEvaluation`,
`SituationExpectationEvaluator`, deterministic evaluation IDs, and plain-text
formatters. Evaluation records preserve immutable source snapshots, entry
provenance, UTC windows, facts, exact policy/contract versions, and Surprise.

## Seven rule semantics

1. Volume confirmation requires measured threshold attainment; measured
   non-attainment may be `MISSING`, unavailable volume is `EXPIRED`, and stored
   structure/maturity deterioration contradicts.
2. Momentum confirmation uses the same availability-aware boundary and stored
   initiating-factor contradiction rule.
3. Persistence requires sufficiently measured continued factor strength;
   measured collapse contradicts and unavailable persistence expires.
4. Appearance requires MISSING-to-AVAILABLE transition; repeated explicit
   MISSING can prove non-occurrence, while ERROR/STALE/UNSUPPORTED cannot.
5. Stage advance requires the exact next recorded stage; a two-stage jump is
   not silently accepted.
6. Stage persistence fulfills on measured continued stage and contradicts on a
   recorded change.
7. Invalidation risk evaluates stored classification weakening/strengthening
   facts and never predicts price direction.

Simultaneous fulfillment and contradiction is `INDETERMINATE`.

## MISSING versus EXPIRED

Example `MISSING`: volume was AVAILABLE and measured below 35 through at least
60% of eligible observations until window close. Example `EXPIRED`: volume was
MISSING/STALE/UNSUPPORTED/ERROR or no adequate later observation existed.
Provider coverage failure is not market failure.

## Surprise formula and unexpected events

`U = min(20, 10 * unexpected_count)`. Bases are fulfilled 0, missing
`50 + 20*(1-coverage)`, contradicted `70 + .20*severity`, expired 25,
indeterminate `40 + .20*max(severity,50)`, and pending 0; non-pending results
add `U` and cap at 100. Unexpected events are deterministic material Timeline
changes: unrelated factor appearance, stage jump, strong factor becoming
unavailable, emergence collapse with high horizon, or sharp maturity rise
without fulfillment.

## Anti-hindsight guarantees

The evaluator validates source identity/snapshot, consumes only later entries
within the historical window and evaluation cutoff, ignores post-window facts,
uses stored structured metadata as authority, never parses criteria prose,
never fetches external outcomes, and never mutates expectation, Timeline, or
prior evaluations.

## Live sanitized demo

Read-only command:

```bash
./venv/bin/python run_expectation_evaluation_demo.py \
  --assets BTC,ETH,SOL --limit 5 --timeframe 15m --interval-seconds 0
```

At `2026-07-15T17:26:42Z` and `2026-07-15T17:26:47Z`, two real scans produced
three active process-local Timelines, six expectations, and six evaluations.
The zero-second test interval avoids a blocking wait while preserving actual
scan timestamps; it fabricates neither expiration nor historical time. The
normal CLI default remains 60 seconds.

## Status distribution

`FULFILLED=3`, `PENDING=3`. The fulfilled records were early conclusive stage
persistence facts; invalidation-risk windows remained correctly pending. No
`MISSING`, `EXPIRED`, or contradiction was fabricated before window close.

## Files changed

- `app/intelligence/timeline/expectations.py`
- `app/intelligence/timeline/expectation_evaluation.py`
- `app/intelligence/timeline/__init__.py` (exports only)
- `run_expectation_evaluation_demo.py`
- `test_situation_expectations.py`
- `test_expectation_evaluation.py`
- Step 5 ADR, SPEC, and report (contract amendment only)
- Step 6 ADR, SPEC, and this report

## Verification

Focused evaluator tests: 35 passed. Amended expectation tests: 45 passed. The
explicit safe unit regression suite passed 530 tests; `test_core.py`,
`test_filter.py`, and `test_parser.py` passed. Python 3.9 compile and runtime
dependency checks passed.

An exploratory unrestricted `unittest discover` found 709 tests but retains
seven pre-existing unsafe/environment failures: six production/Telegram/storage
imports use Python 3.10 union syntax under the repository's Python 3.9 runtime,
and one Telegram module performs an import-time network send. Those modules are
outside the approved safe suite and were not changed or rerun as live tests.

## Production impact

- Production decisions/pipeline: **UNCHANGED**
- Telegram: **UNCHANGED**
- Hostinger/deployment: **UNCHANGED / NONE**
- Persistence/database/disk writes: **NONE**
- Learning/calibration: **NONE**
- Third-party dependencies: **NONE**

## Open questions

1. Persistence and retention of evaluation records require separate review.
2. Policy calibration and learning are intentionally deferred.
3. UI grouping of multiple evaluations and retention of repeated Timeline
   version evaluations require product decisions.
