"""Immutable record envelope for a historical compatibility decision."""

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
from .compatibility_decision_reference_models import (
    RealityGapCompatibilityDecisionReference,
)
from .compatibility_models import RealityGapAttachmentCompatibilityDecision


_ENVELOPE_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")


class CompatibilityDecisionRecordEnvelopeValidationError(ValueError):
    """Validation failure for a compatibility decision record envelope."""

    def __init__(self, field_name: str, reason: str) -> None:
        self.field_name = field_name
        self.reason = reason
        super().__init__("{0}: {1}".format(field_name, reason))


def _error(
    field_name: str, reason: str
) -> CompatibilityDecisionRecordEnvelopeValidationError:
    return CompatibilityDecisionRecordEnvelopeValidationError(field_name, reason)


def _envelope_version(value: Any) -> str:
    normalized = required_text(value, "envelope_version", _error)
    if _ENVELOPE_VERSION.fullmatch(normalized) is None:
        raise CompatibilityDecisionRecordEnvelopeValidationError(
            "envelope_version",
            "must contain only letters, digits, dot, underscore, colon, or hyphen",
        )
    return normalized


@dataclass(frozen=True)
class RealityGapCompatibilityDecisionRecordEnvelope:
    """Bind one immutable decision payload to its historical identity.

    This contract performs no compatibility evaluation, digest calculation,
    reference resolution, or current-version substitution.
    """

    decision_reference: RealityGapCompatibilityDecisionReference
    decision_payload: RealityGapAttachmentCompatibilityDecision
    envelope_version: str
    created_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(
            self.decision_reference, RealityGapCompatibilityDecisionReference
        ):
            raise CompatibilityDecisionRecordEnvelopeValidationError(
                "decision_reference",
                "must be a RealityGapCompatibilityDecisionReference",
            )
        if not isinstance(
            self.decision_payload, RealityGapAttachmentCompatibilityDecision
        ):
            raise CompatibilityDecisionRecordEnvelopeValidationError(
                "decision_payload",
                "must be a RealityGapAttachmentCompatibilityDecision",
            )
        envelope_version = _envelope_version(self.envelope_version)
        created_at = utc_datetime(self.created_at, "created_at", _error)

        object.__setattr__(self, "envelope_version", envelope_version)
        object.__setattr__(self, "created_at", created_at)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_reference": self.decision_reference.to_dict(),
            "decision_payload": self.decision_payload.to_dict(),
            "envelope_version": self.envelope_version,
            "created_at": self.created_at.isoformat(),
        }

    def canonical_json(self) -> str:
        """Return deterministic JSON without calculating a decision digest."""

        return canonical_json_bytes(self.to_dict()).decode("utf-8")

    @classmethod
    def from_dict(
        cls, value: Mapping[str, Any]
    ) -> "RealityGapCompatibilityDecisionRecordEnvelope":
        payload = mapping_payload(
            value,
            tuple(item.name for item in fields(cls)),
            cls.__name__,
            _error,
        )
        try:
            payload["decision_reference"] = (
                RealityGapCompatibilityDecisionReference.from_dict(
                    payload["decision_reference"]
                )
            )
        except ValueError as error:
            raise CompatibilityDecisionRecordEnvelopeValidationError(
                "decision_reference", str(error)
            )
        try:
            payload["decision_payload"] = (
                RealityGapAttachmentCompatibilityDecision.from_dict(
                    payload["decision_payload"]
                )
            )
        except ValueError as error:
            raise CompatibilityDecisionRecordEnvelopeValidationError(
                "decision_payload", str(error)
            )
        payload["created_at"] = parse_datetime(
            payload["created_at"], "created_at", _error
        )
        return cls(**payload)


__all__ = [
    "CompatibilityDecisionRecordEnvelopeValidationError",
    "RealityGapCompatibilityDecisionRecordEnvelope",
]
