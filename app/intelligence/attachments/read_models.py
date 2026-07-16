"""Immutable Reality Gap attachment read contracts."""

from collections.abc import Mapping
from dataclasses import dataclass, fields
from datetime import datetime
from typing import Any, Dict

from ._read_validation import (
    canonical_json,
    exact_mapping,
    parse_datetime,
    positive_version,
    required_text,
    utc_datetime,
)
from .read_enums import AttachmentAvailabilityStatus


class AttachmentReadValidationError(ValueError):
    """Validation failure at the attachment consumer boundary."""

    def __init__(self, field_name: str, reason: str) -> None:
        self.field_name = field_name
        self.reason = reason
        super().__init__("{0}: {1}".format(field_name, reason))


def _validated(function, value: Any, field_name: str):
    try:
        return function(value, field_name)
    except ValueError as error:
        message = str(error)
        prefix = "{0} ".format(field_name)
        reason = message[len(prefix) :] if message.startswith(prefix) else message
        raise AttachmentReadValidationError(field_name, reason)


@dataclass(frozen=True)
class AttachmentReadReference:
    """Identity and version of one referenced immutable artifact.

    The record deliberately carries no artifact payload or runtime locator.
    """

    reference_id: str
    reference_version: int

    def __post_init__(self) -> None:
        reference_id = _validated(required_text, self.reference_id, "reference_id")
        reference_version = _validated(
            positive_version, self.reference_version, "reference_version"
        )
        object.__setattr__(self, "reference_id", reference_id)
        object.__setattr__(self, "reference_version", reference_version)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reference_id": self.reference_id,
            "reference_version": self.reference_version,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "AttachmentReadReference":
        try:
            payload = exact_mapping(
                value,
                ("reference_id", "reference_version"),
                cls.__name__,
            )
        except ValueError as error:
            raise AttachmentReadValidationError("reference", str(error))
        return cls(**payload)


@dataclass(frozen=True)
class RealityGapAttachmentReadContract:
    """Minimal, read-only view of a Reality Gap analysis attachment."""

    attachment_id: str
    analysis_reference: AttachmentReadReference
    classification_reference: AttachmentReadReference
    metrics_reference: AttachmentReadReference
    attachment_version: int
    availability_status: AttachmentAvailabilityStatus
    created_at: datetime

    def __post_init__(self) -> None:
        attachment_id = _validated(required_text, self.attachment_id, "attachment_id")
        attachment_version = _validated(
            positive_version, self.attachment_version, "attachment_version"
        )
        references = {
            "analysis_reference": self.analysis_reference,
            "classification_reference": self.classification_reference,
            "metrics_reference": self.metrics_reference,
        }
        for field_name, reference in references.items():
            if not isinstance(reference, AttachmentReadReference):
                raise AttachmentReadValidationError(
                    field_name, "must be an AttachmentReadReference"
                )
        try:
            availability_status = (
                self.availability_status
                if isinstance(self.availability_status, AttachmentAvailabilityStatus)
                else AttachmentAvailabilityStatus(self.availability_status)
            )
        except (TypeError, ValueError):
            raise AttachmentReadValidationError(
                "availability_status", "is not a supported availability state"
            )
        created_at = _validated(utc_datetime, self.created_at, "created_at")

        identities = (attachment_id,) + tuple(
            reference.reference_id for reference in references.values()
        )
        if len(set(identities)) != len(identities):
            raise AttachmentReadValidationError(
                "references",
                "attachment, analysis, classification, and metrics identities "
                "must remain distinct",
            )

        object.__setattr__(self, "attachment_id", attachment_id)
        object.__setattr__(self, "attachment_version", attachment_version)
        object.__setattr__(self, "availability_status", availability_status)
        object.__setattr__(self, "created_at", created_at)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attachment_id": self.attachment_id,
            "analysis_reference": self.analysis_reference.to_dict(),
            "classification_reference": self.classification_reference.to_dict(),
            "metrics_reference": self.metrics_reference.to_dict(),
            "attachment_version": self.attachment_version,
            "availability_status": self.availability_status.value,
            "created_at": self.created_at.isoformat(),
        }

    def canonical_json(self) -> str:
        """Return the canonical JSON representation of this read contract."""

        return canonical_json(self.to_dict())

    @classmethod
    def from_dict(
        cls, value: Mapping[str, Any]
    ) -> "RealityGapAttachmentReadContract":
        try:
            payload = exact_mapping(
                value,
                tuple(item.name for item in fields(cls)),
                cls.__name__,
            )
        except ValueError as error:
            raise AttachmentReadValidationError("contract", str(error))

        for field_name in (
            "analysis_reference",
            "classification_reference",
            "metrics_reference",
        ):
            try:
                payload[field_name] = AttachmentReadReference.from_dict(
                    payload[field_name]
                )
            except AttachmentReadValidationError as error:
                raise AttachmentReadValidationError(field_name, error.reason)
        try:
            payload["created_at"] = parse_datetime(payload["created_at"], "created_at")
        except ValueError as error:
            message = str(error)
            prefix = "created_at "
            reason = message[len(prefix) :] if message.startswith(prefix) else message
            raise AttachmentReadValidationError("created_at", reason)
        return cls(**payload)
