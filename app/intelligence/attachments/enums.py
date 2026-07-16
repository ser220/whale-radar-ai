"""Stable validation failure categories for attachment contracts."""

from enum import Enum


class AttachmentFailureCategory(str, Enum):
    MISSING_CLASSIFICATION = "MISSING_CLASSIFICATION"
    MISSING_METRICS = "MISSING_METRICS"
    VERSION_CONFLICT = "VERSION_CONFLICT"
    ANALYSIS_MISMATCH = "ANALYSIS_MISMATCH"
    POLICY_CONFLICT = "POLICY_CONFLICT"
    INVALID_REFERENCE = "INVALID_REFERENCE"


__all__ = ["AttachmentFailureCategory"]
