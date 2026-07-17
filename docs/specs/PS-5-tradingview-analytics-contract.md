# PS-5 TradingView Analytics Contract

## Purpose

`TechnicalSignalSnapshot` is an immutable record of an analytical observation
that was produced outside Whale Radar AI by TradingView. Examples include BOS,
CHoCH, fair-value gaps, liquidity sweeps, trend observations, and custom Pine
indicator output.

The contract records supplied facts only. The `signal_type`, `direction`, and
`indicator_name` strings retain the external producer's semantics; the
contract does not interpret them or turn them into a trading decision.

## Source boundary

The source identity is fixed to:

- `source_category`: `ANALYTICS`;
- `source`: `TRADINGVIEW`.

Other source/category combinations are rejected. This keeps TradingView
analytics separate from exchange prices, derivatives observations, on-chain
activity, news, and social data.

## Contract invariants

The snapshot is a frozen dataclass. Symbol, timeframe, signal type, direction,
and indicator name must be non-empty. Symbol normalizes to uppercase. `value`
must be a finite real number and may be positive, zero, or negative because its
meaning belongs to the external indicator. Booleans, NaN, and infinities are
rejected.

`captured_at` must be timezone-aware and is normalized to UTC. `to_dict()`,
`from_dict()`, and `canonical_json()` provide exact deterministic
serialization consistent with the other PS-5 data source contracts.

## Explicit non-goals

This contract does not:

- execute or compile Pine Script;
- connect to a TradingView API;
- expose or receive a webhook;
- calculate or generate technical or trading signals;
- place orders or open positions;
- persist observations;
- execute or modify PS-4 governance.

A future webhook collector may receive an external TradingView payload and
normalize it into this contract. That collector is a separate future runtime
component and is not part of this architecture layer.
