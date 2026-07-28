# PS-3 Step 2 — Early Bird Funding Divergence Integration Report

## Status

Implemented on `ps-3-early-bird-funding-integration` from `origin/main` at
`0a54ea0`. The integration is experimental, local, public read-only, not
merged, and not deployed. It does not affect Telegram, production decisions,
Trade Readiness, or execution.

## Funding source audit

The clean tracked boundary is:

```text
UnifiedFundingHubService.build(asset)
        |
        +-- OKXPerpetualFundingSnapshotService
        +-- PerpetualFundingSnapshotService (Binance USD-M)
        +-- GatePerpetualFundingSnapshotService
        +-- BybitPerpetualFundingSnapshotService (hot backup)
        |
        v
normalized public result mapping
```

The service uses public read-only endpoints without API keys. Venue requests
are concurrent inside one asset evaluation and failures are returned in
`unavailable_exchanges`; one venue failure does not discard successful venue
rows.

The public `build(asset)` API returns:

- asset and overall status;
- successful rows under `exchanges`;
- per-venue failures under `unavailable_exchanges`;
- active execution-set selection;
- analytics, including an existing cross-venue spread;
- a UTC `captured_at` for the aggregate request.

Each normalized row exposes `funding_percent`, already expressed in percentage
points. Underlying adapters also calculate decimal `current_funding_rate`, but
the unified boundary intentionally exposes the normalized percentage value.
The Early Bird factor recalculates spread from the exact fresh rows it uses so
that availability, timestamp provenance, partial failures, and quality share
one deterministic input set. It does not duplicate venue adapters.

### Supported-symbol and availability limitations

There is no static supported-symbol registry. Venue support is discovered by
public endpoint responses. Therefore `UNSUPPORTED` is emitted only when the
unified result explicitly marks the asset or status unsupported. Ordinary
venue failures are never guessed to mean unsupported.

The hub distinguishes successful and failed venue calls, but does not natively
classify `MISSING`, `STALE`, or `UNSUPPORTED`. Those statuses belong to the new
availability-aware factor boundary.

The unified normalizer currently omits per-row `captured_at` and
`funding_time`, while the aggregate response retains one `captured_at` taken
before the venue requests. The factor accepts per-row `observed_at`,
`captured_at`, or `funding_time` when a future compatible result supplies one;
for the current hub it conservatively assigns the aggregate `captured_at` to
each used venue. Consequently the oldest used timestamp is the hub capture
timestamp in the live Phase 1 path. No production funding service was modified
to change that boundary.

## Factor semantics

`funding_divergence` is unsigned opportunity-interest evidence. It describes
cross-venue disagreement and never creates direction, recommendation, BUY,
SELL, LONG, SHORT, entry, TP, SL, or execution advice.

At least two fresh, finite, comparable venue values are required:

```text
spread = max(funding_percent) - min(funding_percent)

spread <= 0.005 percentage points: base score = 0
spread >= 0.100 percentage points: base score = 100
otherwise: linear interpolation between 0.005 and 0.100

if at least one value > 0 and one value < 0:
    add 15

final score = min(base score + bonus, 100)
```

Sign information is retained only as `mixed_sign` and per-venue provenance in
metadata. It is not directional market meaning.

## Availability and freshness

The explicit Phase 1 funding freshness window is **15 minutes**. It is
independent of the candidate builder's generic one-hour aggregate freshness
decay.

- `AVAILABLE`: at least two fresh comparable valid venues;
- `MISSING`: fewer than two valid venues without confirmed structural
  unsupported status;
- `STALE`: at least two comparable values exist but the fresh combination is
  unavailable because values exceed 15 minutes;
- `ERROR`: the measurement has no valid row and provider failures remain;
- `UNSUPPORTED`: only an explicit structural marker is accepted.

A non-available factor never carries a score. Funding failure does not abort
the candle scan or silently become a measured zero. The candidate builder's
legacy structural placeholder remains an explicit internal compatibility
field and its warning is preserved.

For `AVAILABLE`, `observed_at` is the oldest timestamp among the fresh venue
rows used. For `STALE` and `MISSING`, timestamp and quality are provenance only;
the candidate builder excludes their quality from aggregate quality.

## Quality

Quality is bounded to `0..100` and calculated as:

```text
40% venue coverage
35% timestamp coherence
25% data validity and unit-normalization confidence
```

Coverage and validity include partial venue failures in their denominator.
Timestamp coherence decays with the span between the newest and oldest used
fresh rows over the 15-minute window. Unit validity is capped at 90 because
the hub guarantees percentage-point normalization but does not expose an
explicit per-row unit marker. Therefore clean input is not automatically
assigned quality 100, and partial failures reduce quality.

## Scanner integration

For each requested asset the scanner now:

1. calls `UnifiedFundingHubService.build(asset)` once;
2. converts the result through `FundingDivergenceFactor`;
3. fetches and calculates the original candle factors;
4. passes all eight explicit factor values to
   `EarlyBirdCandidateBuilder`;
5. ranks candidates through the existing `EarlyBirdEngine`.

The default hub timeout is eight seconds per venue request, with venue calls
bounded concurrently inside the hub. Asset order and factor processing remain
deterministic. A candle failure still marks that asset failed; a funding
failure produces an `ERROR` factor while the candle candidate can succeed.

Unchanged availability policy:

- whale activity: `MISSING`;
- OI change: `UNSUPPORTED`;
- liquidity event: `UNSUPPORTED`.

Terminal output shows funding availability, score when measured, and used
venue names. Raw provider payloads and raw error strings are not printed or
stored in factor metadata. Error metadata retains only venue keys and a
sanitized availability label.

## Manual read-only comparison

### Before funding integration

The PS-3 Step 1 report recorded this snapshot at
`2026-07-15T08:24:52.217197+00:00`:

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

### After funding integration

Command:

```bash
./venv/bin/python run_early_bird_demo.py --limit 10
```

Sanitized snapshot at `2026-07-15T09:03:44.930362+00:00`:

| Rank | Asset | Opportunity | Priority | Maturity | Funding | Venues |
|---:|---|---:|---:|---:|---:|---:|
| 1 | BTC | 17.76 | 41.44 | 19.98 | 0.00 | 4 |
| 2 | LINK | 13.37 | 39.76 | 14.11 | 0.00 | 4 |
| 3 | NEAR | 12.90 | 39.01 | 10.64 | 24.38 | 4 |
| 4 | SOL | 8.13 | 37.59 | 8.60 | 2.09 | 4 |
| 5 | BNB | 7.44 | 37.41 | 9.35 | 0.00 | 4 |
| 6 | ETH | 9.05 | 37.09 | 1.74 | 17.78 | 4 |
| 7 | PEPE | 7.87 | 36.96 | 8.58 | 15.00 | 2 |
| 8 | DOGE | 7.83 | 36.96 | 4.71 | 0.00 | 4 |
| 9 | SUI | 7.54 | 36.82 | 4.65 | 1.53 | 4 |
| 10 | XRP | 7.67 | 36.64 | 2.85 | 0.00 | 4 |

Funding was `AVAILABLE` for all ten assets; nine used four venues and PEPE
used two. Ten assets succeeded and zero failed.

These are different market-time snapshots, so the ranking delta cannot be
attributed solely to funding. The comparison verifies operational integration,
availability, provenance, and deterministic scoring mechanics only. It does
not demonstrate prediction quality or profitability.

## Files

Created:

- `app/intelligence/early_bird/scanner/funding_factor.py`;
- `test_early_bird_funding_factor.py`;
- `docs/reports/PS-3_STEP_2_REPORT.md`.

Modified:

- `app/intelligence/early_bird/scanner/scanner.py`;
- `app/intelligence/early_bird/scanner/formatter.py`;
- `app/intelligence/early_bird/scanner/__init__.py`;
- `test_early_bird_scanner.py`.

No production pipeline, Telegram, database, repository, Decision Engine,
Trade Readiness, API, requirements, or Hostinger file was modified.

## Verification

Python: `3.9.6`. No dependency or requirements file changed.

Commands:

```bash
PYTHONPYCACHEPREFIX=/tmp/whale_radar_pycache ./venv/bin/python -m py_compile \
  app/intelligence/early_bird/scanner/__init__.py \
  app/intelligence/early_bird/scanner/funding_factor.py \
  app/intelligence/early_bird/scanner/scanner.py \
  app/intelligence/early_bird/scanner/formatter.py \
  run_early_bird_demo.py \
  test_early_bird_funding_factor.py \
  test_early_bird_scanner.py

./venv/bin/python -m unittest -v test_early_bird_funding_factor.py
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
./venv/bin/python run_early_bird_demo.py --limit 10
```

Results:

- Python 3.9 compile: passed;
- funding factor and integration: 23 passed;
- scanner/formatter/dependency boundary: 25 passed;
- candidate builder and availability: 66 passed;
- Early Bird foundation: 61 passed;
- MarketSituation/Fast/Correlation: 58 passed;
- Shadow/Contracts/MarketState: 54 passed;
- total unit tests: 287 passed;
- safe core/filter/parser smoke checks: passed;
- public read-only scan: 10 successful, 0 failed;
- dependency boundary: only the tracked unified hub is imported; the factor
  imports no provider adapter, Telegram, database, repository, decision,
  MarketState, Expert, Arkham, CoinGlass, Nansen, or networking client;
- production pipeline changed: no;
- Hostinger changed or deployed: no.

## Open questions

1. Should a future non-production hub contract preserve each venue's native
   observation timestamp and explicit unit marker?
2. Should symbol support become a tracked capability registry so that
   `UNSUPPORTED` can be distinguished from transient provider errors without
   inference?
3. Should future scans parallelize assets under an explicit global rate and
   concurrency policy, while retaining deterministic result ordering?
4. Which historical outcome-review process should calibrate spread thresholds
   without turning funding divergence into a directional trading signal?
