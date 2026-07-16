"""Public enum contracts for Classification and Metrics records."""

from enum import Enum


class ClassificationFailureCategory(str, Enum):
    """Stable validation failure categories for classifications."""

    MISSING_IDENTITY = "MISSING_IDENTITY"
    INVALID_POLICY_VERSION = "INVALID_POLICY_VERSION"
    INVALID_ANALYSIS_REFERENCE = "INVALID_ANALYSIS_REFERENCE"
    INVALID_DIMENSION = "INVALID_DIMENSION"
    INVALID_CATEGORY = "INVALID_CATEGORY"
    INVALID_TIMESTAMP = "INVALID_TIMESTAMP"
    MUTABLE_PAYLOAD = "MUTABLE_PAYLOAD"


class MetricFailureCategory(str, Enum):
    """Stable validation failure categories for metric sets and values."""

    MISSING_IDENTITY = "MISSING_IDENTITY"
    INVALID_POLICY_VERSION = "INVALID_POLICY_VERSION"
    INVALID_ANALYSIS_REFERENCE = "INVALID_ANALYSIS_REFERENCE"
    INVALID_METRIC = "INVALID_METRIC"
    INVALID_AVAILABILITY = "INVALID_AVAILABILITY"
    INVALID_TIMESTAMP = "INVALID_TIMESTAMP"
    MUTABLE_PAYLOAD = "MUTABLE_PAYLOAD"


class MetricAvailability(str, Enum):
    """Whether one metric value was actually measured."""

    AVAILABLE = "AVAILABLE"
    MISSING = "MISSING"
    STALE = "STALE"
    UNSUPPORTED = "UNSUPPORTED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


__all__ = [
    "ClassificationFailureCategory",
    "MetricAvailability",
    "MetricFailureCategory",
]
