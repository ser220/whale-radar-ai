"""Immutable Analysis, Classification, and MetricSet attachment records."""

from collections.abc import Mapping
from dataclasses import dataclass, field, fields
from datetime import datetime
import re
from typing import Any, Dict

from ._validation import (
    canonical_json_bytes,
    frozen_metadata,
    mapping_payload,
    parse_datetime,
    plain,
    positive_version,
    required_text,
    utc_datetime,
)
from .enums import AttachmentFailureCategory


_POLICY_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_SNAPSHOT_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


class AttachmentValidationError(ValueError):
    """Categorized contract validation failure with no partial attachment."""

    def __init__(
        self,
        category: AttachmentFailureCategory,
        field_name: str,
        reason: str,
    ) -> None:
        self.category = category
        self.field_name = field_name
        self.reason = reason
        super().__init__("{0}: {1}: {2}".format(category.value, field_name, reason))


def _error(category: AttachmentFailureCategory):
    def factory(field_name: str, reason: str) -> AttachmentValidationError:
        return AttachmentValidationError(category, field_name, reason)

    return factory


def _snapshot_digest(value: Any, field_name: str) -> str:
    error = _error(AttachmentFailureCategory.INVALID_REFERENCE)
    normalized = required_text(value, field_name, error)
    if _SNAPSHOT_DIGEST.fullmatch(normalized) is None:
        raise error(
            field_name,
            "must be canonical sha256:<64 lowercase hex> material",
        )
    return normalized


@dataclass(frozen=True)
class AnalysisReference:
    """Exact logical identity and version of one Analysis revision."""

    analysis_id: str
    analysis_version: int

    def __post_init__(self) -> None:
        identity_error = _error(AttachmentFailureCategory.INVALID_REFERENCE)
        version_error = _error(AttachmentFailureCategory.VERSION_CONFLICT)
        object.__setattr__(
            self,
            "analysis_id",
            required_text(self.analysis_id, "analysis_id", identity_error),
        )
        object.__setattr__(
            self,
            "analysis_version",
            positive_version(
                self.analysis_version, "analysis_version", version_error
            ),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "analysis_version": self.analysis_version,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "AnalysisReference":
        payload = mapping_payload(
            value,
            tuple(item.name for item in fields(cls)),
            cls.__name__,
            _error(AttachmentFailureCategory.INVALID_REFERENCE),
        )
        return cls(**payload)


@dataclass(frozen=True)
class ClassificationReference:
    """Exact Classification identity and canonical snapshot revision."""

    classification_id: str
    canonical_snapshot_digest: str

    def __post_init__(self) -> None:
        error = _error(AttachmentFailureCategory.INVALID_REFERENCE)
        object.__setattr__(
            self,
            "classification_id",
            required_text(
                self.classification_id, "classification_id", error
            ),
        )
        object.__setattr__(
            self,
            "canonical_snapshot_digest",
            _snapshot_digest(
                self.canonical_snapshot_digest,
                "classification canonical_snapshot_digest",
            ),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "classification_id": self.classification_id,
            "canonical_snapshot_digest": self.canonical_snapshot_digest,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ClassificationReference":
        payload = mapping_payload(
            value,
            tuple(item.name for item in fields(cls)),
            cls.__name__,
            _error(AttachmentFailureCategory.INVALID_REFERENCE),
        )
        return cls(**payload)


@dataclass(frozen=True)
class MetricSetReference:
    """Exact MetricSet identity and canonical snapshot revision."""

    metric_set_id: str
    canonical_snapshot_digest: str

    def __post_init__(self) -> None:
        error = _error(AttachmentFailureCategory.INVALID_REFERENCE)
        object.__setattr__(
            self,
            "metric_set_id",
            required_text(self.metric_set_id, "metric_set_id", error),
        )
        object.__setattr__(
            self,
            "canonical_snapshot_digest",
            _snapshot_digest(
                self.canonical_snapshot_digest,
                "metric canonical_snapshot_digest",
            ),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_set_id": self.metric_set_id,
            "canonical_snapshot_digest": self.canonical_snapshot_digest,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "MetricSetReference":
        payload = mapping_payload(
            value,
            tuple(item.name for item in fields(cls)),
            cls.__name__,
            _error(AttachmentFailureCategory.INVALID_REFERENCE),
        )
        return cls(**payload)


@dataclass(frozen=True)
class RealityGapAnalysisAttachment:
    """One immutable relationship among exact independent artifacts."""

    attachment_id: str
    attachment_version: int
    analysis_reference: AnalysisReference
    classification_reference: ClassificationReference
    metric_set_reference: MetricSetReference
    attachment_policy_version: str
    created_at: datetime
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        reference_error = _error(AttachmentFailureCategory.INVALID_REFERENCE)
        version_error = _error(AttachmentFailureCategory.VERSION_CONFLICT)
        policy_error = _error(AttachmentFailureCategory.POLICY_CONFLICT)
        attachment_id = required_text(
            self.attachment_id, "attachment_id", reference_error
        )
        attachment_version = positive_version(
            self.attachment_version, "attachment_version", version_error
        )
        if not isinstance(self.analysis_reference, AnalysisReference):
            raise reference_error(
                "analysis_reference", "must be an AnalysisReference"
            )
        if self.classification_reference is None:
            raise AttachmentValidationError(
                AttachmentFailureCategory.MISSING_CLASSIFICATION,
                "classification_reference",
                "is required",
            )
        if not isinstance(self.classification_reference, ClassificationReference):
            raise reference_error(
                "classification_reference", "must be a ClassificationReference"
            )
        if self.metric_set_reference is None:
            raise AttachmentValidationError(
                AttachmentFailureCategory.MISSING_METRICS,
                "metric_set_reference",
                "is required",
            )
        if not isinstance(self.metric_set_reference, MetricSetReference):
            raise reference_error(
                "metric_set_reference", "must be a MetricSetReference"
            )
        policy = required_text(
            self.attachment_policy_version,
            "attachment_policy_version",
            policy_error,
        )
        if _POLICY_VERSION.fullmatch(policy) is None:
            raise policy_error(
                "attachment_policy_version",
                "contains unsupported characters",
            )
        created_at = utc_datetime(self.created_at, "created_at", reference_error)
        metadata = frozen_metadata(self.metadata, "metadata", reference_error)

        ids = {
            attachment_id,
            self.analysis_reference.analysis_id,
            self.classification_reference.classification_id,
            self.metric_set_reference.metric_set_id,
        }
        if len(ids) != 4:
            if attachment_id == self.analysis_reference.analysis_id:
                category = AttachmentFailureCategory.ANALYSIS_MISMATCH
            else:
                category = AttachmentFailureCategory.INVALID_REFERENCE
            raise AttachmentValidationError(
                category,
                "identity",
                "analysis, classification, metric, and attachment IDs must remain separate",
            )

        expected_metadata = {
            "attachment_id": (attachment_id, AttachmentFailureCategory.INVALID_REFERENCE),
            "attachment_version": (
                attachment_version,
                AttachmentFailureCategory.VERSION_CONFLICT,
            ),
            "analysis_id": (
                self.analysis_reference.analysis_id,
                AttachmentFailureCategory.ANALYSIS_MISMATCH,
            ),
            "analysis_version": (
                self.analysis_reference.analysis_version,
                AttachmentFailureCategory.ANALYSIS_MISMATCH,
            ),
            "classification_id": (
                self.classification_reference.classification_id,
                AttachmentFailureCategory.INVALID_REFERENCE,
            ),
            "classification_snapshot_digest": (
                self.classification_reference.canonical_snapshot_digest,
                AttachmentFailureCategory.INVALID_REFERENCE,
            ),
            "metric_set_id": (
                self.metric_set_reference.metric_set_id,
                AttachmentFailureCategory.INVALID_REFERENCE,
            ),
            "metric_snapshot_digest": (
                self.metric_set_reference.canonical_snapshot_digest,
                AttachmentFailureCategory.INVALID_REFERENCE,
            ),
            "attachment_policy_version": (
                policy,
                AttachmentFailureCategory.POLICY_CONFLICT,
            ),
        }
        for key, expected in expected_metadata.items():
            if key in metadata and metadata[key] != expected[0]:
                raise AttachmentValidationError(
                    expected[1],
                    "metadata.{0}".format(key),
                    "must agree with the explicit attachment field",
                )
        if "trace_reference" in metadata:
            trace_reference = metadata["trace_reference"]
            if not isinstance(trace_reference, str) or not trace_reference.strip():
                raise reference_error(
                    "metadata.trace_reference", "must be a non-empty string"
                )
            if trace_reference in ids:
                raise reference_error(
                    "metadata.trace_reference",
                    "trace identity must remain separate",
                )

        object.__setattr__(self, "attachment_id", attachment_id)
        object.__setattr__(self, "attachment_version", attachment_version)
        object.__setattr__(self, "attachment_policy_version", policy)
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "metadata", metadata)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attachment_id": self.attachment_id,
            "attachment_version": self.attachment_version,
            "analysis_reference": self.analysis_reference.to_dict(),
            "classification_reference": self.classification_reference.to_dict(),
            "metric_set_reference": self.metric_set_reference.to_dict(),
            "attachment_policy_version": self.attachment_policy_version,
            "created_at": self.created_at.isoformat(),
            "metadata": plain(self.metadata),
        }

    def to_json_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_dict())

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RealityGapAnalysisAttachment":
        reference_error = _error(AttachmentFailureCategory.INVALID_REFERENCE)
        if not isinstance(value, Mapping):
            raise reference_error(cls.__name__, "serialized value must be a mapping")
        if "classification_reference" not in value or value.get(
            "classification_reference"
        ) is None:
            raise AttachmentValidationError(
                AttachmentFailureCategory.MISSING_CLASSIFICATION,
                "classification_reference",
                "is required",
            )
        if "metric_set_reference" not in value or value.get(
            "metric_set_reference"
        ) is None:
            raise AttachmentValidationError(
                AttachmentFailureCategory.MISSING_METRICS,
                "metric_set_reference",
                "is required",
            )
        payload = mapping_payload(
            value,
            tuple(item.name for item in fields(cls)),
            cls.__name__,
            reference_error,
        )
        payload["analysis_reference"] = AnalysisReference.from_dict(
            payload["analysis_reference"]
        )
        payload["classification_reference"] = ClassificationReference.from_dict(
            payload["classification_reference"]
        )
        payload["metric_set_reference"] = MetricSetReference.from_dict(
            payload["metric_set_reference"]
        )
        payload["created_at"] = parse_datetime(
            payload["created_at"], "created_at", reference_error
        )
        return cls(**payload)


__all__ = [
    "AnalysisReference",
    "AttachmentValidationError",
    "ClassificationReference",
    "MetricSetReference",
    "RealityGapAnalysisAttachment",
]
