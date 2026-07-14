"""Immutable, infrastructure-free Market Situation domain contracts."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import math
from numbers import Real
from types import MappingProxyType
from typing import Any, Dict, Iterable, Optional, Tuple, Type, TypeVar

from app.intelligence.situations.enums import (
    ExpectationStatus,
    ExpectationViolationType,
    SituationHealth,
    SituationStage,
    TimelineEventType,
)


EnumT = TypeVar("EnumT", bound=Enum)


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError("{0} must be a string".format(field_name))
    normalized = value.strip()
    if not normalized:
        raise ValueError("{0} must not be empty".format(field_name))
    return normalized


def _optional_text(value: Any, field_name: str) -> Optional[str]:
    if value is None:
        return None
    return _required_text(value, field_name)


def _percentage(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError("{0} must be a real number".format(field_name))
    normalized = float(value)
    if not math.isfinite(normalized) or not 0.0 <= normalized <= 100.0:
        raise ValueError("{0} must be between 0 and 100".format(field_name))
    return normalized


def _utc_datetime(value: Any, field_name: str) -> datetime:
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


def _enum_value(enum_type: Type[EnumT], value: Any, field_name: str) -> EnumT:
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid {0}: {1!r}".format(field_name, value)) from exc


def _unique_string_tuple(
    values: Iterable[str],
    field_name: str,
    require_non_empty: bool = False,
) -> Tuple[str, ...]:
    if isinstance(values, str) or isinstance(values, (set, frozenset)):
        raise TypeError("{0} must be an ordered collection of strings".format(field_name))
    try:
        raw_values = tuple(values)
    except TypeError as exc:
        raise TypeError(
            "{0} must be an ordered collection of strings".format(field_name)
        ) from exc
    normalized = tuple(
        _required_text(item, "{0} item".format(field_name)) for item in raw_values
    )
    if require_non_empty and not normalized:
        raise ValueError("{0} must not be empty".format(field_name))
    if len(set(normalized)) != len(normalized):
        raise ValueError("{0} must not contain duplicate IDs".format(field_name))
    return normalized


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        items = []
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("metadata keys must be strings")
            items.append((key, _freeze(item)))
        items.sort(key=lambda pair: pair[0])
        return MappingProxyType(dict(items))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, (set, frozenset)):
        frozen_items = tuple(_freeze(item) for item in value)
        return tuple(sorted(frozen_items, key=repr))
    return value


def _frozen_metadata(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError("metadata must be a mapping")
    return _freeze(value)


def _to_plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return _utc_datetime(value, "timestamp").isoformat()
    if isinstance(value, Mapping):
        return {key: _to_plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_to_plain(item) for item in value]
    return value


def _mapping_payload(value: Any, model_name: str) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError("{0} data must be a mapping".format(model_name))
    return dict(value)


def _typed_tuple(values: Any, expected_type: Type[Any], field_name: str) -> Tuple[Any, ...]:
    if isinstance(values, (str, bytes, set, frozenset)):
        raise TypeError("{0} must be an ordered collection".format(field_name))
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise TypeError("{0} must be an ordered collection".format(field_name)) from exc
    if not all(isinstance(item, expected_type) for item in normalized):
        raise TypeError(
            "{0} must contain only {1} objects".format(
                field_name, expected_type.__name__
            )
        )
    return normalized


@dataclass(frozen=True)
class SituationTimelineEntry:
    """One explicit historical fact in a MarketSituation timeline."""

    entry_id: str
    event_type: TimelineEventType
    occurred_at: datetime
    summary: str
    artifact_ids: Tuple[str, ...]
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "entry_id", _required_text(self.entry_id, "entry_id"))
        object.__setattr__(
            self,
            "event_type",
            _enum_value(TimelineEventType, self.event_type, "event_type"),
        )
        object.__setattr__(
            self, "occurred_at", _utc_datetime(self.occurred_at, "occurred_at")
        )
        object.__setattr__(self, "summary", _required_text(self.summary, "summary"))
        object.__setattr__(
            self,
            "artifact_ids",
            _unique_string_tuple(self.artifact_ids, "artifact_ids"),
        )
        object.__setattr__(self, "metadata", _frozen_metadata(self.metadata))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "event_type": self.event_type.value,
            "occurred_at": self.occurred_at.isoformat(),
            "summary": self.summary,
            "artifact_ids": list(self.artifact_ids),
            "metadata": _to_plain(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SituationTimelineEntry":
        payload = _mapping_payload(data, "timeline entry")
        payload["event_type"] = _enum_value(
            TimelineEventType, payload.get("event_type"), "event_type"
        )
        payload["occurred_at"] = _parse_datetime(
            payload.get("occurred_at"), "occurred_at"
        )
        return cls(**payload)


@dataclass(frozen=True)
class ConfidencePoint:
    """Historical system confidence without trade authorization semantics."""

    recorded_at: datetime
    value: float
    source: str
    reason: str
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "recorded_at", _utc_datetime(self.recorded_at, "recorded_at")
        )
        object.__setattr__(self, "value", _percentage(self.value, "value"))
        object.__setattr__(self, "source", _required_text(self.source, "source"))
        object.__setattr__(self, "reason", _required_text(self.reason, "reason"))
        object.__setattr__(self, "metadata", _frozen_metadata(self.metadata))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recorded_at": self.recorded_at.isoformat(),
            "value": self.value,
            "source": self.source,
            "reason": self.reason,
            "metadata": _to_plain(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ConfidencePoint":
        payload = _mapping_payload(data, "confidence point")
        payload["recorded_at"] = _parse_datetime(
            payload.get("recorded_at"), "recorded_at"
        )
        return cls(**payload)


@dataclass(frozen=True)
class ExpectationRecord:
    """An expectation and its explicitly supplied evaluation state."""

    expectation_id: str
    created_at: datetime
    window_start: datetime
    window_end: datetime
    description: str
    basis_artifact_ids: Tuple[str, ...]
    status: ExpectationStatus
    expected_event_type: str
    observed_event_ids: Tuple[str, ...]
    violation_type: ExpectationViolationType
    gap_severity: float
    learning_conclusion: Optional[str]
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "expectation_id", _required_text(self.expectation_id, "expectation_id")
        )
        object.__setattr__(
            self, "created_at", _utc_datetime(self.created_at, "created_at")
        )
        object.__setattr__(
            self, "window_start", _utc_datetime(self.window_start, "window_start")
        )
        object.__setattr__(
            self, "window_end", _utc_datetime(self.window_end, "window_end")
        )
        if self.window_start > self.window_end:
            raise ValueError("window_start must not be after window_end")
        if self.created_at > self.window_end:
            raise ValueError("created_at must not be after window_end")
        object.__setattr__(
            self, "description", _required_text(self.description, "description")
        )
        object.__setattr__(
            self,
            "basis_artifact_ids",
            _unique_string_tuple(
                self.basis_artifact_ids,
                "basis_artifact_ids",
                require_non_empty=True,
            ),
        )
        object.__setattr__(
            self, "status", _enum_value(ExpectationStatus, self.status, "status")
        )
        object.__setattr__(
            self,
            "expected_event_type",
            _required_text(self.expected_event_type, "expected_event_type"),
        )
        object.__setattr__(
            self,
            "observed_event_ids",
            _unique_string_tuple(self.observed_event_ids, "observed_event_ids"),
        )
        object.__setattr__(
            self,
            "violation_type",
            _enum_value(
                ExpectationViolationType, self.violation_type, "violation_type"
            ),
        )
        object.__setattr__(
            self, "gap_severity", _percentage(self.gap_severity, "gap_severity")
        )
        object.__setattr__(
            self,
            "learning_conclusion",
            _optional_text(self.learning_conclusion, "learning_conclusion"),
        )
        object.__setattr__(self, "metadata", _frozen_metadata(self.metadata))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "expectation_id": self.expectation_id,
            "created_at": self.created_at.isoformat(),
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "description": self.description,
            "basis_artifact_ids": list(self.basis_artifact_ids),
            "status": self.status.value,
            "expected_event_type": self.expected_event_type,
            "observed_event_ids": list(self.observed_event_ids),
            "violation_type": self.violation_type.value,
            "gap_severity": self.gap_severity,
            "learning_conclusion": self.learning_conclusion,
            "metadata": _to_plain(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExpectationRecord":
        payload = _mapping_payload(data, "expectation record")
        for field_name in ("created_at", "window_start", "window_end"):
            payload[field_name] = _parse_datetime(payload.get(field_name), field_name)
        payload["status"] = _enum_value(
            ExpectationStatus, payload.get("status"), "status"
        )
        payload["violation_type"] = _enum_value(
            ExpectationViolationType,
            payload.get("violation_type"),
            "violation_type",
        )
        return cls(**payload)


@dataclass(frozen=True)
class MarketSituation:
    """One immutable version of a market story and its artifact references."""

    situation_id: str
    asset: str
    created_at: datetime
    updated_at: datetime
    stage: SituationStage
    health: SituationHealth
    version: int
    fast_event_ids: Tuple[str, ...]
    observation_ids: Tuple[str, ...]
    expert_opinion_ids: Tuple[str, ...]
    expert_names: Tuple[str, ...]
    correlation_ids: Tuple[str, ...]
    market_state_ids: Tuple[str, ...]
    decision_context_ids: Tuple[str, ...]
    outcome_ids: Tuple[str, ...]
    learning_record_ids: Tuple[str, ...]
    memory_reference_ids: Tuple[str, ...]
    timeline: Tuple[SituationTimelineEntry, ...]
    confidence_history: Tuple[ConfidencePoint, ...]
    expectation_history: Tuple[ExpectationRecord, ...]
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "situation_id", _required_text(self.situation_id, "situation_id")
        )
        object.__setattr__(self, "asset", _required_text(self.asset, "asset").upper())
        object.__setattr__(
            self, "created_at", _utc_datetime(self.created_at, "created_at")
        )
        object.__setattr__(
            self, "updated_at", _utc_datetime(self.updated_at, "updated_at")
        )
        if self.updated_at < self.created_at:
            raise ValueError("updated_at must not be before created_at")
        object.__setattr__(
            self, "stage", _enum_value(SituationStage, self.stage, "stage")
        )
        object.__setattr__(
            self, "health", _enum_value(SituationHealth, self.health, "health")
        )
        if isinstance(self.version, bool) or not isinstance(self.version, int):
            raise TypeError("version must be an integer")
        if self.version < 1:
            raise ValueError("version must be at least 1")

        reference_fields = (
            "fast_event_ids",
            "observation_ids",
            "expert_opinion_ids",
            "expert_names",
            "correlation_ids",
            "market_state_ids",
            "decision_context_ids",
            "outcome_ids",
            "learning_record_ids",
            "memory_reference_ids",
        )
        for field_name in reference_fields:
            object.__setattr__(
                self,
                field_name,
                _unique_string_tuple(getattr(self, field_name), field_name),
            )

        timeline = _typed_tuple(self.timeline, SituationTimelineEntry, "timeline")
        if any(
            previous.occurred_at > current.occurred_at
            for previous, current in zip(timeline, timeline[1:])
        ):
            raise ValueError("timeline must be sorted by occurred_at")
        entry_ids = tuple(item.entry_id for item in timeline)
        if len(set(entry_ids)) != len(entry_ids):
            raise ValueError("timeline must not contain duplicate entry IDs")
        object.__setattr__(self, "timeline", timeline)

        confidence_history = _typed_tuple(
            self.confidence_history, ConfidencePoint, "confidence_history"
        )
        if any(
            previous.recorded_at > current.recorded_at
            for previous, current in zip(
                confidence_history, confidence_history[1:]
            )
        ):
            raise ValueError("confidence_history must be sorted by recorded_at")
        object.__setattr__(self, "confidence_history", confidence_history)

        expectation_history = _typed_tuple(
            self.expectation_history, ExpectationRecord, "expectation_history"
        )
        expectation_order = tuple(
            (item.created_at, item.expectation_id) for item in expectation_history
        )
        if expectation_order != tuple(sorted(expectation_order)):
            raise ValueError(
                "expectation_history must be sorted by created_at and expectation_id"
            )
        expectation_ids = tuple(item.expectation_id for item in expectation_history)
        if len(set(expectation_ids)) != len(expectation_ids):
            raise ValueError(
                "expectation_history must not contain duplicate expectation IDs"
            )
        object.__setattr__(self, "expectation_history", expectation_history)
        object.__setattr__(self, "metadata", _frozen_metadata(self.metadata))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "situation_id": self.situation_id,
            "asset": self.asset,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "stage": self.stage.value,
            "health": self.health.value,
            "version": self.version,
            "fast_event_ids": list(self.fast_event_ids),
            "observation_ids": list(self.observation_ids),
            "expert_opinion_ids": list(self.expert_opinion_ids),
            "expert_names": list(self.expert_names),
            "correlation_ids": list(self.correlation_ids),
            "market_state_ids": list(self.market_state_ids),
            "decision_context_ids": list(self.decision_context_ids),
            "outcome_ids": list(self.outcome_ids),
            "learning_record_ids": list(self.learning_record_ids),
            "memory_reference_ids": list(self.memory_reference_ids),
            "timeline": [item.to_dict() for item in self.timeline],
            "confidence_history": [
                item.to_dict() for item in self.confidence_history
            ],
            "expectation_history": [
                item.to_dict() for item in self.expectation_history
            ],
            "metadata": _to_plain(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "MarketSituation":
        payload = _mapping_payload(data, "market situation")
        payload["created_at"] = _parse_datetime(
            payload.get("created_at"), "created_at"
        )
        payload["updated_at"] = _parse_datetime(
            payload.get("updated_at"), "updated_at"
        )
        payload["stage"] = _enum_value(
            SituationStage, payload.get("stage"), "stage"
        )
        payload["health"] = _enum_value(
            SituationHealth, payload.get("health"), "health"
        )
        payload["timeline"] = tuple(
            SituationTimelineEntry.from_dict(item)
            for item in payload.get("timeline", ())
        )
        payload["confidence_history"] = tuple(
            ConfidencePoint.from_dict(item)
            for item in payload.get("confidence_history", ())
        )
        payload["expectation_history"] = tuple(
            ExpectationRecord.from_dict(item)
            for item in payload.get("expectation_history", ())
        )
        return cls(**payload)
