"""Immutable point-in-time contracts for a Market Situation timeline."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import math
from numbers import Real
from types import MappingProxyType
from typing import Any, Dict, Optional, Tuple

from app.intelligence.early_bird import EmergingStage


_FACTOR_FIELDS = (
    "whale_activity",
    "funding_divergence",
    "volume_expansion",
    "structure_event",
    "momentum_shift",
    "relative_strength",
    "open_interest_change",
    "liquidity_event",
)

_PERCENTAGE_FIELDS = (
    "completeness",
    "quality",
    "freshness",
    "opportunity",
    "priority",
    "maturity",
    "emergence",
    "horizon",
    "detection_confidence",
)


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


def _optional_percentage(value: Any, field_name: str) -> Optional[float]:
    if value is None:
        return None
    return _percentage(value, field_name)


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


def _stage(value: Any, field_name: str) -> EmergingStage:
    if isinstance(value, EmergingStage):
        return value
    try:
        return EmergingStage(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid {0}: {1!r}".format(field_name, value)) from exc


def _unique_string_tuple(values: Any, field_name: str) -> Tuple[str, ...]:
    if isinstance(values, (str, bytes, set, frozenset)):
        raise TypeError("{0} must be an ordered collection".format(field_name))
    try:
        materialized = tuple(values)
    except TypeError as exc:
        raise TypeError("{0} must be an ordered collection".format(field_name)) from exc
    normalized = tuple(
        _required_text(value, "{0} item".format(field_name))
        for value in materialized
    )
    if len(set(normalized)) != len(normalized):
        raise ValueError("{0} must not contain duplicates".format(field_name))
    return normalized


def _freeze(value: Any, field_name: str = "metadata") -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("{0} numeric values must be finite".format(field_name))
        return value
    if isinstance(value, Enum):
        return _freeze(value.value, field_name)
    if isinstance(value, datetime):
        return _utc_datetime(value, field_name).isoformat()
    if isinstance(value, Mapping):
        items = []
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("{0} keys must be strings".format(field_name))
            items.append((key, _freeze(item, field_name)))
        items.sort(key=lambda pair: pair[0])
        return MappingProxyType(dict(items))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item, field_name) for item in value)
    if isinstance(value, (set, frozenset)):
        return tuple(sorted((_freeze(item, field_name) for item in value), key=repr))
    if isinstance(value, Real):
        normalized = float(value)
        if not math.isfinite(normalized):
            raise ValueError("{0} numeric values must be finite".format(field_name))
        return normalized
    raise TypeError("{0} values must be serializable primitives".format(field_name))


def _frozen_mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError("{0} must be a mapping".format(field_name))
    return _freeze(value, field_name)


def _availability_mapping(value: Any) -> Mapping[str, str]:
    if not isinstance(value, Mapping):
        raise TypeError("factor_availability must be a mapping")
    items = []
    for key, state in value.items():
        normalized_key = _required_text(key, "factor_availability key")
        normalized_state = _required_text(state, "factor_availability value")
        items.append((normalized_key, normalized_state))
    items.sort(key=lambda pair: pair[0])
    return MappingProxyType(dict(items))


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


def _typed_entries(values: Any) -> Tuple["MarketSituationTimelineEntry", ...]:
    if isinstance(values, (str, bytes, set, frozenset)):
        raise TypeError("entries must be an ordered collection")
    try:
        entries = tuple(values)
    except TypeError as exc:
        raise TypeError("entries must be an ordered collection") from exc
    if not all(isinstance(entry, MarketSituationTimelineEntry) for entry in entries):
        raise TypeError("entries must contain only MarketSituationTimelineEntry objects")
    return entries


@dataclass(frozen=True)
class SituationDNA:
    """Point-in-time normalized knowledge used by one timeline entry."""

    whale_activity: Optional[float]
    funding_divergence: Optional[float]
    volume_expansion: Optional[float]
    structure_event: Optional[float]
    momentum_shift: Optional[float]
    relative_strength: Optional[float]
    open_interest_change: Optional[float]
    liquidity_event: Optional[float]
    completeness: float
    quality: float
    freshness: float
    opportunity: float
    priority: float
    maturity: float
    emergence: float
    horizon: float
    detection_confidence: float
    factor_availability: Mapping[str, str]
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        for field_name in _FACTOR_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _optional_percentage(getattr(self, field_name), field_name),
            )
        for field_name in _PERCENTAGE_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _percentage(getattr(self, field_name), field_name),
            )
        object.__setattr__(
            self,
            "factor_availability",
            _availability_mapping(self.factor_availability),
        )
        object.__setattr__(self, "metadata", _frozen_mapping(self.metadata, "metadata"))

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            field_name: getattr(self, field_name) for field_name in _FACTOR_FIELDS
        }
        payload.update(
            {field_name: getattr(self, field_name) for field_name in _PERCENTAGE_FIELDS}
        )
        payload["factor_availability"] = _to_plain(self.factor_availability)
        payload["metadata"] = _to_plain(self.metadata)
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SituationDNA":
        return cls(**_mapping_payload(data, "situation DNA"))


@dataclass(frozen=True)
class MarketSituationTimelineEntry:
    """Immutable facts and interpretation captured at one lifecycle moment."""

    entry_id: str
    timeline_id: str
    created_at: datetime
    stage: EmergingStage
    dna: SituationDNA
    supporting_factors: Tuple[str, ...]
    limiting_factors: Tuple[str, ...]
    expected_events: Tuple[str, ...]
    observed_events: Tuple[str, ...]
    missing_expected_events: Tuple[str, ...]
    unexpected_events: Tuple[str, ...]
    transition_reason: str
    source_assessment_id: Optional[str]
    source_candidate_id: Optional[str]
    source_situation_id: Optional[str]
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "entry_id", _required_text(self.entry_id, "entry_id"))
        object.__setattr__(
            self, "timeline_id", _required_text(self.timeline_id, "timeline_id")
        )
        object.__setattr__(
            self, "created_at", _utc_datetime(self.created_at, "created_at")
        )
        object.__setattr__(self, "stage", _stage(self.stage, "stage"))
        if not isinstance(self.dna, SituationDNA):
            raise TypeError("dna must be a SituationDNA")
        for field_name in (
            "supporting_factors",
            "limiting_factors",
            "expected_events",
            "observed_events",
            "missing_expected_events",
            "unexpected_events",
        ):
            object.__setattr__(
                self,
                field_name,
                _unique_string_tuple(getattr(self, field_name), field_name),
            )
        object.__setattr__(
            self,
            "transition_reason",
            _required_text(self.transition_reason, "transition_reason"),
        )
        for field_name in (
            "source_assessment_id",
            "source_candidate_id",
            "source_situation_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _optional_text(getattr(self, field_name), field_name),
            )
        object.__setattr__(self, "metadata", _frozen_mapping(self.metadata, "metadata"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "timeline_id": self.timeline_id,
            "created_at": self.created_at.isoformat(),
            "stage": self.stage.value,
            "dna": self.dna.to_dict(),
            "supporting_factors": list(self.supporting_factors),
            "limiting_factors": list(self.limiting_factors),
            "expected_events": list(self.expected_events),
            "observed_events": list(self.observed_events),
            "missing_expected_events": list(self.missing_expected_events),
            "unexpected_events": list(self.unexpected_events),
            "transition_reason": self.transition_reason,
            "source_assessment_id": self.source_assessment_id,
            "source_candidate_id": self.source_candidate_id,
            "source_situation_id": self.source_situation_id,
            "metadata": _to_plain(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "MarketSituationTimelineEntry":
        payload = _mapping_payload(data, "timeline entry")
        payload["created_at"] = _parse_datetime(payload.get("created_at"), "created_at")
        payload["stage"] = _stage(payload.get("stage"), "stage")
        payload["dna"] = SituationDNA.from_dict(payload.get("dna"))
        return cls(**payload)


@dataclass(frozen=True)
class MarketSituationTimeline:
    """Immutable version of the lifecycle history for one market situation."""

    timeline_id: str
    asset: str
    created_at: datetime
    updated_at: datetime
    entries: Tuple[MarketSituationTimelineEntry, ...]
    current_stage: EmergingStage
    version: int
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "timeline_id", _required_text(self.timeline_id, "timeline_id")
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
        entries = _typed_entries(self.entries)
        object.__setattr__(self, "entries", entries)
        current_stage = _stage(self.current_stage, "current_stage")
        object.__setattr__(self, "current_stage", current_stage)
        if isinstance(self.version, bool) or not isinstance(self.version, int):
            raise TypeError("version must be an integer")
        if self.version < 1:
            raise ValueError("version must be at least 1")
        entry_ids = set()
        previous_created_at = None
        for entry in entries:
            if entry.timeline_id != self.timeline_id:
                raise ValueError("every entry timeline_id must match timeline_id")
            if entry.entry_id in entry_ids:
                raise ValueError("entry IDs must be unique")
            entry_ids.add(entry.entry_id)
            if previous_created_at is not None and entry.created_at < previous_created_at:
                raise ValueError("entries must be ordered by created_at")
            previous_created_at = entry.created_at
        if entries:
            if current_stage is not entries[-1].stage:
                raise ValueError("current_stage must equal the last entry stage")
            if self.updated_at < entries[-1].created_at:
                raise ValueError("updated_at must not be before the last entry")
        elif current_stage is not EmergingStage.UNKNOWN:
            raise ValueError("empty timeline requires UNKNOWN current_stage")
        object.__setattr__(self, "metadata", _frozen_mapping(self.metadata, "metadata"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timeline_id": self.timeline_id,
            "asset": self.asset,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "entries": [entry.to_dict() for entry in self.entries],
            "current_stage": self.current_stage.value,
            "version": self.version,
            "metadata": _to_plain(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "MarketSituationTimeline":
        payload = _mapping_payload(data, "timeline")
        payload["created_at"] = _parse_datetime(payload.get("created_at"), "created_at")
        payload["updated_at"] = _parse_datetime(payload.get("updated_at"), "updated_at")
        raw_entries = payload.get("entries")
        if isinstance(raw_entries, (str, bytes, set, frozenset)):
            raise TypeError("entries must be an ordered collection")
        try:
            payload["entries"] = tuple(
                MarketSituationTimelineEntry.from_dict(entry) for entry in raw_entries
            )
        except TypeError as exc:
            raise TypeError("entries must be an ordered collection") from exc
        payload["current_stage"] = _stage(
            payload.get("current_stage"), "current_stage"
        )
        return cls(**payload)


__all__ = [
    "MarketSituationTimeline",
    "MarketSituationTimelineEntry",
    "SituationDNA",
]
