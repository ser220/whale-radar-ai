"""Immutable Reality Gap attachment compatibility policy contracts."""

from collections.abc import Mapping
from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
import json
from typing import Any, Dict, Tuple

from .compatibility_enums import (
    AttachmentCompatibilityStatus,
    AttachmentVersionCondition,
)
from .lifecycle_enums import AttachmentRevisionAxis
from .lifecycle_models import canonical_revision_axes
from .read_models import AttachmentReadReference


class AttachmentCompatibilityValidationError(ValueError):
    """Validation failure within the compatibility contract boundary."""

    def __init__(self, field_name: str, reason: str) -> None:
        self.field_name = field_name
        self.reason = reason
        super().__init__("{0}: {1}".format(field_name, reason))


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise AttachmentCompatibilityValidationError(
            field_name, "must be a string"
        )
    normalized = value.strip()
    if not normalized:
        raise AttachmentCompatibilityValidationError(
            field_name, "must not be empty"
        )
    return normalized


def _enum(value: Any, enum_type, field_name: str):
    try:
        return value if isinstance(value, enum_type) else enum_type(value)
    except (TypeError, ValueError):
        raise AttachmentCompatibilityValidationError(
            field_name, "contains an unsupported value"
        )


def _utc_datetime(value: Any, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise AttachmentCompatibilityValidationError(
            field_name, "must be a datetime"
        )
    if value.tzinfo is None or value.utcoffset() is None:
        raise AttachmentCompatibilityValidationError(
            field_name, "must be timezone-aware"
        )
    return value.astimezone(timezone.utc)


def _parse_datetime(value: Any, field_name: str) -> datetime:
    if isinstance(value, datetime):
        return _utc_datetime(value, field_name)
    if not isinstance(value, str):
        raise AttachmentCompatibilityValidationError(
            field_name, "must be a datetime or ISO-8601 string"
        )
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        raise AttachmentCompatibilityValidationError(
            field_name, "must be a valid ISO-8601 datetime"
        )
    return _utc_datetime(parsed, field_name)


def _exact_mapping(
    value: Any, field_names: Tuple[str, ...], model_name: str
) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise AttachmentCompatibilityValidationError(
            model_name, "serialized value must be a mapping"
        )
    keys = tuple(value)
    if any(not isinstance(key, str) for key in keys):
        raise AttachmentCompatibilityValidationError(
            model_name, "serialized field names must be strings"
        )
    unknown = set(keys) - set(field_names)
    if unknown:
        raise AttachmentCompatibilityValidationError(
            model_name,
            "contains unknown fields: {0}".format(", ".join(sorted(unknown))),
        )
    missing = set(field_names) - set(keys)
    if missing:
        raise AttachmentCompatibilityValidationError(
            model_name,
            "is missing fields: {0}".format(", ".join(sorted(missing))),
        )
    return {name: value[name] for name in field_names}


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def canonical_compatibility_categories(
) -> Tuple[AttachmentCompatibilityStatus, ...]:
    """Return the complete Phase 1 decision vocabulary in stable order."""

    return (
        AttachmentCompatibilityStatus.COMPATIBLE,
        AttachmentCompatibilityStatus.INCOMPATIBLE,
        AttachmentCompatibilityStatus.REQUIRES_REVIEW,
    )


def canonical_version_outcomes(
) -> Tuple[Tuple[AttachmentVersionCondition, AttachmentCompatibilityStatus], ...]:
    """Return the fixed declarative condition-to-status policy."""

    return (
        (
            AttachmentVersionCondition.SAME_CONTRACT_VERSION,
            AttachmentCompatibilityStatus.COMPATIBLE,
        ),
        (
            AttachmentVersionCondition.MAJOR_VERSION_MISMATCH,
            AttachmentCompatibilityStatus.INCOMPATIBLE,
        ),
        (
            AttachmentVersionCondition.MINOR_VERSION_EVOLUTION,
            AttachmentCompatibilityStatus.REQUIRES_REVIEW,
        ),
        (
            AttachmentVersionCondition.PATCH_VERSION_CHANGE,
            AttachmentCompatibilityStatus.COMPATIBLE,
        ),
        (
            AttachmentVersionCondition.UNKNOWN_VERSION,
            AttachmentCompatibilityStatus.REQUIRES_REVIEW,
        ),
    )


@dataclass(frozen=True)
class AttachmentVersionCompatibilityRule:
    """One immutable declarative version-compatibility rule."""

    condition: AttachmentVersionCondition
    compatibility_status: AttachmentCompatibilityStatus

    def __post_init__(self) -> None:
        condition = _enum(
            self.condition, AttachmentVersionCondition, "condition"
        )
        status = _enum(
            self.compatibility_status,
            AttachmentCompatibilityStatus,
            "compatibility_status",
        )
        expected = dict(canonical_version_outcomes())[condition]
        if status is not expected:
            raise AttachmentCompatibilityValidationError(
                "compatibility_status",
                "must be {0} for {1}".format(expected.value, condition.value),
            )
        object.__setattr__(self, "condition", condition)
        object.__setattr__(self, "compatibility_status", status)

    def to_dict(self) -> Dict[str, str]:
        return {
            "condition": self.condition.value,
            "compatibility_status": self.compatibility_status.value,
        }

    @classmethod
    def from_dict(
        cls, value: Mapping[str, Any]
    ) -> "AttachmentVersionCompatibilityRule":
        payload = _exact_mapping(
            value,
            ("condition", "compatibility_status"),
            cls.__name__,
        )
        return cls(**payload)


def canonical_version_rules() -> Tuple[AttachmentVersionCompatibilityRule, ...]:
    """Build the immutable canonical rules without evaluating any versions."""

    return tuple(
        AttachmentVersionCompatibilityRule(condition, status)
        for condition, status in canonical_version_outcomes()
    )


@dataclass(frozen=True)
class RealityGapAttachmentCompatibilityPolicy:
    """Versioned, declarative attachment compatibility policy.

    The record contains no parser, evaluator, artifact resolver, migration, or
    current-version lookup behavior.
    """

    policy_version: str
    compatibility_categories: Tuple[AttachmentCompatibilityStatus, ...] = field(
        default_factory=canonical_compatibility_categories
    )
    version_rules: Tuple[AttachmentVersionCompatibilityRule, ...] = field(
        default_factory=canonical_version_rules
    )
    independent_version_axes: Tuple[AttachmentRevisionAxis, ...] = field(
        default_factory=canonical_revision_axes
    )
    historical_integrity_required: bool = True
    preserve_historical_references: bool = True
    allow_current_default_substitution: bool = False

    def __post_init__(self) -> None:
        policy_version = _required_text(self.policy_version, "policy_version")

        categories = self._ordered_tuple(
            self.compatibility_categories, "compatibility_categories"
        )
        categories = tuple(
            _enum(item, AttachmentCompatibilityStatus, "compatibility_categories")
            for item in categories
        )
        if categories != canonical_compatibility_categories():
            raise AttachmentCompatibilityValidationError(
                "compatibility_categories",
                "must contain the complete canonical category set in stable order",
            )

        rules = self._ordered_tuple(self.version_rules, "version_rules")
        if any(
            not isinstance(item, AttachmentVersionCompatibilityRule)
            for item in rules
        ):
            raise AttachmentCompatibilityValidationError(
                "version_rules",
                "must contain AttachmentVersionCompatibilityRule records",
            )
        if rules != canonical_version_rules():
            raise AttachmentCompatibilityValidationError(
                "version_rules", "must equal the canonical Phase 1 rule set"
            )

        axes = self._ordered_tuple(
            self.independent_version_axes, "independent_version_axes"
        )
        axes = tuple(
            _enum(item, AttachmentRevisionAxis, "independent_version_axes")
            for item in axes
        )
        if axes != canonical_revision_axes():
            raise AttachmentCompatibilityValidationError(
                "independent_version_axes",
                "must preserve four independent artifact version axes",
            )

        invariants = (
            (
                "historical_integrity_required",
                self.historical_integrity_required,
                True,
            ),
            (
                "preserve_historical_references",
                self.preserve_historical_references,
                True,
            ),
            (
                "allow_current_default_substitution",
                self.allow_current_default_substitution,
                False,
            ),
        )
        for field_name, value, required in invariants:
            if type(value) is not bool or value is not required:
                raise AttachmentCompatibilityValidationError(
                    field_name,
                    "must be {0} for historical integrity".format(required),
                )

        object.__setattr__(self, "policy_version", policy_version)
        object.__setattr__(self, "compatibility_categories", categories)
        object.__setattr__(self, "version_rules", rules)
        object.__setattr__(self, "independent_version_axes", axes)

    @staticmethod
    def _ordered_tuple(value: Any, field_name: str) -> Tuple[Any, ...]:
        if isinstance(value, (str, bytes, set, frozenset, Mapping)):
            raise AttachmentCompatibilityValidationError(
                field_name, "must be an ordered collection"
            )
        try:
            return tuple(value)
        except TypeError:
            raise AttachmentCompatibilityValidationError(
                field_name, "must be an ordered collection"
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_version": self.policy_version,
            "compatibility_categories": [
                item.value for item in self.compatibility_categories
            ],
            "version_rules": [item.to_dict() for item in self.version_rules],
            "independent_version_axes": [
                item.value for item in self.independent_version_axes
            ],
            "historical_integrity_required": self.historical_integrity_required,
            "preserve_historical_references": self.preserve_historical_references,
            "allow_current_default_substitution": (
                self.allow_current_default_substitution
            ),
        }

    def canonical_json(self) -> str:
        return _canonical_json(self.to_dict())

    @classmethod
    def from_dict(
        cls, value: Mapping[str, Any]
    ) -> "RealityGapAttachmentCompatibilityPolicy":
        payload = _exact_mapping(
            value, tuple(item.name for item in fields(cls)), cls.__name__
        )
        raw_rules = cls._ordered_tuple(payload["version_rules"], "version_rules")
        payload["version_rules"] = tuple(
            AttachmentVersionCompatibilityRule.from_dict(item)
            for item in raw_rules
        )
        return cls(**payload)


@dataclass(frozen=True)
class RealityGapAttachmentCompatibilityDecision:
    """Immutable record of an externally supplied compatibility decision."""

    attachment_reference: AttachmentReadReference
    analysis_reference: AttachmentReadReference
    classification_reference: AttachmentReadReference
    metrics_reference: AttachmentReadReference
    compatibility_status: AttachmentCompatibilityStatus
    policy_version: str
    evaluated_at: datetime

    def __post_init__(self) -> None:
        references = {
            "attachment_reference": self.attachment_reference,
            "analysis_reference": self.analysis_reference,
            "classification_reference": self.classification_reference,
            "metrics_reference": self.metrics_reference,
        }
        for field_name, reference in references.items():
            if not isinstance(reference, AttachmentReadReference):
                raise AttachmentCompatibilityValidationError(
                    field_name, "must be an AttachmentReadReference"
                )
        identities = tuple(
            reference.reference_id for reference in references.values()
        )
        if len(set(identities)) != len(identities):
            raise AttachmentCompatibilityValidationError(
                "references", "artifact identities must remain distinct"
            )
        status = _enum(
            self.compatibility_status,
            AttachmentCompatibilityStatus,
            "compatibility_status",
        )
        policy_version = _required_text(self.policy_version, "policy_version")
        evaluated_at = _utc_datetime(self.evaluated_at, "evaluated_at")

        object.__setattr__(self, "compatibility_status", status)
        object.__setattr__(self, "policy_version", policy_version)
        object.__setattr__(self, "evaluated_at", evaluated_at)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attachment_reference": self.attachment_reference.to_dict(),
            "analysis_reference": self.analysis_reference.to_dict(),
            "classification_reference": self.classification_reference.to_dict(),
            "metrics_reference": self.metrics_reference.to_dict(),
            "compatibility_status": self.compatibility_status.value,
            "policy_version": self.policy_version,
            "evaluated_at": self.evaluated_at.isoformat(),
        }

    def canonical_json(self) -> str:
        return _canonical_json(self.to_dict())

    @classmethod
    def from_dict(
        cls, value: Mapping[str, Any]
    ) -> "RealityGapAttachmentCompatibilityDecision":
        payload = _exact_mapping(
            value, tuple(item.name for item in fields(cls)), cls.__name__
        )
        for field_name in (
            "attachment_reference",
            "analysis_reference",
            "classification_reference",
            "metrics_reference",
        ):
            try:
                payload[field_name] = AttachmentReadReference.from_dict(
                    payload[field_name]
                )
            except ValueError as error:
                raise AttachmentCompatibilityValidationError(field_name, str(error))
        payload["evaluated_at"] = _parse_datetime(
            payload["evaluated_at"], "evaluated_at"
        )
        return cls(**payload)
