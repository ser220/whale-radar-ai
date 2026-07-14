"""Normalized price-structure facts without confirmation inference."""

from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional

from app.intelligence.observations.base import (
    Observation,
    bounded_number,
    enum_value,
    optional_finite_number,
)
from app.intelligence.observations.enums import StructureBreak, TrendBias


def _optional_positive(value: Optional[float], field_name: str) -> Optional[float]:
    normalized = optional_finite_number(value, field_name)
    if normalized is not None and normalized <= 0.0:
        raise ValueError(f"{field_name} must be greater than 0")
    return normalized


@dataclass(frozen=True)
class StructureObservation(Observation):
    observation_id: str
    asset: str
    source: str
    timeframe: str
    quality: float
    observed_at: datetime
    structure_break: StructureBreak
    higher_timeframe_bias: TrendBias
    structure_quality: float
    swing_high: Optional[float] = None
    swing_low: Optional[float] = None
    range_high: Optional[float] = None
    range_low: Optional[float] = None
    current_price: Optional[float] = None
    version: int = 1
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    OBSERVATION_TYPE = "structure"

    def __post_init__(self) -> None:
        self._validate_common()
        object.__setattr__(
            self,
            "structure_break",
            enum_value(StructureBreak, self.structure_break, "structure_break"),
        )
        object.__setattr__(
            self,
            "higher_timeframe_bias",
            enum_value(TrendBias, self.higher_timeframe_bias, "higher_timeframe_bias"),
        )
        object.__setattr__(
            self,
            "structure_quality",
            bounded_number(self.structure_quality, "structure_quality", 0, 100),
        )
        for field_name in (
            "swing_high",
            "swing_low",
            "range_high",
            "range_low",
            "current_price",
        ):
            object.__setattr__(
                self, field_name, _optional_positive(getattr(self, field_name), field_name)
            )
        if (
            self.range_low is not None
            and self.range_high is not None
            and self.range_low > self.range_high
        ):
            raise ValueError("range_low must be less than or equal to range_high")
        if (
            self.swing_low is not None
            and self.swing_high is not None
            and self.swing_low > self.swing_high
        ):
            raise ValueError("swing_low must be less than or equal to swing_high")

    def to_dict(self) -> Dict[str, Any]:
        payload = self._common_dict()
        payload.update(
            {
                "structure_break": self.structure_break.value,
                "swing_high": self.swing_high,
                "swing_low": self.swing_low,
                "range_high": self.range_high,
                "range_low": self.range_low,
                "current_price": self.current_price,
                "higher_timeframe_bias": self.higher_timeframe_bias.value,
                "structure_quality": self.structure_quality,
            }
        )
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "StructureObservation":
        payload = cls._payload(data)
        payload["structure_break"] = enum_value(
            StructureBreak, payload.get("structure_break"), "structure_break"
        )
        payload["higher_timeframe_bias"] = enum_value(
            TrendBias,
            payload.get("higher_timeframe_bias"),
            "higher_timeframe_bias",
        )
        return cls(**payload)
