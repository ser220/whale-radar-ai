"""Immutable provenance association for attachment compatibility records."""

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


_CONTRACT_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")


class CompatibilityDecisionAssociationValidationError(ValueError):
    """Validation failure for immutable compatibility provenance association."""

    def __init__(self, field_name: str, reason: str) -> None:
        self.field_name = field_name
        self.reason = reason
        super().__init__("{0}: {1}".format(field_name, reason))


def _error(
    field_name: str, reason: str
) -> CompatibilityDecisionAssociationValidationError:
    return CompatibilityDecisionAssociationValidationError(field_name, reason)


def _contract_version(value: Any) -> str:
    normalized = required_text(
        value, "association_contract_version", _error
    )
    if _CONTRACT_VERSION.fullmatch(normalized) is None:
        raise CompatibilityDecisionAssociationValidationError(
            "association_contract_version",
            "must contain only letters, digits, dot, underscore, colon, or hyphen",
        )
    return normalized


@dataclass(frozen=True)
class RealityGapCompatibilityDecisionAssociation:
    """Historical link between a decision, its basis, and one attachment.

    Decision and basis references are opaque immutable identities. The contract
    does not resolve them, embed their payloads, or evaluate compatibility.
    """

    association_id: str
    attachment_reference: RealityGapArtifactReference
    compatibility_decision_reference: str
    decision_basis_reference: str
    associated_at: datetime
    association_contract_version: str

    def __post_init__(self) -> None:
        association_id = required_text(
            self.association_id, "association_id", _error
        )
        if not isinstance(self.attachment_reference, RealityGapArtifactReference):
            raise CompatibilityDecisionAssociationValidationError(
                "attachment_reference",
                "must be a RealityGapArtifactReference",
            )
        if (
            self.attachment_reference.artifact_type
            is not RealityGapArtifactType.ATTACHMENT
        ):
            raise CompatibilityDecisionAssociationValidationError(
                "attachment_reference",
                "artifact_type must be ATTACHMENT",
            )
        compatibility_decision_reference = required_text(
            self.compatibility_decision_reference,
            "compatibility_decision_reference",
            _error,
        )
        decision_basis_reference = required_text(
            self.decision_basis_reference,
            "decision_basis_reference",
            _error,
        )
        associated_at = utc_datetime(self.associated_at, "associated_at", _error)
        association_contract_version = _contract_version(
            self.association_contract_version
        )

        identities = (
            association_id,
            self.attachment_reference.artifact_id,
            compatibility_decision_reference,
            decision_basis_reference,
        )
        if len(set(identities)) != len(identities):
            raise CompatibilityDecisionAssociationValidationError(
                "identity",
                "association, attachment, decision, and basis identities "
                "must be distinct",
            )

        object.__setattr__(self, "association_id", association_id)
        object.__setattr__(
            self,
            "compatibility_decision_reference",
            compatibility_decision_reference,
        )
        object.__setattr__(
            self, "decision_basis_reference", decision_basis_reference
        )
        object.__setattr__(self, "associated_at", associated_at)
        object.__setattr__(
            self, "association_contract_version", association_contract_version
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "association_id": self.association_id,
            "attachment_reference": self.attachment_reference.to_dict(),
            "compatibility_decision_reference": (
                self.compatibility_decision_reference
            ),
            "decision_basis_reference": self.decision_basis_reference,
            "associated_at": self.associated_at.isoformat(),
            "association_contract_version": self.association_contract_version,
        }

    def canonical_json(self) -> str:
        """Return deterministic JSON without resolving or converting references."""

        return canonical_json_bytes(self.to_dict()).decode("utf-8")

    @classmethod
    def from_dict(
        cls, value: Mapping[str, Any]
    ) -> "RealityGapCompatibilityDecisionAssociation":
        payload = mapping_payload(
            value,
            tuple(item.name for item in fields(cls)),
            cls.__name__,
            _error,
        )
        try:
            payload["attachment_reference"] = RealityGapArtifactReference.from_dict(
                payload["attachment_reference"]
            )
        except ValueError as error:
            raise CompatibilityDecisionAssociationValidationError(
                "attachment_reference", str(error)
            )
        payload["associated_at"] = parse_datetime(
            payload["associated_at"], "associated_at", _error
        )
        return cls(**payload)


__all__ = [
    "CompatibilityDecisionAssociationValidationError",
    "RealityGapCompatibilityDecisionAssociation",
]
