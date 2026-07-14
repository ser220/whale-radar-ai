"""Normalized momentum facts without directional conclusions."""

from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional

from app.intelligence.observations.base import (
    Observation,
    bounded_number,
    enum_value,
    optional_bounded_number,
    optional_finite_number,
)
from app.intelligence.observations.enums import DataTrend


@dataclass(frozen=True)
class MomentumObservation(Observation):
    observation_id: str
    asset: str
    source: str
    timeframe: str
    quality: float
    observed_at: datetime
    momentum_score: float
    momentum_trend: DataTrend
    acceleration_score: float
    rsi: Optional[float] = None
    macd_histogram: Optional[float] = None
    volume_change_pct: Optional[float] = None
    version: int = 1
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    OBSERVATION_TYPE = "momentum"

    def __post_init__(self) -> None:
        self._validate_common()
        object.__setattr__(
            self,
            "momentum_score",
            bounded_number(self.momentum_score, "momentum_score", 0, 100),
        )
        object.__setattr__(
            self,
            "momentum_trend",
            enum_value(DataTrend, self.momentum_trend, "momentum_trend"),
        )
        object.__setattr__(
            self,
            "acceleration_score",
            bounded_number(self.acceleration_score, "acceleration_score", -100, 100),
        )
        object.__setattr__(self, "rsi", optional_bounded_number(self.rsi, "rsi", 0, 100))
        object.__setattr__(
            self,
            "macd_histogram",
            optional_finite_number(self.macd_histogram, "macd_histogram"),
        )
        object.__setattr__(
            self,
            "volume_change_pct",
            optional_finite_number(self.volume_change_pct, "volume_change_pct"),
        )

    def to_dict(self) -> Dict[str, Any]:
        payload = self._common_dict()
        payload.update(
            {
                "momentum_score": self.momentum_score,
                "momentum_trend": self.momentum_trend.value,
                "acceleration_score": self.acceleration_score,
                "rsi": self.rsi,
                "macd_histogram": self.macd_histogram,
                "volume_change_pct": self.volume_change_pct,
            }
        )
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "MomentumObservation":
        payload = cls._payload(data)
        payload["momentum_trend"] = enum_value(
            DataTrend, payload.get("momentum_trend"), "momentum_trend"
        )
        return cls(**payload)
