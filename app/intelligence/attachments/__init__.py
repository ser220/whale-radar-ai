"""Read-only attachment contracts for Reality Gap consumers.

The package exposes immutable records only.  It does not resolve references,
load payloads, persist data, or integrate with production services.
"""

from .read_enums import AttachmentAvailabilityStatus
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
from .lifecycle_enums import AttachmentLifecycleState, AttachmentRevisionAxis
from .lifecycle_models import (
    AttachmentLifecycleTransition,
    AttachmentLifecycleValidationError,
    RealityGapAttachmentLifecyclePolicy,
    canonical_lifecycle_transitions,
    canonical_revision_axes,
)
from .read_models import (
    AttachmentReadReference,
    AttachmentReadValidationError,
    RealityGapAttachmentReadContract,
)

__all__ = [
    "AttachmentAvailabilityStatus",
    "AttachmentCompatibilityStatus",
    "AttachmentCompatibilityValidationError",
    "AttachmentLifecycleState",
    "AttachmentLifecycleTransition",
    "AttachmentLifecycleValidationError",
    "AttachmentReadReference",
    "AttachmentReadValidationError",
    "AttachmentRevisionAxis",
    "AttachmentVersionCompatibilityRule",
    "AttachmentVersionCondition",
    "RealityGapAttachmentCompatibilityDecision",
    "RealityGapAttachmentCompatibilityPolicy",
    "RealityGapAttachmentLifecyclePolicy",
    "RealityGapAttachmentReadContract",
    "canonical_lifecycle_transitions",
    "canonical_compatibility_categories",
    "canonical_revision_axes",
    "canonical_version_rules",
]
