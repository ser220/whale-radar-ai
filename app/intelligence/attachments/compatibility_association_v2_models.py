"""Typed immutable provenance association for compatibility records."""

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
from .compatibility_basis_reference_models import (
    RealityGapCompatibilityDecisionBasisReference,
)
from .compatibility_decision_reference_models import (
    RealityGapCompatibilityDecisionReference,
)


_CONTRACT_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")


class CompatibilityDecisionAssociationV2ValidationError(ValueError):
    """Validation failure for the typed compatibility association boundary."""

    def __init__(self, field_name: str, reason: str) -> None:
        self.field_name = field_name
        self.reason = reason
        super().__init__("{0}: {1}".format(field_name, reason))


def _error(
    field_name: str, reason: str
) -> CompatibilityDecisionAssociationV2ValidationError:
    return CompatibilityDecisionAssociationV2ValidationError(field_name, reason)


def _contract_version(value: Any) -> str:
    normalized = required_text(
        value, "association_contract_version", _error
    )
    if _CONTRACT_VERSION.fullmatch(normalized) is None:
        raise CompatibilityDecisionAssociationV2ValidationError(
            "association_contract_version",
            "must contain only letters, digits, dot, underscore, colon, or hyphen",
        )
    return normalized


@dataclass(frozen=True)
class RealityGapCompatibilityDecisionAssociationV2:
    """Typed historical link among attachment, decision, and basis identities.

    The association contains reference envelopes only. It does not embed their
    payloads, resolve their identities, or evaluate compatibility.
    """

    association_id: str
    attachment_reference: RealityGapArtifactReference
    decision_reference: RealityGapCompatibilityDecisionReference
    basis_reference: RealityGapCompatibilityDecisionBasisReference
    associated_at: datetime
    association_contract_version: str

    def __post_init__(self) -> None:
        association_id = required_text(
            self.association_id, "association_id", _error
        )
        if not isinstance(self.attachment_reference, RealityGapArtifactReference):
            raise CompatibilityDecisionAssociationV2ValidationError(
                "attachment_reference",
                "must be a RealityGapArtifactReference",
            )
        if (
            self.attachment_reference.artifact_type
            is not RealityGapArtifactType.ATTACHMENT
        ):
            raise CompatibilityDecisionAssociationV2ValidationError(
                "attachment_reference", "artifact_type must be ATTACHMENT"
            )
        if not isinstance(
            self.decision_reference, RealityGapCompatibilityDecisionReference
        ):
            raise CompatibilityDecisionAssociationV2ValidationError(
                "decision_reference",
                "must be a RealityGapCompatibilityDecisionReference",
            )
        if not isinstance(
            self.basis_reference,
            RealityGapCompatibilityDecisionBasisReference,
        ):
            raise CompatibilityDecisionAssociationV2ValidationError(
                "basis_reference",
                "must be a RealityGapCompatibilityDecisionBasisReference",
            )
        associated_at = utc_datetime(self.associated_at, "associated_at", _error)
        association_contract_version = _contract_version(
            self.association_contract_version
        )

        identities = (
            association_id,
            self.attachment_reference.artifact_id,
            self.decision_reference.decision_id,
            self.basis_reference.basis_id,
        )
        if len(set(identities)) != len(identities):
            raise CompatibilityDecisionAssociationV2ValidationError(
                "identity",
                "association, attachment, decision, and basis identities "
                "must be distinct",
            )

        object.__setattr__(self, "association_id", association_id)
        object.__setattr__(self, "associated_at", associated_at)
        object.__setattr__(
            self, "association_contract_version", association_contract_version
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "association_id": self.association_id,
            "attachment_reference": self.attachment_reference.to_dict(),
            "decision_reference": self.decision_reference.to_dict(),
            "basis_reference": self.basis_reference.to_dict(),
            "associated_at": self.associated_at.isoformat(),
            "association_contract_version": self.association_contract_version,
        }

    def canonical_json(self) -> str:
        """Return deterministic JSON without resolving reference envelopes."""

        return canonical_json_bytes(self.to_dict()).decode("utf-8")

    @classmethod
    def from_dict(
        cls, value: Mapping[str, Any]
    ) -> "RealityGapCompatibilityDecisionAssociationV2":
        payload = mapping_payload(
            value,
            tuple(item.name for item in fields(cls)),
            cls.__name__,
            _error,
        )
        nested_contracts = (
            (
                "attachment_reference",
                RealityGapArtifactReference,
            ),
            (
                "decision_reference",
                RealityGapCompatibilityDecisionReference,
            ),
            (
                "basis_reference",
                RealityGapCompatibilityDecisionBasisReference,
            ),
        )
        for field_name, contract_type in nested_contracts:
            try:
                payload[field_name] = contract_type.from_dict(payload[field_name])
            except ValueError as error:
                raise CompatibilityDecisionAssociationV2ValidationError(
                    field_name, str(error)
                )
        payload["associated_at"] = parse_datetime(
            payload["associated_at"], "associated_at", _error
        )
        return cls(**payload)


__all__ = [
    "CompatibilityDecisionAssociationV2ValidationError",
    "RealityGapCompatibilityDecisionAssociationV2",
]
