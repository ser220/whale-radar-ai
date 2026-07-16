"""Immutable contracts defining the Reality Gap attachment lifecycle policy."""

from collections.abc import Mapping
from dataclasses import dataclass, field, fields
import json
from typing import Any, Dict, Tuple

from .lifecycle_enums import AttachmentLifecycleState, AttachmentRevisionAxis


class AttachmentLifecycleValidationError(ValueError):
    """Validation failure within the lifecycle policy contract layer."""

    def __init__(self, field_name: str, reason: str) -> None:
        self.field_name = field_name
        self.reason = reason
        super().__init__("{0}: {1}".format(field_name, reason))


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise AttachmentLifecycleValidationError(field_name, "must be a string")
    normalized = value.strip()
    if not normalized:
        raise AttachmentLifecycleValidationError(field_name, "must not be empty")
    return normalized


def _state(value: Any, field_name: str) -> AttachmentLifecycleState:
    try:
        return (
            value
            if isinstance(value, AttachmentLifecycleState)
            else AttachmentLifecycleState(value)
        )
    except (TypeError, ValueError):
        raise AttachmentLifecycleValidationError(
            field_name, "is not a supported lifecycle state"
        )


def _axis(value: Any) -> AttachmentRevisionAxis:
    try:
        return (
            value
            if isinstance(value, AttachmentRevisionAxis)
            else AttachmentRevisionAxis(value)
        )
    except (TypeError, ValueError):
        raise AttachmentLifecycleValidationError(
            "independent_revision_axes", "contains an unsupported revision axis"
        )


def _exact_mapping(
    value: Any, field_names: Tuple[str, ...], model_name: str
) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise AttachmentLifecycleValidationError(
            model_name, "serialized value must be a mapping"
        )
    keys = tuple(value)
    if any(not isinstance(key, str) for key in keys):
        raise AttachmentLifecycleValidationError(
            model_name, "serialized field names must be strings"
        )
    unknown = set(keys) - set(field_names)
    if unknown:
        raise AttachmentLifecycleValidationError(
            model_name,
            "contains unknown fields: {0}".format(", ".join(sorted(unknown))),
        )
    missing = set(field_names) - set(keys)
    if missing:
        raise AttachmentLifecycleValidationError(
            model_name,
            "is missing fields: {0}".format(", ".join(sorted(missing))),
        )
    return {name: value[name] for name in field_names}


@dataclass(frozen=True)
class AttachmentLifecycleTransition:
    """One permitted forward-only transition in the lifecycle graph."""

    from_state: AttachmentLifecycleState
    to_state: AttachmentLifecycleState

    def __post_init__(self) -> None:
        from_state = _state(self.from_state, "from_state")
        to_state = _state(self.to_state, "to_state")
        if (from_state, to_state) not in canonical_lifecycle_pairs():
            raise AttachmentLifecycleValidationError(
                "transition",
                "{0} -> {1} is not permitted".format(
                    from_state.value, to_state.value
                ),
            )
        object.__setattr__(self, "from_state", from_state)
        object.__setattr__(self, "to_state", to_state)

    def to_dict(self) -> Dict[str, str]:
        return {
            "from_state": self.from_state.value,
            "to_state": self.to_state.value,
        }

    @classmethod
    def from_dict(
        cls, value: Mapping[str, Any]
    ) -> "AttachmentLifecycleTransition":
        payload = _exact_mapping(
            value, ("from_state", "to_state"), cls.__name__
        )
        return cls(**payload)


def canonical_lifecycle_pairs(
) -> Tuple[Tuple[AttachmentLifecycleState, AttachmentLifecycleState], ...]:
    """Return the fixed Phase 1 lifecycle graph in deterministic order."""

    return (
        (AttachmentLifecycleState.CREATED, AttachmentLifecycleState.ACTIVE),
        (AttachmentLifecycleState.ACTIVE, AttachmentLifecycleState.SUPERSEDED),
        (AttachmentLifecycleState.SUPERSEDED, AttachmentLifecycleState.ARCHIVED),
    )


def canonical_lifecycle_transitions() -> Tuple[AttachmentLifecycleTransition, ...]:
    """Build the immutable canonical transition declarations."""

    return tuple(
        AttachmentLifecycleTransition(from_state, to_state)
        for from_state, to_state in canonical_lifecycle_pairs()
    )


def canonical_revision_axes() -> Tuple[AttachmentRevisionAxis, ...]:
    """Return the independently versioned axes in stable public order."""

    return (
        AttachmentRevisionAxis.ATTACHMENT,
        AttachmentRevisionAxis.ANALYSIS,
        AttachmentRevisionAxis.CLASSIFICATION,
        AttachmentRevisionAxis.METRICS,
    )


@dataclass(frozen=True)
class RealityGapAttachmentLifecyclePolicy:
    """Versioned declaration of attachment lifecycle and history invariants.

    This contract describes policy only.  It performs no transition, lookup,
    persistence, supersession, archival, or artifact resolution operation.
    """

    lifecycle_state: AttachmentLifecycleState
    policy_version: str
    revision_policy_identifier: str
    allowed_transitions: Tuple[AttachmentLifecycleTransition, ...] = field(
        default_factory=canonical_lifecycle_transitions
    )
    independent_revision_axes: Tuple[AttachmentRevisionAxis, ...] = field(
        default_factory=canonical_revision_axes
    )
    immutable_historical_attachments: bool = True
    preserve_historical_references: bool = True
    allow_current_default_substitution: bool = False

    def __post_init__(self) -> None:
        lifecycle_state = _state(self.lifecycle_state, "lifecycle_state")
        policy_version = _required_text(self.policy_version, "policy_version")
        revision_policy_identifier = _required_text(
            self.revision_policy_identifier, "revision_policy_identifier"
        )

        if isinstance(
            self.allowed_transitions, (str, bytes, set, frozenset, Mapping)
        ):
            raise AttachmentLifecycleValidationError(
                "allowed_transitions", "must be an ordered collection"
            )
        try:
            transitions = tuple(self.allowed_transitions)
        except TypeError:
            raise AttachmentLifecycleValidationError(
                "allowed_transitions", "must be an ordered collection"
            )
        if any(
            not isinstance(item, AttachmentLifecycleTransition)
            for item in transitions
        ):
            raise AttachmentLifecycleValidationError(
                "allowed_transitions",
                "must contain AttachmentLifecycleTransition records",
            )
        if transitions != canonical_lifecycle_transitions():
            raise AttachmentLifecycleValidationError(
                "allowed_transitions",
                "must equal the canonical forward-only lifecycle graph",
            )

        if isinstance(
            self.independent_revision_axes,
            (str, bytes, set, frozenset, Mapping),
        ):
            raise AttachmentLifecycleValidationError(
                "independent_revision_axes", "must be an ordered collection"
            )
        try:
            axes = tuple(_axis(item) for item in self.independent_revision_axes)
        except TypeError:
            raise AttachmentLifecycleValidationError(
                "independent_revision_axes", "must be an ordered collection"
            )
        if axes != canonical_revision_axes():
            raise AttachmentLifecycleValidationError(
                "independent_revision_axes",
                "must preserve attachment, analysis, classification, and metrics "
                "as independent revision axes",
            )

        boolean_invariants = (
            (
                "immutable_historical_attachments",
                self.immutable_historical_attachments,
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
        for field_name, value, required in boolean_invariants:
            if type(value) is not bool or value is not required:
                raise AttachmentLifecycleValidationError(
                    field_name,
                    "must be {0} for historical integrity".format(required),
                )

        object.__setattr__(self, "lifecycle_state", lifecycle_state)
        object.__setattr__(self, "policy_version", policy_version)
        object.__setattr__(
            self, "revision_policy_identifier", revision_policy_identifier
        )
        object.__setattr__(self, "allowed_transitions", transitions)
        object.__setattr__(self, "independent_revision_axes", axes)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lifecycle_state": self.lifecycle_state.value,
            "policy_version": self.policy_version,
            "revision_policy_identifier": self.revision_policy_identifier,
            "allowed_transitions": [
                transition.to_dict() for transition in self.allowed_transitions
            ],
            "independent_revision_axes": [
                axis.value for axis in self.independent_revision_axes
            ],
            "immutable_historical_attachments": (
                self.immutable_historical_attachments
            ),
            "preserve_historical_references": self.preserve_historical_references,
            "allow_current_default_substitution": (
                self.allow_current_default_substitution
            ),
        }

    def canonical_json(self) -> str:
        """Return deterministic canonical JSON for policy comparison/audit."""

        return json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )

    @classmethod
    def from_dict(
        cls, value: Mapping[str, Any]
    ) -> "RealityGapAttachmentLifecyclePolicy":
        payload = _exact_mapping(
            value, tuple(item.name for item in fields(cls)), cls.__name__
        )
        raw_transitions = payload["allowed_transitions"]
        if isinstance(
            raw_transitions, (str, bytes, set, frozenset, Mapping)
        ):
            raise AttachmentLifecycleValidationError(
                "allowed_transitions", "must be an ordered collection"
            )
        try:
            payload["allowed_transitions"] = tuple(
                AttachmentLifecycleTransition.from_dict(item)
                for item in raw_transitions
            )
        except TypeError:
            raise AttachmentLifecycleValidationError(
                "allowed_transitions", "must be an ordered collection"
            )
        return cls(**payload)
