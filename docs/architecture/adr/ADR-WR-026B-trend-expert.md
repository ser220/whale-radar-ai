# ADR-WR-026B — Trend Expert

## Status

Accepted for implementation; Architecture Review is required before merge.

## Context

WR-026A established immutable normalized Observation Contracts. Whale Radar AI
now needs its first independent Expert to interpret trend and structure facts
into the WR-024.5 `ExpertOpinion` language consumed by WR-025
`MarketStateEngine`. The existing production pipeline must remain unchanged,
and no Observation Builder or live source integration exists in this task.

## Decision

Create a pure synchronous `TrendExpert` under
`app.intelligence.experts.trend`. It accepts exactly one version 1
`TrendObservation` and one compatible version 1 `StructureObservation`, applies
an immutable deterministic policy, and returns one `ExpertOpinion` named
`"trend"`.

The Expert:

- validates type, version, asset, timeframe, and output timestamp;
- computes symmetric bullish and bearish support;
- decides direction from a configurable evidence lead;
- classifies state independently with explicit precedence;
- computes separate score, confidence, and input quality metrics;
- provides deterministic reasons, warnings, and structured metadata;
- never mutates observations or accesses infrastructure.

## Why Trend Expert consumes observations rather than raw candles

Observation Builders own raw-source parsing and fact normalization. If the
Expert parsed candles or exchange payloads directly, its analytical rules would
be coupled to provider schemas, transport, missing-data behavior, and indicator
calculation. Typed observations provide a stable versioned boundary and allow
the Expert to be tested without sources or networking.

## Why deterministic rules are used in Phase 1

- Every contribution and threshold is inspectable.
- The same observations, policy, and timestamp produce equal output.
- Failures and conflicting evidence can be explained through reasons/warnings.
- No training data, calibration service, model runtime, or third-party TA
  dependency is required.
- The baseline creates measurable behavior for later calibration rather than a
  hidden adaptive policy.

## Alternatives considered

### Raw-data-aware Expert

Rejected because it would duplicate Builder responsibilities and couple domain
analysis to payloads, exchange clients, and indicator calculation.

### Indicator library

Rejected because pandas/NumPy/TA libraries would add dependencies and shift raw
calculation into the Expert. Phase 1 consumes already normalized facts.

### ML classifier

Rejected because no approved labeled dataset, feature governance, calibration,
or model lifecycle exists. It would reduce explainability and determinism.

### Deterministic observation-based Expert

Selected because it preserves architectural boundaries and provides a
transparent, testable baseline for future empirical calibration.

## Selected approach

Bullish and bearish raw evidence use symmetric contributions with a maximum of
117 points and are normalized independently to `0..100`. A support lead of at
least 15 selects direction; otherwise direction is neutral.

State precedence is: low-quality `UNKNOWN`, supported opposing-CHOCH
`REVERSAL`, multi-signal higher-timeframe opposition `CORRECTION`, aligned
continuation evidence `TREND`, weak balanced in/near-range evidence `RANGE`,
then `UNKNOWN`. CHOCH alone never forces reversal.

Score is 45% evidence strength, 30% builder-provided trend strength, and 25%
structure support. Confidence is 35% agreement, 30% quality robustness, 25%
structure clarity, and 10% timestamp coherence. Output quality is 60% trend
observation quality and 40% structure observation quality.

## Trade-offs

- Coefficients and thresholds are transparent but not yet market-calibrated.
- Normalized `trend_strength` is trusted as a builder-produced fact; its future
  Builder must document a deterministic formula.
- Simple timeframe syntax recognition warns but does not reject other normalized
  strings because WR-026A deliberately keeps timeframe as a string.
- One `structure_break` field cannot represent CHOCH plus later BOS
  confirmation simultaneously. Phase 1 reversal confidence is therefore capped
  at 70 and explicitly warns about missing separate BOS confirmation.
- Direction and state may intentionally differ, which is more expressive but
  requires downstream consumers to respect both fields.

## Explainability

Reasons include only materially used bias, structure, state, and lead evidence
in stable order, capped at 12. Warnings identify quality, timestamp,
contradiction, bias, lead, structure, reversal-confirmation, and timeframe
limitations, also deduplicated and capped at 12. Metadata contains normalized
support values, IDs, timeframe, versions, policy version, timestamp delta, and
classification flags; it never embeds raw observation objects.

## Future calibration

Later approved work may backtest coefficients, thresholds, and confidence
calibration against versioned observations and outcomes. Calibration must
preserve deterministic policy versions and distinguish input quality from
conclusion confidence. It must not silently change policy version `1.0`.

## Dependency boundaries

Trend Expert may import only Python standard-library modules, WR-024.5 pure
contracts, WR-026A observations, and its local policy/module. It must not import
Telegram, FastAPI, databases, repositories, persistence, pipeline, Arkham,
funding or exchange services, networking, pandas, NumPy, TA libraries,
`MarketStateEngine` implementation, or another Expert.

## Future compatibility with MTF Observation Builder and WR-026C

A future multi-timeframe Builder may create versioned observations with an
explicit timeframe contract. A later WR-026C may add another independent Expert
alongside TrendExpert. Neither may make Experts parse raw payloads, call each
other, or add interpretation to Observation Contracts. WR-026B implements no
Builder, WR-026C component, or production integration.
