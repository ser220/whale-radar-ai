"""Immutable RealityGapAttachment governance contracts."""

from .enums import AttachmentFailureCategory
from .models import (
    AnalysisReference,
    AttachmentValidationError,
    ClassificationReference,
    MetricSetReference,
    RealityGapAnalysisAttachment,
)

from .read_enums import AttachmentAvailabilityStatus
from .read_models import RealityGapAttachmentReadContract

from .lifecycle_enums import AttachmentLifecycleState
from .lifecycle_models import RealityGapAttachmentLifecyclePolicy

from .compatibility_enums import AttachmentCompatibilityStatus
from .compatibility_models import (
    RealityGapAttachmentCompatibilityPolicy,
    RealityGapAttachmentCompatibilityDecision,
)


__all__ = [
    # Core attachment contract
    "AnalysisReference",
    "AttachmentFailureCategory",
    "AttachmentValidationError",
    "ClassificationReference",
    "MetricSetReference",
    "RealityGapAnalysisAttachment",

    # Read boundary
    "AttachmentAvailabilityStatus",
    "RealityGapAttachmentReadContract",

    # Lifecycle
    "AttachmentLifecycleState",
    "RealityGapAttachmentLifecyclePolicy",

    # Compatibility
    "AttachmentCompatibilityStatus",
    "RealityGapAttachmentCompatibilityPolicy",
    "RealityGapAttachmentCompatibilityDecision",
]
