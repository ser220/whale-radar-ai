"""Immutable attachment relationship contracts."""

from .enums import AttachmentFailureCategory
from .models import (
    AnalysisReference,
    AttachmentValidationError,
    ClassificationReference,
    MetricSetReference,
    RealityGapAnalysisAttachment,
)

__all__ = [
    "AnalysisReference",
    "AttachmentFailureCategory",
    "AttachmentValidationError",
    "ClassificationReference",
    "MetricSetReference",
    "RealityGapAnalysisAttachment",
]
