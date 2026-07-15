"""Immutable input and output contracts for Early Bird."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import math
from numbers import Real
from types import MappingProxyType
from typing import Any, Dict, Iterable, Mapping as TypingMapping, Optional, Tuple


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError("{0} must be a string".format(field_name))
    normalized = value.strip()
    if not normalized:
        raise ValueError("{0} must not be empty".format(field_name))
    return normalized


def _percentage(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError("{0} must be a real number".format(field_name))
    normalized = float(value)
    if not math.isfinite(normalized) or not 0.0 <= normalized <= 100.0:
        raise ValueError("{0} must be between 0 and 100".format(field_name))
    return normalized


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("{0} must be an integer".format(field_name))
    if value < 1:
        raise ValueError("{0} must be at least 1".format(field_name))
    return value


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


def _unique_references(values: Iterable[str], field_name: str) -> Tuple[str, ...]:
    if isinstance(values, (str, bytes, set, frozenset)):
        raise TypeError("{0} must be an ordered collection".format(field_name))
    try:
        raw_values = tuple(values)
    except TypeError as exc:
        raise TypeError("{0} must be an ordered collection".format(field_name)) from exc
    normalized = tuple(
        _required_text(item, "{0} item".format(field_name)) for item in raw_values
    )
    if len(set(normalized)) != len(normalized):
        raise ValueError("{0} must not contain duplicates".format(field_name))
    return normalized


def _string_tuple(values: Iterable[str], field_name: str) -> Tuple[str, ...]:
    return _unique_references(values, field_name)


def _freeze_serializable(value: Any, field_name: str = "metadata") -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("{0} numeric values must be finite".format(field_name))
        return value
    if isinstance(value, Enum):
        return _freeze_serializable(value.value, field_name)
    if isinstance(value, datetime):
        return _utc_datetime(value, field_name).isoformat()
    if isinstance(value, Mapping):
        items = []
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("{0} keys must be strings".format(field_name))
            items.append((key, _freeze_serializable(item, field_name)))
        items.sort(key=lambda pair: pair[0])
        return MappingProxyType(dict(items))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_serializable(item, field_name) for item in value)
    if isinstance(value, (set, frozenset)):
        frozen = tuple(_freeze_serializable(item, field_name) for item in value)
        return tuple(sorted(frozen, key=repr))
    if isinstance(value, Real):
        normalized = float(value)
        if not math.isfinite(normalized):
            raise ValueError("{0} numeric values must be finite".format(field_name))
        return normalized
    raise TypeError("{0} values must be serializable primitives".format(field_name))


def _frozen_mapping(value: Any, field_name: str) -> TypingMapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError("{0} must be a mapping".format(field_name))
    return _freeze_serializable(value, field_name)


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


@dataclass(frozen=True)
class EarlyBirdCandidate:
    """One provider-neutral asset candidate containing normalized facts only."""

    candidate_id: str
    asset: str
    observed_at: datetime
    source: str
    quality: float
    whale_activity_score: float
    open_interest_change_score: float
    funding_divergence_score: float
    volume_expansion_score: float
    relative_strength_score: float
    liquidity_event_score: float
    structure_event_score: float
    momentum_shift_score: float
    freshness_score: float
    data_completeness_score: float
    fast_event_ids: Tuple[str, ...]
    observation_ids: Tuple[str, ...]
    metadata: TypingMapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "candidate_id", _required_text(self.candidate_id, "candidate_id")
        )
        object.__setattr__(self, "asset", _required_text(self.asset, "asset").upper())
        object.__setattr__(
            self, "observed_at", _utc_datetime(self.observed_at, "observed_at")
        )
        object.__setattr__(self, "source", _required_text(self.source, "source"))
        score_fields = (
            "quality",
            "whale_activity_score",
            "open_interest_change_score",
            "funding_divergence_score",
            "volume_expansion_score",
            "relative_strength_score",
            "liquidity_event_score",
            "structure_event_score",
            "momentum_shift_score",
            "freshness_score",
            "data_completeness_score",
        )
        for field_name in score_fields:
            object.__setattr__(
                self, field_name, _percentage(getattr(self, field_name), field_name)
            )
        object.__setattr__(
            self,
            "fast_event_ids",
            _unique_references(self.fast_event_ids, "fast_event_ids"),
        )
        object.__setattr__(
            self,
            "observation_ids",
            _unique_references(self.observation_ids, "observation_ids"),
        )
        object.__setattr__(self, "metadata", _frozen_mapping(self.metadata, "metadata"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "asset": self.asset,
            "observed_at": self.observed_at.isoformat(),
            "source": self.source,
            "quality": self.quality,
            "whale_activity_score": self.whale_activity_score,
            "open_interest_change_score": self.open_interest_change_score,
            "funding_divergence_score": self.funding_divergence_score,
            "volume_expansion_score": self.volume_expansion_score,
            "relative_strength_score": self.relative_strength_score,
            "liquidity_event_score": self.liquidity_event_score,
            "structure_event_score": self.structure_event_score,
            "momentum_shift_score": self.momentum_shift_score,
            "freshness_score": self.freshness_score,
            "data_completeness_score": self.data_completeness_score,
            "fast_event_ids": list(self.fast_event_ids),
            "observation_ids": list(self.observation_ids),
            "metadata": _to_plain(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: TypingMapping[str, Any]) -> "EarlyBirdCandidate":
        payload = _mapping_payload(data, "early bird candidate")
        payload["observed_at"] = _parse_datetime(
            payload.get("observed_at"), "observed_at"
        )
        return cls(**payload)


@dataclass(frozen=True)
class EarlyBirdAssessment:
    """Explainable attention ranking output without trade semantics."""

    assessment_id: str
    candidate_id: str
    asset: str
    evaluated_at: datetime
    opportunity_score: float
    priority_score: float
    maturity_score: float
    quality: float
    rank: Optional[int]
    reasons: Tuple[str, ...]
    warnings: Tuple[str, ...]
    factor_contributions: TypingMapping[str, Any]
    source_event_ids: Tuple[str, ...]
    source_observation_ids: Tuple[str, ...]
    metadata: TypingMapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "assessment_id", _required_text(self.assessment_id, "assessment_id")
        )
        object.__setattr__(
            self, "candidate_id", _required_text(self.candidate_id, "candidate_id")
        )
        object.__setattr__(self, "asset", _required_text(self.asset, "asset").upper())
        object.__setattr__(
            self, "evaluated_at", _utc_datetime(self.evaluated_at, "evaluated_at")
        )
        for field_name in (
            "opportunity_score",
            "priority_score",
            "maturity_score",
            "quality",
        ):
            object.__setattr__(
                self, field_name, _percentage(getattr(self, field_name), field_name)
            )
        if self.rank is not None:
            object.__setattr__(self, "rank", _positive_int(self.rank, "rank"))
        object.__setattr__(self, "reasons", _string_tuple(self.reasons, "reasons"))
        object.__setattr__(self, "warnings", _string_tuple(self.warnings, "warnings"))
        object.__setattr__(
            self,
            "factor_contributions",
            _frozen_mapping(self.factor_contributions, "factor_contributions"),
        )
        object.__setattr__(
            self,
            "source_event_ids",
            _unique_references(self.source_event_ids, "source_event_ids"),
        )
        object.__setattr__(
            self,
            "source_observation_ids",
            _unique_references(
                self.source_observation_ids, "source_observation_ids"
            ),
        )
        object.__setattr__(self, "metadata", _frozen_mapping(self.metadata, "metadata"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "candidate_id": self.candidate_id,
            "asset": self.asset,
            "evaluated_at": self.evaluated_at.isoformat(),
            "opportunity_score": self.opportunity_score,
            "priority_score": self.priority_score,
            "maturity_score": self.maturity_score,
            "quality": self.quality,
            "rank": self.rank,
            "reasons": list(self.reasons),
            "warnings": list(self.warnings),
            "factor_contributions": _to_plain(self.factor_contributions),
            "source_event_ids": list(self.source_event_ids),
            "source_observation_ids": list(self.source_observation_ids),
            "metadata": _to_plain(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: TypingMapping[str, Any]) -> "EarlyBirdAssessment":
        payload = _mapping_payload(data, "early bird assessment")
        payload["evaluated_at"] = _parse_datetime(
            payload.get("evaluated_at"), "evaluated_at"
        )
        return cls(**payload)
