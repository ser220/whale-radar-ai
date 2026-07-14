# WR-026A — Observation Contracts Specification

## Objective

Establish a pure immutable language for normalized market facts consumed by
future independent Experts, without parsing raw payloads or producing trading
interpretations.

## Scope

- Add `app.intelligence.observations`.
- Define the abstract common Observation contract and shared enums.
- Define six typed frozen observation dataclasses.
- Validate identifiers, numeric facts, UTC time, metadata, and versions.
- Provide per-type dictionary serialization and deserialization.
- Add focused standard-library tests and package documentation.

## Out of scope

Observation Builders, candle parsing, exchange clients, live collection,
multi-timeframe aggregation, all concrete Experts, MarketStateEngine
integration, trade readiness, ETA, lifecycle transitions, persistence,
Telegram/API presentation, automatic trading, ML, and LLM calls are explicitly
out of scope. WR-026B is not part of WR-026A.

## Common fields

Every concrete observation exposes:

- `observation_id: str` — trimmed, non-empty.
- `asset: str` — trimmed, non-empty, normalized uppercase.
- `source: str` — trimmed, non-empty.
- `timeframe: str` — trimmed, non-empty.
- `quality: float` — finite, inclusive `0..100`.
- `observed_at: datetime` — aware and normalized to UTC.
- `version: int = 1` — integer at least `1`, boolean rejected.
- `metadata: Mapping[str, Any]` — defensively and recursively frozen.

`Observation` is abstract and cannot be instantiated directly. Every concrete
observation is a frozen dataclass.

## Shared enums

- `StructureBreak`: `NONE`, `BULLISH_BOS`, `BEARISH_BOS`, `BULLISH_CHOCH`,
  `BEARISH_CHOCH`
- `TrendBias`: `BULLISH`, `BEARISH`, `NEUTRAL`
- `FundingBias`: `LONG_CROWDED`, `SHORT_CROWDED`, `BALANCED`, `UNKNOWN`
- `LiquiditySide`: `BUY_SIDE`, `SELL_SIDE`, `BOTH`, `NONE`
- `DataTrend`: `RISING`, `FALLING`, `STABLE`, `UNKNOWN`

These are string-valued enums. Existing `Direction`, `TrendState`, and
`LifecycleState` remain unchanged and are not duplicated.

## TrendObservation

Fields:

- `price_change_pct: float` — finite.
- `higher_high`, `higher_low`, `lower_high`, `lower_low: bool`.
- `trend_bias: TrendBias`.
- `trend_strength: float` — `0..100`.
- `distance_from_range_pct: float` — finite.
- `moving_average_alignment: TrendBias`.
- `slope: float` — finite.

Contradictory structure flags are accepted. The contract calculates no
continuation/reversal probability, signal, or lifecycle state.

## MomentumObservation

Fields:

- `momentum_score: float` — `0..100`.
- `momentum_trend: DataTrend`.
- `acceleration_score: float` — `-100..100`.
- `rsi: Optional[float]` — `0..100` when present.
- `macd_histogram: Optional[float]` — finite when present.
- `volume_change_pct: Optional[float]` — finite when present.

The contract generates no bullish or bearish conclusion.

## StructureObservation

Fields:

- `structure_break: StructureBreak`.
- `swing_high`, `swing_low`, `range_high`, `range_low`, `current_price` —
  optional finite values greater than zero.
- `higher_timeframe_bias: TrendBias`.
- `structure_quality: float` — `0..100`.

When both range endpoints exist, `range_low <= range_high`. When both swing
endpoints exist, `swing_low <= swing_high`. The contract does not infer
correction completion or reversal confirmation.

## FundingObservation

Fields:

- `funding_rate: float` — finite, positive or negative.
- `annualized_funding_pct: Optional[float]` — finite when present.
- `funding_bias: FundingBias`.
- `funding_trend: DataTrend`.
- `exchange_count: int` — integer at least zero, boolean rejected.
- `spread_pct: Optional[float]` — finite and non-negative when present.

The contract produces no trade direction or squeeze prediction.

## OpenInterestObservation

Fields:

- `open_interest: float` — finite and non-negative.
- `open_interest_change_pct: float` — finite.
- `oi_trend: DataTrend`.
- `price_change_pct: float` — finite.
- `leverage_concentration: float` — `0..100`.
- `exchange_count: int` — integer at least zero, boolean rejected.

The contract does not derive new-long/new-short, liquidation, continuation, or
reversal semantics.

## LiquidityObservation

Fields:

- `nearest_liquidity_side: LiquiditySide`.
- `buy_side_liquidity_usd`, `sell_side_liquidity_usd: float` — finite and
  non-negative.
- `distance_to_buy_side_pct`, `distance_to_sell_side_pct: Optional[float]` —
  finite and non-negative when present.
- `liquidity_imbalance: float` — `-100..100`.
- `liquidity_quality: float` — `0..100`.

The contract does not provide entry, target, stop-loss, or sweep predictions.

## Validation

- Numeric fields reject booleans and non-real values.
- Every supplied numeric value must be finite; NaN and infinities fail.
- Per-field ranges and ordering invariants are enforced at construction and
  deserialization.
- Enum fields accept their enum instance or exact public string value.
- Required common strings reject blank and non-string values.
- Naive timestamps fail; aware timestamps normalize to `timezone.utc`.
- Mutable metadata mappings and nested standard collections are copied into
  immutable structures.
- No validation rule turns facts into an Expert opinion or trading conclusion.

## Serialization

Every concrete model implements `to_dict()` and `from_dict()`.

- Enums serialize as public string values.
- `observed_at` serializes as an ISO-8601 UTC string and accepts ISO-8601 or an
  aware `datetime` when loading.
- Metadata serializes as ordinary dictionaries/lists and is frozen again when
  loading.
- `version` is preserved.
- `observation_type` identifies the concrete type and mismatched identifiers
  are rejected by that type's loader.
- A model-to-dict-to-same-model round trip preserves value equality.

No global polymorphic loader or migration framework exists in Phase 1.

## Versioning

Default version is `1`; versions below `1` are invalid. Models preserve but do
not interpret higher versions. Future builders and Experts must explicitly
support and test the versions they produce or consume. No migration is implied.

## Public API

Exported from `app.intelligence.observations`:

- `Observation`
- `StructureBreak`, `TrendBias`, `FundingBias`, `LiquiditySide`, `DataTrend`
- `TrendObservation`, `MomentumObservation`, `StructureObservation`
- `FundingObservation`, `OpenInterestObservation`, `LiquidityObservation`

No top-level `app.intelligence` re-export is required by WR-026A.

## Dependency boundaries

The observations package may import only the Python standard library and its
own observation modules. It must not import Telegram, FastAPI, pipelines,
Arkham, exchange or funding services, databases, repositories, persistence,
networking, `MarketStateEngine`, `ExpertRegistry`, concrete Experts, ML, or LLM
components. No third-party dependency may be added.

## Acceptance criteria

- All required files, schemas, enums, exports, and documentation exist.
- Concrete observations are immutable frozen dataclasses.
- Common and per-schema validation follows this specification.
- Every type round-trips with enums, version, UTC time, and metadata preserved.
- At least the 38 required focused scenarios pass under `unittest`.
- Python 3.9 compilation, WR-024.5/WR-025 regressions, and safe smoke tests pass.
- Import audit and complete diff review show no forbidden dependencies or
  production, Telegram, database, requirements, or archive changes.

## Verification commands

```bash
PYTHONPYCACHEPREFIX=/tmp/whale_radar_pycache ./venv/bin/python -m py_compile \
  app/intelligence/observations/__init__.py \
  app/intelligence/observations/base.py \
  app/intelligence/observations/enums.py \
  app/intelligence/observations/trend.py \
  app/intelligence/observations/momentum.py \
  app/intelligence/observations/structure.py \
  app/intelligence/observations/funding.py \
  app/intelligence/observations/open_interest.py \
  app/intelligence/observations/liquidity.py \
  test_observation_contracts.py

./venv/bin/python -m unittest -v test_observation_contracts.py
./venv/bin/python -m unittest -v test_intelligence_contracts.py
./venv/bin/python -m unittest -v test_market_state_engine.py
./venv/bin/python test_core.py
./venv/bin/python test_filter.py
./venv/bin/python test_parser.py

rg -n '^(from|import) ' app/intelligence/observations
git diff --check
git diff --stat origin/main...HEAD
git diff --name-status origin/main...HEAD
git log --oneline origin/main..HEAD
git status --short
```
