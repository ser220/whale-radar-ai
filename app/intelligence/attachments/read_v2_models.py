"""Lossless canonical read boundary v2 for Reality Gap artifacts."""

from collections.abc import Mapping
from dataclasses import dataclass, fields
from typing import Any, Dict

from ._read_validation import canonical_json, exact_mapping
from .artifact_models import RealityGapArtifactReference
from .read_enums import AttachmentAvailabilityStatus


class AttachmentReadV2ValidationError(ValueError):
    """Validation failure at the canonical read v2 boundary."""

    def __init__(self, field_name: str, reason: str) -> None:
        self.field_name = field_name
        self.reason = reason
        super().__init__("{0}: {1}".format(field_name, reason))


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise AttachmentReadV2ValidationError(field_name, "must be a string")
    normalized = value.strip()
    if not normalized:
        raise AttachmentReadV2ValidationError(field_name, "must not be empty")
    return normalized


@dataclass(frozen=True)
class RealityGapAttachmentReadReferenceV2:
    """Consumer-safe reference preserving every canonical historical locator.

    This record wraps an existing canonical reference.  It does not derive,
    calculate, resolve, or replace an artifact version or snapshot digest.
    """

    artifact_reference: RealityGapArtifactReference
    availability_status: AttachmentAvailabilityStatus
    read_contract_version: str

    def __post_init__(self) -> None:
        if not isinstance(self.artifact_reference, RealityGapArtifactReference):
            raise AttachmentReadV2ValidationError(
                "artifact_reference", "must be a RealityGapArtifactReference"
            )
        try:
            availability_status = (
                self.availability_status
                if isinstance(self.availability_status, AttachmentAvailabilityStatus)
                else AttachmentAvailabilityStatus(self.availability_status)
            )
        except (TypeError, ValueError):
            raise AttachmentReadV2ValidationError(
                "availability_status", "is not a supported availability state"
            )
        read_contract_version = _required_text(
            self.read_contract_version, "read_contract_version"
        )

        object.__setattr__(self, "availability_status", availability_status)
        object.__setattr__(self, "read_contract_version", read_contract_version)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_reference": self.artifact_reference.to_dict(),
            "availability_status": self.availability_status.value,
            "read_contract_version": self.read_contract_version,
        }

    def canonical_json(self) -> str:
        """Return deterministic JSON with canonical locator values unchanged."""

        return canonical_json(self.to_dict())

    @classmethod
    def from_dict(
        cls, value: Mapping[str, Any]
    ) -> "RealityGapAttachmentReadReferenceV2":
        try:
            payload = exact_mapping(
                value,
                tuple(item.name for item in fields(cls)),
                cls.__name__,
            )
        except ValueError as error:
            raise AttachmentReadV2ValidationError("contract", str(error))
        try:
            payload["artifact_reference"] = RealityGapArtifactReference.from_dict(
                payload["artifact_reference"]
            )
        except ValueError as error:
            raise AttachmentReadV2ValidationError(
                "artifact_reference", str(error)
            )
        return cls(**payload)


__all__ = [
    "AttachmentReadV2ValidationError",
    "RealityGapAttachmentReadReferenceV2",
]
