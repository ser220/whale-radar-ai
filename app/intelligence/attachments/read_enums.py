"""Enumerations for the Reality Gap attachment read boundary."""

from enum import Enum


class AttachmentAvailabilityStatus(str, Enum):
    """Availability of an attachment to a read-only consumer."""

    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    SUPERSEDED = "SUPERSEDED"
