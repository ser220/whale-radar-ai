"""Normalized liquidity facts without execution or sweep prediction."""

from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional

from app.intelligence.observations.base import (
    Observation,
    bounded_number,
    enum_value,
    non_negative_number,
    optional_non_negative_number,
)
from app.intelligence.observations.enums import LiquiditySide


@dataclass(frozen=True)
class LiquidityObservation(Observation):
    observation_id: str
    asset: str
    source: str
    timeframe: str
    quality: float
    observed_at: datetime
    nearest_liquidity_side: LiquiditySide
    buy_side_liquidity_usd: float
    sell_side_liquidity_usd: float
    liquidity_imbalance: float
    liquidity_quality: float
    distance_to_buy_side_pct: Optional[float] = None
    distance_to_sell_side_pct: Optional[float] = None
    version: int = 1
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    OBSERVATION_TYPE = "liquidity"

    def __post_init__(self) -> None:
        self._validate_common()
        object.__setattr__(
            self,
            "nearest_liquidity_side",
            enum_value(
                LiquiditySide, self.nearest_liquidity_side, "nearest_liquidity_side"
            ),
        )
        object.__setattr__(
            self,
            "buy_side_liquidity_usd",
            non_negative_number(self.buy_side_liquidity_usd, "buy_side_liquidity_usd"),
        )
        object.__setattr__(
            self,
            "sell_side_liquidity_usd",
            non_negative_number(self.sell_side_liquidity_usd, "sell_side_liquidity_usd"),
        )
        object.__setattr__(
            self,
            "distance_to_buy_side_pct",
            optional_non_negative_number(
                self.distance_to_buy_side_pct, "distance_to_buy_side_pct"
            ),
        )
        object.__setattr__(
            self,
            "distance_to_sell_side_pct",
            optional_non_negative_number(
                self.distance_to_sell_side_pct, "distance_to_sell_side_pct"
            ),
        )
        object.__setattr__(
            self,
            "liquidity_imbalance",
            bounded_number(self.liquidity_imbalance, "liquidity_imbalance", -100, 100),
        )
        object.__setattr__(
            self,
            "liquidity_quality",
            bounded_number(self.liquidity_quality, "liquidity_quality", 0, 100),
        )

    def to_dict(self) -> Dict[str, Any]:
        payload = self._common_dict()
        payload.update(
            {
                "nearest_liquidity_side": self.nearest_liquidity_side.value,
                "buy_side_liquidity_usd": self.buy_side_liquidity_usd,
                "sell_side_liquidity_usd": self.sell_side_liquidity_usd,
                "distance_to_buy_side_pct": self.distance_to_buy_side_pct,
                "distance_to_sell_side_pct": self.distance_to_sell_side_pct,
                "liquidity_imbalance": self.liquidity_imbalance,
                "liquidity_quality": self.liquidity_quality,
            }
        )
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "LiquidityObservation":
        payload = cls._payload(data)
        payload["nearest_liquidity_side"] = enum_value(
            LiquiditySide,
            payload.get("nearest_liquidity_side"),
            "nearest_liquidity_side",
        )
        return cls(**payload)
