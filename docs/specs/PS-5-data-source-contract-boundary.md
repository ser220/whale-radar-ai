# PS-5 Data Source Contract Boundary

## Objective

Define a pure immutable language for normalized observations produced by
future external market data collectors. This phase establishes contract
boundaries only; it adds no collector, API client, network call, runtime
execution, persistence, indicator calculation, wallet resolution, or trading
behavior.

## Package boundary

The contracts live in `app.intelligence.data_sources`. This package is separate
from the existing runtime adapters in `app.sources` and has no dependency on
them. It uses only the Python 3.9 standard library and does not import or modify
the PS-4 attachment governance package.

Future integration may follow this one-way flow:

```text
External API response
        |
        v
Future collector / normalizer
        |
        v
Immutable data snapshot contract
        |
        v
Explicit future PS-4 integration boundary
```

The future integration boundary is not implemented here. PS-4 governance
remains independently immutable.

## Source taxonomy

`DataSourceCategory` contains `EXCHANGE`, `DERIVATIVES`, `ON_CHAIN`, `NEWS`,
`SOCIAL`, `ANALYTICS`, and `UNKNOWN`.

`DataSourceType` contains:

- exchange: `BINANCE`, `OKX`, `BYBIT`, `GATE`, `MEXC`, `BITGET`, `KUCOIN`,
  `COINBASE`;
- derivatives: `COINGLASS`;
- on-chain: `ARKHAM`, `NANSEN`;
- analytics: `TRADINGVIEW`;
- future or not-yet-typed sources: `UNKNOWN`.

The category/source matrix is strict. `TRADINGVIEW` is accepted only for
`ANALYTICS`. `UNKNOWN` is accepted only for `NEWS`, `SOCIAL`, and `UNKNOWN`
categories until explicit typed sources are introduced. Every concrete
snapshot also requires its own category: market snapshots are exchange
observations, derivatives snapshots are derivatives observations, whale and
smart-money snapshots are on-chain observations, news snapshots are news
observations, and technical-signal snapshots are analytics observations.

## Immutable snapshots

- `MarketSnapshot`: exchange price, 24-hour volume and change.
- `DerivativesSnapshot`: open interest, funding, long/short ratio and
  liquidation volume.
- `WhaleActivitySnapshot`: an observed wallet movement and source label.
- `SmartMoneySnapshot`: an observed smart-money wallet activity.
- `NewsEventSnapshot`: an external news event classification supplied by a
  future collector.
- `TechnicalSignalSnapshot`: an external TradingView analytical observation,
  including market-structure events, trend observations, or custom indicator
  output.

All listed fields are required. Symbols and assets normalize to uppercase;
other textual facts are trimmed but otherwise preserved. Aware timestamps
normalize to UTC. Naive timestamps fail.

## Numeric invariants

- every numeric value is a finite real number and booleans are rejected;
- price and transfer/activity amounts are greater than zero;
- volume, open interest, long/short ratio and liquidation volume are
  non-negative;
- change and funding rate may be positive, zero or negative.

The contracts do not derive indicators, impact, direction, trading decisions,
or governance outcomes from these facts.

## Serialization

Every snapshot is a frozen dataclass implementing exact `to_dict()`,
`from_dict()`, and deterministic `canonical_json()`. Enum values serialize as
their public strings, datetimes serialize as UTC ISO-8601 strings, and numeric
values normalize to finite floats. Deserialization rejects unknown and missing
fields.

## Explicit non-goals

This boundary does not add API integration, collectors, source discovery,
networking, polling, scheduling, retries, indicator engines, wallet resolvers,
trading execution, databases, repositories, persistence, migrations, or PS-4
contract changes.

TradingView support is observation-only. It does not execute Pine Script,
connect to TradingView APIs, receive webhooks, calculate signals, or open
positions. Future webhook collectors may consume and normalize external data
into `TechnicalSignalSnapshot`, but collectors remain a separate component.
