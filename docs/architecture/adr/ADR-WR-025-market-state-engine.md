# ADR-WR-025 — Market State Engine, Phase 1

## Status

Accepted for implementation; Architecture Review is required before merge.

## Context

WR-024.5 established immutable `ExpertOpinion` and `MarketState` contracts. The
next architecture layer must combine independent opinions into one explainable
market state without coupling domain synthesis to sources, delivery, storage,
or concrete Expert implementations. The existing Arkham-to-Telegram production
path must remain unchanged.

## Decision

Add a pure, synchronous `MarketStateEngine` under
`app.intelligence.market_state`. It accepts an iterable of already-produced
`ExpertOpinion` values and returns one immutable `MarketState` using a
deterministic, configurable `SynthesisPolicy`.

The effective contribution of expert `i` is:

```text
effective_weight_i = configured_weight_i
                     * confidence_i / 100
                     * quality_i / 100
```

The engine uses weighted direction balance, weighted canonical state support,
and documented weighted metrics. It aggregates source explanations and adds
synthesis warnings. It neither invokes Experts nor accesses infrastructure.

## Why a pure orchestration engine

- Inputs and outputs are the approved WR-024.5 domain contracts.
- The same inputs and fixed timestamp produce equal outputs.
- The policy can be tested without services, adapters, or mocks.
- Domain decisions remain auditable and portable.
- Future delivery and persistence adapters may depend on the result without the
  domain depending on them.

## Why Experts remain independent

Experts represent separate evidence axes. Allowing them to call each other
would introduce order dependence, hidden coupling, and correlated failure.
Phase 1 therefore combines completed opinions centrally and never exposes
concrete Expert implementations to the engine.

## Alternatives considered

### Direct source-aware engine

An engine could query Arkham, funding, databases, or network adapters itself.
This was rejected because it would mix acquisition with synthesis, make tests
service-dependent, and couple the new architecture to the production pipeline.

### Expert-to-expert communication

Experts could refine or challenge each other's results. This was rejected for
Phase 1 because it would make output depend on execution order and create
cycles between otherwise independent evidence producers.

### Simple unweighted voting

One vote per Expert is easy to understand, but treats low-confidence and
low-quality opinions as equivalent to strong evidence and provides no safe way
to exclude or tune an Expert.

### Weighted deterministic synthesis

The selected approach scales configured weight by each opinion's confidence
and quality. It preserves explainability, remains deterministic, and handles
weak, neutral, conflicting, or excluded contributions explicitly.

## Selected approach

Use weighted deterministic synthesis with immutable WR-024.5 contracts and a
small frozen policy object. The default direction threshold is 0.15. Canonical
state selection requires at least 20% support and a 10% lead. Direction
conflict means bullish and bearish shares are each at least 20%. Aggregate
quality below 50 produces a warning. Fewer than two positive contributors
produces an insufficient-contributors warning.

## Trade-offs

- Fixed formulas are transparent but intentionally provisional.
- Configured weights require future calibration and governance.
- `market_maturity` is only a score/confidence/quality proxy; it is not a
  market-cycle completion estimate.
- State-string canonicalization is tolerant but cannot recover semantics from
  unsupported labels.
- Independent state support values do not form a probability distribution and
  need not sum to 100.
- A single strong Expert may determine direction while still receiving a low
  stability score and an insufficient-contributors warning.

## Consequences

### Positive

- A stable pure-domain orchestration boundary now exists.
- Inputs are not mutated and duplicate expert names fail fast.
- Neutral, missing, weak, and conflicting evidence are represented safely.
- Reasons and warnings make synthesis explainable.
- No third-party dependency or production integration is introduced.

### Negative

- Phase 1 thresholds are policy defaults, not empirically calibrated values.
- `decision_stability` measures deterministic consensus robustness rather than
  predictive accuracy.
- The engine operates on one snapshot and has no history or temporal context.

## Dependency boundaries

`app.intelligence.market_state` may import Python standard-library modules,
`app.intelligence.contracts`, and its own policy module. It must not import
Telegram, FastAPI, databases, repositories, persistence, Arkham, funding,
source adapters, the production pipeline, networking, background jobs, or
concrete Experts.

## Future compatibility with WR-026 and later Experts

Future approved Experts may independently create `ExpertOpinion` values and
pass them to this engine. WR-026 or later work may add concrete Experts,
calibrated policies, history, or downstream decision layers alongside this
API. Such work must not make Experts call each other or make the engine source
aware. No WR-026 implementation or production integration is part of WR-025.
