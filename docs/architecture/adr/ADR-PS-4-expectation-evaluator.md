# ADR: PS-4 Market Situation Expectation Evaluator

## Status

Proposed; awaiting Architecture Review.

## Context

Step 5 records immutable, pre-window expectations. Whale Radar AI needs a
separate component to compare those hypotheses with later facts without
changing either the expectation or append-only Timeline. Availability-aware
evidence makes the distinction between a measured event that failed to occur
and a provider observation that was never measurable essential.

## Decision

Add a deterministic, process-local `SituationExpectationEvaluator`. It accepts
one immutable expectation and a later version of the same Timeline and returns
one immutable `SituationExpectationEvaluation`. Generation owns hypotheses;
evaluation owns only classification of later Timeline evidence.

The evaluator uses `metadata.evaluation_contract` version `"1"` as its sole
rule authority. Fulfillment/contradiction prose is presentation only. Explicit
handlers cover volume confirmation, momentum confirmation, factor persistence,
factor appearance, stage advance, stage persistence, and invalidation risk.

## MISSING versus EXPIRED

`MISSING` means measured evidence covered the window sufficiently and confirmed
that the expected event did not occur. `EXPIRED` means the window ended without
enough measured evidence, including unavailable, stale, unsupported, or failed
factor observations. Provider absence is never converted into a failed market
event.

## Anti-hindsight guarantees

- only entries later than the source entry and no later than evaluation time
  are candidates;
- evidence after `window_end` is ignored for that historical window;
- the stored evaluation contract is authoritative;
- current defaults cannot fill absent/incomplete historical contracts;
- source identity, version, stage, values, and availability are validated;
- expectation, Timeline, and prior evaluation records are never mutated;
- no outcome, provider, price, or external data is fetched.

## Immutable evaluation records

Every evaluation is a new value containing its source expectation snapshot,
evaluated entry IDs, policy/contract versions, observed facts, status, reality
gap, and Surprise Score. Later Timeline versions can produce new records without
overwriting history.

## Alternatives considered

### Parse descriptive text

Rejected because wording is not a stable contract and permits semantic drift.

### Evaluate inside the generator

Rejected because generation and later evidence occur at different times and
combining them weakens anti-hindsight guarantees.

### Treat unavailable evidence as failure

Rejected because it confuses provider coverage with market behavior.

### Mutate SituationExpectation with status

Rejected because it rewrites the historical hypothesis and loses multiple
evaluations against later Timeline versions.

## Consequences

Positive consequences are deterministic classification, explicit uncertainty,
traceable provenance, safe historical comparison, and no external dependency.
Trade-offs are conservative `EXPIRED`/`INDETERMINATE` outcomes, fixed Phase 1
rules, no persistence, and no calibration or learning.

## Dependency boundaries

Runtime imports only Python standard library, Timeline models, expectation
contracts, and public `EmergingStage`. It does not import scanners, providers,
exchange/network clients, Telegram, database, repositories, pipeline, Decision
Engine, Trade Readiness, MarketStateEngine, Experts, or learning. The local demo
may compose existing scanner, adapter, evolution, and expectation components
but remains read-only and process-local.
