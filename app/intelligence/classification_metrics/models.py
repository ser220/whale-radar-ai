"""Immutable, calculation-free Classification and Metrics records."""

from collections.abc import Mapping
from dataclasses import dataclass, field, fields
from datetime import datetime
from types import MappingProxyType
from typing import Any, Dict, Optional, Tuple

from app.intelligence.reality_gap.enums import RealityGapDimension

from ._validation import (
    canonical_json_bytes,
    category_tokens,
    frozen_metadata,
    mapping_payload,
    metric_key,
    metric_scalar,
    optional_text,
    ordered_references,
    parse_datetime,
    plain,
    policy_version,
    required_text,
    utc_datetime,
)
from .enums import (
    ClassificationFailureCategory,
    MetricAvailability,
    MetricFailureCategory,
)


class ClassificationValidationError(ValueError):
    """A categorized Classification contract validation failure."""

    def __init__(
        self,
        category: ClassificationFailureCategory,
        field_name: str,
        reason: str,
    ) -> None:
        self.category = category
        self.field_name = field_name
        self.reason = reason
        super().__init__("{0}: {1}: {2}".format(category.value, field_name, reason))


class MetricValidationError(ValueError):
    """A categorized Metrics contract validation failure."""

    def __init__(
        self,
        category: MetricFailureCategory,
        field_name: str,
        reason: str,
    ) -> None:
        self.category = category
        self.field_name = field_name
        self.reason = reason
        super().__init__("{0}: {1}: {2}".format(category.value, field_name, reason))


def _classification_error(
    category: ClassificationFailureCategory,
):
    def factory(field_name: str, reason: str) -> ClassificationValidationError:
        return ClassificationValidationError(category, field_name, reason)

    return factory


def _metric_error(category: MetricFailureCategory):
    def factory(field_name: str, reason: str) -> MetricValidationError:
        return MetricValidationError(category, field_name, reason)

    return factory


def _classification_dimensions(value: Any) -> Tuple[RealityGapDimension, ...]:
    error = _classification_error(ClassificationFailureCategory.INVALID_DIMENSION)
    if isinstance(value, (str, bytes, set, frozenset, Mapping)):
        raise error("dimensions", "must be an ordered collection")
    try:
        raw_items = tuple(value)
    except TypeError:
        raise error("dimensions", "must be an ordered collection")
    if not raw_items:
        raise error("dimensions", "must contain at least one dimension")
    dimensions = []
    for item in raw_items:
        try:
            dimension = (
                item if isinstance(item, RealityGapDimension) else RealityGapDimension(item)
            )
        except (TypeError, ValueError):
            raise error("dimensions", "contains an unsupported dimension")
        if dimension is RealityGapDimension.UNKNOWN:
            raise error("dimensions", "UNKNOWN is not an approved dimension")
        dimensions.append(dimension)
    if len(set(dimensions)) != len(dimensions):
        raise error("dimensions", "must not contain duplicates")
    return tuple(sorted(dimensions, key=lambda item: item.value))


def _validate_identity_separation(
    output_id: str,
    analysis_reference: str,
    trace_reference: str,
    input_references: Tuple[str, ...],
    error_factory,
) -> None:
    if len({output_id, analysis_reference, trace_reference}) != 3:
        raise error_factory(
            "identity",
            "output, analysis, and trace identities must remain separate",
        )
    if output_id in input_references or trace_reference in input_references:
        raise error_factory(
            "input_references",
            "must not collapse output or trace identity into input lineage",
        )


@dataclass(frozen=True)
class RealityGapClassification:
    """Versioned categorization output with no classification behavior."""

    classification_id: str
    classification_policy_version: str
    analysis_reference: str
    input_references: Tuple[str, ...]
    dimensions: Tuple[RealityGapDimension, ...]
    categories: Tuple[str, ...]
    created_at: datetime
    trace_reference: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        identity_error = _classification_error(
            ClassificationFailureCategory.MISSING_IDENTITY
        )
        policy_error = _classification_error(
            ClassificationFailureCategory.INVALID_POLICY_VERSION
        )
        analysis_error = _classification_error(
            ClassificationFailureCategory.INVALID_ANALYSIS_REFERENCE
        )
        category_error = _classification_error(
            ClassificationFailureCategory.INVALID_CATEGORY
        )
        timestamp_error = _classification_error(
            ClassificationFailureCategory.INVALID_TIMESTAMP
        )
        payload_error = _classification_error(
            ClassificationFailureCategory.MUTABLE_PAYLOAD
        )

        classification_id = required_text(
            self.classification_id, "classification_id", identity_error
        )
        policy = policy_version(
            self.classification_policy_version,
            "classification_policy_version",
            policy_error,
        )
        analysis_reference = required_text(
            self.analysis_reference, "analysis_reference", analysis_error
        )
        references = ordered_references(
            self.input_references, "input_references", analysis_error
        )
        dimensions = _classification_dimensions(self.dimensions)
        categories = category_tokens(self.categories, category_error)
        created_at = utc_datetime(self.created_at, "created_at", timestamp_error)
        trace_reference = required_text(
            self.trace_reference, "trace_reference", identity_error
        )
        metadata = frozen_metadata(self.metadata, "metadata", payload_error)

        _validate_identity_separation(
            classification_id,
            analysis_reference,
            trace_reference,
            references,
            identity_error,
        )

        object.__setattr__(self, "classification_id", classification_id)
        object.__setattr__(self, "classification_policy_version", policy)
        object.__setattr__(self, "analysis_reference", analysis_reference)
        object.__setattr__(self, "input_references", references)
        object.__setattr__(self, "dimensions", dimensions)
        object.__setattr__(self, "categories", categories)
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "trace_reference", trace_reference)
        object.__setattr__(self, "metadata", metadata)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "classification_id": self.classification_id,
            "classification_policy_version": self.classification_policy_version,
            "analysis_reference": self.analysis_reference,
            "input_references": list(self.input_references),
            "dimensions": [item.value for item in self.dimensions],
            "categories": list(self.categories),
            "created_at": self.created_at.isoformat(),
            "trace_reference": self.trace_reference,
            "metadata": plain(self.metadata),
        }

    def to_json_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_dict())

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RealityGapClassification":
        payload_error = _classification_error(
            ClassificationFailureCategory.MUTABLE_PAYLOAD
        )
        timestamp_error = _classification_error(
            ClassificationFailureCategory.INVALID_TIMESTAMP
        )
        payload = mapping_payload(
            value,
            tuple(item.name for item in fields(cls)),
            cls.__name__,
            payload_error,
        )
        payload["created_at"] = parse_datetime(
            payload["created_at"], "created_at", timestamp_error
        )
        return cls(**payload)


@dataclass(frozen=True)
class RealityGapMetricValue:
    """One explicitly available or unavailable metric value."""

    availability: MetricAvailability
    value: Optional[float]
    unit: Optional[str]
    policy_reference: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        availability_error = _metric_error(
            MetricFailureCategory.INVALID_AVAILABILITY
        )
        metric_error = _metric_error(MetricFailureCategory.INVALID_METRIC)
        policy_error = _metric_error(MetricFailureCategory.INVALID_POLICY_VERSION)
        payload_error = _metric_error(MetricFailureCategory.MUTABLE_PAYLOAD)

        try:
            availability = (
                self.availability
                if isinstance(self.availability, MetricAvailability)
                else MetricAvailability(self.availability)
            )
        except (TypeError, ValueError):
            raise availability_error(
                "availability", "is not a supported availability state"
            )

        if availability is MetricAvailability.AVAILABLE:
            if self.value is None:
                raise availability_error("value", "AVAILABLE requires a value")
            value = metric_scalar(self.value, metric_error)
        else:
            if self.value is not None:
                raise availability_error(
                    "value",
                    "non-AVAILABLE states must not contain a measured value",
                )
            value = None

        unit = optional_text(self.unit, "unit", metric_error)
        policy = policy_version(
            self.policy_reference, "policy_reference", policy_error
        )
        metadata = frozen_metadata(self.metadata, "metadata", payload_error)

        object.__setattr__(self, "availability", availability)
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "unit", unit)
        object.__setattr__(self, "policy_reference", policy)
        object.__setattr__(self, "metadata", metadata)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "availability": self.availability.value,
            "value": self.value,
            "unit": self.unit,
            "policy_reference": self.policy_reference,
            "metadata": plain(self.metadata),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RealityGapMetricValue":
        payload_error = _metric_error(MetricFailureCategory.MUTABLE_PAYLOAD)
        payload = mapping_payload(
            value,
            tuple(item.name for item in fields(cls)),
            cls.__name__,
            payload_error,
        )
        return cls(**payload)


@dataclass(frozen=True)
class RealityGapMetricSet:
    """Versioned metric output with no calculation or scoring behavior."""

    metric_set_id: str
    metric_policy_version: str
    analysis_reference: str
    input_references: Tuple[str, ...]
    metrics: Mapping[str, RealityGapMetricValue]
    created_at: datetime
    trace_reference: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        identity_error = _metric_error(MetricFailureCategory.MISSING_IDENTITY)
        policy_error = _metric_error(MetricFailureCategory.INVALID_POLICY_VERSION)
        analysis_error = _metric_error(
            MetricFailureCategory.INVALID_ANALYSIS_REFERENCE
        )
        metric_error = _metric_error(MetricFailureCategory.INVALID_METRIC)
        timestamp_error = _metric_error(MetricFailureCategory.INVALID_TIMESTAMP)
        payload_error = _metric_error(MetricFailureCategory.MUTABLE_PAYLOAD)

        metric_set_id = required_text(
            self.metric_set_id, "metric_set_id", identity_error
        )
        policy = policy_version(
            self.metric_policy_version, "metric_policy_version", policy_error
        )
        analysis_reference = required_text(
            self.analysis_reference, "analysis_reference", analysis_error
        )
        references = ordered_references(
            self.input_references, "input_references", analysis_error
        )
        if not isinstance(self.metrics, Mapping):
            raise payload_error("metrics", "must be a mapping")
        if not self.metrics:
            raise metric_error("metrics", "must contain at least one metric")
        normalized_metrics = {}
        for raw_key in self.metrics:
            key = metric_key(raw_key, metric_error)
            metric = self.metrics[raw_key]
            if not isinstance(metric, RealityGapMetricValue):
                raise metric_error(
                    "metrics.{0}".format(key),
                    "must be a RealityGapMetricValue",
                )
            normalized_metrics[key] = metric
        metrics = MappingProxyType(
            {key: normalized_metrics[key] for key in sorted(normalized_metrics)}
        )
        created_at = utc_datetime(self.created_at, "created_at", timestamp_error)
        trace_reference = required_text(
            self.trace_reference, "trace_reference", identity_error
        )
        metadata = frozen_metadata(self.metadata, "metadata", payload_error)

        _validate_identity_separation(
            metric_set_id,
            analysis_reference,
            trace_reference,
            references,
            identity_error,
        )

        object.__setattr__(self, "metric_set_id", metric_set_id)
        object.__setattr__(self, "metric_policy_version", policy)
        object.__setattr__(self, "analysis_reference", analysis_reference)
        object.__setattr__(self, "input_references", references)
        object.__setattr__(self, "metrics", metrics)
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "trace_reference", trace_reference)
        object.__setattr__(self, "metadata", metadata)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_set_id": self.metric_set_id,
            "metric_policy_version": self.metric_policy_version,
            "analysis_reference": self.analysis_reference,
            "input_references": list(self.input_references),
            "metrics": {
                key: self.metrics[key].to_dict() for key in sorted(self.metrics)
            },
            "created_at": self.created_at.isoformat(),
            "trace_reference": self.trace_reference,
            "metadata": plain(self.metadata),
        }

    def to_json_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_dict())

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RealityGapMetricSet":
        payload_error = _metric_error(MetricFailureCategory.MUTABLE_PAYLOAD)
        timestamp_error = _metric_error(MetricFailureCategory.INVALID_TIMESTAMP)
        metric_error = _metric_error(MetricFailureCategory.INVALID_METRIC)
        payload = mapping_payload(
            value,
            tuple(item.name for item in fields(cls)),
            cls.__name__,
            payload_error,
        )
        payload["created_at"] = parse_datetime(
            payload["created_at"], "created_at", timestamp_error
        )
        if not isinstance(payload["metrics"], Mapping):
            raise metric_error("metrics", "must be a mapping")
        payload["metrics"] = {
            key: RealityGapMetricValue.from_dict(metric)
            for key, metric in payload["metrics"].items()
        }
        return cls(**payload)


__all__ = [
    "ClassificationValidationError",
    "MetricValidationError",
    "RealityGapClassification",
    "RealityGapMetricSet",
    "RealityGapMetricValue",
]
