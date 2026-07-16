"""Immutable contracts for candidate representations in explanation contexts."""

from .enums import ProjectionFailureCategory
from .models import (
    CandidateProjection,
    EvidenceReferenceSnapshot,
    ProjectionValidationError,
)

__all__ = [
    "CandidateProjection",
    "EvidenceReferenceSnapshot",
    "ProjectionFailureCategory",
    "ProjectionValidationError",
]
