# PS-3 Step 3 — Early Bird Explainability Report

## Status

Implemented on `ps-3-early-bird-explainability` from `origin/main` at
`0a54ea0`. The feature is descriptive, provider-neutral, local-only, not
merged, and not deployed. It does not alter Opportunity, Priority, Maturity,
weights, ranking, Telegram, production decisions, or execution.

The branch is intentionally independent of the unmerged PS-3 Step 2 funding
branch. When funding later becomes `AVAILABLE`, the same explanation boundary
will include it automatically from the existing assessment and availability
contracts.

## Public API

`app/intelligence/early_bird/explain.py` adds:

- immutable `EarlyBirdExplanation`;
- `EarlyBirdExplainer.explain()` for one assessment/build-result pair;
- `EarlyBirdExplainer.explain_ranked()` for contiguous ranked pairs;
- `format_explanation()` for one plain terminal explanation;
- `format_explanations()` for multiple explanations in supplied order.

These names are exported through `app.intelligence.early_bird`.

## Explanation model

`EarlyBirdExplanation` contains exactly the descriptive result domains:

- asset;
- unchanged Opportunity, Priority, and Maturity scores;
- immutable factor breakdown;
- deterministically ordered positive factors;
- missing, unsupported, and error groups;
- warnings;
- deterministic `why_ranked_here` statements;
- deterministic `why_not_higher` limitations;
- immutable provenance metadata.

The model supports primitive `to_dict()` / `from_dict()` round trips. It has no
direction, recommendation, signal, trade, entry, target, stop, or execution
field.

## Contribution model

The explainer consumes `EarlyBirdAssessment.factor_contributions` produced by
the existing engine. It does not reconstruct policy weights or calculate new
scores. For every `AVAILABLE` factor it exposes:

```text
raw_score
weight
weighted_contribution
contribution_percent
```

Contribution percentage is normalized over positive weighted contributions
from `AVAILABLE` factors only:

```text
factor weighted contribution
--------------------------------- × 100
sum of AVAILABLE weighted contributions
```

Rounding is deterministically reconciled so the total is 100 within
`0.0001` whenever positive measured contribution exists. Missing, stale,
unsupported, and error factors never appear as zero contributions. They remain
explicit availability limitations.

If all measured weighted contributions are genuinely zero, every contribution
percentage is explicitly zero and metadata sets `zero_contribution_basis`.
Assigning a fictitious 100% share in that case would misrepresent evidence, so
the mathematically undefined normalization is not fabricated.

Positive factors are ordered by weighted contribution descending, with the
canonical factor order as the stable tie-breaker.

## Why ranked here

Deterministic descriptive statements identify:

- the highest measured weighted contributor;
- material funding share when funding is actually available;
- early measured structure;
- developing measured momentum.

Statements are generated only from the supplied build result and assessment.
They contain no predictive or trading advice.

## Why not higher

Limitations identify:

- each missing factor;
- each stale factor;
- each unsupported factor;
- each factor in error;
- incomplete supported evidence;
- immature measured structure;
- weak measured momentum;
- measured factor deficits versus the asset immediately above.

The existing builder uses structural zero placeholders to preserve the legacy
candidate contract. Explainability never presents those placeholders as
measurements: availability is authoritative.

## Adjacent comparison

Comparison requires both assessment/build-result pairs and contiguous ranks.
For the current asset and the immediately higher asset, only factors marked
`AVAILABLE` in both are compared. A limitation is generated when the current
factor's weighted contribution is lower, including the exact weighted-point
deficit.

Unavailable evidence is never invented or compared. If shared measured factor
contributions do not explain the rank gap, the output explicitly says that
other existing priority inputs—freshness, urgency, quality, or deterministic
tie-breaking—may account for it. It does not claim which one without evidence.

`explain_ranked()` sorts supplied contiguous ranked pairs and automatically
uses only each immediate predecessor.

## Warning semantics

Builder and assessment warnings are deduplicated. When whale availability is
not `AVAILABLE`, the legacy engine warning saying no whale activity is present
is removed; absence of input is not presented as measured absence. The
availability warning remains visible.

## Terminal formatter

The formatter is plain text and shows:

- unchanged scores;
- measured contribution percentages and raw calculation fields;
- missing, unsupported, and error groups;
- why ranked here;
- why not higher;
- warnings.

It contains no Telegram markup and no BUY, SELL, LONG, SHORT, entry, TP, SL,
or execution wording.

## Files

Created:

- `app/intelligence/early_bird/explain.py`;
- `test_early_bird_explainability.py`;
- `docs/reports/PS-3_STEP_3_REPORT.md`.

Modified:

- `app/intelligence/early_bird/__init__.py` for public exports only.

No scanner, engine, policy, scoring formula, weight, production pipeline,
Telegram, database, repository, API, requirements, or Hostinger file changed.

## Verification

Python: `3.9.6`. No dependency or requirements file changed.

Commands:

```bash
PYTHONPYCACHEPREFIX=/tmp/whale_radar_pycache ./venv/bin/python -m py_compile \
  app/intelligence/early_bird/__init__.py \
  app/intelligence/early_bird/explain.py \
  test_early_bird_explainability.py

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
- explainability focused tests: 21 passed;
- candle/scanner regressions: 40 passed;
- builder/availability regressions: 66 passed;
- Early Bird foundation regressions: 61 passed;
- MarketSituation/Fast/Correlation regressions: 58 passed;
- Shadow/Contracts/MarketState regressions: 54 passed;
- total unit tests: 300 passed;
- safe core/filter/parser smoke checks: passed;
- dependency boundary: standard library plus local Early Bird builder/models
  only; no provider, network, Telegram, database, repository, Decision,
  MarketState, or Expert import;
- scoring engine/policy changed: no;
- production pipeline changed: no;
- Hostinger changed or deployed: no.

## Open questions

1. Should a future UI show priority component decomposition—opportunity,
   freshness, urgency, and effective quality—as a separate descriptive block?
2. Should explanation wording be versioned independently from calculation
   structure once localization is introduced?
3. Should future historical review store rendered explanation text or only the
   immutable explanation payload and renderer version?
