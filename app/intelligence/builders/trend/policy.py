"""Immutable validated policy for Phase 1 trend observation building."""

from dataclasses import dataclass
import math
from numbers import Real


def _window(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 2:
        raise ValueError(f"{field_name} must be at least 2")
    return value


def _finite_non_negative(value: Real, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{field_name} must be a real number")
    normalized = float(value)
    if not math.isfinite(normalized) or normalized < 0.0:
        raise ValueError(f"{field_name} must be finite and non-negative")
    return normalized


def _percentage(value: Real, field_name: str) -> float:
    normalized = _finite_non_negative(value, field_name)
    if normalized > 100.0:
        raise ValueError(f"{field_name} must be between 0 and 100")
    return normalized


@dataclass(frozen=True)
class TrendObservationBuilderPolicy:
    """All thresholds used by the deterministic builder."""

    minimum_candles: int = 20
    short_window: int = 5
    long_window: int = 20
    slope_window: int = 10
    swing_lookback: int = 5
    range_lookback: int = 20
    break_tolerance_pct: float = 0.10
    flat_slope_threshold: float = 0.05
    weak_trend_threshold: float = 35.0
    strong_trend_threshold: float = 70.0
    policy_version: str = "1.0"
    observation_version: int = 1

    def __post_init__(self) -> None:
        for field_name in (
            "minimum_candles",
            "short_window",
            "long_window",
            "slope_window",
            "swing_lookback",
            "range_lookback",
        ):
            object.__setattr__(
                self, field_name, _window(getattr(self, field_name), field_name)
            )
        for field_name in ("break_tolerance_pct", "flat_slope_threshold"):
            object.__setattr__(
                self,
                field_name,
                _finite_non_negative(getattr(self, field_name), field_name),
            )
        for field_name in ("weak_trend_threshold", "strong_trend_threshold"):
            object.__setattr__(
                self, field_name, _percentage(getattr(self, field_name), field_name)
            )

        if self.long_window < self.short_window:
            raise ValueError("long_window must be greater than or equal to short_window")
        if self.minimum_candles < self.long_window:
            raise ValueError("minimum_candles must be at least long_window")
        if self.slope_window > self.minimum_candles:
            raise ValueError("slope_window must not exceed minimum_candles")
        if 2 * self.swing_lookback > self.minimum_candles:
            raise ValueError("minimum_candles must cover two swing_lookback blocks")
        if self.range_lookback > self.minimum_candles:
            raise ValueError("range_lookback must not exceed minimum_candles")
        if self.weak_trend_threshold > self.strong_trend_threshold:
            raise ValueError(
                "weak_trend_threshold must not exceed strong_trend_threshold"
            )
        if self.observation_version != 1:
            raise ValueError("Phase 1 supports only observation_version 1")
        if not isinstance(self.policy_version, str):
            raise TypeError("policy_version must be a string")
        if not self.policy_version.strip():
            raise ValueError("policy_version must not be empty")
        object.__setattr__(self, "policy_version", self.policy_version.strip())
