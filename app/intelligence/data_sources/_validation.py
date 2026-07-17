"""Pure validation and deterministic serialization for source contracts."""

from collections.abc import Mapping
from datetime import datetime, timezone
from enum import Enum
import json
import math
from numbers import Real
from typing import Any, Dict, Iterable, Type, TypeVar


EnumT = TypeVar("EnumT", bound=Enum)


def required_text(value: Any, field_name: str, uppercase: bool = False) -> str:
    if not isinstance(value, str):
        raise TypeError("{0} must be a string".format(field_name))
    normalized = value.strip()
    if not normalized:
        raise ValueError("{0} must not be empty".format(field_name))
    return normalized.upper() if uppercase else normalized


def finite_number(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError("{0} must be a real number".format(field_name))
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError("{0} must be finite".format(field_name))
    return normalized


def positive_number(value: Any, field_name: str) -> float:
    normalized = finite_number(value, field_name)
    if normalized <= 0.0:
        raise ValueError("{0} must be greater than 0".format(field_name))
    return normalized


def non_negative_number(value: Any, field_name: str) -> float:
    normalized = finite_number(value, field_name)
    if normalized < 0.0:
        raise ValueError(
            "{0} must be greater than or equal to 0".format(field_name)
        )
    return normalized


def utc_datetime(value: Any, field_name: str = "captured_at") -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("{0} must be a datetime".format(field_name))
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("{0} must be timezone-aware".format(field_name))
    return value.astimezone(timezone.utc)


def parse_datetime(value: Any, field_name: str = "captured_at") -> datetime:
    if isinstance(value, datetime):
        return utc_datetime(value, field_name)
    if not isinstance(value, str):
        raise TypeError(
            "{0} must be a datetime or ISO-8601 string".format(field_name)
        )
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise ValueError(
            "{0} must be a valid ISO-8601 datetime".format(field_name)
        ) from error
    return utc_datetime(parsed, field_name)


def enum_value(enum_type: Type[EnumT], value: Any, field_name: str) -> EnumT:
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(value)
    except (TypeError, ValueError) as error:
        raise ValueError(
            "invalid {0}: {1!r}".format(field_name, value)
        ) from error


def exact_payload(
    value: Any,
    field_names: Iterable[str],
    model_name: str,
) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError("{0} data must be a mapping".format(model_name))
    expected = tuple(field_names)
    keys = tuple(value)
    if any(not isinstance(key, str) for key in keys):
        raise TypeError("{0} field names must be strings".format(model_name))
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
    return {field_name: value[field_name] for field_name in expected}


def canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


__all__ = [
    "canonical_json",
    "enum_value",
    "exact_payload",
    "finite_number",
    "non_negative_number",
    "parse_datetime",
    "positive_number",
    "required_text",
    "utc_datetime",
]
