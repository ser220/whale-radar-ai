# WR-025 — Market State Engine, Phase 1 Specification

## Objective

Create a pure deterministic orchestration engine that synthesizes approved
`ExpertOpinion` contracts into one explainable `MarketState` without changing
the production pipeline.

## Inputs

- `opinions`: any iterable of `ExpertOpinion`, including list, tuple, or
  generator.
- `weights`: optional mapping of expert name to finite non-negative configured
  weight. Missing names default to `1.0`; zero excludes an opinion. Unknown
  names are ignored with a warning after their values are validated.
- `timestamp`: optional timezone-aware `datetime`. It is normalized to UTC. If
  omitted, current aware UTC time is used.

Duplicate `expert_name` values raise `ValueError`. Non-`ExpertOpinion` values
raise `TypeError`. Input opinions are never modified.

## Output

One immutable WR-024.5 `MarketState` containing direction, trend, numeric
synthesis metrics, source-attributed reasons, warnings, and a UTC timestamp.

## Public API

```python
from app.intelligence.market_state import MarketStateEngine, SynthesisPolicy

engine = MarketStateEngine()
state = engine.synthesize(opinions, weights=None, timestamp=None)
```

`SynthesisPolicy` is an optional frozen configuration model. Its percentage
fractions are finite values in `0..1`; `low_quality_threshold` is in `0..100`;
reason and warning limits are positive integers.

## Aggregation formulas

For expert `i`:

```text
c_i = configured_weight_i
q_i = quality_i / 100
f_i = confidence_i / 100
w_i = c_i * f_i * q_i
```

Only `w_i > 0` opinions contribute to direction, state, strength, maturity,
probability support, reasons, and source warnings.

### Direction

```text
direction_value = BULLISH:+1, BEARISH:-1, NEUTRAL:0
balance = sum(w_i * direction_value_i) / sum(w_i)
```

- `balance >= 0.15`: `BULLISH`
- `balance <= -0.15`: `BEARISH`
- otherwise: `NEUTRAL`

### Trend state

Trim and uppercase `ExpertOpinion.state`. `TREND`, `CORRECTION`, `REVERSAL`,
`RANGE`, and `UNKNOWN` map to the corresponding `TrendState`; unsupported
values map to `UNKNOWN` with a warning.

The winning non-UNKNOWN state is selected by summed effective weight. It must
have at least 20% of total effective support and lead the second non-UNKNOWN
state by at least 10% of total support. Otherwise the result is `UNKNOWN`.
Direction never implies trend state.

### Numeric metrics

All results are clamped to `0..100` and rounded to six decimal places.

```text
strength = sum(score_i * w_i) / sum(w_i)

overall_confidence =
    sum(confidence_i * c_i * q_i) / sum(c_i * q_i)

continuation_probability = 100 * TREND support / total effective support
correction_probability = 100 * CORRECTION support / total effective support
reversal_probability = 100 * REVERSAL support / total effective support

maturity_proxy_i = 0.50 * score_i
                   + 0.30 * confidence_i
                   + 0.20 * quality_i
market_maturity = sum(maturity_proxy_i * w_i) / sum(w_i)

aggregate_quality = sum(quality_i * c_i) / sum(c_i)
```

The three probability fields are independent support scores. `RANGE`,
`UNKNOWN`, and neutral evidence may consume support, so these fields are not
required to sum to 100.

`market_maturity` is a provisional Phase 1 synthesis proxy. It does not measure
actual market-cycle completion.

### Decision stability

```text
direction_agreement = max(direction support) / total effective support
state_agreement = max(non-UNKNOWN state support) / total effective support
contributor_factor = min(positive contributor count / 2, 1)

decision_stability = 100 * contributor_factor * (
    0.30 * direction_agreement
  + 0.25 * state_agreement
  + 0.25 * overall_confidence / 100
  + 0.20 * aggregate_quality / 100
)
```

This is a consensus-robustness metric, not a direction, trade signal, or
predictive-accuracy score.

## Thresholds

- Direction neutral threshold: `0.15`.
- Meaningful bullish/bearish support for conflict: `20%` each.
- Meaningful state support: `20%`.
- State winner minimum lead: `10%`.
- Low aggregate quality warning: below `50`.
- Insufficient contributors: fewer than `2` positive effective weights.
- Reasons cap: `20`; warnings cap: `20`.

## Conflict behavior

- Material direction conflict adds a warning when both bullish and bearish
  effective support shares are at least 20%.
- State disagreement adds a warning when multiple non-UNKNOWN states each have
  at least 20% support and no state satisfies the winner rule.
- Low aggregate quality and insufficient contributors are warnings, not
  exceptions.
- Source warnings are source-prefixed and aggregated after synthesis warnings,
  so the bounded output retains the engine's safety signals.

## Empty-input behavior

Empty input returns a valid state with `NEUTRAL` direction, `UNKNOWN` trend,
all numeric fields equal to zero, empty reasons, and a warning that no opinions
were supplied. If every effective weight is zero, the same zero state is
returned with no-positive-weight and insufficient-contributor warnings.

## Reasons and warnings

Contributing source messages are prefixed with `expert_name`, deduplicated in
input order, and capped at 20. Engine warnings are deterministic and prioritized
before source warnings in the final capped list.

## Validation

- Opinion values must be `ExpertOpinion` instances.
- Expert names must be unique within a synthesis call.
- Weight keys must be non-empty strings.
- Weight values must be real, finite, non-negative, and not booleans.
- The timestamp must be aware and is normalized to UTC.
- The engine relies on WR-024.5 contracts for opinion metric validation.
- The engine does not mutate its input iterable elements.

## Forbidden dependencies

No Telegram, FastAPI, database, repository, persistence, Arkham, funding,
source adapter, pipeline, networking, background-job, concrete Expert, ML, or
LLM dependency is permitted in the market-state package.

## Out of scope

Production integration, Expert execution, async orchestration, concrete Trend,
Funding, Arkham, Narrative, Correction or Reversal Experts, history,
persistence, velocity, ETA, trade readiness, lifecycle transitions, Telegram
formatting, API routes, database schemas, automated trading, background jobs,
ML, LLM calls, and WR-026 are explicitly out of scope.

## Acceptance criteria

- Required package and public API exist and are Python 3.9 compatible.
- Deterministic formulas and default thresholds match this specification.
- Empty, invalid, duplicate, neutral, excluded, weak, conflicting, and unknown
  inputs behave as specified.
- Output metrics remain in `0..100` and output timestamp is UTC-aware.
- At least 20 focused `unittest` cases pass.
- WR-024.5 regression tests and safe local smoke tests pass.
- Forbidden-import audit passes.
- No production, Telegram, database, dependency, or chat-archive file changes.

## Verification commands

```bash
PYTHONPYCACHEPREFIX=/tmp/whale_radar_pycache ./venv/bin/python -m py_compile \
  app/intelligence/__init__.py \
  app/intelligence/market_state/__init__.py \
  app/intelligence/market_state/engine.py \
  app/intelligence/market_state/policy.py \
  test_market_state_engine.py

./venv/bin/python -m unittest -v test_market_state_engine.py
./venv/bin/python -m unittest -v test_intelligence_contracts.py
./venv/bin/python test_core.py
./venv/bin/python test_filter.py
./venv/bin/python test_parser.py

rg '^from |^import ' app/intelligence/market_state
git diff --stat 94d65b4...HEAD
git diff --name-status 94d65b4...HEAD
git log --oneline 94d65b4..HEAD
git status --short
```
