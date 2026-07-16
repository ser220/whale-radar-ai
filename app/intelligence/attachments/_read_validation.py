"""Validation and canonical serialization helpers for attachment read contracts."""

from collections.abc import Mapping
from datetime import datetime, timezone
import json
from typing import Any, Dict, Iterable


def required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError("{0} must be a string".format(field_name))
    normalized = value.strip()
    if not normalized:
        raise ValueError("{0} must not be empty".format(field_name))
    return normalized


def positive_version(value: Any, field_name: str) -> int:
    if type(value) is not int or value < 1:
        raise ValueError("{0} must be a positive integer".format(field_name))
    return value


def utc_datetime(value: Any, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("{0} must be a datetime".format(field_name))
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("{0} must be timezone-aware".format(field_name))
    return value.astimezone(timezone.utc)


def parse_datetime(value: Any, field_name: str) -> datetime:
    if isinstance(value, datetime):
        return utc_datetime(value, field_name)
    if not isinstance(value, str):
        raise ValueError(
            "{0} must be a datetime or ISO-8601 string".format(field_name)
        )
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        raise ValueError("{0} must be a valid ISO-8601 datetime".format(field_name))
    return utc_datetime(parsed, field_name)


def exact_mapping(
    value: Any,
    field_names: Iterable[str],
    model_name: str,
) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("{0} must be a mapping".format(model_name))
    expected = tuple(field_names)
    keys = tuple(value)
    if any(not isinstance(key, str) for key in keys):
        raise ValueError("{0} field names must be strings".format(model_name))
    unknown = set(keys) - set(expected)
    if unknown:
        raise ValueError(
            "{0} contains unknown fields: {1}".format(
                model_name, ", ".join(sorted(unknown))
            )
        )
    missing = set(expected) - set(keys)
    if missing:
        raise ValueError(
            "{0} is missing fields: {1}".format(
                model_name, ", ".join(sorted(missing))
            )
        )
    return {name: value[name] for name in expected}


def canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
