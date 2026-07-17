# PS-5 Exchange Market Collector Boundary

## Objective

Define the interface between an exchange response adapter and the immutable
`MarketSnapshot` contract. The protocol remains independent of concrete
transport implementations.

```text
External exchange response
        |
        v
Future ExchangeMarketCollector adapter
        |
        v
MarketSnapshot
```

## Interface

`ExchangeMarketCollector` is a runtime-checkable structural protocol with:

- immutable collector metadata;
- a `transform(response) -> MarketSnapshot` operation.

The response is deliberately represented as an opaque mapping. Exchange-
specific schemas belong to future adapter implementations and do not leak into
the normalized snapshot contract.

`ExchangeMarketCollectorMetadata` contains:

- `source`;
- `category`;
- `supported_symbols`.

The category must be `EXCHANGE`. This first boundary accepts only `BINANCE`,
`OKX`, and `GATE`. Supported symbols are non-empty, unique, normalized to
uppercase, and stored as an immutable tuple.

## Adapter-only responsibility

An implementation may map fields from an exchange payload into
`MarketSnapshot`. It must not add intelligence, interpret market conditions,
calculate indicators, evaluate decisions, or execute trades.

## Explicit non-goals

The protocol and metadata boundary contain no:

- networking or live API calls;
- API keys, credentials, or secrets;
- exchange SDK or other external dependency;
- persistence, database, or migration;
- scheduling, polling, retries, or runtime service;
- indicator calculation or signal evaluation;
- order execution, position management, or trading logic;
- dependency on or modification of PS-4 governance.

`BinanceMarketCollector` is the first concrete implementation and keeps its
public HTTP transport outside the protocol. Concrete OKX and Gate collectors
remain future components and should follow the same one-way boundary.
