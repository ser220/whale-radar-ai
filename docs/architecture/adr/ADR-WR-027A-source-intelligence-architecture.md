# ADR-WR-027A: Provider-neutral source intelligence architecture

## Status

Proposed — pending Architecture Review.

## Context

Whale Radar AI currently has two source paths that are only loosely connected:

1. Arkham-like webhook payloads enter the legacy alert pipeline, where they are
   filtered, stored, scored, clustered, interpreted, and possibly sent to
   Telegram.
2. The `/analyze` command attempts to combine the latest stored Arkham event
   with public exchange funding, open-interest, and price data.

The repository also contains immutable observation contracts, a Trend Expert,
and MarketStateEngine, but those foundations are intentionally not integrated
into production. Future Experts must not depend on Arkham, Nansen, CoinGlass,
or exchange-specific payloads.

The checked-in `origin/main` cannot locally reproduce the complete `/analyze`
path because several imported snapshot/decision modules are absent. This ADR
therefore distinguishes verified repository behavior from claims about the live
deployment.

## Decision

Adopt the following permanent boundary:

```text
Provider API
    -> Provider Adapter
    -> typed provider-neutral SourceRecord
    -> Observation Builder
    -> immutable Observation contract
    -> independent Expert
    -> ExpertOpinion
    -> MarketStateEngine
    -> future Decision Intelligence
```

WR-027A documents the boundary only. It adds no adapters, protocols, runtime
models, production wiring, credentials, dependencies, or Telegram changes.

## SourceProvider boundary

A future `SourceProvider` protocol should expose:

```text
provider_name: str
capabilities() -> immutable capability set
health() -> ProviderHealth
fetch(query: typed SourceQuery) -> sequence[typed SourceRecord]
```

`fetch` is a conceptual operation: push consumers, WebSocket sessions, and REST
pollers may implement different transport components behind the same normalized
record boundary. Capability discovery must precede requests, and unsupported
capabilities must fail explicitly rather than returning a neutral market fact.

## SourceRecord boundary

`SourceRecord` is an immutable provenance envelope with:

- `provider`;
- `record_type` enum;
- normalized `asset` identity;
- timezone-aware `observed_at` (provider/event time);
- timezone-aware `received_at` (system time);
- provider `source_id`;
- bounded `quality`;
- `payload_version`;
- sanitized provenance metadata.

The envelope must contain a typed record body, not a universal untyped
dictionary. Initial record families should include:

- `TransferSourceRecord` — chain, transaction hash, addresses, optional entity
  labels, normalized asset, quantity and USD value;
- `WalletLabelSourceRecord` — address/entity identity, label class, provider
  confidence, effective time;
- `DerivativesSourceRecord` — exchange, instrument, metric type, value, unit,
  interval and aggregation scope;
- `RealizedLiquidationSourceRecord` — exchange order/event identity, side,
  price, quantity and USD value;
- `EstimatedLiquiditySourceRecord` — model/provider, price band, side,
  magnitude and estimation confidence.

Confirmed transfers and provider narratives must remain separate. Realized
liquidations and estimated heatmap clusters must remain different record types.

Raw authenticated provider payloads must not be the public domain API and must
not be retained by default.

## ProviderHealth boundary

`ProviderHealth` should report:

- status: `HEALTHY`, `DEGRADED`, `STALE`, `RATE_LIMITED`, `UNAVAILABLE`, or
  `UNKNOWN`;
- last successful receive and event times;
- latency and freshness age;
- sanitized error category, never raw headers/body;
- rate-limit state as remaining/capacity/reset only when non-secret;
- capability-specific degradation.

Health is provider state, not market direction. An unavailable source must not
be converted to a neutral opinion.

## Identity, agreement, and precedence

The canonical cross-provider transfer identity is `(chain, transaction_hash)`.
Transaction hashes must be chain-qualified. If a provider omits the hash, a
lower-confidence fingerprint may support within-provider idempotency, but it
must not silently deduplicate records across providers.

Arkham and Nansen agreement may increase source confidence after deduplication.
Disagreement creates a warning and preserves both provenances. Absence from one
provider is missing evidence, not contradiction.

For derivatives, a native exchange is authoritative for its own execution
market and timestamp. CoinGlass is valuable for cross-exchange aggregation.
Stale aggregate data must not override a fresher native record. No provider
label is ground truth: label confidence, age, and provenance remain visible.

## Freshness model

Every record must retain both event and receive times. Builders use event age,
provider health, and capability-specific TTLs. The proposed initial policy is:

| Domain | Fresh | Stale-but-usable | Unavailable for new inference |
| --- | ---: | ---: | ---: |
| realized liquidation | <= 30 s | <= 2 min | > 2 min |
| funding/OI/price snapshot | <= 60 s | <= 5 min | > 5 min |
| estimated liquidation heatmap | <= 5 min | <= 15 min | > 15 min |
| transfer for immediate flow | <= 15 min | <= 6 h | > 6 h |
| transfer for historical context | <= 6 h | <= 48 h | > 48 h |
| wallet/entity label | <= 24 h | <= 7 d | > 7 d or unknown revision |

These are proposed defaults requiring empirical review. Cached records retain
their original `observed_at`; reading cache never refreshes age.

## Quality model

Source quality should be transparent and bounded. It combines schema
completeness, event freshness, provider health, identifier strength, label
confidence, and independent-source agreement. Agreement may raise confidence
only after deduplication. Provider popularity, directional impact, and paid-plan
status must not themselves increase quality.

## Missing, neutral, stale, and unavailable

- `NEUTRAL`: valid fresh evidence measures no directional imbalance.
- `MISSING`: no record exists for the requested capability/window.
- `STALE`: a record exists but exceeds its fresh TTL.
- `UNAVAILABLE`: provider or entitlement cannot serve the capability.
- `RATE_LIMITED`: temporary provider state with optional cache fallback.

These states are not interchangeable. Partial outage preserves unaffected
capabilities. Rate-limit fallback may use a cache only within its stale-usable
window and must mark it stale. Beyond that window the capability is missing.

## Observation boundaries

### OnChainFlowObservation

Consumes deduplicated transfer records. It may express confirmed exchange
inflow/outflow, wallet/entity category, value, direction, chain, agreement,
freshness, and quality. It must not turn a transfer into an intent narrative.

### WalletIntelligenceObservation

Consumes typed label, balance, history, and behavior records. It may express
smart-money classification, labels, historical behavior, realized/unrealized
context when licensed and available, source confidence, freshness, and quality.
Provider labels remain probabilistic assertions.

### DerivativesObservation

Consumes native and aggregate derivatives records. It may express funding, OI,
OI change, long/short ratios, basis, exchange dispersion, freshness, and
quality. It excludes liquidation event/heatmap semantics.

### LiquidationObservation

Consumes either realized liquidation records or estimated liquidity records,
with an explicit kind discriminator. It may express side, magnitude, distance,
confidence, source/model, freshness, and quality. It must never merge realized
events and heatmap estimates into one confirmed total.

## Expert boundaries

- `OnChainFlowExpert` accepts only on-chain flow observations and evaluates
  directional exchange/entity flow. It cannot import providers, infer wallet
  intent, or make trade decisions.
- `WalletIntelligenceExpert` accepts wallet intelligence observations and
  evaluates behavior/label evidence. It cannot treat labels as truth or count
  transfers already owned by the flow expert.
- `DerivativesExpert` accepts derivatives observations and evaluates leverage,
  crowding, basis, and cross-exchange agreement. It cannot interpret on-chain
  identity or liquidation heatmaps.
- `LiquidationExpert` accepts liquidation observations and separately evaluates
  realized stress and estimated liquidation proximity. It cannot present model
  clusters as executed events.
- `NarrativeExpert` accepts future normalized narrative observations, not
  provider responses. It evaluates corroborated narrative context and cannot
  manufacture facts or override market measurements.

Each emits `ExpertOpinion`; MarketStateEngine synthesizes opinions. Experts do
not call each other and never import provider adapters.

## Failure and fallback policy

Adapters return typed errors: authentication, entitlement, validation,
rate-limit, timeout, provider 4xx/5xx, and parse/version mismatch. Logs contain
provider, capability, status category, timing, and correlation ID only. They do
not contain credentials, authorization headers, cookies, or complete private
responses.

Fallback order is fresh primary -> fresh corroborating provider -> eligible
stale cache -> missing/unavailable. A fallback never changes provider
provenance. Circuit breakers and bounded backoff belong in future adapters;
WR-027A implements neither.

## Alternatives considered

### Experts call providers directly

Rejected because transport, entitlement, schema, and provider failure would
become expert behavior and make cross-provider testing impossible.

### One universal provider dictionary

Rejected because it moves schema ambiguity downstream and permits confirmed
events, inferred labels, and estimated heatmaps to be mixed.

### One observation per provider

Rejected because Experts would still bind to provider identity and duplicated
facts could be counted twice.

### Provider-neutral typed records and domain observations

Selected because it preserves provenance while separating transport,
normalization, fact construction, interpretation, and synthesis.

## Security and licensing consequences

Credentials must be environment/vault supplied, scoped read-only, rotatable,
and absent from logs and domain metadata. The repository currently contains a
hard-coded webhook credential and should receive a separate rotation/remediation
task; this ADR intentionally does not change production.

Provider entitlement and redistribution rules must be reviewed before adapter
implementation. Nansen documents endpoint-specific attribution, restricted,
and prohibited redistribution categories. Arkham and CoinGlass subscription
terms require explicit confirmation for storage, derived redistribution, and
customer-facing output. Only normalized minimum-necessary facts should be
stored.

## Consequences

Positive:

- Experts remain provider-independent;
- missing data is no longer confused with neutral evidence;
- overlap can improve confidence without double counting;
- provider outages and plan limits are explicit;
- security, licensing, and provenance become testable boundaries.

Trade-offs:

- more types and builders than a dictionary-based integration;
- event-time normalization and cross-provider identity require careful work;
- source agreement needs deterministic matching and quality policy;
- each provider still requires a dedicated adapter and contract fixtures;
- licensing can constrain storage and Telegram presentation.

## Implementation sequence

First restore repository/deployment parity and harden current Arkham matching
and observability (Option A). Then introduce pure source contracts/health,
complete normalized native candle sourcing, add CoinGlass in shadow mode, and
build domain observations/Experts. Private Arkham pull and Nansen wallet
intelligence follow after entitlement and licensing confirmation. Production
integration is last and must begin in shadow mode.

No adapter or production integration is authorized by this ADR.
