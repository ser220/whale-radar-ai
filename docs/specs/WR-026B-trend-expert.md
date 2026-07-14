# WR-026B — Trend Expert Specification

## Objective

Create a pure deterministic Expert that converts compatible normalized trend
and structure facts into one explainable immutable `ExpertOpinion` without
production integration or trading decisions.

## Inputs

- Exactly one `TrendObservation`.
- Exactly one `StructureObservation`.
- Optional output `timestamp`.

Both observations must be exact supported classes, version 1, and share the
same asset and timeframe. Their `observed_at` delta may exceed policy tolerance;
this creates a warning and reduces confidence rather than raising.

## Output

One WR-024.5 `ExpertOpinion` with:

- `expert_name = "trend"`
- direction: `BULLISH`, `BEARISH`, or `NEUTRAL`
- state: `TREND`, `CORRECTION`, `REVERSAL`, `RANGE`, or `UNKNOWN`
- bounded score, confidence, and quality
- deterministic reasons and warnings
- serializable immutable metadata
- aware UTC output timestamp

No output field represents a trade instruction or profit probability.

## Public API

```python
from app.intelligence.experts.trend import TrendExpert, TrendExpertPolicy

expert = TrendExpert(policy=None)
opinion = expert.evaluate(trend, structure, timestamp=None)
```

`TrendExpert.name == "trend"`; `TrendExpert.policy` exposes its frozen policy.
Both public classes are also re-exported from `app.intelligence.experts`, but
not from the broad `app.intelligence` package.

## Supported versions

Phase 1 accepts only:

```text
TrendObservation.version == 1
StructureObservation.version == 1
```

Any other version raises `ValueError` naming the concrete observation type and
unsupported version. `TrendExpertPolicy.supported_versions` is fixed to `(1,)`
in Phase 1; migration logic is absent.

## Direction scoring

Raw bullish evidence:

```text
trend_bias BULLISH                    +25
moving_average_alignment BULLISH     +15
higher_high                           +12
higher_low                            +12
positive slope                        +min(slope * 10, 10)
positive price_change_pct             +min(price_change_pct, 8)
BULLISH_BOS                           +20
BULLISH_CHOCH                         +12
higher_timeframe_bias BULLISH         +15
```

Bearish evidence is symmetric using bearish bias/alignment, lower-high,
lower-low, absolute negative slope/change, bearish BOS/CHOCH, and bearish HTF
bias.

Maximum raw support per side is 117. Each support is normalized independently:

```text
normalized_support = 100 * raw_support / 117
directional_lead = bullish_support - bearish_support
```

- lead `>= +15`: `BULLISH`
- lead `<= -15`: `BEARISH`
- otherwise: `NEUTRAL`

Trend bias alone contributes only 25 raw points and does not force direction.

## Structure support

Separate bullish/bearish structure support is bounded to `0..100`:

```text
HH or LH flag: 25 on its side
HL or LL flag: 25 on its side
BOS: 50 on its side
CHOCH: 30 on its side
```

Selected structure support follows the selected direction; neutral direction
uses the stronger side only as classification evidence.

## State classification

State is independent from direction and uses this precedence:

1. `UNKNOWN` when effective input quality is below 50.
2. `REVERSAL` when CHOCH opposes current trend bias, selected direction has
   changed to that opposing side, and its support is at least 25.
3. `CORRECTION` when HTF bias is directional, at least two of short-term trend
   bias, MA alignment, slope, and price change oppose it, and no opposing BOS
   invalidates that HTF context.
4. `TREND` when trend bias, MA alignment, and HTF bias align directionally and
   same-direction BOS or consistent HH/HL or LH/LL supports continuation, with
   no strong opposing CHOCH.
5. `RANGE` when there is no structure break, slope magnitude is at most 0.10,
   price-change magnitude is at most 1.0, price is inside a defined range or
   absolute range distance is at most 1.0, directional flags are balanced, and
   context is neutral/balanced.
6. Otherwise `UNKNOWN`.

CHOCH alone does not produce `REVERSAL`. Because WR-026A exposes a single
`structure_break`, CHOCH and a later confirming BOS cannot coexist in one
StructureObservation. Every Phase 1 reversal is capped at confidence 70 and
warns about unavailable separate BOS confirmation.

## Score formula

For directional results, evidence strength is the larger normalized support.
For neutral results it is `100 - abs(directional_lead)`, bounded to `0..100`,
which represents strength of the balanced classification rather than direction.

```text
score = 0.45 * evidence_strength
      + 0.30 * TrendObservation.trend_strength
      + 0.25 * selected_structure_support
```

Score is trend conviction/classification strength, not profit probability.

## Confidence formula

Directional agreement combines 55% absolute evidence lead and 45% agreement of
trend bias, MA alignment, and HTF bias with selected direction. For neutral
direction, agreement is `100 - abs(directional_lead)`.

```text
quality = 0.60 * trend.quality + 0.40 * structure.quality
confidence_quality = 0.50 * quality
                   + 0.50 * min(trend.quality, structure.quality)

confidence = 0.35 * evidence_agreement
           + 0.30 * confidence_quality
           + 0.25 * structure_clarity
           + 0.10 * timestamp_coherence
```

Base structure clarity is selected structure support. Clear RANGE evidence with
no structure break uses base clarity 80. The confidence component is then
`0.70 * base structure clarity + 0.30 * structure_quality`. Contradictory high
flags subtract 25, contradictory low flags subtract 25, and BOS conflict
subtracts 20, bounded at zero.

Timestamp coherence is 100 within the 300-second tolerance. Beyond it:

```text
max(0, 100 - 100 * (delta - tolerance) / max(tolerance, 1))
```

Low-quality conclusions are capped by effective input quality. Reversal
confidence is capped at 70. Final confidence is bounded to `0..100`.

## Quality formula

```text
quality = 0.60 * TrendObservation.quality
        + 0.40 * StructureObservation.quality
```

Quality describes inputs only. Confidence separately penalizes the weaker input
through `min(...)`; a quality gap of at least 25 adds a warning.

## Policy defaults

```text
direction_lead_threshold = 15
low_quality_threshold = 50
timestamp_tolerance_seconds = 300
reason_limit = 12
warning_limit = 12
supported_versions = (1,)
policy_version = "1.0"
reversal_support_threshold = 25
reversal_confidence_cap = 70
weak_slope_threshold = 0.10
weak_price_change_threshold = 1.0
insufficient_structure_threshold = 25
quality_gap_warning_threshold = 25
```

The policy is frozen, validates types/ranges, and has no environment or
infrastructure dependency.

## Reasons

Reasons are concise, stable, deduplicated, capped at 12, and include only
material bias/alignment, structure flags/break, state context, and directional
lead evidence. They contain no Telegram markup or trading instructions.

## Warnings

Warnings are stable, deduplicated, capped at 12, and cover:

- low input quality and material quality gaps;
- timestamp delta above tolerance;
- contradictory high/low flags;
- mixed trend and HTF bias;
- weak directional lead;
- BOS conflict with observed trend direction;
- developing but unconfirmed reversal;
- Phase 1 reversal without separate BOS confirmation;
- insufficient structure support;
- unrecognized simple timeframe semantics.

Warnings do not replace compatibility/type/version exceptions.

## Metadata

Metadata contains only serializable structured explainability:

- supported observation versions and policy version;
- timeframe and timestamp delta;
- bullish/bearish support and signed lead;
- selected structure support;
- trend and structure observation IDs;
- boolean classification details.

It never contains raw observation instances or raw source payloads.

## Validation

- Inputs must be exact `TrendObservation` and `StructureObservation` types.
- Both must be supported version 1 and match asset/timeframe.
- Output timestamp must be aware and is normalized to UTC; omission uses current
  aware UTC.
- Timestamp mismatch warns rather than raises.
- Low-quality but valid observations return `UNKNOWN`/low confidence.
- Inputs remain unchanged.

## Dependency boundaries

Production Expert modules may import only standard library, WR-024.5 contracts,
WR-026A observations, and local Expert code. Telegram, FastAPI, database,
repositories, persistence, pipeline, Arkham, funding/exchange services,
networking, pandas, NumPy, TA libraries, MarketStateEngine implementation,
another Expert, ML, and LLM imports are forbidden.

## Out of scope

Raw candle parsing, exchange APIs, Observation Builders, MTF aggregation, live
data, production integration, Telegram/API output, MarketStateEngine
orchestration changes, other Experts, trade readiness, ETA, lifecycle, Decision
Engine, persistence, ML, LLM calls, and execution are explicitly out of scope.
WR-026C is not part of WR-026B.

## Acceptance criteria

- Required API/package/docs exist and compile on Python 3.9.
- Direction, state, score, confidence, quality, reasons, warnings, and metadata
  follow the exact policy above and are deterministic.
- Version/type/asset/timeframe/timestamp rules are enforced.
- Focused tests and WR-024.5/025/026A regressions pass.
- MarketStateEngine accepts the resulting public `ExpertOpinion` without any
  production integration change.
- Safe smoke scripts, dependency audit, and diff checks pass.
- No production, Telegram, database/API, requirements, archive, or third-party
  dependency change occurs.

## Verification commands

```bash
PYTHONPYCACHEPREFIX=/tmp/whale_radar_pycache ./venv/bin/python -m py_compile \
  app/intelligence/experts/__init__.py \
  app/intelligence/experts/trend/__init__.py \
  app/intelligence/experts/trend/policy.py \
  app/intelligence/experts/trend/expert.py \
  test_trend_expert.py

./venv/bin/python -m unittest -v test_trend_expert.py
./venv/bin/python -m unittest -v test_observation_contracts.py
./venv/bin/python -m unittest -v test_intelligence_contracts.py
./venv/bin/python -m unittest -v test_market_state_engine.py
./venv/bin/python test_core.py
./venv/bin/python test_filter.py
./venv/bin/python test_parser.py

rg -n '^(from|import) ' app/intelligence/experts
git diff --check
git diff --stat origin/main...HEAD
git diff --name-status origin/main...HEAD
git log --oneline origin/main..HEAD
git status --short
```
