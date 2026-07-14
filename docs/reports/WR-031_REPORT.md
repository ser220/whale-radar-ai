# WR-031 Intelligence Timing Architecture Report

## Status

Completed on `wr-031-intelligence-timing-architecture`; pending Architecture
Review. Documentation only.

## Objective

Define separate timing and authority boundaries for Fast Intelligence and Deep
Intelligence so Whale Radar AI can preserve early detection without presenting
incomplete evidence as final confidence or synthesis.

## Document

- [`WR-031_INTELLIGENCE_TIMING_ARCHITECTURE.md`](../architecture/WR-031_INTELLIGENCE_TIMING_ARCHITECTURE.md)

## Decision summary

Fast Intelligence detects emerging normalized events with low latency and may
produce early observations plus a future `EarlyState`. It explicitly accepts
incomplete context and has no final confidence, readiness, decision or
execution authority.

Deep Intelligence evaluates normalized observations through independent
Experts and synthesizes `ExpertOpinion` values through `MarketStateEngine`. It
is slower and more contextual, and makes agreement, conflict, missing evidence,
quality and confidence visible.

A future Decision Layer consumes both horizons. It does not force fast evidence
to masquerade as confirmation or allow deep synthesis to erase an earlier
event.

## Decision Stability

Decision Stability is defined as a confidence/consensus robustness metric, not
an entry blocker. Low stability qualifies uncertainty; high stability improves
trust but neither guarantees an outcome nor authorizes execution. The existing
`MarketState.decision_stability` remains a provisional synthesis metric.
WR-031 does not implement or specify a new Decision Stability Engine formula.

## Architecture rules captured

1. Fast Intelligence may create early observations.
2. Deep Intelligence owns expert synthesis.
3. Decision Stability is not a universal entry gate.
4. Missing confirmation does not invalidate valid early detection.
5. Experts remain independent.
6. A future Decision Layer consumes early and deep intelligence.
7. Missing, neutral, stale, conflict and unconfirmed remain distinct.
8. Neither layer creates trades or execution instructions.

## Data flows documented

- current conceptual Sources -> Observations -> Experts -> MarketState ->
  Decision flow;
- future Fast Observations -> Early State flow;
- future Deep Observations -> Experts -> MarketState -> Stability flow;
- combined early/deep inputs into future Decision Intelligence.

The architecture document includes Mermaid diagrams for each relationship.

## Scenarios documented

- fast bullish breakout with missing deep confirmation: early alert may be
  possible with lower confidence and explicit missing context;
- fast and deep agreement: higher contextual confidence while retaining the
  original early event;
- fast bullish and deep bearish: explicit conflict, not automatic rejection or
  silent overwrite.

These are intelligence behavior examples, not trading signals.

## Migration impact documented

The document defines consequences for Legacy Intelligence, Trend Expert, future
Funding, Arkham/on-chain and OI Experts, MarketStateEngine and Trade Readiness.
It explicitly warns against double-counting one underlying event as independent
fast and deep confirmation.

## Files created

- `docs/architecture/WR-031_INTELLIGENCE_TIMING_ARCHITECTURE.md`
- `docs/reports/WR-031_REPORT.md`

## Files modified

None.

## Production safety

- Python/application code changed: **NO**
- Production pipeline changed: **NO**
- Telegram changed: **NO**
- Hostinger changed/deployed: **NO**
- Decision Stability Engine created: **NO**
- Trading signals created: **NO**
- Dependency/workflow/service configuration changed: **NO**
- Secrets added or inspected: **NO**

## Verification

```bash
git status --short
git diff --check
git diff --name-status origin/main...HEAD
git diff --stat origin/main...HEAD
```

Before commit, confirm that only the two WR-031 Markdown documents are staged;
all unrelated untracked files remain unstaged and unchanged.

## Architecture deviations

None. `EarlyState`, Decision Intelligence and a dedicated stability component
are described only as future conceptual boundaries and are not implemented.

## Open questions

1. What latency budget and freshness window apply to each fast observation
   family?
2. What minimum evidence defines an informational early alert without turning
   it into a trading signal?
3. How should future Decision Intelligence correlate fast and deep artifacts
   without double-counting shared source facts?
4. Which temporal and expert-agreement inputs should a future Decision
   Stability specification include?
5. What shadow evaluation dataset and calibration period are required before
   production timing thresholds are proposed?

Architecture Review is required before merge. No implementation or subsequent
WR task is authorized by this report.
