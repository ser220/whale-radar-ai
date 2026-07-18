"""Immutable normalized market observations without interpretations."""

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any, Dict, Mapping

from app.intelligence.observations.base import (
    finite_number,
    required_text,
    parse_datetime,
)

from app.intelligence.observations.enums import MarketObservationType


@dataclass(frozen=True)
class MarketObservation:
    source_category: str
    source: str
    symbol: str

    observation_type: MarketObservationType
    severity: str

    value: float
    reference_value: float

    captured_at: datetime


    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_category",
            required_text(
                self.source_category,
                "source_category",
            ),
        )

        object.__setattr__(
            self,
            "source",
            required_text(
                self.source,
                "source",
            ),
        )

        object.__setattr__(
            self,
            "symbol",
            required_text(
                self.symbol,
                "symbol",
            ).upper(),
        )

        if not isinstance(self.observation_type, MarketObservationType):
            object.__setattr__(
                self,
                "observation_type",
                MarketObservationType(self.observation_type),
            )

        object.__setattr__(
            self,
            "severity",
            required_text(
                self.severity,
                "severity",
            ),
        )

        object.__setattr__(
            self,
            "value",
            finite_number(
                self.value,
                "value",
            ),
        )

        object.__setattr__(
            self,
            "reference_value",
            finite_number(
                self.reference_value,
                "reference_value",
            ),
        )

        object.__setattr__(
            self,
            "captured_at",
            parse_datetime(
                self.captured_at,
                "captured_at",
            ),
        )


    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_category": self.source_category,
            "source": self.source,
            "symbol": self.symbol,
            "observation_type": self.observation_type.value,
            "severity": self.severity,
            "value": self.value,
            "reference_value": self.reference_value,
            "captured_at": self.captured_at.isoformat(),
        }

    def canonical_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

    @classmethod
    def from_dict(
        cls,
        data: Mapping[str, Any],
    ) -> "MarketObservation":

        payload = dict(data)

        payload["captured_at"] = parse_datetime(
            payload["captured_at"],
            "captured_at",
        )

        return cls(**payload)
