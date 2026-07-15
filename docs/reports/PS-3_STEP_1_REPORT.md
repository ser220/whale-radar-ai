# PS-3 Step 1 — First Working Early Bird Scanner Report

## Status

Implemented on `ps-3-first-working-early-bird` from `origin/main` at
`14df5d4`. The scanner is experimental, read-only, local-only, not merged, and
not deployed. It does not affect Telegram or production decisions.

## Scanner architecture

```text
approved base assets
        |
        v
Binance public USDT spot candles
        |
        v
completed-candle factor calculator
        |
        v
EarlyBirdFactorValue[8]
        |
        v
EarlyBirdCandidateBuilder
        |
        v
EarlyBirdEngine ranking
        |
        v
plain-text local output
```

`EarlyBirdScanner` fetches the BTC benchmark once, fetches every other
requested asset once, records per-asset failures, ranks successful candidates,
and returns immutable `EarlyBirdScanItem` and `EarlyBirdScanResult` objects.
A result limit restricts displayed ranked items without misclassifying valid
unranked assets as failures.

No Arkham, CoinGlass, Nansen, private API, OI, funding, liquidity, database,
Telegram, Decision Engine, Trade Readiness, Expert, or MarketStateEngine path
is called.

## Default scan policy

- assets: `BTC, ETH, BNB, SOL, XRP, DOGE, SUI, LINK, NEAR, PEPE`;
- quote: Binance `USDT` spot;
- timeframe: `15m`;
- requested history: `100` candles plus two retrieval-buffer rows;
- calculation input: completed candles only;
- factor timestamp: latest measured candle close time, calculated as tracked
  candle open time plus the fixed timeframe duration;
- benchmark: `BTCUSDT`, retrieved once and reused;
- caller asset override: supported;
- duplicate assets: deterministically deduplicated in first-seen order.

The default universe is explicit; the scanner does not discover or silently
add assets.

## Implemented factors

### Volume expansion

Uses the latest completed candle and the preceding 20 completed candles.

```text
baseline = median(previous_20.volume)
ratio = latest.volume / baseline

ratio <= 1.0: score = 0
ratio >= 4.0: score = 100
otherwise: score = 100 * (ratio - 1) / 3
```

A zero median produces `ERROR`, not a score.

### Relative strength

Uses the latest 20 aligned completed asset/BTC candles.

```text
asset_return = 100 * (asset_last_close / asset_first_close - 1)
btc_return = 100 * (btc_last_close / btc_first_close - 1)
excess = asset_return - btc_return
score = clamp(100 * (excess + 5) / 10, 0, 100)
```

Therefore `-5%` excess maps to 0, `0%` to 50, and `+5%` to 100. Fewer than 20
exactly timestamp-aligned candles produces `ERROR`. BTC uses score 50 and
explicit `benchmark_self_case` metadata.

### Structure event

The latest completed close is compared with the high/low range of the preceding
20 completed candles.

- above reference high: `60 + 40 * min(distance_percent / 5, 1)`;
- below reference low: `60 + 40 * min(distance_percent / 5, 1)`;
- inside range: 0 at range centre, increasing linearly to 50 at the nearest
  boundary.

Direction (`UP`, `DOWN`, `INSIDE`) is metadata only. Score is unsigned
structural activity and has no trade meaning. A zero reference range produces
`ERROR`.

### Momentum shift

Uses per-candle open-to-close returns from 13 completed candles.

```text
baseline = mean(first 10 candle returns)
recent = mean(latest 3 candle returns)
delta = recent - baseline
magnitude = abs(delta)

magnitude <= 0.10 percentage points: score = 0
magnitude >= 1.50 percentage points: score = 100
otherwise: score = 100 * (magnitude - 0.10) / 1.40
```

`UP`, `DOWN`, or `FLAT` is metadata only. Score represents magnitude, not
direction.

## Factor availability

Every successful scan explicitly supplies all eight canonical values:

- `AVAILABLE`: volume expansion, relative strength, structure event, momentum
  shift when their input requirements pass;
- `MISSING`: whale activity and funding divergence because those inputs are not
  part of this candle scan;
- `UNSUPPORTED`: OI change and liquidity event;
- `ERROR`: any candle factor whose samples, baseline, alignment, or calculation
  are invalid.

With all four candle factors available, completeness is:

```text
100 * 4 AVAILABLE / (4 AVAILABLE + 2 MISSING) = 66.666667
```

The two `UNSUPPORTED` factors are excluded. Missing/unsupported/error states
remain visible in `EarlyBirdCandidateBuildResult`; their candidate field zero
is structural only.

The terminal formatter suppresses the legacy engine sentence “No whale
activity is present” when whale availability is not `AVAILABLE`. It displays
the correct explicit builder warning that whale input is missing.

## Quality

Quality is calculated, not assigned blindly.

For one candle series:

```text
count_quality = min(100, completed_count / 100 * 100)
regularity_quality = percent of adjacent opens exactly one timeframe apart
validity_quality = valid Candle rows / all supplied rows * 100

series_quality = 40% count_quality
               + 40% regularity_quality
               + 20% validity_quality
```

Relative-strength quality is `40%` asset-series quality, `40%` BTC-series
quality, and `20%` alignment quality. Irregular or malformed input therefore
reduces quality. Freshness is subsequently calculated by the approved candidate
builder from actual factor timestamps.

## Local formatter and demo

`run_early_bird_demo.py` supports:

```bash
./venv/bin/python run_early_bird_demo.py \
  --assets BTC,ETH,SOL \
  --timeframe 15m \
  --limit 10
```

It has no import-time scan, daemon, scheduler, persistence, or database write.
It exits non-zero only when the result contains no successful items. Output is
plain terminal text with ranks, Opportunity, Priority, Maturity, effective
quality, factor availability, reasons, warnings, and separate asset errors.

## Manual read-only verification

Command:

```bash
./venv/bin/python run_early_bird_demo.py --limit 10
```

Sanitized snapshot:

- scan timestamp: `2026-07-15T08:24:52.217197+00:00`;
- successful assets: `10`;
- failed assets: `0`;
- availability for every ranked asset: volume/relative strength/structure/
  momentum available; whale/funding missing; OI/liquidity unsupported;
- no credentials, private headers, account access, or writes were used.

| Rank | Asset | Opportunity | Priority | Maturity |
|---:|---|---:|---:|---:|
| 1 | LINK | 17.96 | 37.85 | 22.47 |
| 2 | BNB | 11.41 | 36.86 | 25.73 |
| 3 | NEAR | 10.57 | 35.37 | 17.36 |
| 4 | BTC | 9.60 | 35.12 | 15.92 |
| 5 | SOL | 9.50 | 35.05 | 15.76 |
| 6 | ETH | 9.93 | 34.41 | 12.04 |
| 7 | PEPE | 6.82 | 33.81 | 14.34 |
| 8 | SUI | 7.27 | 33.71 | 10.04 |
| 9 | DOGE | 7.17 | 33.25 | 7.16 |
| 10 | XRP | 6.93 | 32.78 | 4.19 |

This single observation verifies read-only operation and real data flow only.
It is not evidence of profitability, prediction quality, or trade suitability.

## Files created

- `app/intelligence/early_bird/scanner/__init__.py`
- `app/intelligence/early_bird/scanner/candle_factors.py`
- `app/intelligence/early_bird/scanner/scanner.py`
- `app/intelligence/early_bird/scanner/formatter.py`
- `run_early_bird_demo.py`
- `test_early_bird_candle_factors.py`
- `test_early_bird_scanner.py`
- `docs/reports/PS-3_STEP_1_REPORT.md`

No existing production file was modified.

## Verification

Python: 3.9.6. No third-party dependency added.

```bash
PYTHONPYCACHEPREFIX=/tmp/whale_radar_pycache ./venv/bin/python -m py_compile \
  app/intelligence/early_bird/scanner/__init__.py \
  app/intelligence/early_bird/scanner/candle_factors.py \
  app/intelligence/early_bird/scanner/scanner.py \
  app/intelligence/early_bird/scanner/formatter.py \
  run_early_bird_demo.py \
  test_early_bird_candle_factors.py \
  test_early_bird_scanner.py

./venv/bin/python -m unittest -v test_early_bird_candle_factors.py
./venv/bin/python -m unittest -v test_early_bird_scanner.py
./venv/bin/python -m unittest -v test_early_bird_candidate_builder.py
./venv/bin/python -m unittest -v test_early_bird_availability.py
./venv/bin/python -m unittest -v test_early_bird.py
./venv/bin/python -m unittest -v test_market_situation.py
./venv/bin/python -m unittest -v test_fast_intelligence.py
./venv/bin/python -m unittest -v test_intelligence_correlation.py
./venv/bin/python -m unittest -v test_shadow_intelligence.py
./venv/bin/python -m unittest -v test_intelligence_contracts.py
./venv/bin/python -m unittest -v test_market_state_engine.py

./venv/bin/python test_core.py
./venv/bin/python test_filter.py
./venv/bin/python test_parser.py
```

Results:

- Python 3.9 compile: passed;
- candle factors: 18 passed;
- scanner/formatter/dependency boundary: 22 passed;
- existing Early Bird and intelligence regressions: 239 passed;
- total unittest tests: 279 passed;
- safe core/filter/parser smoke checks: passed;
- one real public Binance read-only scan: 10 successful, 0 failed.

## Production safety

- Production decision logic changed: **NO**
- Production pipeline changed: **NO**
- Telegram changed: **NO**
- Database/repository changed: **NO**
- Hostinger changed/deployed: **NO**
- Arkham/CoinGlass/Nansen/private APIs called: **NO**
- OI magnitude treated as OI change: **NO**
- BUY/SELL/LONG/SHORT/entry/TP/SL created: **NO**
- Dependency/requirements changed: **NO**

## Open questions

1. Should candle volume eventually use quote-volume notional rather than base
   asset volume for cross-asset comparability?
2. Which outcome-review process will calibrate the 5% structure distance cap
   and momentum thresholds without turning the scanner into a signal engine?
3. Should benchmark-relative strength eventually compare against a market
   basket rather than BTC only?
4. Which approved source-specific freshness windows should replace the generic
   builder policy?
5. Should a future local scan retain non-top successful candidates in a
   separate immutable collection rather than only `successful_assets`?
