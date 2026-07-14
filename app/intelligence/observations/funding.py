"""Normalized funding facts without trade or squeeze prediction."""

from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional

from app.intelligence.observations.base import (
    Observation,
    enum_value,
    finite_number,
    non_negative_integer,
    optional_finite_number,
    optional_non_negative_number,
)
from app.intelligence.observations.enums import DataTrend, FundingBias


@dataclass(frozen=True)
class FundingObservation(Observation):
    observation_id: str
    asset: str
    source: str
    timeframe: str
    quality: float
    observed_at: datetime
    funding_rate: float
    funding_bias: FundingBias
    funding_trend: DataTrend
    exchange_count: int
    annualized_funding_pct: Optional[float] = None
    spread_pct: Optional[float] = None
    version: int = 1
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    OBSERVATION_TYPE = "funding"

    def __post_init__(self) -> None:
        self._validate_common()
        object.__setattr__(
            self, "funding_rate", finite_number(self.funding_rate, "funding_rate")
        )
        object.__setattr__(
            self,
            "funding_bias",
            enum_value(FundingBias, self.funding_bias, "funding_bias"),
        )
        object.__setattr__(
            self,
            "funding_trend",
            enum_value(DataTrend, self.funding_trend, "funding_trend"),
        )
        object.__setattr__(
            self,
            "exchange_count",
            non_negative_integer(self.exchange_count, "exchange_count"),
        )
        object.__setattr__(
            self,
            "annualized_funding_pct",
            optional_finite_number(self.annualized_funding_pct, "annualized_funding_pct"),
        )
        object.__setattr__(
            self,
            "spread_pct",
            optional_non_negative_number(self.spread_pct, "spread_pct"),
        )

    def to_dict(self) -> Dict[str, Any]:
        payload = self._common_dict()
        payload.update(
            {
                "funding_rate": self.funding_rate,
                "annualized_funding_pct": self.annualized_funding_pct,
                "funding_bias": self.funding_bias.value,
                "funding_trend": self.funding_trend.value,
                "exchange_count": self.exchange_count,
                "spread_pct": self.spread_pct,
            }
        )
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "FundingObservation":
        payload = cls._payload(data)
        payload["funding_bias"] = enum_value(
            FundingBias, payload.get("funding_bias"), "funding_bias"
        )
        payload["funding_trend"] = enum_value(
            DataTrend, payload.get("funding_trend"), "funding_trend"
        )
        return cls(**payload)
