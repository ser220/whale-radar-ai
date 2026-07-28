"""Read-only orchestration for local Early Bird candle scans."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from types import MappingProxyType
from typing import Any, Dict, Iterable, Mapping as TypingMapping, Optional, Tuple

from app.intelligence.early_bird.availability import (
    EarlyBirdFactorValue,
    FactorAvailability,
)
from app.intelligence.early_bird.builder import (
    EarlyBirdCandidateBuilder,
    EarlyBirdCandidateBuildResult,
)
from app.intelligence.early_bird.engine import EarlyBirdEngine
from app.intelligence.early_bird.models import (
    EarlyBirdAssessment,
    _frozen_mapping,
    _required_text,
    _unique_references,
    _utc_datetime,
)
from app.intelligence.early_bird.scanner.candle_factors import (
    CandleFactorCalculator,
    SOURCE_NAME,
    timeframe_seconds,
)
from app.intelligence.early_bird.scanner.funding_factor import (
    FRESHNESS_WINDOW as FUNDING_FRESHNESS_WINDOW,
    FundingDivergenceFactor,
)
from app.services.unified_funding_hub import UnifiedFundingHubService
from app.sources.binance_candle_source import BinanceCandleSource


DEFAULT_ASSETS = (
    "BTC",
    "ETH",
    "BNB",
    "SOL",
    "XRP",
    "DOGE",
    "SUI",
    "LINK",
    "NEAR",
    "PEPE",
)

DEFAULT_TIMEFRAME = "15m"
DEFAULT_CANDLE_COUNT = 100
DEFAULT_LIMIT = 10


def _asset(value: Any) -> str:
    normalized = _required_text(value, "asset").upper()
    normalized = (
        normalized.replace("/", "")
        .replace("-", "")
        .replace("_", "")
        .replace(" ", "")
    )
    if normalized.endswith("USDT") and len(normalized) > 4:
        normalized = normalized[:-4]
    if not normalized:
        raise ValueError("asset must not be empty")
    return normalized


def _assets(values: Iterable[str]) -> Tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError("assets must be an iterable of asset strings")
    try:
        raw_values = tuple(values)
    except TypeError as exc:
        raise TypeError("assets must be an iterable of asset strings") from exc
    if not raw_values:
        raise ValueError("assets must not be empty")

    result = []
    seen = set()
    for value in raw_values:
        normalized = _asset(value)
        if normalized not in seen:
            result.append(normalized)
            seen.add(normalized)
    return tuple(result)


def _positive_integer(value: Any, field_name: str, minimum: int = 1) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("{0} must be an integer".format(field_name))
    if value < minimum:
        raise ValueError(
            "{0} must be at least {1}".format(field_name, minimum)
        )
    return value


def _error_text(exc: Exception) -> str:
    message = str(exc).strip() or "No error detail was provided."
    return "{0}: {1}".format(type(exc).__name__, message)


@dataclass(frozen=True)
class EarlyBirdScanItem:
    """One ranked asset with its assessment and availability provenance."""

    assessment: EarlyBirdAssessment
    build_result: EarlyBirdCandidateBuildResult
    symbol: str
    timeframe: str
    scanned_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.assessment, EarlyBirdAssessment):
            raise TypeError("assessment must be an EarlyBirdAssessment")
        if not isinstance(self.build_result, EarlyBirdCandidateBuildResult):
            raise TypeError(
                "build_result must be an EarlyBirdCandidateBuildResult"
            )
        normalized_symbol = _asset(self.symbol)
        if self.assessment.candidate_id != self.build_result.candidate.candidate_id:
            raise ValueError("assessment and build_result candidate IDs must match")
        if self.assessment.asset != self.build_result.candidate.asset:
            raise ValueError("assessment and build_result assets must match")
        if normalized_symbol != self.build_result.candidate.asset:
            raise ValueError("symbol must match the candidate asset")
        object.__setattr__(self, "symbol", normalized_symbol)
        object.__setattr__(
            self,
            "timeframe",
            _required_text(self.timeframe, "timeframe"),
        )
        object.__setattr__(
            self,
            "scanned_at",
            _utc_datetime(self.scanned_at, "scanned_at"),
        )


@dataclass(frozen=True)
class EarlyBirdScanResult:
    """Immutable successful rankings and explicit per-asset failures."""

    items: Tuple[EarlyBirdScanItem, ...]
    errors: TypingMapping[str, str]
    started_at: datetime
    completed_at: datetime
    timeframe: str
    requested_assets: Tuple[str, ...]
    successful_assets: Tuple[str, ...]
    failed_assets: Tuple[str, ...]
    metadata: TypingMapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if isinstance(self.items, (str, bytes)):
            raise TypeError("items must be a collection of EarlyBirdScanItem")
        try:
            normalized_items = tuple(self.items)
        except TypeError as exc:
            raise TypeError(
                "items must be a collection of EarlyBirdScanItem"
            ) from exc
        if not all(isinstance(item, EarlyBirdScanItem) for item in normalized_items):
            raise TypeError("items must contain only EarlyBirdScanItem objects")

        if not isinstance(self.errors, Mapping):
            raise TypeError("errors must be a mapping")
        normalized_errors = {}
        for key, value in self.errors.items():
            normalized_key = _asset(key)
            normalized_errors[normalized_key] = _required_text(value, "error")

        started = _utc_datetime(self.started_at, "started_at")
        completed = _utc_datetime(self.completed_at, "completed_at")
        if completed < started:
            raise ValueError("completed_at must not be before started_at")

        requested = _unique_references(self.requested_assets, "requested_assets")
        successful = _unique_references(
            self.successful_assets,
            "successful_assets",
        )
        failed = _unique_references(self.failed_assets, "failed_assets")
        item_symbols = tuple(item.symbol for item in normalized_items)
        if len(set(item_symbols)) != len(item_symbols):
            raise ValueError("ranked items must not contain duplicate assets")
        if not set(item_symbols).issubset(set(successful)):
            raise ValueError("ranked items must be successful assets")
        if set(successful) & set(failed):
            raise ValueError("successful_assets and failed_assets must not overlap")
        if set(successful) | set(failed) != set(requested):
            raise ValueError("successful and failed assets must cover requested assets")
        if set(normalized_errors) != set(failed):
            raise ValueError("errors must match failed_assets")

        object.__setattr__(self, "items", normalized_items)
        object.__setattr__(self, "errors", MappingProxyType(normalized_errors))
        object.__setattr__(self, "started_at", started)
        object.__setattr__(self, "completed_at", completed)
        object.__setattr__(
            self,
            "timeframe",
            _required_text(self.timeframe, "timeframe"),
        )
        object.__setattr__(self, "requested_assets", requested)
        object.__setattr__(self, "successful_assets", successful)
        object.__setattr__(self, "failed_assets", failed)
        object.__setattr__(
            self,
            "metadata",
            _frozen_mapping(self.metadata, "metadata"),
        )


class EarlyBirdScanner:
    """Fetch public candles once per symbol and rank successful candidates."""

    def __init__(
        self,
        candle_source: Any = None,
        factor_calculator: Any = None,
        funding_service: Any = None,
        funding_calculator: Any = None,
        candidate_builder: Any = None,
        engine: Any = None,
    ) -> None:
        self._candle_source = (
            BinanceCandleSource() if candle_source is None else candle_source
        )
        self._factor_calculator = (
            CandleFactorCalculator()
            if factor_calculator is None
            else factor_calculator
        )
        self._funding_service = (
            UnifiedFundingHubService(timeout=8.0)
            if funding_service is None
            else funding_service
        )
        self._funding_calculator = (
            FundingDivergenceFactor()
            if funding_calculator is None
            else funding_calculator
        )
        self._candidate_builder = (
            EarlyBirdCandidateBuilder()
            if candidate_builder is None
            else candidate_builder
        )
        self._engine = EarlyBirdEngine() if engine is None else engine

    def scan(
        self,
        assets: Iterable[str] = DEFAULT_ASSETS,
        *,
        timeframe: str = DEFAULT_TIMEFRAME,
        candle_count: int = DEFAULT_CANDLE_COUNT,
        limit: int = DEFAULT_LIMIT,
        timestamp: Optional[datetime] = None,
    ) -> EarlyBirdScanResult:
        requested_assets = _assets(assets)
        normalized_timeframe = _required_text(timeframe, "timeframe")
        interval_seconds = timeframe_seconds(normalized_timeframe)
        normalized_candle_count = _positive_integer(
            candle_count,
            "candle_count",
            minimum=21,
        )
        normalized_limit = _positive_integer(limit, "limit")
        evaluated_at = (
            datetime.now(timezone.utc)
            if timestamp is None
            else _utc_datetime(timestamp, "timestamp")
        )
        started_at = evaluated_at
        request_limit = normalized_candle_count + 2
        start_time = evaluated_at - timedelta(
            seconds=interval_seconds * request_limit
        )

        cache: Dict[str, Tuple[Any, ...]] = {}
        benchmark_error = None
        try:
            cache["BTC"] = tuple(
                self._candle_source.get_candles(
                    "BTC",
                    normalized_timeframe,
                    start_time,
                    evaluated_at,
                    request_limit,
                )
            )
        except Exception as exc:
            cache["BTC"] = ()
            benchmark_error = _error_text(exc)

        errors: Dict[str, str] = {}
        build_results: Dict[str, EarlyBirdCandidateBuildResult] = {}
        source_name = (
            self._candle_source.source_name()
            if callable(getattr(self._candle_source, "source_name", None))
            else SOURCE_NAME
        )

        for asset in requested_assets:
            try:
                funding_result = self._funding_service.build(asset)
                funding_factor = self._funding_calculator.build(
                    asset,
                    funding_result,
                    evaluated_at=evaluated_at,
                )
            except Exception as exc:
                funding_factor = self._funding_calculator.error(
                    asset,
                    exc,
                    evaluated_at=evaluated_at,
                )

            if asset == "BTC":
                candles = cache["BTC"]
                if benchmark_error is not None:
                    errors[asset] = benchmark_error
                    continue
            else:
                try:
                    candles = tuple(
                        self._candle_source.get_candles(
                            asset,
                            normalized_timeframe,
                            start_time,
                            evaluated_at,
                            request_limit,
                        )
                    )
                except Exception as exc:
                    errors[asset] = _error_text(exc)
                    continue

            try:
                candle_factors = self._factor_calculator.build(
                    asset,
                    candles,
                    cache["BTC"],
                    timeframe=normalized_timeframe,
                    evaluated_at=evaluated_at,
                    source=source_name,
                )
                factor_values = (
                    EarlyBirdFactorValue(
                        "whale_activity",
                        FactorAvailability.MISSING,
                        reason=(
                            "No Arkham webhook input is part of this candle scan."
                        ),
                    ),
                    EarlyBirdFactorValue(
                        "open_interest_change",
                        FactorAvailability.UNSUPPORTED,
                        reason=(
                            "OI change is not implemented from candle data."
                        ),
                    ),
                    funding_factor,
                    EarlyBirdFactorValue(
                        "liquidity_event",
                        FactorAvailability.UNSUPPORTED,
                        reason=(
                            "Market liquidity events are not supported in Step 1."
                        ),
                    ),
                ) + tuple(candle_factors)
                candidate_id = "early-bird:{0}:{1}:{2}".format(
                    asset.lower(),
                    normalized_timeframe,
                    int(evaluated_at.timestamp()),
                )
                build_result = self._candidate_builder.build(
                    factor_values,
                    candidate_id=candidate_id,
                    asset=asset,
                    observed_at=evaluated_at,
                    source="early_bird_public_market_scanner",
                    metadata={
                        "timeframe": normalized_timeframe,
                        "requested_candle_count": normalized_candle_count,
                        "received_candle_count": len(candles),
                        "benchmark": "BTCUSDT",
                        "funding_source": "unified_funding_hub",
                    },
                )
                build_results[candidate_id] = build_result
            except Exception as exc:
                errors[asset] = _error_text(exc)

        assessments = self._engine.rank_candidates(
            tuple(result.candidate for result in build_results.values()),
            limit=normalized_limit,
            timestamp=evaluated_at,
        )
        items = tuple(
            EarlyBirdScanItem(
                assessment=assessment,
                build_result=build_results[assessment.candidate_id],
                symbol=assessment.asset,
                timeframe=normalized_timeframe,
                scanned_at=evaluated_at,
            )
            for assessment in assessments
        )
        successful_set = {
            result.candidate.asset for result in build_results.values()
        }
        successful_assets = tuple(
            asset for asset in requested_assets if asset in successful_set
        )
        failed_assets = tuple(
            asset for asset in requested_assets if asset not in successful_set
        )
        ordered_errors = {
            asset: errors[asset]
            for asset in failed_assets
        }
        completed_at = max(datetime.now(timezone.utc), started_at)
        return EarlyBirdScanResult(
            items=items,
            errors=ordered_errors,
            started_at=started_at,
            completed_at=completed_at,
            timeframe=normalized_timeframe,
            requested_assets=requested_assets,
            successful_assets=successful_assets,
            failed_assets=failed_assets,
            metadata={
                "candle_count": normalized_candle_count,
                "result_limit": normalized_limit,
                "benchmark": "BTCUSDT",
                "benchmark_error": benchmark_error,
                "funding_freshness_window_seconds": int(
                    FUNDING_FRESHNESS_WINDOW.total_seconds()
                ),
                "mode": "read-only-local-experimental",
            },
        )
