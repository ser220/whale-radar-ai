"""Read-only attachment contracts for Reality Gap consumers.

The package exposes immutable records only.  It does not resolve references,
load payloads, persist data, or integrate with production services.
"""

from .read_enums import AttachmentAvailabilityStatus
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
    "AttachmentLifecycleState",
    "AttachmentLifecycleTransition",
    "AttachmentLifecycleValidationError",
    "AttachmentReadReference",
    "AttachmentReadValidationError",
    "AttachmentRevisionAxis",
    "RealityGapAttachmentLifecyclePolicy",
    "RealityGapAttachmentReadContract",
    "canonical_lifecycle_transitions",
    "canonical_revision_axes",
]
