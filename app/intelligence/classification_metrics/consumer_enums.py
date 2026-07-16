"""Public enums for read-only Classification and Metrics consumers."""

from enum import Enum


class ClassificationConsumerFailureCategory(str, Enum):
    INVALID_INPUT_REFERENCE = "INVALID_INPUT_REFERENCE"
    POLICY_MISMATCH = "POLICY_MISMATCH"
    UNSUPPORTED_DIMENSION = "UNSUPPORTED_DIMENSION"
    VERSION_CONFLICT = "VERSION_CONFLICT"


class MetricsConsumerFailureCategory(str, Enum):
    INVALID_INPUT_REFERENCE = "INVALID_INPUT_REFERENCE"
    POLICY_MISMATCH = "POLICY_MISMATCH"
    UNSUPPORTED_METRIC = "UNSUPPORTED_METRIC"
    VERSION_CONFLICT = "VERSION_CONFLICT"


class MetricIndicator(str, Enum):
    """Approved transparent indicators implemented in Phase 1."""

    EVIDENCE_AVAILABILITY_RATIO = "evidence_availability_ratio"
    REFERENCE_COVERAGE = "reference_coverage"


__all__ = [
    "ClassificationConsumerFailureCategory",
    "MetricIndicator",
    "MetricsConsumerFailureCategory",
]
