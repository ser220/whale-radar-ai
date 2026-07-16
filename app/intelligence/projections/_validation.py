"""Validation and canonical serialization helpers for projection contracts."""

from collections.abc import Mapping
from datetime import datetime, timezone
from enum import Enum
import json
import math
from types import MappingProxyType
from typing import Any, Dict, Iterable, Mapping as TypingMapping, Tuple, Type, TypeVar

from .enums import ProjectionFailureCategory


EnumType = TypeVar("EnumType", bound=Enum)


class ProjectionValidationError(ValueError):
    """A deterministic contract failure with a stable public category."""

    def __init__(
        self,
        category: ProjectionFailureCategory,
        field_name: str,
        reason: str,
    ) -> None:
        self.category = category
        self.field_name = field_name
        self.reason = reason
        super().__init__("{0}: {1}: {2}".format(category.value, field_name, reason))


def fail(
    category: ProjectionFailureCategory,
    field_name: str,
    reason: str,
) -> None:
    raise ProjectionValidationError(category, field_name, reason)


def required_text(
    value: Any,
    field_name: str,
    category: ProjectionFailureCategory,
) -> str:
    if not isinstance(value, str):
        fail(category, field_name, "must be a string")
    normalized = value.strip()
    if not normalized:
        fail(category, field_name, "must not be empty")
    return normalized


def positive_version(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        fail(
            ProjectionFailureCategory.VERSION_CONFLICT,
            field_name,
            "must be an integer",
        )
    if value < 1:
        fail(
            ProjectionFailureCategory.VERSION_CONFLICT,
            field_name,
            "must be at least 1",
        )
    return value


def enum_value(
    value: Any,
    enum_type: Type[EnumType],
    field_name: str,
) -> EnumType:
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(value)
    except (TypeError, ValueError):
        fail(
            ProjectionFailureCategory.INVALID_POLICY_VERSION,
            field_name,
            "is not a supported explicit decision value",
        )


def utc_datetime(value: Any, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        fail(
            ProjectionFailureCategory.INVALID_TIMESTAMP,
            field_name,
            "must be a datetime",
        )
    if value.tzinfo is None or value.utcoffset() is None:
        fail(
            ProjectionFailureCategory.INVALID_TIMESTAMP,
            field_name,
            "must be timezone-aware",
        )
    return value.astimezone(timezone.utc)


def parse_datetime(value: Any, field_name: str) -> datetime:
    if isinstance(value, datetime):
        return utc_datetime(value, field_name)
    if not isinstance(value, str):
        fail(
            ProjectionFailureCategory.INVALID_TIMESTAMP,
            field_name,
            "must be a datetime or ISO-8601 string",
        )
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        fail(
            ProjectionFailureCategory.INVALID_TIMESTAMP,
            field_name,
            "must be a valid ISO-8601 datetime",
        )
    return utc_datetime(parsed, field_name)


def reference_tuple(value: Any, field_name: str) -> Tuple[str, ...]:
    if isinstance(value, (str, bytes, set, frozenset, Mapping)):
        fail(
            ProjectionFailureCategory.INVALID_EVIDENCE_REFERENCE,
            field_name,
            "must be an ordered collection of reference IDs",
        )
    try:
        raw_items = tuple(value)
    except TypeError:
        fail(
            ProjectionFailureCategory.INVALID_EVIDENCE_REFERENCE,
            field_name,
            "must be an ordered collection of reference IDs",
        )

    items = tuple(
        required_text(
            item,
            "{0} item".format(field_name),
            ProjectionFailureCategory.INVALID_EVIDENCE_REFERENCE,
        )
        for item in raw_items
    )
    if len(set(items)) != len(items):
        fail(
            ProjectionFailureCategory.INVALID_EVIDENCE_REFERENCE,
            field_name,
            "must not contain duplicates",
        )
    return tuple(sorted(items))


def _freeze(value: Any, field_name: str) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            fail(
                ProjectionFailureCategory.MUTABLE_PAYLOAD,
                field_name,
                "numeric values must be finite",
            )
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return utc_datetime(value, field_name).isoformat()
    if isinstance(value, Mapping):
        frozen_items = {}
        keys = tuple(value)
        if any(not isinstance(key, str) or not key.strip() for key in keys):
            fail(
                ProjectionFailureCategory.MUTABLE_PAYLOAD,
                field_name,
                "mapping keys must be non-empty strings",
            )
        for key in sorted(keys):
            frozen_items[key] = _freeze(
                value[key],
                "{0}.{1}".format(field_name, key),
            )
        return MappingProxyType(frozen_items)
    if isinstance(value, (list, tuple)):
        return tuple(
            _freeze(item, "{0}[]".format(field_name)) for item in value
        )
    fail(
        ProjectionFailureCategory.MUTABLE_PAYLOAD,
        field_name,
        "contains a mutable, unordered, or unsupported value",
    )


def frozen_metadata(value: Any) -> TypingMapping[str, Any]:
    if not isinstance(value, Mapping):
        fail(
            ProjectionFailureCategory.MUTABLE_PAYLOAD,
            "metadata",
            "must be a mapping",
        )
    frozen = _freeze(value, "metadata")
    return frozen


def plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return utc_datetime(value, "created_at").isoformat()
    if isinstance(value, Mapping):
        return {key: plain(value[key]) for key in sorted(value)}
    if isinstance(value, tuple):
        return [plain(item) for item in value]
    return value


def canonical_json_bytes(value: TypingMapping[str, Any]) -> bytes:
    return json.dumps(
        plain(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def mapping_payload(
    value: Any,
    field_names: Iterable[str],
    model_name: str,
) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        fail(
            ProjectionFailureCategory.MUTABLE_PAYLOAD,
            model_name,
            "serialized value must be a mapping",
        )
    expected = tuple(field_names)
    keys = tuple(value)
    if any(not isinstance(key, str) for key in keys):
        fail(
            ProjectionFailureCategory.MUTABLE_PAYLOAD,
            model_name,
            "serialized field names must be strings",
        )
    unknown = set(keys) - set(expected)
    if unknown:
        fail(
            ProjectionFailureCategory.MUTABLE_PAYLOAD,
            model_name,
            "contains unknown fields: {0}".format(", ".join(sorted(unknown))),
        )
    missing = set(expected) - set(keys)
    if missing:
        fail(
            ProjectionFailureCategory.MISSING_IDENTITY,
            model_name,
            "is missing fields: {0}".format(", ".join(sorted(missing))),
        )
    return {field_name: value[field_name] for field_name in expected}


__all__ = [
    "ProjectionValidationError",
    "canonical_json_bytes",
    "enum_value",
    "frozen_metadata",
    "mapping_payload",
    "parse_datetime",
    "plain",
    "positive_version",
    "reference_tuple",
    "required_text",
    "utc_datetime",
]
