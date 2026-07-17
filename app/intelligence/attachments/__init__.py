"""Immutable RealityGapAttachment governance contracts."""

from .enums import AttachmentFailureCategory
from .artifact_enums import RealityGapArtifactType
from .artifact_models import (
    ArtifactReferenceValidationError,
    RealityGapArtifactReference,
)
from .models import (
    AnalysisReference,
    AttachmentValidationError,
    ClassificationReference,
    MetricSetReference,
    RealityGapAnalysisAttachment,
)

from .read_enums import AttachmentAvailabilityStatus
from .read_models import (
    AttachmentReadReference,
    AttachmentReadValidationError,
    RealityGapAttachmentReadContract,
)
from .read_v2_models import (
    AttachmentReadV2ValidationError,
    RealityGapAttachmentReadReferenceV2,
)

from .lifecycle_enums import AttachmentLifecycleState, AttachmentRevisionAxis
from .lifecycle_models import (
    AttachmentLifecycleTransition,
    AttachmentLifecycleValidationError,
    RealityGapAttachmentLifecyclePolicy,
    canonical_lifecycle_transitions,
    canonical_revision_axes,
)

from .compatibility_enums import (
    AttachmentCompatibilityStatus,
    AttachmentVersionCondition,
)
from .compatibility_models import (
    AttachmentCompatibilityValidationError,
    AttachmentVersionCompatibilityRule,
    RealityGapAttachmentCompatibilityDecision,
    RealityGapAttachmentCompatibilityPolicy,
    canonical_compatibility_categories,
    canonical_version_rules,
)
from .compatibility_basis_enums import CompatibilityDecisionBasisType
from .compatibility_basis_models import (
    CompatibilityDecisionBasisValidationError,
    RealityGapCompatibilityDecisionBasis,
)
from .compatibility_association_models import (
    CompatibilityDecisionAssociationValidationError,
    RealityGapCompatibilityDecisionAssociation,
)
from .compatibility_decision_reference_models import (
    CompatibilityDecisionReferenceValidationError,
    RealityGapCompatibilityDecisionReference,
)
from .compatibility_basis_reference_models import (
    CompatibilityDecisionBasisReferenceValidationError,
    RealityGapCompatibilityDecisionBasisReference,
)
from .compatibility_association_v2_models import (
    CompatibilityDecisionAssociationV2ValidationError,
    RealityGapCompatibilityDecisionAssociationV2,
)
from .compatibility_decision_record_models import (
    CompatibilityDecisionRecordEnvelopeValidationError,
    RealityGapCompatibilityDecisionRecordEnvelope,
)
from .compatibility_basis_record_models import (
    CompatibilityDecisionBasisRecordEnvelopeValidationError,
    RealityGapCompatibilityDecisionBasisRecordEnvelope,
)
from .governance_provenance_bundle_models import (
    GovernanceProvenanceBundleValidationError,
    RealityGapGovernanceProvenanceBundle,
)


__all__ = [
    # Canonical artifact reference
    "ArtifactReferenceValidationError",
    "RealityGapArtifactReference",
    "RealityGapArtifactType",

    # Core attachment contract
    "AnalysisReference",
    "AttachmentFailureCategory",
    "AttachmentValidationError",
    "ClassificationReference",
    "MetricSetReference",
    "RealityGapAnalysisAttachment",

    # Read boundary
    "AttachmentAvailabilityStatus",
    "AttachmentReadReference",
    "AttachmentReadValidationError",
    "AttachmentReadV2ValidationError",
    "RealityGapAttachmentReadContract",
    "RealityGapAttachmentReadReferenceV2",

    # Lifecycle
    "AttachmentLifecycleState",
    "AttachmentLifecycleTransition",
    "AttachmentLifecycleValidationError",
    "AttachmentRevisionAxis",
    "RealityGapAttachmentLifecyclePolicy",
    "canonical_lifecycle_transitions",
    "canonical_revision_axes",

    # Compatibility
    "AttachmentCompatibilityStatus",
    "AttachmentCompatibilityValidationError",
    "CompatibilityDecisionAssociationValidationError",
    "CompatibilityDecisionAssociationV2ValidationError",
    "CompatibilityDecisionBasisType",
    "CompatibilityDecisionBasisReferenceValidationError",
    "CompatibilityDecisionBasisRecordEnvelopeValidationError",
    "CompatibilityDecisionBasisValidationError",
    "CompatibilityDecisionReferenceValidationError",
    "CompatibilityDecisionRecordEnvelopeValidationError",
    "GovernanceProvenanceBundleValidationError",
    "AttachmentVersionCompatibilityRule",
    "AttachmentVersionCondition",
    "RealityGapAttachmentCompatibilityDecision",
    "RealityGapAttachmentCompatibilityPolicy",
    "RealityGapCompatibilityDecisionAssociation",
    "RealityGapCompatibilityDecisionAssociationV2",
    "RealityGapCompatibilityDecisionBasis",
    "RealityGapCompatibilityDecisionBasisReference",
    "RealityGapCompatibilityDecisionBasisRecordEnvelope",
    "RealityGapCompatibilityDecisionReference",
    "RealityGapCompatibilityDecisionRecordEnvelope",
    "RealityGapGovernanceProvenanceBundle",
    "canonical_compatibility_categories",
    "canonical_version_rules",
]
