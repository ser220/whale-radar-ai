"""Artifact vocabulary for canonical Reality Gap references."""

from enum import Enum


class RealityGapArtifactType(str, Enum):
    """Supported immutable artifact kinds at the attachment boundary."""

    ANALYSIS = "ANALYSIS"
    CLASSIFICATION = "CLASSIFICATION"
    METRIC_SET = "METRIC_SET"


__all__ = ["RealityGapArtifactType"]
