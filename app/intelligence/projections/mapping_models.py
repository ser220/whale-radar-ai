"""Immutable contracts for projection-to-RootCauseCandidate mapping."""

from collections.abc import Mapping as RuntimeMapping
from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from enum import Enum
import json
import math
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional, Tuple

from app.intelligence.reality_gap.enums import (
    RealityGapEvidenceEligibility,
    RootCauseDisposition,
    RootCauseRole,
)
from app.intelligence.reality_gap.models import RootCauseCandidate

from .models import CandidateProjection


class MappingFailureCategory(str, Enum):
    UNKNOWN_PROJECTION = "UNKNOWN_PROJECTION"
    LINEAGE_MISMATCH = "LINEAGE_MISMATCH"
    INVALID_EVIDENCE_REFERENCE = "INVALID_EVIDENCE_REFERENCE"
    MISSING_DECISION_SNAPSHOT = "MISSING_DECISION_SNAPSHOT"
    POLICY_CONFLICT = "POLICY_CONFLICT"
    INVALID_PLACEMENT_CONTEXT = "INVALID_PLACEMENT_CONTEXT"


def _text(value: Any, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError("{0} must be a string".format(name))
    normalized = value.strip()
    if not normalized:
        raise ValueError("{0} must not be empty".format(name))
    return normalized


def _optional_text(value: Any, name: str) -> Optional[str]:
    if value is None:
        return None
    return _text(value, name)


def _positive(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("{0} must be an integer".format(name))
    if value < 1:
        raise ValueError("{0} must be at least 1".format(name))
    return value


def _nonnegative(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("{0} must be an integer".format(name))
    if value < 0:
        raise ValueError("{0} must not be negative".format(name))
    return value


def _utc(value: Any, name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("{0} must be a datetime".format(name))
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("{0} must be timezone-aware".format(name))
    return value.astimezone(timezone.utc)


def _parse_time(value: Any, name: str) -> datetime:
    if isinstance(value, datetime):
        return _utc(value, name)
    if not isinstance(value, str):
        raise TypeError("{0} must be a datetime or ISO-8601 string".format(name))
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError("{0} must be a valid ISO-8601 datetime".format(name)) from exc
    return _utc(parsed, name)


def _enum(value: Any, enum_type: Any, name: str) -> Any:
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid {0}".format(name)) from exc


def _refs(value: Any, name: str) -> Tuple[str, ...]:
    if isinstance(value, (str, bytes, set, frozenset, RuntimeMapping)):
        raise TypeError("{0} must be an ordered collection".format(name))
    try:
        items = tuple(_text(item, "{0} item".format(name)) for item in value)
    except TypeError as exc:
        raise TypeError("{0} must be an ordered collection".format(name)) from exc
    if len(set(items)) != len(items):
        raise ValueError("{0} must not contain duplicates".format(name))
    return tuple(sorted(items))


def _freeze(value: Any, name: str) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("{0} numeric values must be finite".format(name))
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return _utc(value, name).isoformat()
    if isinstance(value, RuntimeMapping):
        keys = tuple(value)
        if any(not isinstance(key, str) or not key.strip() for key in keys):
            raise TypeError("{0} keys must be non-empty strings".format(name))
        return MappingProxyType({
            key: _freeze(value[key], "{0}.{1}".format(name, key))
            for key in sorted(keys)
        })
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item, "{0}[]".format(name)) for item in value)
    raise TypeError("{0} contains an unsupported mutable value".format(name))


def _metadata(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, RuntimeMapping):
        raise TypeError("metadata must be a mapping")
    return _freeze(value, "metadata")


def _plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return _utc(value, "timestamp").isoformat()
    if isinstance(value, RuntimeMapping):
        return {key: _plain(value[key]) for key in sorted(value)}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        _plain(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _payload(value: Any, model_type: Any) -> Dict[str, Any]:
    if not isinstance(value, RuntimeMapping):
        raise TypeError("{0} data must be a mapping".format(model_type.__name__))
    names = tuple(item.name for item in fields(model_type))
    unknown = set(value) - set(names)
    missing = set(names) - set(value)
    if unknown:
        raise ValueError("unknown fields: {0}".format(", ".join(sorted(unknown))))
    if missing:
        raise ValueError("missing fields: {0}".format(", ".join(sorted(missing))))
    return {name: value[name] for name in names}


@dataclass(frozen=True)
class ExplanationDescriptorSnapshot:
    candidate_id: str
    candidate_version: int
    subject: str
    description: str
    hypothesis_reference: str
    descriptor_policy_version: str
    created_at: datetime
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("candidate_id", "subject", "description", "hypothesis_reference", "descriptor_policy_version"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "candidate_version", _positive(self.candidate_version, "candidate_version"))
        object.__setattr__(self, "created_at", _utc(self.created_at, "created_at"))
        object.__setattr__(self, "metadata", _metadata(self.metadata))

    def to_dict(self) -> dict:
        return _plain(self.__dict__)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ExplanationDescriptorSnapshot":
        data = _payload(value, cls)
        data["created_at"] = _parse_time(data["created_at"], "created_at")
        return cls(**data)


@dataclass(frozen=True)
class ExplanationDecisionSnapshot:
    projection_id: str
    projection_version: int
    role: RootCauseRole
    disposition: RootCauseDisposition
    decision_reference: str
    independent_support_count: int
    independent_support_provenance_reference: str
    rejection_reason: Optional[str]
    decision_policy_version: str
    mapping_policy_version: str
    created_at: datetime
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "projection_id", "decision_reference", "independent_support_provenance_reference",
            "decision_policy_version", "mapping_policy_version",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "projection_version", _positive(self.projection_version, "projection_version"))
        object.__setattr__(self, "role", _enum(self.role, RootCauseRole, "role"))
        object.__setattr__(self, "disposition", _enum(self.disposition, RootCauseDisposition, "disposition"))
        object.__setattr__(self, "independent_support_count", _nonnegative(self.independent_support_count, "independent_support_count"))
        object.__setattr__(self, "rejection_reason", _optional_text(self.rejection_reason, "rejection_reason"))
        object.__setattr__(self, "created_at", _utc(self.created_at, "created_at"))
        object.__setattr__(self, "metadata", _metadata(self.metadata))

    def to_dict(self) -> dict:
        return _plain(self.__dict__)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ExplanationDecisionSnapshot":
        data = _payload(value, cls)
        data["created_at"] = _parse_time(data["created_at"], "created_at")
        return cls(**data)


@dataclass(frozen=True)
class TreePlacementSnapshot:
    tree_context_reference: str
    tree_version: str
    target_projection_id: str
    parent_projection_id: Optional[str]
    child_projection_ids: Tuple[str, ...]
    alternative_projection_ids: Tuple[str, ...]
    placement_policy_version: str
    created_at: datetime
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("tree_context_reference", "tree_version", "target_projection_id", "placement_policy_version"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        parent = _optional_text(self.parent_projection_id, "parent_projection_id")
        children = _refs(self.child_projection_ids, "child_projection_ids")
        alternatives = _refs(self.alternative_projection_ids, "alternative_projection_ids")
        if self.target_projection_id == parent or self.target_projection_id in children or self.target_projection_id in alternatives:
            raise ValueError("placement must not reference the target projection as related")
        if set(children) & set(alternatives):
            raise ValueError("child and alternative projection references must be disjoint")
        object.__setattr__(self, "parent_projection_id", parent)
        object.__setattr__(self, "child_projection_ids", children)
        object.__setattr__(self, "alternative_projection_ids", alternatives)
        object.__setattr__(self, "created_at", _utc(self.created_at, "created_at"))
        object.__setattr__(self, "metadata", _metadata(self.metadata))

    def to_dict(self) -> dict:
        return _plain(self.__dict__)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "TreePlacementSnapshot":
        data = _payload(value, cls)
        data["created_at"] = _parse_time(data["created_at"], "created_at")
        return cls(**data)


@dataclass(frozen=True)
class EvidenceCatalogEntry:
    evidence_id: str
    eligibility: RealityGapEvidenceEligibility
    observed_at: datetime
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_id", _text(self.evidence_id, "evidence_id"))
        object.__setattr__(self, "eligibility", _enum(self.eligibility, RealityGapEvidenceEligibility, "eligibility"))
        object.__setattr__(self, "observed_at", _utc(self.observed_at, "observed_at"))
        object.__setattr__(self, "metadata", _metadata(self.metadata))

    def to_dict(self) -> dict:
        return _plain(self.__dict__)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "EvidenceCatalogEntry":
        data = _payload(value, cls)
        data["observed_at"] = _parse_time(data["observed_at"], "observed_at")
        return cls(**data)


@dataclass(frozen=True)
class EvidenceCatalogView:
    catalog_id: str
    catalog_version: str
    entries: Tuple[EvidenceCatalogEntry, ...]
    created_at: datetime
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "catalog_id", _text(self.catalog_id, "catalog_id"))
        object.__setattr__(self, "catalog_version", _text(self.catalog_version, "catalog_version"))
        if isinstance(self.entries, (str, bytes, set, frozenset, RuntimeMapping)):
            raise TypeError("entries must be an ordered collection")
        entries = tuple(self.entries)
        if any(not isinstance(item, EvidenceCatalogEntry) for item in entries):
            raise TypeError("entries must contain EvidenceCatalogEntry values")
        ids = tuple(item.evidence_id for item in entries)
        if len(set(ids)) != len(ids):
            raise ValueError("entries must not contain duplicate evidence IDs")
        object.__setattr__(self, "entries", tuple(sorted(entries, key=lambda item: item.evidence_id)))
        object.__setattr__(self, "created_at", _utc(self.created_at, "created_at"))
        object.__setattr__(self, "metadata", _metadata(self.metadata))

    def to_dict(self) -> dict:
        return {
            "catalog_id": self.catalog_id,
            "catalog_version": self.catalog_version,
            "entries": [item.to_dict() for item in self.entries],
            "created_at": self.created_at.isoformat(),
            "metadata": _plain(self.metadata),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "EvidenceCatalogView":
        data = _payload(value, cls)
        data["entries"] = tuple(EvidenceCatalogEntry.from_dict(item) for item in data["entries"])
        data["created_at"] = _parse_time(data["created_at"], "created_at")
        return cls(**data)


@dataclass(frozen=True)
class RootCauseCandidateMappingRequest:
    source_projection: Optional[CandidateProjection]
    explanation_descriptor: Optional[ExplanationDescriptorSnapshot]
    explanation_decision_snapshot: Optional[ExplanationDecisionSnapshot]
    placement_snapshot: Optional[TreePlacementSnapshot]
    evidence_catalog_view: Optional[EvidenceCatalogView]
    mapping_policy_version: str
    created_at: datetime
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        optional_types = (
            ("source_projection", self.source_projection, CandidateProjection),
            ("explanation_descriptor", self.explanation_descriptor, ExplanationDescriptorSnapshot),
            ("explanation_decision_snapshot", self.explanation_decision_snapshot, ExplanationDecisionSnapshot),
            ("placement_snapshot", self.placement_snapshot, TreePlacementSnapshot),
            ("evidence_catalog_view", self.evidence_catalog_view, EvidenceCatalogView),
        )
        for name, value, expected_type in optional_types:
            if value is not None and not isinstance(value, expected_type):
                raise TypeError("{0} must be {1} or None".format(name, expected_type.__name__))
        object.__setattr__(self, "mapping_policy_version", _text(self.mapping_policy_version, "mapping_policy_version"))
        object.__setattr__(self, "created_at", _utc(self.created_at, "created_at"))
        object.__setattr__(self, "metadata", _metadata(self.metadata))

    def to_dict(self) -> dict:
        return {
            "source_projection": None if self.source_projection is None else self.source_projection.to_dict(),
            "explanation_descriptor": None if self.explanation_descriptor is None else self.explanation_descriptor.to_dict(),
            "explanation_decision_snapshot": None if self.explanation_decision_snapshot is None else self.explanation_decision_snapshot.to_dict(),
            "placement_snapshot": None if self.placement_snapshot is None else self.placement_snapshot.to_dict(),
            "evidence_catalog_view": None if self.evidence_catalog_view is None else self.evidence_catalog_view.to_dict(),
            "mapping_policy_version": self.mapping_policy_version,
            "created_at": self.created_at.isoformat(),
            "metadata": _plain(self.metadata),
        }

    def to_json_bytes(self) -> bytes:
        return _json_bytes(self.to_dict())

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RootCauseCandidateMappingRequest":
        data = _payload(value, cls)
        if data["source_projection"] is not None:
            data["source_projection"] = CandidateProjection.from_dict(data["source_projection"])
        if data["explanation_descriptor"] is not None:
            data["explanation_descriptor"] = ExplanationDescriptorSnapshot.from_dict(data["explanation_descriptor"])
        if data["explanation_decision_snapshot"] is not None:
            data["explanation_decision_snapshot"] = ExplanationDecisionSnapshot.from_dict(data["explanation_decision_snapshot"])
        if data["placement_snapshot"] is not None:
            data["placement_snapshot"] = TreePlacementSnapshot.from_dict(data["placement_snapshot"])
        if data["evidence_catalog_view"] is not None:
            data["evidence_catalog_view"] = EvidenceCatalogView.from_dict(data["evidence_catalog_view"])
        data["created_at"] = _parse_time(data["created_at"], "created_at")
        return cls(**data)


@dataclass(frozen=True)
class RootCauseCandidateMappingResult:
    root_cause_candidate: RootCauseCandidate
    source_projection_id: str
    source_projection_version: int
    source_candidate_id: str
    source_candidate_version: int
    mapping_policy_version: str
    mapping_trace: Tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.root_cause_candidate, RootCauseCandidate):
            raise TypeError("root_cause_candidate must be a RootCauseCandidate")
        for name in ("source_projection_id", "source_candidate_id", "mapping_policy_version"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "source_projection_version", _positive(self.source_projection_version, "source_projection_version"))
        object.__setattr__(self, "source_candidate_version", _positive(self.source_candidate_version, "source_candidate_version"))
        object.__setattr__(self, "mapping_trace", _refs(self.mapping_trace, "mapping_trace"))
        if self.root_cause_candidate.candidate_id != self.source_projection_id:
            raise ValueError("target candidate identity must equal source projection identity")

    def to_dict(self) -> dict:
        return {
            "root_cause_candidate": self.root_cause_candidate.to_dict(),
            "source_projection_id": self.source_projection_id,
            "source_projection_version": self.source_projection_version,
            "source_candidate_id": self.source_candidate_id,
            "source_candidate_version": self.source_candidate_version,
            "mapping_policy_version": self.mapping_policy_version,
            "mapping_trace": list(self.mapping_trace),
        }

    def to_json_bytes(self) -> bytes:
        return _json_bytes(self.to_dict())

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RootCauseCandidateMappingResult":
        data = _payload(value, cls)
        data["root_cause_candidate"] = RootCauseCandidate.from_dict(data["root_cause_candidate"])
        return cls(**data)


@dataclass(frozen=True)
class RootCauseCandidateMappingFailure:
    category: MappingFailureCategory
    reason: str
    source_projection_id: Optional[str]
    source_projection_version: Optional[int]
    mapping_policy_version: str
    created_at: datetime
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "category", _enum(self.category, MappingFailureCategory, "category"))
        object.__setattr__(self, "reason", _text(self.reason, "reason"))
        object.__setattr__(self, "source_projection_id", _optional_text(self.source_projection_id, "source_projection_id"))
        if self.source_projection_version is not None:
            object.__setattr__(self, "source_projection_version", _positive(self.source_projection_version, "source_projection_version"))
        object.__setattr__(self, "mapping_policy_version", _text(self.mapping_policy_version, "mapping_policy_version"))
        object.__setattr__(self, "created_at", _utc(self.created_at, "created_at"))
        object.__setattr__(self, "metadata", _metadata(self.metadata))

    def to_dict(self) -> dict:
        return _plain(self.__dict__)

    def to_json_bytes(self) -> bytes:
        return _json_bytes(self.to_dict())

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RootCauseCandidateMappingFailure":
        data = _payload(value, cls)
        data["created_at"] = _parse_time(data["created_at"], "created_at")
        return cls(**data)


__all__ = [
    "EvidenceCatalogEntry",
    "EvidenceCatalogView",
    "ExplanationDecisionSnapshot",
    "ExplanationDescriptorSnapshot",
    "MappingFailureCategory",
    "RootCauseCandidateMappingFailure",
    "RootCauseCandidateMappingRequest",
    "RootCauseCandidateMappingResult",
    "TreePlacementSnapshot",
]
