"""Lossless canonical artifact references for Reality Gap attachments."""

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
from .artifact_enums import RealityGapArtifactType


_SNAPSHOT_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_REFERENCE_CONTRACT_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")


class ArtifactReferenceValidationError(ValueError):
    """Validation failure for a canonical artifact reference."""

    def __init__(self, field_name: str, reason: str) -> None:
        self.field_name = field_name
        self.reason = reason
        super().__init__("{0}: {1}".format(field_name, reason))


def _error(field_name: str, reason: str) -> ArtifactReferenceValidationError:
    return ArtifactReferenceValidationError(field_name, reason)


def _artifact_type(value: Any) -> RealityGapArtifactType:
    try:
        return (
            value
            if isinstance(value, RealityGapArtifactType)
            else RealityGapArtifactType(value)
        )
    except (TypeError, ValueError):
        raise ArtifactReferenceValidationError(
            "artifact_type", "is not a supported artifact type"
        )


def _optional_version(value: Any) -> Optional[int]:
    if value is None:
        return None
    return positive_version(value, "artifact_version", _error)


def _optional_snapshot_digest(value: Any) -> Optional[str]:
    if value is None:
        return None
    normalized = required_text(value, "snapshot_digest", _error)
    if _SNAPSHOT_DIGEST.fullmatch(normalized) is None:
        raise ArtifactReferenceValidationError(
            "snapshot_digest", "must match sha256:<64 lowercase hex>"
        )
    return normalized


def _reference_contract_version(value: Any) -> str:
    normalized = required_text(value, "reference_contract_version", _error)
    if _REFERENCE_CONTRACT_VERSION.fullmatch(normalized) is None:
        raise ArtifactReferenceValidationError(
            "reference_contract_version",
            "must contain only letters, digits, dot, underscore, colon, or hyphen",
        )
    return normalized


@dataclass(frozen=True)
class RealityGapArtifactReference:
    """Identity plus every available historical locator for one artifact.

    ``artifact_version`` and ``snapshot_digest`` are independent.  The contract
    never derives one from the other, and it allows both when a source owns both
    forms of historical addressing.
    """

    artifact_type: RealityGapArtifactType
    artifact_id: str
    artifact_version: Optional[int]
    snapshot_digest: Optional[str]
    reference_contract_version: str

    def __post_init__(self) -> None:
        artifact_type = _artifact_type(self.artifact_type)
        artifact_id = required_text(self.artifact_id, "artifact_id", _error)
        artifact_version = _optional_version(self.artifact_version)
        snapshot_digest = _optional_snapshot_digest(self.snapshot_digest)
        reference_contract_version = _reference_contract_version(
            self.reference_contract_version
        )

        if artifact_version is None and snapshot_digest is None:
            raise ArtifactReferenceValidationError(
                "historical_locator",
                "artifact_version or snapshot_digest is required",
            )

        object.__setattr__(self, "artifact_type", artifact_type)
        object.__setattr__(self, "artifact_id", artifact_id)
        object.__setattr__(self, "artifact_version", artifact_version)
        object.__setattr__(self, "snapshot_digest", snapshot_digest)
        object.__setattr__(
            self, "reference_contract_version", reference_contract_version
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_type": self.artifact_type.value,
            "artifact_id": self.artifact_id,
            "artifact_version": self.artifact_version,
            "snapshot_digest": self.snapshot_digest,
            "reference_contract_version": self.reference_contract_version,
        }

    def canonical_json(self) -> str:
        """Return deterministic canonical JSON without locator conversion."""

        return canonical_json_bytes(self.to_dict()).decode("utf-8")

    @classmethod
    def from_dict(
        cls, value: Mapping[str, Any]
    ) -> "RealityGapArtifactReference":
        payload = mapping_payload(
            value,
            tuple(item.name for item in fields(cls)),
            cls.__name__,
            _error,
        )
        return cls(**payload)


__all__ = [
    "ArtifactReferenceValidationError",
    "RealityGapArtifactReference",
]
