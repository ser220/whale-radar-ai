"""Enumerations for the immutable attachment compatibility boundary."""

from enum import Enum


class AttachmentCompatibilityStatus(str, Enum):
    """Outcome recorded by a compatibility decision."""

    COMPATIBLE = "COMPATIBLE"
    INCOMPATIBLE = "INCOMPATIBLE"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"


class AttachmentVersionCondition(str, Enum):
    """Version relationship described by one declarative policy rule."""

    SAME_CONTRACT_VERSION = "SAME_CONTRACT_VERSION"
    MAJOR_VERSION_MISMATCH = "MAJOR_VERSION_MISMATCH"
    MINOR_VERSION_EVOLUTION = "MINOR_VERSION_EVOLUTION"
    PATCH_VERSION_CHANGE = "PATCH_VERSION_CHANGE"
    UNKNOWN_VERSION = "UNKNOWN_VERSION"
