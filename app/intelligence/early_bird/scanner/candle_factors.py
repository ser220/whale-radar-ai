"""Deterministic direction-neutral factors derived from completed candles."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import mean, median
from typing import Any, Iterable, Tuple

from app.domain.candle import Candle
from app.intelligence.early_bird.availability import (
    EarlyBirdFactorValue,
    FactorAvailability,
)
from app.intelligence.early_bird.models import _required_text, _utc_datetime


SOURCE_NAME = "binance-public-spot"
RECOMMENDED_CANDLE_COUNT = 100
VOLUME_BASELINE_COUNT = 20
RELATIVE_STRENGTH_COUNT = 20
STRUCTURE_REFERENCE_COUNT = 20
MOMENTUM_RECENT_COUNT = 3
MOMENTUM_BASELINE_COUNT = 10


_TIMEFRAME_SECONDS = {
    "1s": 1,
    "1m": 60,
    "3m": 180,
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "1h": 3600,
    "2h": 7200,
    "4h": 14400,
    "6h": 21600,
    "8h": 28800,
    "12h": 43200,
    "1d": 86400,
    "3d": 259200,
    "1w": 604800,
}


def timeframe_seconds(timeframe: str) -> int:
    normalized = _required_text(timeframe, "timeframe")
    if normalized not in _TIMEFRAME_SECONDS:
        raise ValueError(
            "timeframe must be a fixed Binance interval supported by the scanner"
        )
    return _TIMEFRAME_SECONDS[normalized]


def _bounded(value: float) -> float:
    return round(min(100.0, max(0.0, float(value))), 6)


@dataclass(frozen=True)
class _PreparedCandles:
    candles: Tuple[Candle, ...]
    malformed_count: int
    raw_count: int
    interval_seconds: int
    evaluated_at: datetime

    @property
    def latest(self) -> Any:
        return self.candles[-1] if self.candles else None

    @property
    def latest_close_at(self) -> Any:
        if self.latest is None:
            return None
        return self.latest.timestamp + timedelta(seconds=self.interval_seconds)


def _prepare(
    candles: Iterable[Candle],
    timeframe: str,
    evaluated_at: datetime,
) -> _PreparedCandles:
    if isinstance(candles, (str, bytes)):
        raise TypeError("candles must be an iterable of Candle objects")
    try:
        raw = tuple(candles)
    except TypeError as exc:
        raise TypeError("candles must be an iterable of Candle objects") from exc

    interval = timeframe_seconds(timeframe)
    evaluated_utc = _utc_datetime(evaluated_at, "evaluated_at")
    valid = tuple(item for item in raw if isinstance(item, Candle))
    malformed_count = len(raw) - len(valid)
    unique = {item.timestamp: item for item in valid}
    ordered = tuple(sorted(unique.values(), key=lambda item: item.timestamp))
    completed = tuple(
        item
        for item in ordered
        if item.timestamp + timedelta(seconds=interval) <= evaluated_utc
    )
    return _PreparedCandles(
        candles=completed,
        malformed_count=malformed_count,
        raw_count=len(raw),
        interval_seconds=interval,
        evaluated_at=evaluated_utc,
    )


def _regularity(series: _PreparedCandles) -> float:
    if len(series.candles) < 2:
        return 0.0
    expected = float(series.interval_seconds)
    regular = sum(
        abs(
            (
                current.timestamp - previous.timestamp
            ).total_seconds()
            - expected
        )
        <= 1.0
        for previous, current in zip(series.candles, series.candles[1:])
    )
    return 100.0 * regular / (len(series.candles) - 1)


def _series_quality(series: _PreparedCandles) -> float:
    count_quality = min(
        100.0,
        len(series.candles) / RECOMMENDED_CANDLE_COUNT * 100.0,
    )
    regularity_quality = _regularity(series)
    validity_quality = (
        100.0
        * (series.raw_count - series.malformed_count)
        / series.raw_count
        if series.raw_count
        else 0.0
    )
    return _bounded(
        0.40 * count_quality
        + 0.40 * regularity_quality
        + 0.20 * validity_quality
    )


def _error(
    factor_name: str,
    reason: str,
    series: _PreparedCandles,
    source: str,
) -> EarlyBirdFactorValue:
    return EarlyBirdFactorValue(
        factor_name=factor_name,
        availability=FactorAvailability.ERROR,
        observed_at=series.latest_close_at,
        source=source,
        quality=_series_quality(series),
        reason=reason,
        metadata={
            "completed_candles": len(series.candles),
            "malformed_candles": series.malformed_count,
        },
    )


def _available(
    factor_name: str,
    score: float,
    observed_at: datetime,
    source: str,
    quality: float,
    metadata: Any,
) -> EarlyBirdFactorValue:
    return EarlyBirdFactorValue(
        factor_name=factor_name,
        availability=FactorAvailability.AVAILABLE,
        score=_bounded(score),
        observed_at=observed_at,
        source=source,
        quality=_bounded(quality),
        metadata=metadata,
    )


def _volume_expansion(
    series: _PreparedCandles,
    source: str,
) -> EarlyBirdFactorValue:
    required = VOLUME_BASELINE_COUNT + 1
    if len(series.candles) < required:
        return _error(
            "volume_expansion",
            "At least 21 completed candles are required for volume expansion.",
            series,
            source,
        )

    latest = series.candles[-1]
    baseline = series.candles[-required:-1]
    baseline_median = float(median(item.volume for item in baseline))
    if baseline_median <= 0.0:
        return _error(
            "volume_expansion",
            "Median baseline volume is zero.",
            series,
            source,
        )

    ratio = latest.volume / baseline_median
    score = _bounded((ratio - 1.0) / 3.0 * 100.0)
    return _available(
        "volume_expansion",
        score,
        series.latest_close_at,
        source,
        _series_quality(series),
        {
            "latest_volume": latest.volume,
            "median_volume": baseline_median,
            "volume_ratio": round(ratio, 6),
            "baseline_candles": VOLUME_BASELINE_COUNT,
            "direction_semantics": "NONE",
        },
    )


def _return_percent(candles: Tuple[Candle, ...]) -> float:
    return (candles[-1].close / candles[0].close - 1.0) * 100.0


def _relative_strength(
    asset: str,
    series: _PreparedCandles,
    benchmark: _PreparedCandles,
    source: str,
) -> EarlyBirdFactorValue:
    factor_name = "relative_strength"
    if asset == "BTC":
        if len(series.candles) < RELATIVE_STRENGTH_COUNT:
            return _error(
                factor_name,
                "At least 20 completed candles are required for relative strength.",
                series,
                source,
            )
        sample = series.candles[-RELATIVE_STRENGTH_COUNT:]
        return _available(
            factor_name,
            50.0,
            sample[-1].timestamp + timedelta(seconds=series.interval_seconds),
            source,
            _series_quality(series),
            {
                "benchmark": "BTCUSDT",
                "benchmark_self_case": True,
                "asset_return_percent": round(_return_percent(sample), 6),
                "benchmark_return_percent": round(_return_percent(sample), 6),
                "excess_return_percent": 0.0,
                "aligned_candles": RELATIVE_STRENGTH_COUNT,
                "direction_semantics": "NONE",
            },
        )

    asset_by_time = {item.timestamp: item for item in series.candles}
    benchmark_by_time = {item.timestamp: item for item in benchmark.candles}
    common_times = tuple(sorted(set(asset_by_time) & set(benchmark_by_time)))
    if len(common_times) < RELATIVE_STRENGTH_COUNT:
        return _error(
            factor_name,
            "Asset and BTC require at least 20 aligned completed candles.",
            series,
            source,
        )

    aligned_times = common_times[-RELATIVE_STRENGTH_COUNT:]
    asset_sample = tuple(asset_by_time[item] for item in aligned_times)
    benchmark_sample = tuple(benchmark_by_time[item] for item in aligned_times)
    asset_return = _return_percent(asset_sample)
    benchmark_return = _return_percent(benchmark_sample)
    excess_return = asset_return - benchmark_return
    score = _bounded((excess_return + 5.0) / 10.0 * 100.0)

    possible_alignment = min(
        RECOMMENDED_CANDLE_COUNT,
        len(series.candles),
        len(benchmark.candles),
    )
    alignment_quality = (
        100.0 * min(len(common_times), possible_alignment) / possible_alignment
        if possible_alignment
        else 0.0
    )
    quality = _bounded(
        0.40 * _series_quality(series)
        + 0.40 * _series_quality(benchmark)
        + 0.20 * alignment_quality
    )
    observed_at = aligned_times[-1] + timedelta(seconds=series.interval_seconds)
    return _available(
        factor_name,
        score,
        observed_at,
        source,
        quality,
        {
            "benchmark": "BTCUSDT",
            "benchmark_self_case": False,
            "asset_return_percent": round(asset_return, 6),
            "benchmark_return_percent": round(benchmark_return, 6),
            "excess_return_percent": round(excess_return, 6),
            "aligned_candles": RELATIVE_STRENGTH_COUNT,
            "alignment_quality": round(alignment_quality, 6),
            "direction_semantics": "NONE",
        },
    )


def _structure_event(
    series: _PreparedCandles,
    source: str,
) -> EarlyBirdFactorValue:
    factor_name = "structure_event"
    required = STRUCTURE_REFERENCE_COUNT + 1
    if len(series.candles) < required:
        return _error(
            factor_name,
            "At least 21 completed candles are required for structure.",
            series,
            source,
        )

    latest = series.candles[-1]
    reference = series.candles[-required:-1]
    reference_high = max(item.high for item in reference)
    reference_low = min(item.low for item in reference)
    reference_range = reference_high - reference_low
    if reference_range <= 0.0:
        return _error(
            factor_name,
            "Reference structure range is zero.",
            series,
            source,
        )

    if latest.close > reference_high:
        direction = "UP"
        distance_percent = (latest.close / reference_high - 1.0) * 100.0
        score = 60.0 + min(distance_percent / 5.0, 1.0) * 40.0
    elif latest.close < reference_low:
        direction = "DOWN"
        distance_percent = (reference_low / latest.close - 1.0) * 100.0
        score = 60.0 + min(distance_percent / 5.0, 1.0) * 40.0
    else:
        direction = "INSIDE"
        distance_percent = 0.0
        half_range = reference_range / 2.0
        nearest_distance = min(
            latest.close - reference_low,
            reference_high - latest.close,
        )
        proximity = 1.0 - nearest_distance / half_range
        score = _bounded(proximity * 50.0)

    return _available(
        factor_name,
        score,
        series.latest_close_at,
        source,
        _series_quality(series),
        {
            "structure_direction": direction,
            "direction_semantics": "METADATA_ONLY",
            "reference_high": reference_high,
            "reference_low": reference_low,
            "latest_close": latest.close,
            "distance_percent": round(distance_percent, 6),
            "reference_candles": STRUCTURE_REFERENCE_COUNT,
        },
    )


def _momentum_shift(
    series: _PreparedCandles,
    source: str,
) -> EarlyBirdFactorValue:
    factor_name = "momentum_shift"
    required = MOMENTUM_RECENT_COUNT + MOMENTUM_BASELINE_COUNT
    if len(series.candles) < required:
        return _error(
            factor_name,
            "At least 13 completed candles are required for momentum shift.",
            series,
            source,
        )

    sample = series.candles[-required:]
    candle_returns = tuple(
        (item.close / item.open - 1.0) * 100.0 for item in sample
    )
    baseline_mean = mean(candle_returns[:MOMENTUM_BASELINE_COUNT])
    recent_mean = mean(candle_returns[-MOMENTUM_RECENT_COUNT:])
    delta = recent_mean - baseline_mean
    magnitude = abs(delta)
    score = _bounded((magnitude - 0.10) / 1.40 * 100.0)
    if delta > 0.0:
        direction = "UP"
    elif delta < 0.0:
        direction = "DOWN"
    else:
        direction = "FLAT"

    return _available(
        factor_name,
        score,
        series.latest_close_at,
        source,
        _series_quality(series),
        {
            "momentum_direction": direction,
            "direction_semantics": "METADATA_ONLY",
            "recent_mean_return_percent": round(recent_mean, 6),
            "baseline_mean_return_percent": round(baseline_mean, 6),
            "delta_percentage_points": round(delta, 6),
            "recent_candles": MOMENTUM_RECENT_COUNT,
            "baseline_candles": MOMENTUM_BASELINE_COUNT,
        },
    )


class CandleFactorCalculator:
    """Create the four Phase 1 candle factors without trade semantics."""

    def build(
        self,
        asset: str,
        candles: Iterable[Candle],
        benchmark_candles: Iterable[Candle],
        *,
        timeframe: str,
        evaluated_at: datetime,
        source: str = SOURCE_NAME,
    ) -> Tuple[EarlyBirdFactorValue, ...]:
        normalized_asset = _required_text(asset, "asset").upper()
        if normalized_asset.endswith("USDT"):
            normalized_asset = normalized_asset[:-4]
        normalized_source = _required_text(source, "source")
        series = _prepare(candles, timeframe, evaluated_at)
        benchmark = (
            series
            if normalized_asset == "BTC"
            else _prepare(benchmark_candles, timeframe, evaluated_at)
        )
        return (
            _volume_expansion(series, normalized_source),
            _relative_strength(
                normalized_asset,
                series,
                benchmark,
                normalized_source,
            ),
            _structure_event(series, normalized_source),
            _momentum_shift(series, normalized_source),
        )
