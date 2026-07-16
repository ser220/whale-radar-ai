"""Immutable Classification and Metrics output contracts.

This package contains domain records only.  It does not classify Reality Gaps,
calculate metrics, access providers, or integrate with production paths.
"""

from .enums import (
    ClassificationFailureCategory,
    MetricAvailability,
    MetricFailureCategory,
)
from .consumer_enums import (
    ClassificationConsumerFailureCategory,
    MetricIndicator,
    MetricsConsumerFailureCategory,
)
from .consumer_models import (
    ClassificationAssignment,
    ClassificationConsumerError,
    ClassificationConsumerPolicy,
    MetricsConsumerError,
    MetricsConsumerPolicy,
    RealityGapConsumerContext,
)
from .consumers import classify_reality_gap, measure_reality_gap
from .models import (
    ClassificationValidationError,
    MetricValidationError,
    RealityGapClassification,
    RealityGapMetricSet,
    RealityGapMetricValue,
)

__all__ = [
    "ClassificationAssignment",
    "ClassificationConsumerError",
    "ClassificationConsumerFailureCategory",
    "ClassificationConsumerPolicy",
    "ClassificationFailureCategory",
    "ClassificationValidationError",
    "MetricAvailability",
    "MetricIndicator",
    "MetricsConsumerError",
    "MetricsConsumerFailureCategory",
    "MetricsConsumerPolicy",
    "MetricFailureCategory",
    "MetricValidationError",
    "RealityGapClassification",
    "RealityGapConsumerContext",
    "RealityGapMetricSet",
    "RealityGapMetricValue",
    "classify_reality_gap",
    "measure_reality_gap",
]
