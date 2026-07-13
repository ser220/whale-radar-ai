"""Validation and serialization helpers internal to the contracts package."""

from collections.abc import Mapping
from datetime import datetime, timezone
from enum import Enum
import math
from numbers import Real
from types import MappingProxyType
from typing import Any, Iterable, Tuple


def bounded_percentage(value: Real, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{field_name} must be a real number")

    normalized = float(value)
    if not math.isfinite(normalized) or not 0.0 <= normalized <= 100.0:
        raise ValueError(f"{field_name} must be between 0 and 100")
    return normalized


def string_tuple(values: Iterable[str], field_name: str) -> Tuple[str, ...]:
    if isinstance(values, str):
        raise TypeError(f"{field_name} must be a collection of strings")

    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise TypeError(f"{field_name} must be a collection of strings") from exc

    if not all(isinstance(item, str) for item in normalized):
        raise TypeError(f"{field_name} must contain only strings")
    return normalized


def required_string(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value


def optional_string(value: Any, field_name: str) -> Any:
    if value is not None and not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string or None")
    return value


def utc_datetime(value: datetime, field_name: str = "timestamp") -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_datetime(value: Any, field_name: str = "timestamp") -> datetime:
    if isinstance(value, datetime):
        return utc_datetime(value, field_name)
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a datetime or ISO-8601 string")

    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid ISO-8601 datetime") from exc
    return utc_datetime(parsed, field_name)


def frozen_mapping(value: Mapping[str, Any], field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping")
    return MappingProxyType({key: freeze(item) for key, item in value.items()})


def freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(freeze(item) for item in value)
    return value


def to_plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return utc_datetime(value).isoformat()
    if isinstance(value, Mapping):
        return {key: to_plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [to_plain(item) for item in value]
    return value
