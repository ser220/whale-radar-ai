"""Normalized market facts without trading conclusions."""

from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional

from app.intelligence.observations.base import (
    Observation,
    enum_value,
    bounded_number,
    optional_finite_number,
)

from app.intelligence.observations.enums import (
    MarketObservationType,
    ObservationSeverity,
)


@dataclass(frozen=True)
class MarketObservation(Observation):
    observation_id: str
    asset: str
    source: str
    timeframe: str
    quality: float
    observed_at: datetime

    observation_kind: MarketObservationType
    severity: ObservationSeverity

    value: float
    reference_value: Optional[float] = None

    version: int = 1
    metadata: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    OBSERVATION_TYPE = "market"

    def __post_init__(self) -> None:
        self._validate_common()

        object.__setattr__(
            self,
            "observation_kind",
            enum_value(
                MarketObservationType,
                self.observation_kind,
                "observation_kind",
            ),
        )

        object.__setattr__(
            self,
            "severity",
            enum_value(
                ObservationSeverity,
                self.severity,
                "severity",
            ),
        )

        object.__setattr__(
            self,
            "value",
            bounded_number(
                self.value,
                "value",
                -1000000000,
                1000000000,
            ),
        )

        object.__setattr__(
            self,
            "reference_value",
            optional_finite_number(
                self.reference_value,
                "reference_value",
            ),
        )

    def to_dict(self) -> Dict[str, Any]:
        payload = self._common_dict()

        payload.update(
            {
                "observation_kind": self.observation_kind.value,
                "severity": self.severity.value,
                "value": self.value,
                "reference_value": self.reference_value,
            }
        )

        return payload

    @classmethod
    def from_dict(
        cls,
        data: Mapping[str, Any],
    ) -> "MarketObservation":

        payload = cls._payload(data)

        payload["observation_kind"] = enum_value(
            MarketObservationType,
            payload.get("observation_kind"),
            "observation_kind",
        )

        payload["severity"] = enum_value(
            ObservationSeverity,
            payload.get("severity"),
            "severity",
        )

        return cls(**payload)
