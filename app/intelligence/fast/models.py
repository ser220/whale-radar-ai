"""Immutable contracts for early normalized event awareness."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import math
from numbers import Real
from types import MappingProxyType
from typing import Any, Dict, Mapping as TypingMapping


class FastEventType(str, Enum):
    """Initial event families with no attached trading meaning."""

    BREAKOUT = "BREAKOUT"
    STRUCTURE_BREAK = "STRUCTURE_BREAK"
    VOLUME_EXPANSION = "VOLUME_EXPANSION"
    LIQUIDITY_EVENT = "LIQUIDITY_EVENT"
    MOMENTUM_SHIFT = "MOMENTUM_SHIFT"


def _required_text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError("{0} must be a string".format(field_name))
    normalized = value.strip()
    if not normalized:
        raise ValueError("{0} must not be empty".format(field_name))
    return normalized


def _percentage(value: Real, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError("{0} must be a real number".format(field_name))
    normalized = float(value)
    if not math.isfinite(normalized) or not 0.0 <= normalized <= 100.0:
        raise ValueError("{0} must be between 0 and 100".format(field_name))
    return normalized


def _utc_datetime(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("timestamp must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return value.astimezone(timezone.utc)


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return _utc_datetime(value)
    if not isinstance(value, str):
        raise TypeError("timestamp must be a datetime or ISO-8601 string")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError("timestamp must be a valid ISO-8601 datetime") from exc
    return _utc_datetime(parsed)


def _event_type(value: Any) -> FastEventType:
    if isinstance(value, FastEventType):
        return value
    try:
        return FastEventType(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid event_type: {0!r}".format(value)) from exc


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze(item) for item in value)
    return value


def _frozen_metadata(value: TypingMapping[str, Any]) -> TypingMapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError("metadata must be a mapping")
    return MappingProxyType({key: _freeze(item) for key, item in value.items()})


def _to_plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return _utc_datetime(value).isoformat()
    if isinstance(value, Mapping):
        return {key: _to_plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [_to_plain(item) for item in value]
    return value


@dataclass(frozen=True)
class FastObservation:
    """One early normalized event without recommendation or trade semantics."""

    event_id: str
    asset: str
    timestamp: datetime
    source: str
    event_type: FastEventType
    strength: float
    quality: float
    description: str
    metadata: TypingMapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "event_id", _required_text(self.event_id, "event_id"))
        object.__setattr__(self, "asset", _required_text(self.asset, "asset").upper())
        object.__setattr__(self, "timestamp", _utc_datetime(self.timestamp))
        object.__setattr__(self, "source", _required_text(self.source, "source"))
        object.__setattr__(self, "event_type", _event_type(self.event_type))
        object.__setattr__(self, "strength", _percentage(self.strength, "strength"))
        object.__setattr__(self, "quality", _percentage(self.quality, "quality"))
        object.__setattr__(
            self,
            "description",
            _required_text(self.description, "description"),
        )
        object.__setattr__(self, "metadata", _frozen_metadata(self.metadata))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the contract to public primitive values."""
        return {
            "event_id": self.event_id,
            "asset": self.asset,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "event_type": self.event_type.value,
            "strength": self.strength,
            "quality": self.quality,
            "description": self.description,
            "metadata": _to_plain(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: TypingMapping[str, Any]) -> "FastObservation":
        """Restore a contract from primitive serialized values."""
        if not isinstance(data, Mapping):
            raise TypeError("fast observation data must be a mapping")
        payload = dict(data)
        payload["timestamp"] = _parse_datetime(payload.get("timestamp"))
        payload["event_type"] = _event_type(payload.get("event_type"))
        return cls(**payload)
