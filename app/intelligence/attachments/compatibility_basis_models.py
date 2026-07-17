"""Immutable historical basis for an attachment compatibility decision."""

from collections.abc import Mapping
from dataclasses import dataclass, fields
from types import MappingProxyType
from typing import Any, Dict, Mapping as TypingMapping

from ._validation import canonical_json_bytes, mapping_payload, required_text
from .artifact_models import RealityGapArtifactReference
from .compatibility_basis_enums import CompatibilityDecisionBasisType


class CompatibilityDecisionBasisValidationError(ValueError):
    """Validation failure for compatibility decision basis provenance."""

    def __init__(self, field_name: str, reason: str) -> None:
        self.field_name = field_name
        self.reason = reason
        super().__init__("{0}: {1}".format(field_name, reason))


def _error(
    field_name: str, reason: str
) -> CompatibilityDecisionBasisValidationError:
    return CompatibilityDecisionBasisValidationError(field_name, reason)


def _basis_type(value: Any) -> CompatibilityDecisionBasisType:
    try:
        return (
            value
            if isinstance(value, CompatibilityDecisionBasisType)
            else CompatibilityDecisionBasisType(value)
        )
    except (TypeError, ValueError):
        raise CompatibilityDecisionBasisValidationError(
            "basis_type", "is not a supported basis type"
        )


def _reference_snapshot(
    value: Any,
) -> TypingMapping[str, RealityGapArtifactReference]:
    if not isinstance(value, Mapping):
        raise CompatibilityDecisionBasisValidationError(
            "reference_snapshot", "must be a mapping"
        )
    if not value:
        raise CompatibilityDecisionBasisValidationError(
            "reference_snapshot", "must contain at least one historical reference"
        )

    references = {}
    for raw_name in value:
        name = required_text(raw_name, "reference_snapshot key", _error)
        if name != raw_name:
            raise CompatibilityDecisionBasisValidationError(
                "reference_snapshot", "reference names must not contain outer whitespace"
            )
        reference = value[raw_name]
        if not isinstance(reference, RealityGapArtifactReference):
            raise CompatibilityDecisionBasisValidationError(
                "reference_snapshot.{0}".format(name),
                "must be a RealityGapArtifactReference",
            )
        references[name] = reference

    return MappingProxyType(
        {name: references[name] for name in sorted(references)}
    )


@dataclass(frozen=True)
class RealityGapCompatibilityDecisionBasis:
    """Immutable explanation basis supplied with a compatibility decision.

    The record preserves which canonical references and declared rule supported
    a decision. It does not calculate, validate, or change compatibility status.
    """

    basis_type: CompatibilityDecisionBasisType
    policy_version: str
    rule_code: str
    reference_snapshot: TypingMapping[str, RealityGapArtifactReference]

    def __post_init__(self) -> None:
        basis_type = _basis_type(self.basis_type)
        policy_version = required_text(
            self.policy_version, "policy_version", _error
        )
        rule_code = required_text(self.rule_code, "rule_code", _error)
        reference_snapshot = _reference_snapshot(self.reference_snapshot)

        object.__setattr__(self, "basis_type", basis_type)
        object.__setattr__(self, "policy_version", policy_version)
        object.__setattr__(self, "rule_code", rule_code)
        object.__setattr__(self, "reference_snapshot", reference_snapshot)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "basis_type": self.basis_type.value,
            "policy_version": self.policy_version,
            "rule_code": self.rule_code,
            "reference_snapshot": {
                name: self.reference_snapshot[name].to_dict()
                for name in sorted(self.reference_snapshot)
            },
        }

    def canonical_json(self) -> str:
        """Return deterministic JSON without converting historical locators."""

        return canonical_json_bytes(self.to_dict()).decode("utf-8")

    @classmethod
    def from_dict(
        cls, value: Mapping[str, Any]
    ) -> "RealityGapCompatibilityDecisionBasis":
        payload = mapping_payload(
            value,
            tuple(item.name for item in fields(cls)),
            cls.__name__,
            _error,
        )
        raw_snapshot = payload["reference_snapshot"]
        if not isinstance(raw_snapshot, Mapping):
            raise CompatibilityDecisionBasisValidationError(
                "reference_snapshot", "must be a mapping"
            )

        references = {}
        for name in raw_snapshot:
            if not isinstance(name, str):
                raise CompatibilityDecisionBasisValidationError(
                    "reference_snapshot", "reference names must be strings"
                )
            try:
                references[name] = RealityGapArtifactReference.from_dict(
                    raw_snapshot[name]
                )
            except ValueError as error:
                raise CompatibilityDecisionBasisValidationError(
                    "reference_snapshot.{0}".format(name), str(error)
                )
        payload["reference_snapshot"] = references
        return cls(**payload)


__all__ = [
    "CompatibilityDecisionBasisValidationError",
    "RealityGapCompatibilityDecisionBasis",
]
