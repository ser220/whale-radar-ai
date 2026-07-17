# PS-5 Data Source Contract Boundary Report

## Scope

Implemented an additive, contract-only boundary for immutable observations from
future external market data collectors. The work is isolated in
`app.intelligence.data_sources` and is based on `origin/main` commit `51369bd`.

No existing runtime adapter, persistence component, or PS-4 governance
contract was modified.

## Delivered contracts

- `DataSourceCategory` and `DataSourceType` source taxonomies;
- `MarketSnapshot` for exchange observations;
- `DerivativesSnapshot` for derivatives observations;
- `WhaleActivitySnapshot` and `SmartMoneySnapshot` for on-chain observations;
- `NewsEventSnapshot` for external news observations.

Every snapshot is a frozen dataclass with strict source/category pairing,
required-text validation, finite numeric validation, aware timestamp
normalization to UTC, exact dictionary serialization, exact deserialization,
and deterministic canonical JSON.

## Architecture verification

- package imports are restricted to the Python standard library and its own
  relative modules;
- no API client, collector, network request, scheduler, or runtime service is
  present;
- no indicator, wallet resolution, compatibility evaluation, or trading logic
  is present;
- no database, repository, persistence, or migration is present;
- PS-4 remains an independent downstream governance boundary;
- existing contracts and application modules are unchanged.

## Verification results

- `python3 -m unittest -v test_data_source_contracts.py`: 22 tests passed;
- focused PS-4 and intelligence contract regression suite: 108 tests passed;
- `python3 -m compileall -q app/intelligence/data_sources test_data_source_contracts.py`:
  passed;
- `git diff --check`: passed.

The focused PS-5 suite covers all source enums, exchange/derivatives/on-chain
pairing, invalid sources, immutable behavior, exact public shapes, empty
required fields, invalid numeric values, UTC normalization, deterministic
canonical JSON, serialization round trips, and the no-runtime-dependency
architecture boundary.
