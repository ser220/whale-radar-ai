"""Immutable Classification and Metrics output contracts.

This package contains domain records only.  It does not classify Reality Gaps,
calculate metrics, access providers, or integrate with production paths.
"""

from .enums import (
    ClassificationFailureCategory,
    MetricAvailability,
    MetricFailureCategory,
)
from .models import (
    ClassificationValidationError,
    MetricValidationError,
    RealityGapClassification,
    RealityGapMetricSet,
    RealityGapMetricValue,
)

__all__ = [
    "ClassificationFailureCategory",
    "ClassificationValidationError",
    "MetricAvailability",
    "MetricFailureCategory",
    "MetricValidationError",
    "RealityGapClassification",
    "RealityGapMetricSet",
    "RealityGapMetricValue",
]
