"""Immutable aggregation snapshot for attachment governance provenance."""

from collections.abc import Mapping
from dataclasses import dataclass, fields
from datetime import datetime
import re
from typing import Any, Dict

from ._validation import (
    canonical_json_bytes,
    mapping_payload,
    parse_datetime,
    required_text,
    utc_datetime,
)
from .artifact_enums import RealityGapArtifactType
from .artifact_models import RealityGapArtifactReference
from .compatibility_association_v2_models import (
    RealityGapCompatibilityDecisionAssociationV2,
)
from .compatibility_basis_record_models import (
    RealityGapCompatibilityDecisionBasisRecordEnvelope,
)
from .compatibility_decision_record_models import (
    RealityGapCompatibilityDecisionRecordEnvelope,
)


_BUNDLE_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")


class GovernanceProvenanceBundleValidationError(ValueError):
    """Validation failure for an immutable governance provenance bundle."""

    def __init__(self, field_name: str, reason: str) -> None:
        self.field_name = field_name
        self.reason = reason
        super().__init__("{0}: {1}".format(field_name, reason))


def _error(
    field_name: str, reason: str
) -> GovernanceProvenanceBundleValidationError:
    return GovernanceProvenanceBundleValidationError(field_name, reason)


def _bundle_version(value: Any) -> str:
    normalized = required_text(value, "bundle_version", _error)
    if _BUNDLE_VERSION.fullmatch(normalized) is None:
        raise GovernanceProvenanceBundleValidationError(
            "bundle_version",
            "must contain only letters, digits, dot, underscore, colon, or hyphen",
        )
    return normalized


@dataclass(frozen=True)
class RealityGapGovernanceProvenanceBundle:
    """Aggregate one immutable historical attachment-governance snapshot.

    The bundle validates structure and typed immutable composition only. It
    deliberately does not compare nested identities or locators, verify or
    calculate digests, resolve references, or evaluate compatibility.
    """

    bundle_id: str
    attachment_reference: RealityGapArtifactReference
    decision_record: RealityGapCompatibilityDecisionRecordEnvelope
    basis_record: RealityGapCompatibilityDecisionBasisRecordEnvelope
    association: RealityGapCompatibilityDecisionAssociationV2
    bundle_version: str
    created_at: datetime

    def __post_init__(self) -> None:
        bundle_id = required_text(self.bundle_id, "bundle_id", _error)
        if not isinstance(self.attachment_reference, RealityGapArtifactReference):
            raise GovernanceProvenanceBundleValidationError(
                "attachment_reference",
                "must be a RealityGapArtifactReference",
            )
        if (
            self.attachment_reference.artifact_type
            is not RealityGapArtifactType.ATTACHMENT
        ):
            raise GovernanceProvenanceBundleValidationError(
                "attachment_reference", "artifact_type must be ATTACHMENT"
            )
        if not isinstance(
            self.decision_record,
            RealityGapCompatibilityDecisionRecordEnvelope,
        ):
            raise GovernanceProvenanceBundleValidationError(
                "decision_record",
                "must be a RealityGapCompatibilityDecisionRecordEnvelope",
            )
        if not isinstance(
            self.basis_record,
            RealityGapCompatibilityDecisionBasisRecordEnvelope,
        ):
            raise GovernanceProvenanceBundleValidationError(
                "basis_record",
                "must be a RealityGapCompatibilityDecisionBasisRecordEnvelope",
            )
        if not isinstance(
            self.association, RealityGapCompatibilityDecisionAssociationV2
        ):
            raise GovernanceProvenanceBundleValidationError(
                "association",
                "must be a RealityGapCompatibilityDecisionAssociationV2",
            )
        bundle_version = _bundle_version(self.bundle_version)
        created_at = utc_datetime(self.created_at, "created_at", _error)

        object.__setattr__(self, "bundle_id", bundle_id)
        object.__setattr__(self, "bundle_version", bundle_version)
        object.__setattr__(self, "created_at", created_at)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "attachment_reference": self.attachment_reference.to_dict(),
            "decision_record": self.decision_record.to_dict(),
            "basis_record": self.basis_record.to_dict(),
            "association": self.association.to_dict(),
            "bundle_version": self.bundle_version,
            "created_at": self.created_at.isoformat(),
        }

    def canonical_json(self) -> str:
        """Return deterministic JSON without resolving nested provenance."""

        return canonical_json_bytes(self.to_dict()).decode("utf-8")

    @classmethod
    def from_dict(
        cls, value: Mapping[str, Any]
    ) -> "RealityGapGovernanceProvenanceBundle":
        payload = mapping_payload(
            value,
            tuple(item.name for item in fields(cls)),
            cls.__name__,
            _error,
        )
        nested_contracts = (
            ("attachment_reference", RealityGapArtifactReference),
            (
                "decision_record",
                RealityGapCompatibilityDecisionRecordEnvelope,
            ),
            (
                "basis_record",
                RealityGapCompatibilityDecisionBasisRecordEnvelope,
            ),
            (
                "association",
                RealityGapCompatibilityDecisionAssociationV2,
            ),
        )
        for field_name, contract_type in nested_contracts:
            try:
                payload[field_name] = contract_type.from_dict(payload[field_name])
            except ValueError as error:
                raise GovernanceProvenanceBundleValidationError(
                    field_name, str(error)
                )
        payload["created_at"] = parse_datetime(
            payload["created_at"], "created_at", _error
        )
        return cls(**payload)


__all__ = [
    "GovernanceProvenanceBundleValidationError",
    "RealityGapGovernanceProvenanceBundle",
]
