"""Pure deterministic conversion of normalized candles into trend facts."""

from dataclasses import dataclass
from statistics import median
from typing import Dict, Optional, Sequence, Tuple

from app.intelligence.builders.candles import Candle
from app.intelligence.builders.trend.policy import TrendObservationBuilderPolicy
from app.intelligence.observations import (
    StructureBreak,
    StructureObservation,
    TrendBias,
    TrendObservation,
)


_PRICE_CHANGE_NORMALIZER_PCT = 5.0
_SLOPE_NORMALIZER_PCT = 1.0
_MA_SEPARATION_NORMALIZER_PCT = 2.0
_INTERVAL_IRREGULARITY_TOLERANCE = 0.10


@dataclass(frozen=True)
class _TrendFacts:
    price_change_pct: float
    short_sma: float
    long_sma: float
    ma_separation_pct: float
    moving_average_alignment: TrendBias
    slope: float
    higher_high: bool
    higher_low: bool
    lower_high: bool
    lower_low: bool
    swing_high: float
    swing_low: float
    trend_bias: TrendBias
    trend_strength: float


class TrendObservationBuilder:
    """Build normalized v1 observations without expert interpretation."""

    def __init__(
        self, policy: Optional[TrendObservationBuilderPolicy] = None
    ) -> None:
        if policy is not None and not isinstance(policy, TrendObservationBuilderPolicy):
            raise TypeError("policy must be a TrendObservationBuilderPolicy")
        self._policy = policy or TrendObservationBuilderPolicy()

    @property
    def policy(self) -> TrendObservationBuilderPolicy:
        return self._policy

    def build(
        self,
        candles: Sequence[Candle],
        *,
        asset: str,
        source: str,
        timeframe: str,
        observation_id_prefix: Optional[str] = None,
    ) -> Tuple[TrendObservation, StructureObservation]:
        values = self._candles(candles)
        normalized_asset = self._text(asset, "asset").upper()
        normalized_source = self._text(source, "source")
        normalized_timeframe = self._text(timeframe, "timeframe")
        prefix = self._prefix(
            observation_id_prefix, normalized_asset, normalized_timeframe
        )

        facts = self._facts(values)
        latest = values[-1]
        range_values = values[-self._policy.range_lookback :]
        range_high = max(item.high for item in range_values)
        range_low = min(item.low for item in range_values)
        distance_from_range_pct = self._distance_from_range(
            latest.close, range_low, range_high
        )

        reference_values = values[-(self._policy.range_lookback + 1) : -1]
        reference_high = max(item.high for item in reference_values)
        reference_low = min(item.low for item in reference_values)
        prior_facts = self._facts(values[:-1]) if len(values) > 1 else None
        structure_break = self._structure_break(
            latest.close,
            reference_high,
            reference_low,
            facts,
            prior_facts,
        )

        metrics = self._data_quality_metrics(values)
        trend_quality = self._trend_quality(metrics)
        structure_quality = self._structure_quality(
            metrics, facts, range_low, range_high, structure_break, latest.close,
            reference_low, reference_high
        )
        structure_observation_quality = self._structure_observation_quality(metrics)
        metadata = self._metadata(
            values,
            facts,
            metrics,
            reference_high,
            reference_low,
        )
        structure_metadata = dict(metadata)
        structure_metadata["higher_timeframe_bias_available"] = False

        timestamp = latest.open_time.isoformat()
        version = self._policy.observation_version
        trend = TrendObservation(
            observation_id=f"{prefix}:trend:v{version}:{timestamp}",
            asset=normalized_asset,
            source=normalized_source,
            timeframe=normalized_timeframe,
            version=version,
            quality=self._bounded(trend_quality),
            observed_at=latest.open_time,
            metadata=metadata,
            price_change_pct=facts.price_change_pct,
            higher_high=facts.higher_high,
            higher_low=facts.higher_low,
            lower_high=facts.lower_high,
            lower_low=facts.lower_low,
            trend_bias=facts.trend_bias,
            trend_strength=facts.trend_strength,
            distance_from_range_pct=distance_from_range_pct,
            moving_average_alignment=facts.moving_average_alignment,
            slope=facts.slope,
        )
        structure = StructureObservation(
            observation_id=f"{prefix}:structure:v{version}:{timestamp}",
            asset=normalized_asset,
            source=normalized_source,
            timeframe=normalized_timeframe,
            version=version,
            quality=self._bounded(structure_observation_quality),
            observed_at=latest.open_time,
            metadata=structure_metadata,
            structure_break=structure_break,
            swing_high=facts.swing_high,
            swing_low=facts.swing_low,
            range_high=range_high,
            range_low=range_low,
            current_price=latest.close,
            higher_timeframe_bias=TrendBias.NEUTRAL,
            structure_quality=self._bounded(structure_quality),
        )
        return trend, structure

    def _candles(self, candles: Sequence[Candle]) -> Tuple[Candle, ...]:
        if isinstance(candles, (str, bytes)):
            raise TypeError("candles must be an iterable of Candle values")
        try:
            values = tuple(candles)
        except TypeError as exc:
            raise TypeError("candles must be an iterable of Candle values") from exc
        if not values:
            raise ValueError("candles must not be empty")
        if len(values) < self._policy.minimum_candles:
            raise ValueError(
                f"at least {self._policy.minimum_candles} candles are required"
            )
        for value in values:
            if type(value) is not Candle:
                raise TypeError("candles must contain only Candle instances")
        for previous, current in zip(values, values[1:]):
            if current.open_time == previous.open_time:
                raise ValueError("duplicate candle open_time is not allowed")
            if current.open_time < previous.open_time:
                raise ValueError("candle open_time values must be strictly increasing")
        return values

    @staticmethod
    def _text(value: str, field_name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string")
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{field_name} must not be empty")
        return normalized

    def _prefix(self, value: Optional[str], asset: str, timeframe: str) -> str:
        if value is None:
            return f"{asset}:{timeframe}"
        return self._text(value, "observation_id_prefix")

    def _facts(self, candles: Sequence[Candle]) -> _TrendFacts:
        analysis = candles[-min(len(candles), self._policy.long_window) :]
        closes = [item.close for item in analysis]
        price_change_pct = 100.0 * (closes[-1] - closes[0]) / closes[0]

        short_values = candles[-min(len(candles), self._policy.short_window) :]
        long_values = candles[-min(len(candles), self._policy.long_window) :]
        short_sma = self._mean([item.close for item in short_values])
        long_sma = self._mean([item.close for item in long_values])
        ma_separation_pct = 100.0 * (short_sma - long_sma) / long_sma
        if len(candles) < self._policy.long_window:
            alignment = TrendBias.NEUTRAL
        elif ma_separation_pct > self._policy.flat_slope_threshold:
            alignment = TrendBias.BULLISH
        elif ma_separation_pct < -self._policy.flat_slope_threshold:
            alignment = TrendBias.BEARISH
        else:
            alignment = TrendBias.NEUTRAL

        slope_values = candles[-min(len(candles), self._policy.slope_window) :]
        slope = self._normalized_slope([item.close for item in slope_values])
        swing = candles[-min(len(candles), 2 * self._policy.swing_lookback) :]
        if len(swing) < 2 * self._policy.swing_lookback:
            previous_block = swing
            current_block = swing
            higher_high = higher_low = lower_high = lower_low = False
        else:
            split = self._policy.swing_lookback
            previous_block = swing[:split]
            current_block = swing[split:]
            previous_high = max(item.high for item in previous_block)
            current_high = max(item.high for item in current_block)
            previous_low = min(item.low for item in previous_block)
            current_low = min(item.low for item in current_block)
            tolerance = self._policy.break_tolerance_pct / 100.0
            higher_high = current_high > previous_high * (1.0 + tolerance)
            lower_high = current_high < previous_high * (1.0 - tolerance)
            higher_low = current_low > previous_low * (1.0 + tolerance)
            lower_low = current_low < previous_low * (1.0 - tolerance)

        swing_high = max(item.high for item in current_block)
        swing_low = min(item.low for item in current_block)
        trend_bias = self._trend_bias(
            price_change_pct,
            slope,
            alignment,
            higher_high,
            higher_low,
            lower_high,
            lower_low,
        )
        trend_strength = self._trend_strength(
            price_change_pct,
            slope,
            ma_separation_pct,
            higher_high,
            higher_low,
            lower_high,
            lower_low,
        )
        return _TrendFacts(
            price_change_pct=price_change_pct,
            short_sma=short_sma,
            long_sma=long_sma,
            ma_separation_pct=ma_separation_pct,
            moving_average_alignment=alignment,
            slope=slope,
            higher_high=higher_high,
            higher_low=higher_low,
            lower_high=lower_high,
            lower_low=lower_low,
            swing_high=swing_high,
            swing_low=swing_low,
            trend_bias=trend_bias,
            trend_strength=trend_strength,
        )

    def _trend_bias(
        self,
        price_change_pct: float,
        slope: float,
        alignment: TrendBias,
        higher_high: bool,
        higher_low: bool,
        lower_high: bool,
        lower_low: bool,
    ) -> TrendBias:
        flat = self._policy.flat_slope_threshold
        bullish = int(price_change_pct > flat) + int(slope > flat)
        bearish = int(price_change_pct < -flat) + int(slope < -flat)
        bullish += int(alignment is TrendBias.BULLISH) + int(higher_high) + int(higher_low)
        bearish += int(alignment is TrendBias.BEARISH) + int(lower_high) + int(lower_low)
        if bullish - bearish >= 2:
            return TrendBias.BULLISH
        if bearish - bullish >= 2:
            return TrendBias.BEARISH
        return TrendBias.NEUTRAL

    @staticmethod
    def _normalized_slope(closes: Sequence[float]) -> float:
        count = len(closes)
        if count < 2:
            return 0.0
        mean_x = (count - 1) / 2.0
        mean_y = sum(closes) / count
        denominator = sum((index - mean_x) ** 2 for index in range(count))
        if denominator == 0.0 or mean_y == 0.0:
            return 0.0
        numerator = sum(
            (index - mean_x) * (value - mean_y)
            for index, value in enumerate(closes)
        )
        return 100.0 * (numerator / denominator) / mean_y

    def _trend_strength(
        self,
        price_change_pct: float,
        slope: float,
        ma_separation_pct: float,
        higher_high: bool,
        higher_low: bool,
        lower_high: bool,
        lower_low: bool,
    ) -> float:
        price = min(abs(price_change_pct) / _PRICE_CHANGE_NORMALIZER_PCT * 100.0, 100.0)
        slope_component = min(abs(slope) / _SLOPE_NORMALIZER_PCT * 100.0, 100.0)
        ma = min(abs(ma_separation_pct) / _MA_SEPARATION_NORMALIZER_PCT * 100.0, 100.0)
        swing = self._swing_consistency(
            higher_high, higher_low, lower_high, lower_low
        )
        return self._bounded(0.30 * price + 0.25 * slope_component + 0.20 * ma + 0.25 * swing)

    @staticmethod
    def _swing_consistency(
        higher_high: bool, higher_low: bool, lower_high: bool, lower_low: bool
    ) -> float:
        if (higher_high and higher_low and not lower_high and not lower_low) or (
            lower_high and lower_low and not higher_high and not higher_low
        ):
            return 100.0
        flags = sum((higher_high, higher_low, lower_high, lower_low))
        bullish_only = (higher_high or higher_low) and not (lower_high or lower_low)
        bearish_only = (lower_high or lower_low) and not (higher_high or higher_low)
        if flags == 1 and (bullish_only or bearish_only):
            return 50.0
        return 0.0

    def _structure_break(
        self,
        close: float,
        reference_high: float,
        reference_low: float,
        current: _TrendFacts,
        prior: Optional[_TrendFacts],
    ) -> StructureBreak:
        tolerance = self._policy.break_tolerance_pct / 100.0
        breaks_high = close > reference_high * (1.0 + tolerance)
        breaks_low = close < reference_low * (1.0 - tolerance)
        prior_bias = prior.trend_bias if prior is not None else TrendBias.NEUTRAL

        if breaks_high:
            if prior_bias is TrendBias.BEARISH:
                return StructureBreak.BULLISH_CHOCH
            if prior_bias is TrendBias.BULLISH:
                return StructureBreak.BULLISH_BOS
            if current.trend_bias is TrendBias.BULLISH or (
                current.moving_average_alignment is TrendBias.BULLISH
            ):
                return StructureBreak.BULLISH_BOS
        elif breaks_low:
            if prior_bias is TrendBias.BULLISH:
                return StructureBreak.BEARISH_CHOCH
            if prior_bias is TrendBias.BEARISH:
                return StructureBreak.BEARISH_BOS
            if current.trend_bias is TrendBias.BEARISH or (
                current.moving_average_alignment is TrendBias.BEARISH
            ):
                return StructureBreak.BEARISH_BOS
        return StructureBreak.NONE

    @staticmethod
    def _distance_from_range(close: float, low: float, high: float) -> float:
        if close > high:
            return 100.0 * (close - high) / high
        if close < low:
            return -100.0 * (low - close) / low
        return 0.0

    def _data_quality_metrics(self, candles: Sequence[Candle]) -> Dict[str, float]:
        count = len(candles)
        count_score = min(
            100.0,
            70.0 + 30.0 * (count - self._policy.minimum_candles) / self._policy.minimum_candles,
        )
        intervals = [
            (current.open_time - previous.open_time).total_seconds()
            for previous, current in zip(candles, candles[1:])
        ]
        median_interval = float(median(intervals))
        if median_interval <= 0.0:
            irregular_ratio = 1.0
        else:
            irregular = sum(
                abs(value - median_interval) / median_interval
                > _INTERVAL_IRREGULARITY_TOLERANCE
                for value in intervals
            )
            irregular_ratio = irregular / len(intervals)
        regularity = 100.0 * (1.0 - irregular_ratio)
        volume = 100.0 * sum(item.volume > 0.0 for item in candles) / count
        active = 100.0 * sum(item.high > item.low for item in candles) / count
        windows = (
            self._policy.short_window,
            self._policy.long_window,
            self._policy.slope_window,
            2 * self._policy.swing_lookback,
            self._policy.range_lookback,
        )
        coverage = sum(min(100.0, 100.0 * count / value) for value in windows) / len(windows)
        return {
            "count_score": self._bounded(count_score),
            "median_interval_seconds": median_interval,
            "irregular_interval_ratio": irregular_ratio,
            "regularity_score": self._bounded(regularity),
            "volume_score": self._bounded(volume),
            "activity_score": self._bounded(active),
            "coverage_score": self._bounded(coverage),
        }

    @staticmethod
    def _trend_quality(metrics: Dict[str, float]) -> float:
        return (
            0.30 * metrics["count_score"]
            + 0.25 * metrics["regularity_score"]
            + 0.15 * metrics["volume_score"]
            + 0.15 * metrics["activity_score"]
            + 0.15 * metrics["coverage_score"]
        )

    @staticmethod
    def _structure_observation_quality(metrics: Dict[str, float]) -> float:
        return (
            0.25 * metrics["count_score"]
            + 0.30 * metrics["regularity_score"]
            + 0.10 * metrics["volume_score"]
            + 0.15 * metrics["activity_score"]
            + 0.20 * metrics["coverage_score"]
        )

    def _structure_quality(
        self,
        metrics: Dict[str, float],
        facts: _TrendFacts,
        range_low: float,
        range_high: float,
        structure_break: StructureBreak,
        close: float,
        reference_low: float,
        reference_high: float,
    ) -> float:
        swing = self._swing_consistency(
            facts.higher_high,
            facts.higher_low,
            facts.lower_high,
            facts.lower_low,
        )
        range_validity = 100.0 if range_high > range_low else 0.0
        if structure_break is not StructureBreak.NONE:
            break_clarity = 100.0
        else:
            tolerance = self._policy.break_tolerance_pct / 100.0
            clearly_inside = (
                close <= reference_high * (1.0 - tolerance)
                and close >= reference_low * (1.0 + tolerance)
            )
            break_clarity = 100.0 if clearly_inside else 50.0
        return (
            0.20 * metrics["count_score"]
            + 0.25 * swing
            + 0.20 * range_validity
            + 0.15 * break_clarity
            + 0.20 * metrics["regularity_score"]
        )

    def _metadata(
        self,
        candles: Sequence[Candle],
        facts: _TrendFacts,
        metrics: Dict[str, float],
        reference_high: float,
        reference_low: float,
    ) -> Dict[str, object]:
        return {
            "candle_count": len(candles),
            "first_open_time": candles[0].open_time.isoformat(),
            "latest_open_time": candles[-1].open_time.isoformat(),
            "median_interval_seconds": metrics["median_interval_seconds"],
            "irregular_interval_ratio": metrics["irregular_interval_ratio"],
            "short_sma": facts.short_sma,
            "long_sma": facts.long_sma,
            "reference_range_high": reference_high,
            "reference_range_low": reference_low,
            "builder_policy_version": self._policy.policy_version,
            "calculation_window": min(len(candles), self._policy.long_window),
        }

    @staticmethod
    def _mean(values: Sequence[float]) -> float:
        return sum(values) / len(values)

    @staticmethod
    def _bounded(value: float) -> float:
        return round(max(0.0, min(100.0, value)), 6)
