# PS-2 Early Bird Data Source Audit

## Status and scope

This is a tracked-source audit at `main` commit `6ea65de`. It does not
implement a scanner or candidate builder and does not change production,
Telegram, Hostinger, dependencies, services, or deployment.

Only files returned by `git ls-files` were treated as repository capabilities.
Untracked WR-026C work, the untracked WR-027B inventory, `docs/chat_archive/`,
and any Hostinger-only files were excluded. In particular,
`app/intelligence/snapshot_fact_builder.py` is tracked but imports the absent,
untracked-and-unavailable module `app.intelligence.market_snapshot`; that path
is therefore not a usable GitHub-main data source.

## Safety rule for missing factors

An absent source is **unknown/missing**, not a market observation with score
zero. Missing factors must reduce `data_completeness_score` and be recorded in
factor availability/provenance. Specifically:

- no Arkham webhook means missing whale evidence, not “no whale activity”;
- a current OI snapshot is not an OI change;
- a source error or unsupported symbol is missing, not a neutral market fact;
- one source artifact must not be counted as multiple independent factors.

There is a Phase 1 contract mismatch to resolve before a safe live builder is
implemented: `EarlyBirdCandidate` currently requires all eight numeric factor
scores, and `EarlyBirdEngine` evaluates every one of them. Its warning logic
also describes `whale_activity_score == 0` as no whale activity. Metadata and
completeness alone cannot distinguish a measured zero from an unavailable
factor. A future builder therefore needs an explicit availability mask/status
(and the engine must exclude missing factors), or an approved optional-score
contract extension. Filling missing values with zero and presenting them as
observed market meaning is not acceptable.

## Source overview

| Factor | Tracked raw data | Historical delta | Phase 1 status |
|---|---|---|---|
| Whale activity | Arkham webhook event and stored event rows | Event history exists only for received webhooks; no factor delta function | Conditionally usable |
| OI change | Current multi-exchange OI snapshot | No | Unavailable |
| Funding divergence | Current and recent funding from four exchanges; hub spread | Per-exchange history exists; no persisted hub divergence series required for current spread | Usable now |
| Volume expansion | Binance spot OHLCV candles | Yes, in requested candle window | Derivable after builder policy is defined |
| Relative strength | Binance spot close history for asset and benchmark | Yes, if synchronized series are fetched | Derivable after benchmark/window policy is defined |
| Liquidity event | No order-book, liquidation, or liquidity-map source | No | Unavailable |
| Structure event | Binance spot OHLC candles | Yes, in requested candle window | Derivable after structure policy is defined |
| Momentum shift | Binance spot OHLCV candles | Yes, in requested candle window | Derivable after momentum policy is defined |

“Derivable” means the tracked repository has sufficient raw input, not that a
tracked normalized factor function already exists.

## Factor findings

### 1. `whale_activity_score`

1. **Existing source and function.** `app/main.py::arkham_webhook` receives the
   webhook; `app/sources/manager.py::SourceManager.parse` dispatches it;
   `app/sources/arkham.py::ArkhamAdapter.parse` creates `MarketEvent`;
   `app/engine/pipeline.py::process_event` filters, deduplicates, stores, and
   clusters it. `app/engine/scorer.py::score_event` contains deterministic
   legacy transfer-size/exchange rules, while `app/config_assets.py` provides
   `is_supported_asset`, `get_min_whale`, and `get_asset_weight`.
2. **Actual availability.** Available only when a valid Arkham webhook is
   delivered. The production path accepts the 15 assets in tracked `ASSETS`:
   BTC, ETH, BNB, SOL, XRP, TON, HYPE, LINK, DOGE, AVAX, ADA, TRX, LTC, BCH,
   and SUI. The parser itself accepts other symbols, but the tracked pipeline
   rejects assets outside this registry.
3. **Historical delta.** Accepted events are stored by
   `app/storage/database.py::save_event`; `app/engine/context.py` retains a
   process-local 24-hour event list and `get_cluster` aggregates similar events
   over 30 minutes. There is no tracked Early Bird rolling baseline, persisted
   historical-delta function, or restart-safe cluster reconstruction.
4. **Freshness.** Event-driven at webhook arrival. `MarketEvent` uses naive
   `datetime.utcnow()`, so a builder must attach/normalize UTC explicitly and
   reject stale events using an approved window. Provider event time is not a
   consistently normalized first-class field.
5. **Supported assets.** The production-safe set is the tracked `ASSETS`
   intersection above, not every arbitrary Arkham symbol.
6. **Deterministic normalization.** Yes, conditionally: normalize transfer
   magnitude relative to the asset's `min_whale`, optionally include an
   explicitly defined window aggregate, and preserve event/transaction
   provenance. Legacy `score_event` mixes importance and exchange direction;
   it must not be copied wholesale into a direction-free activity factor.
7. **Missing requirements.** Availability status, event-time policy,
   restart-safe aggregation/deduplication boundary, score cap/formula, and a
   clear rule preventing the same Arkham flow from also masquerading as an
   independent liquidity factor.
8. **Phase 1 fallback.** Populate the factor only for a valid, fresh Arkham
   event. If no webhook exists, mark the factor missing and reduce
   completeness; never emit “zero whale activity.”

### 2. `open_interest_change_score`

1. **Existing source and function.** `app/services/unified_open_interest_hub.py`
   `UnifiedOpenInterestHubService.build` calls `_load_okx`, `_load_binance`,
   `_load_gate`, and `_load_bybit`; `_analytics` calculates current total OI,
   exchange shares, leader, and concentration.
2. **Actual availability.** Current read-only OI magnitude is available from
   whichever public perpetual endpoints succeed. The response explicitly
   reports available exchanges, errors, and UTC `captured_at`.
3. **Historical delta.** Absent. No prior snapshot, persisted series, or
   current-versus-previous calculation exists in the tracked hub.
4. **Freshness.** Live request-time snapshot; freshness is its UTC
   `captured_at`. Cross-exchange calls are concurrent but not exchange-time
   synchronized.
5. **Supported assets.** Dynamic and limited by actual OKX, Binance USD-M,
   Gate USDT perpetual, and Bybit listings. Partial coverage is normal and is
   exposed by the hub.
6. **Deterministic normalization.** **No for OI change.** Current OI magnitude,
   market share, and concentration cannot substitute for change.
7. **Missing requirements.** Timestamped prior snapshots at a defined interval,
   comparable exchange set, delta/window formula, stale/partial-source rules,
   and restart-safe storage or supplied previous snapshot.
8. **Phase 1 fallback.** Mark OI change missing and reduce completeness. Current
   OI may be retained only as provenance/context, never scored as change.

### 3. `funding_divergence_score`

1. **Existing source and function.** `app/services/unified_funding_hub.py`
   `UnifiedFundingHubService.build` combines
   `PerpetualFundingSnapshotService.build`,
   `OKXPerpetualFundingSnapshotService.build`,
   `GatePerpetualFundingSnapshotService.build`, and
   `BybitPerpetualFundingSnapshotService.build`. `_analytics` exposes
   `funding_spread_percent`, consensus, and source coverage; `_divergence`
   classifies the spread as low/moderate/high/extreme.
2. **Actual availability.** Yes when at least one source succeeds, but an
   actual cross-exchange divergence requires at least two comparable active
   execution rows. One exchange is a funding value, not divergence.
3. **Historical delta.** Each exchange service requests recent funding history
   (default 24 samples) and derives a trend. The hub divergence itself is a
   current cross-sectional max-minus-min spread and does not require a time
   delta; no hub-level divergence history is persisted.
4. **Freshness.** Live, read-only build with UTC `captured_at`; individual
   sources also expose current funding and history timestamps.
5. **Supported assets.** Dynamic, depending on USDT/USDC perpetual listings
   and source availability. The safe scanner universe should be the tracked
   `ASSETS` registry intersected with at least two successful markets.
6. **Deterministic normalization.** Yes. A documented monotonic mapping from
   absolute `funding_spread_percent` to 0–100 can reuse the existing thresholds
   or a capped continuous formula. Coverage must affect quality/completeness,
   not the market magnitude.
7. **Missing requirements.** Exact continuous score/cap, minimum exchange
   count, comparable quote/period rules, stale-history policy, and handling of
   partial execution sets.
8. **Phase 1 fallback.** Use only with two or more fresh comparable exchanges;
   otherwise mark missing. Preserve exchange rates, spread, count, and
   `captured_at` as provenance.

### 4. `volume_expansion_score`

1. **Existing source and function.** `app/sources/binance_candle_source.py`
   `BinanceCandleSource.get_candles` retrieves public Binance spot klines and
   `_parse_page` maps OHLCV into immutable `app/domain/candle.py::Candle`.
2. **Actual availability.** Raw volume is available on demand for valid Binance
   spot pairs. No tracked function currently calculates volume expansion.
3. **Historical delta.** Yes: up to 1,000 rows per API page and multiple pages
   can be requested, allowing a recent closed-candle volume to be compared
   with a rolling historical baseline.
4. **Freshness.** Interval-dependent. The source returns candle open timestamps
   and may include the currently forming candle; a builder must use closed
   candles only and record the last closed timestamp.
5. **Supported assets.** Any valid Binance spot pair produced by
   `_normalize_symbol` (USDT by default); not every tracked `ASSETS` member is
   guaranteed to be listed at every time.
6. **Deterministic normalization.** Yes after defining timeframe, closed-candle
   rule, lookback, statistic (for example median/mean), minimum samples, and
   ratio-to-score cap. Raw volume units are comparable only within the same
   asset/pair unless converted to quote notional.
7. **Missing requirements.** Approved formula, timeframe, baseline window,
   insufficient/zero-baseline behavior, outlier policy, and listing check.
8. **Phase 1 fallback.** Derive from fresh closed candles for the same pair and
   timeframe once those policies are approved; otherwise mark missing. Do not
   infer expansion from current price or transfer amount.

### 5. `relative_strength_score`

1. **Existing source and function.** The same
   `BinanceCandleSource.get_candles` provides close-price history for an asset
   and a benchmark. No tracked relative-strength function exists.
2. **Actual availability.** Raw data is available if both asset and selected
   benchmark pairs exist and their closed candles can be aligned.
3. **Historical delta.** Yes, synchronized close-to-close returns can be
   calculated over a requested candle window.
4. **Freshness.** Interval-dependent last closed candle; both series must share
   a common timestamp/window. A stale or missing benchmark makes the factor
   missing.
5. **Supported assets.** Binance spot pairs with adequate history. The
   comparison universe/benchmark is not defined in tracked Early Bird code.
6. **Deterministic normalization.** Yes only after defining benchmark (for
   example BTC or a market basket), timeframe, return window, synchronization,
   and a signed-relative-return to unsigned “interestingness” mapping. The
   factor must not silently become a bullish/bearish recommendation.
7. **Missing requirements.** Benchmark/universe, window, minimum history,
   stablecoin/base-asset policy, delisting gaps, and exact score semantics.
8. **Phase 1 fallback.** Prefer missing until the benchmark policy is approved.
   If Phase 1 explicitly approves BTC as benchmark, use synchronized closed
   candles and record benchmark and window in metadata.

### 6. `liquidity_event_score`

1. **Existing source and function.** No tracked order-book, depth, liquidation,
   liquidation-map, liquidity-pool, or spread-event adapter was found.
   `app/intelligence/observations/liquidity.py::LiquidityObservation` is a
   contract only, not a data source or builder. Arkham may classify an exchange
   inflow/outflow, but that is an on-chain transfer event, not measured market
   liquidity.
2. **Actual availability.** No direct normalized liquidity-event data is
   available from tracked GitHub main.
3. **Historical delta.** Absent.
4. **Freshness.** Not applicable because no source exists.
5. **Supported assets.** None through a tracked liquidity source.
6. **Deterministic normalization.** No, not from current tracked inputs without
   inventing meaning.
7. **Missing requirements.** Approved source (order-book/depth, liquidations,
   or explicit liquidity event), event definition, history/baseline, venue
   aggregation, freshness, quality, and deterministic formula.
8. **Phase 1 fallback.** Mark missing and reduce completeness. Do not reuse an
   Arkham exchange transfer as a second independent liquidity score.

### 7. `structure_event_score`

1. **Existing source and function.** `BinanceCandleSource.get_candles` provides
   OHLC history. `app/intelligence/observations/structure.py` defines the
   immutable `StructureObservation` contract, and Trend Expert consumes it,
   but neither computes structure from raw candles. There is no tracked
   structure builder on main.
2. **Actual availability.** Raw candle highs/lows/closes are available; a
   normalized structure event is not currently produced.
3. **Historical delta.** Yes, candle history supports swing/range comparison.
4. **Freshness.** Last closed candle at the chosen timeframe; current forming
   candle must not be treated as a confirmed break.
5. **Supported assets.** Valid Binance spot pairs with sufficient history.
6. **Deterministic normalization.** Yes after defining pivot/swing rules,
   breakout confirmation, lookback/timeframe, tolerance, and magnitude-to-score
   mapping. Existing observation enums do not supply the missing calculation.
7. **Missing requirements.** Tracked builder, exact BOS/CHOCH/range algorithm,
   multi-timeframe policy, minimum samples, and quality/freshness rules.
8. **Phase 1 fallback.** Either keep missing, or implement a separately reviewed
   single-timeframe closed-candle structure builder before populating it. Do
   not use the Trend Expert's opinion as raw factor input.

### 8. `momentum_shift_score`

1. **Existing source and function.** `BinanceCandleSource.get_candles` provides
   close and volume history. `app/intelligence/observations/momentum.py` defines
   `MomentumObservation` fields such as momentum, acceleration, RSI, MACD
   histogram, and volume change, but is a contract rather than a calculator.
2. **Actual availability.** Raw OHLCV data is available; no tracked momentum
   shift calculation/builder exists.
3. **Historical delta.** Yes, candle sequences permit return, acceleration,
   RSI, or MACD deltas.
4. **Freshness.** Last closed interval; indicator warm-up history is required.
5. **Supported assets.** Valid Binance spot pairs with sufficient continuous
   history.
6. **Deterministic normalization.** Yes after selecting one documented formula,
   timeframe, warm-up, shift threshold, and 0–100 mapping. Combining several
   indicators without policy would be invented semantics.
7. **Missing requirements.** Approved indicator/formula, parameters, baseline,
   minimum samples, timeframe, and distinction between momentum magnitude and
   directional recommendation.
8. **Phase 1 fallback.** Keep missing until a separately tested pure
   closed-candle calculation is approved; then preserve formula/version and
   source timestamps in metadata.

## Other tracked paths reviewed

- `app/engine/live_market.py::get_price` supplies only a current Binance spot
  price. It has no history and cannot support volume, relative strength,
  structure, or momentum deltas by itself.
- `app/engine/market_intelligence.py::build_market_snapshot` reads latest
  database-derived institutional scores via
  `app/engine/institutional_leaders.py::get_institutional_leaders`. These are
  legacy composite outputs, not independent raw Early Bird factors; reusing
  them would introduce circularity and double-counting.
- `app/engine/exchange_stats.py::get_exchange_stats` aggregates stored Arkham
  transfer count/value by entity over a time window. It can support whale-event
  provenance but is not exchange market volume or order-book liquidity.
- `app/domain/perpetual_exchange_registry.py` defines execution/hot-backup/
  intelligence venue metadata. Only the exchanges actually called by the
  funding and OI hubs are live data sources.
- `app/sources/in_memory_candle_source.py::InMemoryCandleSource.get_candles` is
  useful for deterministic tests, not live market coverage.

## Recommended Phase 1 candidate builder

Build an isolated, read-only, availability-aware normalizer before building a
scanner:

1. Accept an explicit asset/event request; do not schedule or scan yet.
2. Restrict the universe to tracked `ASSETS`, then verify each provider listing.
3. Use a real fresh Arkham event for whale activity when present.
4. Use `UnifiedFundingHubService` only when at least two comparable fresh
   exchange rows exist.
5. Fetch synchronized, closed Binance spot candles once for volume, relative
   strength, structure, and momentum; keep each formula/version explicit and
   avoid claiming independence merely because the same OHLCV window yields
   several factors.
6. Leave OI change unavailable until two comparable timestamped OI snapshots
   exist. Leave liquidity unavailable until a direct source exists.
7. Emit per-factor status (`available`, `missing`, `stale`, `unsupported`,
   `error`), source timestamp, source IDs, formula version, and provenance.
8. Calculate completeness from genuinely available factors and quality from
   freshness/coverage. Never convert provider absence into market evidence.
9. Before materializing the current `EarlyBirdCandidate`, extend or accompany
   its contract/engine with an approved missing-factor mask so unavailable
   fields are excluded from contributions and explanations. This is a safety
   prerequisite, not scanner implementation.

The safest immediately usable factors are conditional Arkham whale activity
and multi-exchange funding divergence. OHLCV-derived volume, relative
strength, structure, and momentum are raw-data-ready but need approved pure
normalizers. OI change and liquidity event are unavailable from current
tracked data.

## Verification

- Repository basis: tracked files at `6ea65de` only.
- Production Python changed: **NO**.
- Telegram changed: **NO**.
- Hostinger changed: **NO**.
- Deployment/network/provider calls executed: **NO**.
- Secrets or environment values recorded: **NO**.
