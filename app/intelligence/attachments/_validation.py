"""Pure validation, deep freezing, and canonical JSON helpers."""

from collections.abc import Mapping
from datetime import datetime, timezone
from enum import Enum
import json
import math
from types import MappingProxyType
from typing import Any, Callable, Dict, Iterable, Mapping as TypingMapping


ErrorFactory = Callable[[str, str], ValueError]


def required_text(value: Any, field_name: str, error: ErrorFactory) -> str:
    if not isinstance(value, str):
        raise error(field_name, "must be a string")
    normalized = value.strip()
    if not normalized:
        raise error(field_name, "must not be empty")
    return normalized


def positive_version(value: Any, field_name: str, error: ErrorFactory) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise error(field_name, "must be a positive integer")
    return value


def utc_datetime(value: Any, field_name: str, error: ErrorFactory) -> datetime:
    if not isinstance(value, datetime):
        raise error(field_name, "must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise error(field_name, "must be timezone-aware")
    return value.astimezone(timezone.utc)


def parse_datetime(value: Any, field_name: str, error: ErrorFactory) -> datetime:
    if isinstance(value, datetime):
        return utc_datetime(value, field_name, error)
    if not isinstance(value, str):
        raise error(field_name, "must be a datetime or ISO-8601 string")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        raise error(field_name, "must be a valid ISO-8601 datetime")
    return utc_datetime(parsed, field_name, error)


def _freeze(value: Any, field_name: str, error: ErrorFactory) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise error(field_name, "numeric values must be finite")
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return utc_datetime(value, field_name, error).isoformat()
    if isinstance(value, Mapping):
        keys = tuple(value)
        if any(not isinstance(key, str) or not key.strip() for key in keys):
            raise error(field_name, "mapping keys must be non-empty strings")
        return MappingProxyType(
            {
                key: _freeze(value[key], "{0}.{1}".format(field_name, key), error)
                for key in sorted(keys)
            }
        )
    if isinstance(value, (list, tuple)):
        return tuple(
            _freeze(item, "{0}[]".format(field_name), error) for item in value
        )
    raise error(
        field_name,
        "contains a mutable, unordered, or unsupported value",
    )


def frozen_metadata(
    value: Any,
    field_name: str,
    error: ErrorFactory,
) -> TypingMapping[str, Any]:
    if not isinstance(value, Mapping):
        raise error(field_name, "must be a mapping")
    return _freeze(value, field_name, error)


def plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
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
    error: ErrorFactory,
) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise error(model_name, "serialized value must be a mapping")
    expected = tuple(field_names)
    keys = tuple(value)
    if any(not isinstance(key, str) for key in keys):
        raise error(model_name, "serialized field names must be strings")
    unknown = set(keys) - set(expected)
    if unknown:
        raise error(
            model_name,
            "contains unknown fields: {0}".format(", ".join(sorted(unknown))),
        )
    missing = set(expected) - set(keys)
    if missing:
        raise error(
            model_name,
            "is missing fields: {0}".format(", ".join(sorted(missing))),
        )
    return {name: value[name] for name in expected}


__all__ = [
    "canonical_json_bytes",
    "frozen_metadata",
    "mapping_payload",
    "parse_datetime",
    "plain",
    "positive_version",
    "required_text",
    "utc_datetime",
]
