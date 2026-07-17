# External data source contracts

`app.intelligence.data_sources` defines immutable normalized snapshots for
future exchange, derivatives, on-chain, news, and social collectors. It is a
contract-only package and is intentionally separate from the existing runtime
adapters under `app.sources`.

The package uses only the Python standard library. It performs no networking,
collection, indicator calculation, wallet resolution, trading, persistence,
or PS-4 governance execution. Future collectors may convert an external API
payload into one of these snapshots, but collectors are not part of this
boundary.

Every snapshot is a frozen dataclass with strict validation, exact
`to_dict()`/`from_dict()` round trips, UTC timestamps, and deterministic
`canonical_json()` output.
