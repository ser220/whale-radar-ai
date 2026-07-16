"""Immutable RealityGapAttachment governance contracts."""

from .enums import AttachmentFailureCategory
from .artifact_enums import RealityGapArtifactType
from .artifact_models import (
    ArtifactReferenceValidationError,
    RealityGapArtifactReference,
)
from .models import (
    AnalysisReference,
    AttachmentValidationError,
    ClassificationReference,
    MetricSetReference,
    RealityGapAnalysisAttachment,
)

from .read_enums import AttachmentAvailabilityStatus
from .read_models import (
    AttachmentReadReference,
    AttachmentReadValidationError,
    RealityGapAttachmentReadContract,
)

from .lifecycle_enums import AttachmentLifecycleState, AttachmentRevisionAxis
from .lifecycle_models import (
    AttachmentLifecycleTransition,
    AttachmentLifecycleValidationError,
    RealityGapAttachmentLifecyclePolicy,
    canonical_lifecycle_transitions,
    canonical_revision_axes,
)

from .compatibility_enums import (
    AttachmentCompatibilityStatus,
    AttachmentVersionCondition,
)
from .compatibility_models import (
    AttachmentCompatibilityValidationError,
    AttachmentVersionCompatibilityRule,
    RealityGapAttachmentCompatibilityDecision,
    RealityGapAttachmentCompatibilityPolicy,
    canonical_compatibility_categories,
    canonical_version_rules,
)


__all__ = [
    # Canonical artifact reference
    "ArtifactReferenceValidationError",
    "RealityGapArtifactReference",
    "RealityGapArtifactType",

    # Core attachment contract
    "AnalysisReference",
    "AttachmentFailureCategory",
    "AttachmentValidationError",
    "ClassificationReference",
    "MetricSetReference",
    "RealityGapAnalysisAttachment",

    # Read boundary
    "AttachmentAvailabilityStatus",
    "AttachmentReadReference",
    "AttachmentReadValidationError",
    "RealityGapAttachmentReadContract",

    # Lifecycle
    "AttachmentLifecycleState",
    "AttachmentLifecycleTransition",
    "AttachmentLifecycleValidationError",
    "AttachmentRevisionAxis",
    "RealityGapAttachmentLifecyclePolicy",
    "canonical_lifecycle_transitions",
    "canonical_revision_axes",

    # Compatibility
    "AttachmentCompatibilityStatus",
    "AttachmentCompatibilityValidationError",
    "AttachmentVersionCompatibilityRule",
    "AttachmentVersionCondition",
    "RealityGapAttachmentCompatibilityDecision",
    "RealityGapAttachmentCompatibilityPolicy",
    "canonical_compatibility_categories",
    "canonical_version_rules",
]
