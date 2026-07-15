# ADR-WR-036 — Early Bird Foundation, Phase 1

## Status

Accepted for implementation; Architecture Review is required before merge.

## Context

Whale Radar AI now has contracts for fast events, deep observations, expert
opinions, correlation, market state, and the versioned MarketSituation
identity. It still needs a provider-neutral way to identify which assets merit
attention before expensive deep analysis, without turning early incomplete
facts into a trading signal.

Provider payloads, live scanning, and production presentation are outside this
boundary. WR-036 starts with normalized candidate facts and creates pure,
deterministic, explainable assessments only.

## Decision

Create `app.intelligence.early_bird` as a Python 3.9-compatible,
standard-library-only package containing:

- immutable `EarlyBirdCandidate` and `EarlyBirdAssessment` contracts;
- a public provider-neutral factor enum;
- a frozen, fully validated `EarlyBirdPolicy` with explicit weights,
  thresholds, limits, and version;
- a pure `EarlyBirdEngine` for single-candidate evaluation and deterministic
  multi-candidate ranking;
- stable artifact references and serialization, with no infrastructure imports.

## Why Early Bird is an Opportunity Hunter

Early Bird answers where analytical attention is valuable. It combines
unusual whale activity with independent derivatives, volume, relative
strength, liquidity, structure, and momentum facts. It explains material
contributors, data limitations, urgency, and development progress.

This is deliberately earlier than expert synthesis. Incomplete confirmation is
acceptable as long as quality and completeness are visible and reduce the
score rather than being interpreted as market direction.

## Why it is not a Decision Engine

Attention ranking and trade decisions have different responsibilities and risk
profiles. Early Bird has no position context, directional synthesis, risk
budget, entry planning, or execution authority. Adding those concepts would
make an early-data scanner silently influence production decisions.

The models contain no direction, recommendation, signal, BUY/SELL, LONG/SHORT,
entry, target, stop, or execution fields. The engine does not invoke Experts,
MarketStateEngine, Shadow Intelligence, or the production pipeline.

## Why Opportunity, Priority, and Maturity are separate

- **Opportunity** answers how materially interesting the normalized facts are,
  adjusted for data reliability.
- **Priority** answers how urgently deeper analysis should occur, considering
  freshness and urgent event families.
- **Maturity** answers how far the observable event has developed.

A single score cannot distinguish a strong but early opportunity from a strong
but late one. Separate axes preserve that distinction and keep Maturity from
being mistaken for confidence or trade readiness.

Maturity is explicitly not correction completion, probability of profit,
confidence, trade readiness, or market-cycle maturity.

## Why no direction is produced

The input scores are magnitudes of interest, not signed market conclusions.
Funding divergence or relative strength can be interesting without identifying
the correct trade direction. Direction belongs to independent Experts and
later synthesis. Treating absence or incomplete provider data as bullish or
bearish would create false intelligence.

## Why whale activity is high but not exclusive weight

Whale activity receives the largest Opportunity weight (`25%`) and half of the
event-urgency component because Whale Radar AI is whale-first. It is not
exclusive: OI, volume, relative strength, funding, liquidity, structure, and
momentum can independently surface meaningful situations and protect against a
single noisy transfer dominating the ranking. No-whale and one-factor cases
remain visible with explicit warnings.

## Alternatives considered

### Signal scanner

Rejected because it would collapse early attention into direction or action,
conflict with the system mission, and risk influencing the production
recommendation path.

### Single composite score

Rejected because one number obscures urgency and development. It cannot clearly
represent high opportunity with low maturity or warn that a situation may be
over-mature.

### Provider-specific scanner

Rejected because it couples domain scoring to Arkham, CoinGlass, Nansen, or an
exchange schema and prevents deterministic provider-independent tests.

### Provider-neutral opportunity ranking

Selected. Normalized candidates isolate future adapters from stable scoring,
allow multiple source combinations, and keep missing data explicit through
quality, completeness, warnings, and metadata.

## Trade-offs

- Hand-authored deterministic weights are transparent but not calibrated from
  outcomes yet.
- Normalized candidate builders must be implemented and documented later.
- Magnitude-only factors intentionally cannot express directional context.
- The optional overextension proxy is trusted only when explicitly supplied as
  normalized metadata; Phase 1 does not calculate it.
- Multiple candidates for one asset may appear in results and require future UI
  context such as timeframe/event window.
- A policy threshold produces a warning, not exclusion, so consumers must not
  treat ranking as an eligibility decision.

## Future source adapters

Future reviewed adapters or builders may normalize Arkham, CoinGlass, Nansen,
exchange, or other source data into candidate scores and stable artifact IDs.
They remain outside this package, own missing-source accounting, and may not
inject raw payloads or networking into the engine.

## Future MarketSituation attachment

Phase 1 creates no situation and writes no database. A future orchestrator may
attach an assessment ID and its source artifact IDs to a MarketSituation
version. The assessment itself is not automatically embedded, and Early Bird
does not own the situation lifecycle.

## Future Telegram preview

A future separately approved read-only preview may show ranked Opportunity,
Priority, Maturity, reasons, and warnings. It must label the output experimental
or informational, preserve existing recommendation formatting, and never add
direction or execution language. WR-036 makes no Telegram change.

## Dependency boundaries

The runtime package may import only Python standard-library modules and its own
`app.intelligence.early_bird` modules. Providers, exchange clients, Telegram,
FastAPI, databases, repositories, production pipelines, Experts,
MarketStateEngine, ShadowIntelligenceEngine, MarketSituation objects,
networking, pandas, numpy, and TA libraries are forbidden.

No requirements, Hostinger, deployment, production pipeline, Telegram,
database, or API change is authorized.
