"""Immutable relationship records for fast and deep intelligence artifacts."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import math
from numbers import Real
from types import MappingProxyType
from typing import Any, Dict, Mapping as TypingMapping, Tuple


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


def _utc_datetime(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("{0} must be a datetime".format(field_name))
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("{0} must be timezone-aware".format(field_name))
    return value.astimezone(timezone.utc)


def _parse_datetime(value: Any, field_name: str) -> datetime:
    if isinstance(value, datetime):
        return _utc_datetime(value, field_name)
    if not isinstance(value, str):
        raise TypeError(
            "{0} must be a datetime or ISO-8601 string".format(field_name)
        )
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(
            "{0} must be a valid ISO-8601 datetime".format(field_name)
        ) from exc
    return _utc_datetime(parsed, field_name)


def _time_window(value: Any) -> Tuple[datetime, datetime]:
    if isinstance(value, Mapping):
        start_value = value.get("start")
        end_value = value.get("end")
    else:
        if isinstance(value, (str, bytes)):
            raise TypeError("time_window must contain exactly two datetimes")
        try:
            values = tuple(value)
        except TypeError as exc:
            raise TypeError("time_window must contain exactly two datetimes") from exc
        if len(values) != 2:
            raise ValueError("time_window must contain exactly two datetimes")
        start_value, end_value = values

    start = _parse_datetime(start_value, "time_window start")
    end = _parse_datetime(end_value, "time_window end")
    if start > end:
        raise ValueError("time_window start must not be after end")
    return start, end


def _references(values: Iterable[str], field_name: str) -> Tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError("{0} must be a collection of strings".format(field_name))
    try:
        raw_values = tuple(values)
    except TypeError as exc:
        raise TypeError(
            "{0} must be a collection of strings".format(field_name)
        ) from exc

    normalized = tuple(_required_text(value, field_name) for value in raw_values)
    if len(set(normalized)) != len(normalized):
        raise ValueError("{0} must not contain duplicates".format(field_name))
    return normalized


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
        return _utc_datetime(value, "timestamp").isoformat()
    if isinstance(value, Mapping):
        return {key: _to_plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [_to_plain(item) for item in value]
    return value


@dataclass(frozen=True)
class EventCorrelation:
    """Explicit links between artifacts that may describe one market event."""

    correlation_id: str
    created_at: datetime
    asset: str
    time_window: Tuple[datetime, datetime]
    related_fast_events: Tuple[str, ...]
    related_observations: Tuple[str, ...]
    related_experts: Tuple[str, ...]
    correlation_score: float
    independence_score: float
    metadata: TypingMapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "correlation_id",
            _required_text(self.correlation_id, "correlation_id"),
        )
        object.__setattr__(
            self,
            "created_at",
            _utc_datetime(self.created_at, "created_at"),
        )
        object.__setattr__(self, "asset", _required_text(self.asset, "asset").upper())
        object.__setattr__(self, "time_window", _time_window(self.time_window))
        for field_name in (
            "related_fast_events",
            "related_observations",
            "related_experts",
        ):
            object.__setattr__(
                self,
                field_name,
                _references(getattr(self, field_name), field_name),
            )
        object.__setattr__(
            self,
            "correlation_score",
            _percentage(self.correlation_score, "correlation_score"),
        )
        object.__setattr__(
            self,
            "independence_score",
            _percentage(self.independence_score, "independence_score"),
        )
        object.__setattr__(self, "metadata", _frozen_metadata(self.metadata))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the relationship without changing its semantics."""
        return {
            "correlation_id": self.correlation_id,
            "created_at": self.created_at.isoformat(),
            "asset": self.asset,
            "time_window": {
                "start": self.time_window[0].isoformat(),
                "end": self.time_window[1].isoformat(),
            },
            "related_fast_events": list(self.related_fast_events),
            "related_observations": list(self.related_observations),
            "related_experts": list(self.related_experts),
            "correlation_score": self.correlation_score,
            "independence_score": self.independence_score,
            "metadata": _to_plain(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: TypingMapping[str, Any]) -> "EventCorrelation":
        """Restore a relationship from primitive serialized values."""
        if not isinstance(data, Mapping):
            raise TypeError("event correlation data must be a mapping")
        payload = dict(data)
        payload["created_at"] = _parse_datetime(payload.get("created_at"), "created_at")
        payload["time_window"] = _time_window(payload.get("time_window"))
        return cls(**payload)
