# PS-5 Binance Public Market Collector

## Purpose

`BinanceMarketCollector` is the first live exchange adapter implementing the
`ExchangeMarketCollector` boundary. It retrieves public Binance Spot 24-hour
ticker observations for `BTCUSDT` and `ETHUSDT` and returns the existing
immutable `MarketSnapshot` contract.

```text
Binance public HTTP response
        |
        v
BinanceMarketCollector
        |
        v
MarketSnapshot
```

## Public endpoint

The adapter performs an unauthenticated `GET` request to:

```text
https://data-api.binance.vision/api/v3/ticker/24hr?symbol=<SYMBOL>
```

This is Binance's market-data-only REST host. The adapter has no API-key,
secret, token, signing, account, order, or authentication configuration.
Timeouts are explicit and configurable; the default is 10 seconds.

## Deterministic transformation

The adapter extracts only Binance-provided fields:

- `symbol`;
- `lastPrice` as `price`;
- `volume` as `volume_24h`;
- `priceChangePercent` as `change_24h`;
- `closeTime` as the UTC `captured_at` timestamp.

The transformation does not use the local clock and ignores unrelated Binance
fields. Required values, supported symbols, numeric finiteness, positive price,
non-negative volume, and the millisecond timestamp are validated. A response
whose symbol does not match the requested symbol is rejected.

## Failure boundary

Network timeouts, other transport failures, non-success HTTP statuses, invalid
UTF-8 or JSON, non-object payloads, and invalid ticker fields are reported as
typed collector errors. Tests inject a fake standard-library-compatible opener
and do not perform live network calls.

## Explicit non-goals

The adapter contains no:

- authenticated or account endpoint;
- API keys or credentials;
- order creation, cancellation, or position management;
- persistence, database, cache, or migration;
- indicator calculation, signal evaluation, or AI logic;
- modification or execution of PS-4 governance.

Future live exchange adapters should preserve this separation: isolate
transport, validate source-specific input, and emit an existing PS-5 snapshot
without adding decisions.
