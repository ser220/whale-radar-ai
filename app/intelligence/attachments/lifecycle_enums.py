"""Enumerations for the immutable attachment lifecycle policy boundary."""

from enum import Enum


class AttachmentLifecycleState(str, Enum):
    """Descriptive lifecycle state of an attachment revision."""

    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    ARCHIVED = "ARCHIVED"


class AttachmentRevisionAxis(str, Enum):
    """Independently versioned artifacts participating in an attachment."""

    ATTACHMENT = "ATTACHMENT"
    ANALYSIS = "ANALYSIS"
    CLASSIFICATION = "CLASSIFICATION"
    METRICS = "METRICS"
