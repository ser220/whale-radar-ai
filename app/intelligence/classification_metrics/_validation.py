"""Validation and canonical serialization helpers for domain contracts."""

from collections.abc import Mapping
from datetime import datetime, timezone
from enum import Enum
import json
import math
import re
from types import MappingProxyType
from typing import Any, Callable, Dict, Iterable, Mapping as TypingMapping, Tuple


ErrorFactory = Callable[[str, str], ValueError]

_POLICY_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_CATEGORY = re.compile(r"^[A-Z][A-Z0-9_]*$")
_METRIC_KEY = re.compile(r"^[a-z][a-z0-9_]*$")


def required_text(value: Any, field_name: str, error: ErrorFactory) -> str:
    if not isinstance(value, str):
        raise error(field_name, "must be a string")
    normalized = value.strip()
    if not normalized:
        raise error(field_name, "must not be empty")
    return normalized


def policy_version(value: Any, field_name: str, error: ErrorFactory) -> str:
    normalized = required_text(value, field_name, error)
    if _POLICY_VERSION.fullmatch(normalized) is None:
        raise error(
            field_name,
            "must contain only letters, digits, dot, underscore, colon, or hyphen",
        )
    return normalized


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


def ordered_references(
    value: Any,
    field_name: str,
    error: ErrorFactory,
) -> Tuple[str, ...]:
    if isinstance(value, (str, bytes, set, frozenset, Mapping)):
        raise error(field_name, "must be an ordered collection of references")
    try:
        raw_items = tuple(value)
    except TypeError:
        raise error(field_name, "must be an ordered collection of references")
    if not raw_items:
        raise error(field_name, "must contain at least one reference")
    items = tuple(
        required_text(item, "{0} item".format(field_name), error)
        for item in raw_items
    )
    if len(set(items)) != len(items):
        raise error(field_name, "must not contain duplicates")
    return tuple(sorted(items))


def ordered_tokens(
    value: Any,
    field_name: str,
    pattern: re.Pattern,
    error: ErrorFactory,
) -> Tuple[str, ...]:
    if isinstance(value, (str, bytes, set, frozenset, Mapping)):
        raise error(field_name, "must be an ordered collection")
    try:
        raw_items = tuple(value)
    except TypeError:
        raise error(field_name, "must be an ordered collection")
    if not raw_items:
        raise error(field_name, "must contain at least one item")
    items = tuple(
        required_text(item, "{0} item".format(field_name), error)
        for item in raw_items
    )
    if any(pattern.fullmatch(item) is None for item in items):
        raise error(field_name, "contains an invalid token")
    if len(set(items)) != len(items):
        raise error(field_name, "must not contain duplicates")
    return tuple(sorted(items))


def category_tokens(value: Any, error: ErrorFactory) -> Tuple[str, ...]:
    return ordered_tokens(value, "categories", _CATEGORY, error)


def metric_key(value: Any, error: ErrorFactory) -> str:
    normalized = required_text(value, "metric key", error)
    if _METRIC_KEY.fullmatch(normalized) is None:
        raise error("metric key", "must be lower snake_case")
    return normalized


def optional_text(value: Any, field_name: str, error: ErrorFactory) -> Any:
    if value is None:
        return None
    return required_text(value, field_name, error)


def metric_scalar(value: Any, error: ErrorFactory) -> Any:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise error("value", "must be a finite number")
    if isinstance(value, float) and not math.isfinite(value):
        raise error("value", "must be a finite number")
    return value


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
    "category_tokens",
    "frozen_metadata",
    "mapping_payload",
    "metric_key",
    "metric_scalar",
    "optional_text",
    "ordered_references",
    "plain",
    "policy_version",
    "required_text",
    "parse_datetime",
    "utc_datetime",
]
