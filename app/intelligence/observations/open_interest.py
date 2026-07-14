"""Normalized open-interest facts without derived positioning semantics."""

from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Any, Dict, Mapping

from app.intelligence.observations.base import (
    Observation,
    bounded_number,
    enum_value,
    finite_number,
    non_negative_integer,
    non_negative_number,
)
from app.intelligence.observations.enums import DataTrend


@dataclass(frozen=True)
class OpenInterestObservation(Observation):
    observation_id: str
    asset: str
    source: str
    timeframe: str
    quality: float
    observed_at: datetime
    open_interest: float
    open_interest_change_pct: float
    oi_trend: DataTrend
    price_change_pct: float
    leverage_concentration: float
    exchange_count: int
    version: int = 1
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    OBSERVATION_TYPE = "open_interest"

    def __post_init__(self) -> None:
        self._validate_common()
        object.__setattr__(
            self, "open_interest", non_negative_number(self.open_interest, "open_interest")
        )
        object.__setattr__(
            self,
            "open_interest_change_pct",
            finite_number(self.open_interest_change_pct, "open_interest_change_pct"),
        )
        object.__setattr__(
            self, "oi_trend", enum_value(DataTrend, self.oi_trend, "oi_trend")
        )
        object.__setattr__(
            self, "price_change_pct", finite_number(self.price_change_pct, "price_change_pct")
        )
        object.__setattr__(
            self,
            "leverage_concentration",
            bounded_number(self.leverage_concentration, "leverage_concentration", 0, 100),
        )
        object.__setattr__(
            self,
            "exchange_count",
            non_negative_integer(self.exchange_count, "exchange_count"),
        )

    def to_dict(self) -> Dict[str, Any]:
        payload = self._common_dict()
        payload.update(
            {
                "open_interest": self.open_interest,
                "open_interest_change_pct": self.open_interest_change_pct,
                "oi_trend": self.oi_trend.value,
                "price_change_pct": self.price_change_pct,
                "leverage_concentration": self.leverage_concentration,
                "exchange_count": self.exchange_count,
            }
        )
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "OpenInterestObservation":
        payload = cls._payload(data)
        payload["oi_trend"] = enum_value(DataTrend, payload.get("oi_trend"), "oi_trend")
        return cls(**payload)
