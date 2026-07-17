# PS-5 Binance live smoke runner

## Purpose

The Binance live smoke runner is a small, read-only runtime utility for
verifying that the existing `BinanceMarketCollector` can consume Binance's
public market data and return the existing immutable `MarketSnapshot`.

The runner prints, in order, only the snapshot's `source`, `symbol`, `price`,
`volume_24h`, `change_24h`, and `captured_at` fields.

## Runtime boundary

```text
Binance public ticker response
        |
        v
Existing BinanceMarketCollector
        |
        v
Existing MarketSnapshot
        |
        v
Standard output
```

The CLI always uses the live public collector. It has no fake, fixture, or
offline execution option. Tests do not call Binance: they inject a fake opener
into the existing collector and verify the exact normalized output.

## Exclusions

The utility introduces no contracts and changes no PS-5 model or PS-4
governance component. It does not authenticate, persist data, calculate
indicators, generate decisions, place orders, or execute trading behavior.
