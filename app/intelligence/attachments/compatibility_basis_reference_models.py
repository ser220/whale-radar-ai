"""Immutable identity envelope for a historical compatibility basis."""

from collections.abc import Mapping
from dataclasses import dataclass, fields
import re
from typing import Any, Dict, Optional

from ._validation import (
    canonical_json_bytes,
    mapping_payload,
    positive_version,
    required_text,
)


_BASIS_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_REFERENCE_CONTRACT_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")


class CompatibilityDecisionBasisReferenceValidationError(ValueError):
    """Validation failure for a compatibility basis identity envelope."""

    def __init__(self, field_name: str, reason: str) -> None:
        self.field_name = field_name
        self.reason = reason
        super().__init__("{0}: {1}".format(field_name, reason))


def _error(
    field_name: str, reason: str
) -> CompatibilityDecisionBasisReferenceValidationError:
    return CompatibilityDecisionBasisReferenceValidationError(field_name, reason)


def _optional_digest(value: Any) -> Optional[str]:
    if value is None:
        return None
    normalized = required_text(value, "basis_digest", _error)
    if _BASIS_DIGEST.fullmatch(normalized) is None:
        raise CompatibilityDecisionBasisReferenceValidationError(
            "basis_digest", "must match sha256:<64 lowercase hex>"
        )
    return normalized


def _reference_contract_version(value: Any) -> str:
    normalized = required_text(
        value, "reference_contract_version", _error
    )
    if _REFERENCE_CONTRACT_VERSION.fullmatch(normalized) is None:
        raise CompatibilityDecisionBasisReferenceValidationError(
            "reference_contract_version",
            "must contain only letters, digits, dot, underscore, colon, or hyphen",
        )
    return normalized


@dataclass(frozen=True)
class RealityGapCompatibilityDecisionBasisReference:
    """Identity-only reference to one immutable historical basis revision.

    The envelope contains no basis payload and performs no compatibility
    evaluation, reconstruction, resolution, or current-version lookup.
    """

    basis_id: str
    basis_version: int
    basis_digest: Optional[str]
    reference_contract_version: str

    def __post_init__(self) -> None:
        basis_id = required_text(self.basis_id, "basis_id", _error)
        basis_version = positive_version(
            self.basis_version, "basis_version", _error
        )
        basis_digest = _optional_digest(self.basis_digest)
        reference_contract_version = _reference_contract_version(
            self.reference_contract_version
        )

        object.__setattr__(self, "basis_id", basis_id)
        object.__setattr__(self, "basis_version", basis_version)
        object.__setattr__(self, "basis_digest", basis_digest)
        object.__setattr__(
            self, "reference_contract_version", reference_contract_version
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "basis_id": self.basis_id,
            "basis_version": self.basis_version,
            "basis_digest": self.basis_digest,
            "reference_contract_version": self.reference_contract_version,
        }

    def canonical_json(self) -> str:
        """Return deterministic JSON without recreating a basis payload."""

        return canonical_json_bytes(self.to_dict()).decode("utf-8")

    @classmethod
    def from_dict(
        cls, value: Mapping[str, Any]
    ) -> "RealityGapCompatibilityDecisionBasisReference":
        payload = mapping_payload(
            value,
            tuple(item.name for item in fields(cls)),
            cls.__name__,
            _error,
        )
        return cls(**payload)


__all__ = [
    "CompatibilityDecisionBasisReferenceValidationError",
    "RealityGapCompatibilityDecisionBasisReference",
]
