# ADR: PS-4 Market Situation Expectation Engine

## Status

Proposed; awaiting Architecture Review.

## Context

Whale Radar AI now preserves immutable Market Situation timelines and can
deterministically decide whether a new scan continues an existing situation.
The architecture also requires a historical record of what the system expected
to observe next, created before later facts are known. Without that record,
future comparison can accidentally apply hindsight or rewrite the original
hypothesis after an outcome appears.

Missing, stale, unsupported, and failed inputs already have explicit
availability semantics. Any expectation design must preserve those semantics
and must not treat missing data as measured zero or evidence.

## Decision

Add a pure, process-local `SituationExpectationEngine` beside Timeline. It
consumes only the latest immutable Timeline entry and its SituationDNA and
returns immutable `SituationExpectation` hypotheses.

Expectations are hypotheses, not predictions. They describe a measurable event
that may be observed in a bounded future window, its current measured basis,
fulfillment criteria, and contradiction criteria. They do not estimate profit,
direct a trade, or claim that the event will happen.

Generation and evaluation are separate responsibilities. PS-4 Step 5 generates
expectations only. A future separately reviewed component may compare later
facts with the original payload.

## Historical Integrity Principle

1. Every expectation references one exact timeline ID, timeline version, source
   entry ID, and source stage.
2. Source factor values and availability states are copied into the immutable
   expectation at generation time.
3. The evaluation window begins at or after expectation creation.
4. An expectation cannot be created after its own window end.
5. Future observations cannot mutate the original expectation.
6. Later policy or rendering changes cannot rewrite prior structured payloads;
   each expectation preserves its policy version and rule name.
7. Expectations cannot be created post-outcome and presented as prior
   hypotheses.

## Missing data

Missing data is not evidence. Rules may use `MISSING` only as a target-state
precondition for the single approved causal appearance rule. The evidence for
that rule is strong measured structure and volume activity; absence of funding
is not itself support. `UNSUPPORTED`, `ERROR`, and unavailable values never
become weak measured factors.

## Rule policy

Phase 1 uses a frozen, explicit policy and seven deterministic rules:

1. volume confirmation;
2. momentum confirmation;
3. strong initiating-factor persistence;
4. funding appearance after strong measured structure and volume;
5. one-step stage advance;
6. stage persistence fallback;
7. invalidation risk.

No ML, embeddings, learned weights, historical similarity, providers, or
randomness are used.

## Consequences

### Positive

- Future evaluation can compare later facts with an authentic pre-window
  hypothesis.
- Fulfillment and contradiction semantics are explicit and machine-readable.
- Availability and measured-zero semantics remain intact.
- IDs, ordering, windows, and rules are deterministic and testable.
- Production decisions, Telegram, providers, and persistence remain isolated.

### Negative and trade-offs

- Rules are intentionally conservative and incomplete.
- Phase 1 thresholds are policy choices, not learned probabilities.
- Several hypotheses may coexist for one situation and may later contradict;
  resolution belongs to the future evaluator.
- Process-local expectations disappear when the process exits.
- Formatter wording may evolve, so historical comparison must use structured
  payloads rather than rendered text.

## Dependency boundaries

The runtime may import only Python standard library, Timeline models, and the
public `EmergingStage` contract. It must not import scanners, providers,
exchanges, networking, Telegram, database, repositories, production pipeline,
Decision Engine, Trade Readiness, MarketStateEngine, Experts, outcome, or
learning modules.

The local demo may invoke the existing public scanner and Timeline adapter but
does not write files, persist data, evaluate expectations, or send messages.

## Future evaluation

A future reviewed evaluator may answer what happened that should not have
happened and what did not happen that should have happened. It must consume the
unchanged expectation and later evidence, and it must not retroactively alter
the policy version, source snapshot, criteria, or window.
