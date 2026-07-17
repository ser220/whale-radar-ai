"""Enumerations for immutable compatibility decision explanations."""

from enum import Enum


class CompatibilityDecisionBasisType(str, Enum):
    """Provenance category of an externally supplied compatibility decision."""

    VERSION_RULE = "VERSION_RULE"
    DIGEST_RULE = "DIGEST_RULE"
    MANUAL_REVIEW = "MANUAL_REVIEW"


__all__ = ["CompatibilityDecisionBasisType"]
