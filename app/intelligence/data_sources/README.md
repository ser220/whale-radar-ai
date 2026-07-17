# External data source contracts

`app.intelligence.data_sources` defines immutable normalized snapshots for
exchange, derivatives, on-chain, news, social, and analytics observations. Its
snapshot modules are contract-only and remain separate from runtime behavior.
The nested `collectors` package contains explicitly isolated source adapters.

The snapshot contracts use only the Python standard library. They perform no
networking, collection, indicator calculation, wallet resolution, trading,
persistence, or PS-4 governance execution. Collector adapters may convert an
external payload into a snapshot but cannot move runtime behavior into the
contracts.

`TechnicalSignalSnapshot` records externally produced TradingView analytics.
It does not execute Pine Script, connect to TradingView, receive webhooks, or
generate a trading signal. A future webhook collector may normalize an
external payload into this contract, but that collector remains outside this
package.

Every snapshot is a frozen dataclass with strict validation, exact
`to_dict()`/`from_dict()` round trips, UTC timestamps, and deterministic
`canonical_json()` output.

## Collector interfaces

`app.intelligence.data_sources.collectors` contains contract-only adapter
interfaces. `ExchangeMarketCollector` declares how a future Binance, OKX, or
Gate adapter accepts an already-supplied external response and returns a
`MarketSnapshot`. Its immutable metadata declares the source, exchange
category, and supported symbols.

The interface itself performs no networking. Concrete adapters implement it
as a transformation boundary without intelligence, decisions, persistence, or
trading behavior.

## Binance public adapter

`BinanceMarketCollector` is the first concrete exchange adapter. It uses the
public market-data-only Binance host and `GET /api/v3/ticker/24hr` for
`BTCUSDT` and `ETHUSDT`. It sends no API key or authentication data. Networking
and timeout handling remain inside the adapter, which maps Binance's supplied
24-hour values and close timestamp into `MarketSnapshot`.
