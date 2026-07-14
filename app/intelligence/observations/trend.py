"""Normalized trend facts without trading inference."""

from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Any, Dict, Mapping

from app.intelligence.observations.base import (
    Observation,
    bounded_number,
    enum_value,
    finite_number,
)
from app.intelligence.observations.enums import TrendBias


@dataclass(frozen=True)
class TrendObservation(Observation):
    observation_id: str
    asset: str
    source: str
    timeframe: str
    quality: float
    observed_at: datetime
    price_change_pct: float
    higher_high: bool
    higher_low: bool
    lower_high: bool
    lower_low: bool
    trend_bias: TrendBias
    trend_strength: float
    distance_from_range_pct: float
    moving_average_alignment: TrendBias
    slope: float
    version: int = 1
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    OBSERVATION_TYPE = "trend"

    def __post_init__(self) -> None:
        self._validate_common()
        for field_name in ("higher_high", "higher_low", "lower_high", "lower_low"):
            if not isinstance(getattr(self, field_name), bool):
                raise TypeError(f"{field_name} must be a bool")
        object.__setattr__(
            self, "price_change_pct", finite_number(self.price_change_pct, "price_change_pct")
        )
        object.__setattr__(
            self, "trend_bias", enum_value(TrendBias, self.trend_bias, "trend_bias")
        )
        object.__setattr__(
            self,
            "trend_strength",
            bounded_number(self.trend_strength, "trend_strength", 0, 100),
        )
        object.__setattr__(
            self,
            "distance_from_range_pct",
            finite_number(self.distance_from_range_pct, "distance_from_range_pct"),
        )
        object.__setattr__(
            self,
            "moving_average_alignment",
            enum_value(
                TrendBias, self.moving_average_alignment, "moving_average_alignment"
            ),
        )
        object.__setattr__(self, "slope", finite_number(self.slope, "slope"))

    def to_dict(self) -> Dict[str, Any]:
        payload = self._common_dict()
        payload.update(
            {
                "price_change_pct": self.price_change_pct,
                "higher_high": self.higher_high,
                "higher_low": self.higher_low,
                "lower_high": self.lower_high,
                "lower_low": self.lower_low,
                "trend_bias": self.trend_bias.value,
                "trend_strength": self.trend_strength,
                "distance_from_range_pct": self.distance_from_range_pct,
                "moving_average_alignment": self.moving_average_alignment.value,
                "slope": self.slope,
            }
        )
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "TrendObservation":
        payload = cls._payload(data)
        payload["trend_bias"] = enum_value(TrendBias, payload.get("trend_bias"), "trend_bias")
        payload["moving_average_alignment"] = enum_value(
            TrendBias,
            payload.get("moving_average_alignment"),
            "moving_average_alignment",
        )
        return cls(**payload)
