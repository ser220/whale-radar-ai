"""Shared validation and deterministic serialization helpers."""

from collections.abc import Mapping
from datetime import datetime, timezone
from enum import Enum
import json
import math
from numbers import Real
from types import MappingProxyType
from typing import Any, Dict, Iterable, Mapping as TypingMapping, Optional, Tuple, Type, TypeVar


EnumType = TypeVar("EnumType", bound=Enum)

_FORBIDDEN_METADATA_KEYS = {
    "authorization",
    "credential",
    "credentials",
    "header",
    "headers",
    "host_identifier",
    "hostname",
    "password",
    "private_header",
    "provider_payload",
    "raw_payload",
    "secret",
    "token",
}


def required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError("{0} must be a string".format(field_name))
    normalized = value.strip()
    if not normalized:
        raise ValueError("{0} must not be empty".format(field_name))
    return normalized


def optional_text(value: Any, field_name: str) -> Optional[str]:
    if value is None:
        return None
    return required_text(value, field_name)


def positive_integer(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("{0} must be an integer".format(field_name))
    if value < 1:
        raise ValueError("{0} must be at least 1".format(field_name))
    return value


def nonnegative_integer(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("{0} must be an integer".format(field_name))
    if value < 0:
        raise ValueError("{0} must not be negative".format(field_name))
    return value


def optional_nonnegative_integer(value: Any, field_name: str) -> Optional[int]:
    if value is None:
        return None
    return nonnegative_integer(value, field_name)


def percentage(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError("{0} must be a real number".format(field_name))
    normalized = float(value)
    if not math.isfinite(normalized) or not 0.0 <= normalized <= 100.0:
        raise ValueError("{0} must be between 0 and 100".format(field_name))
    return normalized


def optional_percentage(value: Any, field_name: str) -> Optional[float]:
    if value is None:
        return None
    return percentage(value, field_name)


def utc_datetime(value: Any, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("{0} must be a datetime".format(field_name))
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("{0} must be timezone-aware".format(field_name))
    return value.astimezone(timezone.utc)


def parse_datetime(value: Any, field_name: str) -> datetime:
    if isinstance(value, datetime):
        return utc_datetime(value, field_name)
    if not isinstance(value, str):
        raise TypeError("{0} must be a datetime or ISO-8601 string".format(field_name))
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError("{0} must be a valid ISO-8601 datetime".format(field_name)) from exc
    return utc_datetime(parsed, field_name)


def enum_value(value: Any, enum_type: Type[EnumType], field_name: str) -> EnumType:
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid {0}".format(field_name)) from exc


def text_tuple(value: Any, field_name: str, *, required: bool = False) -> Tuple[str, ...]:
    if isinstance(value, (str, bytes, set, frozenset)):
        raise TypeError("{0} must be an ordered collection".format(field_name))
    try:
        items = tuple(required_text(item, "{0} item".format(field_name)) for item in value)
    except TypeError as exc:
        raise TypeError("{0} must be an ordered collection".format(field_name)) from exc
    if required and not items:
        raise ValueError("{0} must not be empty".format(field_name))
    if len(set(items)) != len(items):
        raise ValueError("{0} must not contain duplicates".format(field_name))
    return items


def enum_tuple(
    value: Any,
    enum_type: Type[EnumType],
    field_name: str,
    *,
    required: bool = False,
) -> Tuple[EnumType, ...]:
    if isinstance(value, (str, bytes, set, frozenset)):
        raise TypeError("{0} must be an ordered collection".format(field_name))
    try:
        items = tuple(enum_value(item, enum_type, "{0} item".format(field_name)) for item in value)
    except TypeError as exc:
        raise TypeError("{0} must be an ordered collection".format(field_name)) from exc
    if required and not items:
        raise ValueError("{0} must not be empty".format(field_name))
    if len(set(items)) != len(items):
        raise ValueError("{0} must not contain duplicates".format(field_name))
    return items


def positive_integer_tuple(value: Any, field_name: str, *, required: bool = False) -> Tuple[int, ...]:
    if isinstance(value, (str, bytes, set, frozenset)):
        raise TypeError("{0} must be an ordered collection".format(field_name))
    try:
        items = tuple(positive_integer(item, "{0} item".format(field_name)) for item in value)
    except TypeError as exc:
        raise TypeError("{0} must be an ordered collection".format(field_name)) from exc
    if required and not items:
        raise ValueError("{0} must not be empty".format(field_name))
    if len(set(items)) != len(items):
        raise ValueError("{0} must not contain duplicates".format(field_name))
    return items


def freeze(value: Any, field_name: str = "metadata") -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("{0} numeric values must be finite".format(field_name))
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return utc_datetime(value, field_name).isoformat()
    if isinstance(value, Mapping):
        items = []
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("{0} keys must be strings".format(field_name))
            normalized_key = key.strip()
            if not normalized_key:
                raise ValueError("{0} keys must not be empty".format(field_name))
            if normalized_key.lower() in _FORBIDDEN_METADATA_KEYS:
                raise ValueError("{0} contains forbidden key {1}".format(field_name, normalized_key))
            items.append((normalized_key, freeze(item, "{0}.{1}".format(field_name, normalized_key))))
        items.sort(key=lambda pair: pair[0])
        return MappingProxyType(dict(items))
    if isinstance(value, (list, tuple)):
        return tuple(freeze(item, field_name) for item in value)
    if isinstance(value, (set, frozenset)):
        return tuple(sorted((freeze(item, field_name) for item in value), key=repr))
    if isinstance(value, Real):
        normalized = float(value)
        if not math.isfinite(normalized):
            raise ValueError("{0} numeric values must be finite".format(field_name))
        return normalized
    raise TypeError("{0} values must be serializable primitives".format(field_name))


def frozen_mapping(value: Any, field_name: str = "metadata") -> TypingMapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError("{0} must be a mapping".format(field_name))
    frozen = freeze(value, field_name)
    if not isinstance(frozen, Mapping):
        raise TypeError("{0} must be a mapping".format(field_name))
    return frozen


def plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return utc_datetime(value, "timestamp").isoformat()
    if isinstance(value, Mapping):
        return {key: plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [plain(item) for item in value]
    return value


def mapping_payload(value: Any, model_name: str) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError("{0} data must be a mapping".format(model_name))
    return dict(value)


def typed_tuple(value: Any, expected_type: Type[Any], field_name: str) -> Tuple[Any, ...]:
    if isinstance(value, (str, bytes, set, frozenset)):
        raise TypeError("{0} must be an ordered collection".format(field_name))
    try:
        items = tuple(value)
    except TypeError as exc:
        raise TypeError("{0} must be an ordered collection".format(field_name)) from exc
    if not all(isinstance(item, expected_type) for item in items):
        raise TypeError("{0} contains an invalid model".format(field_name))
    return items


def canonical_json_bytes(model: Any) -> bytes:
    """Serialize one model or primitive mapping reproducibly without I/O."""

    if callable(getattr(model, "to_dict", None)):
        payload = model.to_dict()
    elif isinstance(model, Mapping):
        payload = plain(freeze(model, "payload"))
    else:
        raise TypeError("model must provide to_dict() or be a mapping")
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def require_disjoint(groups: Iterable[Tuple[str, Tuple[str, ...]]]) -> None:
    seen = {}
    for group_name, values in groups:
        for value in values:
            if value in seen:
                raise ValueError(
                    "{0} appears in both {1} and {2}".format(value, seen[value], group_name)
                )
            seen[value] = group_name


__all__ = ["canonical_json_bytes"]
