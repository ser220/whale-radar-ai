# External data source contracts

`app.intelligence.data_sources` defines immutable normalized snapshots for
future exchange, derivatives, on-chain, news, social, and analytics
collectors. It is a contract-only package and is intentionally separate from
the existing runtime adapters under `app.sources`.

The package uses only the Python standard library. It performs no networking,
collection, indicator calculation, wallet resolution, trading, persistence,
or PS-4 governance execution. Future collectors may convert an external API
payload into one of these snapshots, but collectors are not part of this
boundary.

`TechnicalSignalSnapshot` records externally produced TradingView analytics.
It does not execute Pine Script, connect to TradingView, receive webhooks, or
generate a trading signal. A future webhook collector may normalize an
external payload into this contract, but that collector remains outside this
package.

Every snapshot is a frozen dataclass with strict validation, exact
`to_dict()`/`from_dict()` round trips, UTC timestamps, and deterministic
`canonical_json()` output.
