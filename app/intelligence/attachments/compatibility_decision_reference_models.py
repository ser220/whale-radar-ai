"""Immutable identity envelope for a historical compatibility decision."""

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


_DECISION_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_REFERENCE_CONTRACT_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")


class CompatibilityDecisionReferenceValidationError(ValueError):
    """Validation failure for a compatibility decision identity envelope."""

    def __init__(self, field_name: str, reason: str) -> None:
        self.field_name = field_name
        self.reason = reason
        super().__init__("{0}: {1}".format(field_name, reason))


def _error(
    field_name: str, reason: str
) -> CompatibilityDecisionReferenceValidationError:
    return CompatibilityDecisionReferenceValidationError(field_name, reason)


def _optional_digest(value: Any) -> Optional[str]:
    if value is None:
        return None
    normalized = required_text(value, "decision_digest", _error)
    if _DECISION_DIGEST.fullmatch(normalized) is None:
        raise CompatibilityDecisionReferenceValidationError(
            "decision_digest", "must match sha256:<64 lowercase hex>"
        )
    return normalized


def _reference_contract_version(value: Any) -> str:
    normalized = required_text(
        value, "reference_contract_version", _error
    )
    if _REFERENCE_CONTRACT_VERSION.fullmatch(normalized) is None:
        raise CompatibilityDecisionReferenceValidationError(
            "reference_contract_version",
            "must contain only letters, digits, dot, underscore, colon, or hyphen",
        )
    return normalized


@dataclass(frozen=True)
class RealityGapCompatibilityDecisionReference:
    """Identity-only reference to one immutable historical decision revision.

    The envelope contains no decision payload and performs no compatibility
    evaluation, reconstruction, resolution, or current-version lookup.
    """

    decision_id: str
    decision_version: int
    decision_digest: Optional[str]
    reference_contract_version: str

    def __post_init__(self) -> None:
        decision_id = required_text(self.decision_id, "decision_id", _error)
        decision_version = positive_version(
            self.decision_version, "decision_version", _error
        )
        decision_digest = _optional_digest(self.decision_digest)
        reference_contract_version = _reference_contract_version(
            self.reference_contract_version
        )

        object.__setattr__(self, "decision_id", decision_id)
        object.__setattr__(self, "decision_version", decision_version)
        object.__setattr__(self, "decision_digest", decision_digest)
        object.__setattr__(
            self, "reference_contract_version", reference_contract_version
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "decision_version": self.decision_version,
            "decision_digest": self.decision_digest,
            "reference_contract_version": self.reference_contract_version,
        }

    def canonical_json(self) -> str:
        """Return deterministic JSON without recreating a decision payload."""

        return canonical_json_bytes(self.to_dict()).decode("utf-8")

    @classmethod
    def from_dict(
        cls, value: Mapping[str, Any]
    ) -> "RealityGapCompatibilityDecisionReference":
        payload = mapping_payload(
            value,
            tuple(item.name for item in fields(cls)),
            cls.__name__,
            _error,
        )
        return cls(**payload)


__all__ = [
    "CompatibilityDecisionReferenceValidationError",
    "RealityGapCompatibilityDecisionReference",
]
