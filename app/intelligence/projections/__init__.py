"""Immutable contracts for candidate representations in explanation contexts."""

from .enums import ProjectionFailureCategory
from .models import (
    CandidateProjection,
    EvidenceReferenceSnapshot,
    ProjectionValidationError,
)
from .mapping_models import (
    EvidenceCatalogEntry,
    EvidenceCatalogView,
    ExplanationDecisionSnapshot,
    ExplanationDescriptorSnapshot,
    MappingFailureCategory,
    RootCauseCandidateMappingFailure,
    RootCauseCandidateMappingRequest,
    RootCauseCandidateMappingResult,
    TreePlacementSnapshot,
)
from .mapper import map_projection_to_root_cause_candidate

__all__ = [
    "CandidateProjection",
    "EvidenceCatalogEntry",
    "EvidenceCatalogView",
    "EvidenceReferenceSnapshot",
    "ExplanationDecisionSnapshot",
    "ExplanationDescriptorSnapshot",
    "MappingFailureCategory",
    "ProjectionFailureCategory",
    "ProjectionValidationError",
    "RootCauseCandidateMappingFailure",
    "RootCauseCandidateMappingRequest",
    "RootCauseCandidateMappingResult",
    "TreePlacementSnapshot",
    "map_projection_to_root_cause_candidate",
]
