# WR-034 Market Situation Architecture Report

## Status

Completed on `wr-034-market-situation-architecture`; pending Architecture
Review. Documentation only.

## Objective

Define `MarketSituation` as the central domain identity that follows an
interesting market story from detection through observations, expert analysis,
correlation, decision support, outcome, learning, and memory.

## Mission

Whale Radar AI does not generate trading signals. It detects, observes,
evaluates, remembers, and learns complete market situations to improve trader
decision support.

## Document

- [`WR-034_MARKET_SITUATION_ARCHITECTURE.md`](../architecture/WR-034_MARKET_SITUATION_ARCHITECTURE.md)

## Lifecycle

```text
Detected
  -> Observed
  -> Analyzed
  -> Correlated
  -> Decision Support
  -> Outcome
  -> Learning
  -> Memory
```

The lifecycle is append-oriented and versioned rather than destructively
linear. Late evidence adds a new situation version and timeline event instead
of rewriting what was known earlier.

## MarketSituation boundary

The architecture defines sections for:

- General metadata and lifecycle;
- Asset, timestamps, and Situation ID;
- Fast Intelligence and Early Bird;
- normalized Observations and independent Experts;
- Correlation and MarketState history;
- Decision Support;
- Outcome, Learning, and Memory references.

Large immutable artifacts remain separate and attach through stable IDs. No
Expert, engine, provider, UI, repository, or learning component owns the whole
situation. A future orchestrator may steward lifecycle versions but cannot
become the source of market truth.

## Expectation Analysis

The document defines:

- Expected Events;
- Observed Events;
- Unexpected Events;
- Missing Expected Events;
- Expectation Window;
- Expectation Gap;
- Gap Severity;
- Learning Conclusion.

It explicitly asks:

> What happened that should not have happened?

and:

> What did not happen that should have happened?

Missing data remains distinct from confirmed non-occurrence. Gap severity is an
explainable future policy classification, not a trade-loss score. No formula or
engine is introduced.

## Early Bird

Early Bird is defined as an **Opportunity Hunter**, not a Decision Engine. It
finds situations worth attention and analysis. It must not authorize trades,
replace Deep Intelligence, or create execution instructions.

Future explainable assessments are:

- Opportunity — how interesting/informative the situation appears, not expected
  return;
- Priority — analysis urgency, not entry urgency;
- Maturity — context assembly progress, not correction completion, readiness,
  or MarketState maturity.

## Learning model

Learning compares complete MarketSituations, not isolated indicators,
individual Expert scores, or BUY/SELL correctness labels. Memory stores:

- versioned Situation DNA;
- Outcome trajectory;
- Expert behavior;
- Expectation Gap and severity;
- Pattern evolution and comparable situation references.

Historical feature state is separated from later outcome knowledge to prevent
look-ahead leakage.

## Future attachments

Attachment boundaries are documented for Funding Expert, Arkham Expert,
CoinGlass Expert, Open Interest Expert, Memory Adapter, Decision Stability,
Prediction Review, and Timeline. Each attaches its own immutable/versioned
artifact and cannot own or rewrite the full situation.

## Repository baseline note

The task branch is based on `origin/main` at `c2028c1`. Fast Intelligence is
tracked at that baseline. Correlation is documented as an architectural
attachment point; WR-034 does not claim or integrate an unmerged correlation
runtime. Early Bird remains a concept.

## Files created

- `docs/architecture/WR-034_MARKET_SITUATION_ARCHITECTURE.md`;
- `docs/reports/WR-034_REPORT.md`.

## Files modified

None.

## Production safety

- Python/application code changed: **NO**
- Production pipeline changed: **NO**
- Telegram changed: **NO**
- Hostinger changed/deployed: **NO**
- Trading signal/execution logic created: **NO**
- Dependencies, workflows, services, database, or environment changed: **NO**
- Secrets added or inspected: **NO**

## Verification

```bash
git status --short
git diff --check
git diff --name-status origin/main...HEAD
git diff --stat origin/main...HEAD
```

Before commit, confirm that only the two WR-034 Markdown files are staged and
all unrelated untracked files remain unstaged and unchanged.

## Architecture deviations

None. Runtime objects mentioned in the future integration sections are
conceptual boundaries only and are not implemented by WR-034.

## Open questions

1. What deterministic identity policy creates, merges, and splits Situation
   IDs without embedding direction?
2. Which lifecycle transitions require an orchestrator versus a read-model
   projection?
3. What minimum artifact set permits a situation to advance while still
   representing incomplete data honestly?
4. Which typed fields and policy determine expectation-gap severity?
5. How should Situation DNA support similarity without outcome leakage or
   opaque features?
6. What retention, privacy, and licensing policy applies to long-lived
   situation memory?

Architecture Review is required before merge. No implementation, deployment,
Hostinger change, production integration, or subsequent WR task is authorized.
