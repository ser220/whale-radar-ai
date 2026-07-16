"""Immutable policy and historical-context inputs for pure consumers."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Any, Tuple

from app.intelligence.reality_gap.enums import (
    RealityGapDimension,
    RootCauseCategory,
)

from ._validation import (
    category_tokens,
    frozen_metadata,
    policy_version,
    required_text,
    utc_datetime,
)
from .consumer_enums import (
    ClassificationConsumerFailureCategory,
    MetricIndicator,
    MetricsConsumerFailureCategory,
)


class ClassificationConsumerError(ValueError):
    """Categorized failure with no partial Classification output."""

    def __init__(
        self,
        category: ClassificationConsumerFailureCategory,
        field_name: str,
        reason: str,
    ) -> None:
        self.category = category
        self.field_name = field_name
        self.reason = reason
        super().__init__("{0}: {1}: {2}".format(category.value, field_name, reason))


class MetricsConsumerError(ValueError):
    """Categorized failure with no partial Metrics output."""

    def __init__(
        self,
        category: MetricsConsumerFailureCategory,
        field_name: str,
        reason: str,
    ) -> None:
        self.category = category
        self.field_name = field_name
        self.reason = reason
        super().__init__("{0}: {1}: {2}".format(category.value, field_name, reason))


def _classification_error(
    category: ClassificationConsumerFailureCategory,
):
    def factory(field_name: str, reason: str) -> ClassificationConsumerError:
        return ClassificationConsumerError(category, field_name, reason)

    return factory


def _metrics_error(category: MetricsConsumerFailureCategory):
    def factory(field_name: str, reason: str) -> MetricsConsumerError:
        return MetricsConsumerError(category, field_name, reason)

    return factory


def _reference_tuple(
    value: Any,
    field_name: str,
    allow_empty: bool,
) -> Tuple[str, ...]:
    error = _classification_error(
        ClassificationConsumerFailureCategory.INVALID_INPUT_REFERENCE
    )
    if isinstance(value, (str, bytes, set, frozenset, Mapping)):
        raise error(field_name, "must be an ordered collection")
    try:
        raw = tuple(value)
    except TypeError:
        raise error(field_name, "must be an ordered collection")
    if not raw and not allow_empty:
        raise error(field_name, "must contain at least one reference")
    normalized = tuple(
        required_text(item, "{0} item".format(field_name), error) for item in raw
    )
    if len(set(normalized)) != len(normalized):
        raise error(field_name, "must not contain duplicates")
    return tuple(sorted(normalized))


def _positive_version(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ClassificationConsumerError(
            ClassificationConsumerFailureCategory.VERSION_CONFLICT,
            field_name,
            "must be a positive integer",
        )
    return value


def _dimension_tuple(value: Any) -> Tuple[RealityGapDimension, ...]:
    error = _classification_error(
        ClassificationConsumerFailureCategory.UNSUPPORTED_DIMENSION
    )
    if isinstance(value, (str, bytes, set, frozenset, Mapping)):
        raise error("dimensions", "must be an ordered collection")
    try:
        raw = tuple(value)
    except TypeError:
        raise error("dimensions", "must be an ordered collection")
    if not raw:
        raise error("dimensions", "must contain at least one dimension")
    dimensions = []
    for item in raw:
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


@dataclass(frozen=True)
class RealityGapConsumerContext:
    """Caller-supplied immutable historical evaluation boundary."""

    analysis_reference: str
    analysis_version: int
    analysis_policy_version: str
    evaluated_at: datetime
    eligible_window_start: datetime
    eligible_window_end: datetime
    candidate_references: Tuple[str, ...]
    evidence_references: Tuple[str, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        input_error = _classification_error(
            ClassificationConsumerFailureCategory.INVALID_INPUT_REFERENCE
        )
        policy_error = _classification_error(
            ClassificationConsumerFailureCategory.POLICY_MISMATCH
        )
        analysis_reference = required_text(
            self.analysis_reference, "analysis_reference", input_error
        )
        version = _positive_version(self.analysis_version, "analysis_version")
        policy = policy_version(
            self.analysis_policy_version,
            "analysis_policy_version",
            policy_error,
        )
        evaluated_at = utc_datetime(self.evaluated_at, "evaluated_at", input_error)
        window_start = utc_datetime(
            self.eligible_window_start, "eligible_window_start", input_error
        )
        window_end = utc_datetime(
            self.eligible_window_end, "eligible_window_end", input_error
        )
        if window_start > window_end or window_end > evaluated_at:
            raise input_error(
                "eligible_window",
                "must be ordered and must not extend beyond evaluated_at",
            )
        candidate_refs = _reference_tuple(
            self.candidate_references, "candidate_references", False
        )
        evidence_refs = _reference_tuple(
            self.evidence_references, "evidence_references", True
        )
        if set(candidate_refs) & set(evidence_refs):
            raise input_error(
                "references", "candidate and evidence identities must remain separate"
            )
        metadata = frozen_metadata(self.metadata, "metadata", input_error)

        object.__setattr__(self, "analysis_reference", analysis_reference)
        object.__setattr__(self, "analysis_version", version)
        object.__setattr__(self, "analysis_policy_version", policy)
        object.__setattr__(self, "evaluated_at", evaluated_at)
        object.__setattr__(self, "eligible_window_start", window_start)
        object.__setattr__(self, "eligible_window_end", window_end)
        object.__setattr__(self, "candidate_references", candidate_refs)
        object.__setattr__(self, "evidence_references", evidence_refs)
        object.__setattr__(self, "metadata", metadata)

    def to_dict(self) -> dict:
        return {
            "analysis_reference": self.analysis_reference,
            "analysis_version": self.analysis_version,
            "analysis_policy_version": self.analysis_policy_version,
            "evaluated_at": self.evaluated_at.isoformat(),
            "eligible_window_start": self.eligible_window_start.isoformat(),
            "eligible_window_end": self.eligible_window_end.isoformat(),
            "candidate_references": list(self.candidate_references),
            "evidence_references": list(self.evidence_references),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class ClassificationAssignment:
    """Explicit policy-owned output for one existing candidate category."""

    dimensions: Tuple[RealityGapDimension, ...]
    categories: Tuple[str, ...]

    def __post_init__(self) -> None:
        category_error = _classification_error(
            ClassificationConsumerFailureCategory.POLICY_MISMATCH
        )
        object.__setattr__(self, "dimensions", _dimension_tuple(self.dimensions))
        object.__setattr__(
            self,
            "categories",
            category_tokens(self.categories, category_error),
        )

    def to_dict(self) -> dict:
        return {
            "dimensions": [item.value for item in self.dimensions],
            "categories": list(self.categories),
        }


@dataclass(frozen=True)
class ClassificationConsumerPolicy:
    """Versioned explicit mapping; the consumer owns no hidden taxonomy."""

    policy_version: str
    expected_analysis_policy_version: str
    expected_candidate_policy_version: str
    assignments: Mapping[RootCauseCategory, ClassificationAssignment]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        policy_error = _classification_error(
            ClassificationConsumerFailureCategory.POLICY_MISMATCH
        )
        version = policy_version(self.policy_version, "policy_version", policy_error)
        analysis_policy = policy_version(
            self.expected_analysis_policy_version,
            "expected_analysis_policy_version",
            policy_error,
        )
        candidate_policy = policy_version(
            self.expected_candidate_policy_version,
            "expected_candidate_policy_version",
            policy_error,
        )
        if not isinstance(self.assignments, Mapping) or not self.assignments:
            raise policy_error("assignments", "must contain an explicit mapping")
        normalized = {}
        for raw_category, assignment in self.assignments.items():
            try:
                category = (
                    raw_category
                    if isinstance(raw_category, RootCauseCategory)
                    else RootCauseCategory(raw_category)
                )
            except (TypeError, ValueError):
                raise policy_error("assignments", "contains an unknown candidate category")
            if not isinstance(assignment, ClassificationAssignment):
                raise policy_error(
                    "assignments.{0}".format(category.value),
                    "must be a ClassificationAssignment",
                )
            normalized[category] = assignment
        assignments = MappingProxyType(
            {key: normalized[key] for key in sorted(normalized, key=lambda item: item.value)}
        )
        metadata = frozen_metadata(self.metadata, "metadata", policy_error)

        object.__setattr__(self, "policy_version", version)
        object.__setattr__(
            self, "expected_analysis_policy_version", analysis_policy
        )
        object.__setattr__(
            self, "expected_candidate_policy_version", candidate_policy
        )
        object.__setattr__(self, "assignments", assignments)
        object.__setattr__(self, "metadata", metadata)

    def to_dict(self) -> dict:
        return {
            "policy_version": self.policy_version,
            "expected_analysis_policy_version": self.expected_analysis_policy_version,
            "expected_candidate_policy_version": self.expected_candidate_policy_version,
            "assignments": {
                category.value: self.assignments[category].to_dict()
                for category in self.assignments
            },
        }


@dataclass(frozen=True)
class MetricsConsumerPolicy:
    """Versioned selection of transparent Phase 1 indicators."""

    policy_version: str
    expected_analysis_policy_version: str
    expected_candidate_policy_version: str
    indicators: Tuple[MetricIndicator, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        policy_error = _metrics_error(MetricsConsumerFailureCategory.POLICY_MISMATCH)
        unsupported_error = _metrics_error(
            MetricsConsumerFailureCategory.UNSUPPORTED_METRIC
        )
        version = policy_version(self.policy_version, "policy_version", policy_error)
        analysis_policy = policy_version(
            self.expected_analysis_policy_version,
            "expected_analysis_policy_version",
            policy_error,
        )
        candidate_policy = policy_version(
            self.expected_candidate_policy_version,
            "expected_candidate_policy_version",
            policy_error,
        )
        if isinstance(self.indicators, (str, bytes, set, frozenset, Mapping)):
            raise unsupported_error("indicators", "must be an ordered collection")
        try:
            raw_indicators = tuple(self.indicators)
        except TypeError:
            raise unsupported_error("indicators", "must be an ordered collection")
        if not raw_indicators:
            raise unsupported_error("indicators", "must not be empty")
        indicators = []
        for item in raw_indicators:
            try:
                indicator = (
                    item if isinstance(item, MetricIndicator) else MetricIndicator(item)
                )
            except (TypeError, ValueError):
                raise unsupported_error("indicators", "contains an unsupported metric")
            indicators.append(indicator)
        if len(set(indicators)) != len(indicators):
            raise unsupported_error("indicators", "must not contain duplicates")
        metadata = frozen_metadata(self.metadata, "metadata", policy_error)

        object.__setattr__(self, "policy_version", version)
        object.__setattr__(
            self, "expected_analysis_policy_version", analysis_policy
        )
        object.__setattr__(
            self, "expected_candidate_policy_version", candidate_policy
        )
        object.__setattr__(
            self,
            "indicators",
            tuple(sorted(indicators, key=lambda item: item.value)),
        )
        object.__setattr__(self, "metadata", metadata)

    def to_dict(self) -> dict:
        return {
            "policy_version": self.policy_version,
            "expected_analysis_policy_version": self.expected_analysis_policy_version,
            "expected_candidate_policy_version": self.expected_candidate_policy_version,
            "indicators": [item.value for item in self.indicators],
        }


__all__ = [
    "ClassificationAssignment",
    "ClassificationConsumerError",
    "ClassificationConsumerPolicy",
    "MetricsConsumerError",
    "MetricsConsumerPolicy",
    "RealityGapConsumerContext",
]
