"""Public enums for immutable candidate projection contracts."""

from enum import Enum


class ProjectionFailureCategory(str, Enum):
    """Stable validation categories without projection or analytical behavior."""

    MISSING_IDENTITY = "MISSING_IDENTITY"
    VERSION_CONFLICT = "VERSION_CONFLICT"
    INVALID_EVIDENCE_REFERENCE = "INVALID_EVIDENCE_REFERENCE"
    INVALID_POLICY_VERSION = "INVALID_POLICY_VERSION"
    INVALID_TREE_CONTEXT = "INVALID_TREE_CONTEXT"
    INVALID_TIMESTAMP = "INVALID_TIMESTAMP"
    MUTABLE_PAYLOAD = "MUTABLE_PAYLOAD"


__all__ = ["ProjectionFailureCategory"]
