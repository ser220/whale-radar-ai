# PS-2 Step 3 — Availability-aware Early Bird Candidate Builder Report

## Status

Implemented on `ps-2-availability-aware-candidate-builder` from `origin/main`
at `386aca0`. The feature is not merged or deployed and awaits Architecture
Review.

## Builder

`EarlyBirdCandidateBuilder.build()` is a pure deterministic boundary that
accepts explicit `EarlyBirdFactorValue` objects and returns an immutable
`EarlyBirdCandidateBuildResult`. It performs no provider, exchange, Telegram,
database, repository, pipeline, Expert, MarketStateEngine, or network call.

Input is materialized exactly once. Unknown and duplicate factor names are
rejected. Results use canonical order regardless of input order. A canonical
factor omitted from the input is explicitly synthesized as `MISSING` with the
reason `No factor value was supplied.`; it is never left as an unexplained
numeric zero.

## Public API

Exported from `app.intelligence.early_bird`:

- `EarlyBirdCandidateBuilder`
- `EarlyBirdCandidateBuildResult`

The result contains:

- the existing immutable `EarlyBirdCandidate`;
- a canonical immutable mapping of all eight `EarlyBirdFactorValue` values;
- deterministic tuples for available, missing, stale, unsupported, and error
  factors;
- deterministic warnings;
- deeply frozen builder policy and candidate provenance metadata.

`to_dict()` and `from_dict()` restore the candidate, availability enums, UTC
timestamps, immutable collections, and metadata. Result validation also
ensures candidate scores, completeness, quality, freshness, status groups,
and warnings agree with the factor mapping.

## Canonical factor mapping

| Factor | Existing candidate field |
|---|---|
| `whale_activity` | `whale_activity_score` |
| `open_interest_change` | `open_interest_change_score` |
| `funding_divergence` | `funding_divergence_score` |
| `volume_expansion` | `volume_expansion_score` |
| `relative_strength` | `relative_strength_score` |
| `liquidity_event` | `liquidity_event_score` |
| `structure_event` | `structure_event_score` |
| `momentum_shift` | `momentum_shift_score` |

## Completeness formula

Let:

- `A` = number of `AVAILABLE` canonical factors;
- `M` = number of `MISSING` factors, including omitted inputs synthesized as
  missing;
- `S` = number of `STALE` factors;
- `E` = number of `ERROR` factors.

`UNSUPPORTED` is excluded from the denominator.

```text
expected_supported_count = A + M + S + E
completeness = round(100 * A / expected_supported_count, 6)
```

If the denominator is zero, all factors are unsupported and the builder raises
`ValueError`. The builder also requires at least one `AVAILABLE` factor.
`EarlyBirdCandidate.data_completeness_score` is set directly from this formula,
never from metadata.

## Quality formula

Only `AVAILABLE` factors participate. `STALE`, `MISSING`, `UNSUPPORTED`, and
`ERROR` quality values are provenance only and contribute nothing.

For every available factor:

```text
effective_factor_quality = explicit quality, when present
                         = 50.0, otherwise

candidate_quality = round(
    sum(effective_factor_quality) / available_count,
    6,
)
```

An available factor using the fallback produces an explicit warning. Quality
is not derived from direction, opportunity, score magnitude, or metadata.

## Freshness formula

Only `AVAILABLE` timestamps participate. Builder `observed_at` and all factor
timestamps are timezone-aware UTC values. For each available factor `i`:

```text
age_i_seconds = max(0, builder_observed_at - factor_observed_at)
freshness_i = max(0, 100 - (age_i_seconds / 3600) * 100)
candidate_freshness = round(min(freshness_i), 6)
```

This is a conservative minimum with linear decay from 100 to 0 over 60
minutes. Older values remain at zero. A future timestamp is treated as age
zero so clock skew cannot create freshness above 100. Source-specific freshness
windows remain out of scope.

If every available timestamp is more than 15 minutes from builder
`observed_at`, the result includes a deterministic warning.

## Structural placeholder semantics

The unchanged `EarlyBirdCandidate` requires eight numeric factor fields.
Therefore every non-`AVAILABLE` factor uses `0.0` in its corresponding
candidate field strictly as a structural placeholder.

This `0.0`:

- is not a measured score;
- is not neutral, bearish, bullish, or “no activity” evidence;
- does not enter the completeness numerator;
- does not increase aggregate quality;
- is paired with the original explicit availability value in the build result;
- is documented in `result.metadata["builder_policy"]` and in status warnings.

Downstream code must inspect `EarlyBirdCandidateBuildResult.factor_values`
before interpreting candidate fields. This task does not modify
`EarlyBirdCandidate` or `EarlyBirdEngine`.

## Warning behavior

Warnings are deduplicated and deterministic. Factor-specific warnings follow
canonical factor order and identify:

- `MISSING`;
- `STALE`;
- `UNSUPPORTED`;
- `ERROR`;
- an `AVAILABLE` factor using quality fallback 50.

Global warnings then identify:

- completeness below 50%;
- exactly one available factor;
- whale activity not available;
- no available timestamp within 15 minutes of builder time.

## Files changed

Created:

- `app/intelligence/early_bird/builder.py`
- `test_early_bird_candidate_builder.py`
- `docs/reports/PS-2_STEP_3_REPORT.md`

Modified:

- `app/intelligence/early_bird/__init__.py`

## Verification

Runtime: Python 3.9.6, standard library only.

```bash
PYTHONPYCACHEPREFIX=/tmp/whale_radar_pycache ./venv/bin/python -m py_compile \
  app/intelligence/early_bird/__init__.py \
  app/intelligence/early_bird/builder.py \
  test_early_bird_candidate_builder.py

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
- candidate builder: 40 passed;
- factor availability: 26 passed;
- existing Early Bird: 61 passed;
- MarketSituation: 34 passed;
- Fast Intelligence: 12 passed;
- Correlation: 12 passed;
- Shadow Intelligence: 10 passed;
- Intelligence contracts: 14 passed;
- MarketStateEngine: 30 passed;
- total focused/regression unittest tests: 239 passed;
- safe core/filter/parser smoke checks: passed;
- AST dependency-boundary audit: passed.

## Production impact

- Production pipeline changed: **NO**
- Production decisions changed: **NO**
- Telegram/API/database/repository changed: **NO**
- Hostinger changed/deployed: **NO**
- Provider/exchange/network calls added or executed: **NO**
- Live scanning implemented: **NO**
- Requirements changed: **NO**
- Third-party dependency added: **NO**

## Open questions

1. Which source-specific freshness windows should replace the neutral 60-minute
   Phase 1 policy when live normalized sources are introduced?
2. Should future clock skew beyond a small tolerance become `ERROR` or `STALE`
   instead of being conservatively clamped to age zero?
3. When new canonical factors are approved, what contract-version mechanism
   will distinguish old completeness denominators from the expanded set?
4. Which future orchestration boundary will enforce that consumers retain the
   build result alongside the numeric candidate when calling EarlyBirdEngine?
