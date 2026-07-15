"""Availability-aware values for normalized Early Bird factors.

The contracts in this module describe whether a factor was measured. They do
not create factors, call providers, or attach direction or trade semantics.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional

from app.intelligence.early_bird.models import (
    _frozen_mapping,
    _mapping_payload,
    _parse_datetime,
    _percentage,
    _required_text,
    _to_plain,
    _utc_datetime,
)


class FactorAvailability(str, Enum):
    """Measurement status for one Early Bird factor evaluation."""

    AVAILABLE = "AVAILABLE"
    MISSING = "MISSING"
    STALE = "STALE"
    UNSUPPORTED = "UNSUPPORTED"
    ERROR = "ERROR"


def _availability(value: Any) -> FactorAvailability:
    if isinstance(value, FactorAvailability):
        return value
    try:
        return FactorAvailability(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid availability: {0!r}".format(value)) from exc


def _optional_text(value: Any, field_name: str) -> Optional[str]:
    if value is None:
        return None
    return _required_text(value, field_name)


@dataclass(frozen=True)
class EarlyBirdFactorValue:
    """One immutable factor measurement or explicit unavailability result."""

    factor_name: str
    availability: FactorAvailability
    score: Optional[float] = None
    observed_at: Optional[datetime] = None
    source: Optional[str] = None
    quality: Optional[float] = None
    reason: Optional[str] = None
    metadata: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "factor_name",
            _required_text(self.factor_name, "factor_name"),
        )
        object.__setattr__(
            self,
            "availability",
            _availability(self.availability),
        )

        if self.availability is FactorAvailability.AVAILABLE:
            if self.score is None:
                raise ValueError("AVAILABLE requires score")
            if self.observed_at is None:
                raise ValueError("AVAILABLE requires observed_at")
            if self.source is None:
                raise ValueError("AVAILABLE requires source")
        elif self.score is not None:
            raise ValueError(
                "non-AVAILABLE factor values must not include score"
            )

        if self.score is not None:
            object.__setattr__(
                self,
                "score",
                _percentage(self.score, "score"),
            )
        if self.observed_at is not None:
            object.__setattr__(
                self,
                "observed_at",
                _utc_datetime(self.observed_at, "observed_at"),
            )
        object.__setattr__(
            self,
            "source",
            _optional_text(self.source, "source"),
        )
        if self.quality is not None:
            object.__setattr__(
                self,
                "quality",
                _percentage(self.quality, "quality"),
            )
        object.__setattr__(
            self,
            "reason",
            _optional_text(self.reason, "reason"),
        )
        object.__setattr__(
            self,
            "metadata",
            _frozen_mapping(self.metadata, "metadata"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the value to public primitive values."""

        return {
            "factor_name": self.factor_name,
            "availability": self.availability.value,
            "score": self.score,
            "observed_at": (
                self.observed_at.isoformat()
                if self.observed_at is not None
                else None
            ),
            "source": self.source,
            "quality": self.quality,
            "reason": self.reason,
            "metadata": _to_plain(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "EarlyBirdFactorValue":
        """Restore a value from serialized primitives."""

        payload = _mapping_payload(data, "early bird factor value")
        payload["availability"] = _availability(payload.get("availability"))
        if payload.get("observed_at") is not None:
            payload["observed_at"] = _parse_datetime(
                payload["observed_at"],
                "observed_at",
            )
        return cls(**payload)
