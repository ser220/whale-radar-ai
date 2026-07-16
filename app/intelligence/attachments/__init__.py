"""Read-only attachment contracts for Reality Gap consumers.

The package exposes immutable records only.  It does not resolve references,
load payloads, persist data, or integrate with production services.
"""

from .read_enums import AttachmentAvailabilityStatus
from .read_models import (
    AttachmentReadReference,
    AttachmentReadValidationError,
    RealityGapAttachmentReadContract,
)

__all__ = [
    "AttachmentAvailabilityStatus",
    "AttachmentReadReference",
    "AttachmentReadValidationError",
    "RealityGapAttachmentReadContract",
]
