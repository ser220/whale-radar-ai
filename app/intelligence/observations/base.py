"""Shared validation and serialization behavior for observation contracts."""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from datetime import datetime, timezone
from enum import Enum
import math
from numbers import Real
from types import MappingProxyType
from typing import Any, Dict, Mapping as TypingMapping, Optional, Type, TypeVar


EnumT = TypeVar("EnumT", bound=Enum)


def required_text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def finite_number(value: Real, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{field_name} must be a real number")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"{field_name} must be finite")
    return normalized


def bounded_number(value: Real, field_name: str, minimum: float, maximum: float) -> float:
    normalized = finite_number(value, field_name)
    if not minimum <= normalized <= maximum:
        raise ValueError(f"{field_name} must be between {minimum:g} and {maximum:g}")
    return normalized


def optional_finite_number(value: Optional[Real], field_name: str) -> Optional[float]:
    if value is None:
        return None
    return finite_number(value, field_name)


def optional_bounded_number(
    value: Optional[Real], field_name: str, minimum: float, maximum: float
) -> Optional[float]:
    if value is None:
        return None
    return bounded_number(value, field_name, minimum, maximum)


def non_negative_number(value: Real, field_name: str) -> float:
    normalized = finite_number(value, field_name)
    if normalized < 0.0:
        raise ValueError(f"{field_name} must be greater than or equal to 0")
    return normalized


def optional_non_negative_number(value: Optional[Real], field_name: str) -> Optional[float]:
    if value is None:
        return None
    return non_negative_number(value, field_name)


def non_negative_integer(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be greater than or equal to 0")
    return value


def observation_version(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("version must be an integer")
    if value < 1:
        raise ValueError("version must be greater than or equal to 1")
    return value


def utc_datetime(value: datetime, field_name: str = "observed_at") -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def parse_datetime(value: Any, field_name: str = "observed_at") -> datetime:
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


def enum_value(enum_type: Type[EnumT], value: Any, field_name: str) -> EnumT:
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid {field_name}: {value!r}") from exc


def freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(freeze(item) for item in value)
    return value


def frozen_metadata(value: TypingMapping[str, Any]) -> TypingMapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError("metadata must be a mapping")
    return MappingProxyType({key: freeze(item) for key, item in value.items()})


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


class Observation(ABC):
    """Abstract common contract implemented by every concrete observation."""

    OBSERVATION_TYPE = "observation"

    observation_id: str
    asset: str
    source: str
    timeframe: str
    version: int
    quality: float
    observed_at: datetime
    metadata: TypingMapping[str, Any]

    def _validate_common(self) -> None:
        object.__setattr__(
            self, "observation_id", required_text(self.observation_id, "observation_id")
        )
        object.__setattr__(self, "asset", required_text(self.asset, "asset").upper())
        object.__setattr__(self, "source", required_text(self.source, "source"))
        object.__setattr__(self, "timeframe", required_text(self.timeframe, "timeframe"))
        object.__setattr__(self, "version", observation_version(self.version))
        object.__setattr__(self, "quality", bounded_number(self.quality, "quality", 0, 100))
        object.__setattr__(self, "observed_at", utc_datetime(self.observed_at))
        object.__setattr__(self, "metadata", frozen_metadata(self.metadata))

    def _common_dict(self) -> Dict[str, Any]:
        return {
            "observation_type": self.OBSERVATION_TYPE,
            "observation_id": self.observation_id,
            "asset": self.asset,
            "source": self.source,
            "timeframe": self.timeframe,
            "quality": self.quality,
            "observed_at": self.observed_at.isoformat(),
            "version": self.version,
            "metadata": to_plain(self.metadata),
        }

    @classmethod
    def _payload(cls, data: TypingMapping[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, Mapping):
            raise TypeError("observation data must be a mapping")
        payload = dict(data)
        serialized_type = payload.pop("observation_type", cls.OBSERVATION_TYPE)
        if serialized_type != cls.OBSERVATION_TYPE:
            raise ValueError(
                f"observation_type must be {cls.OBSERVATION_TYPE!r}, "
                f"got {serialized_type!r}"
            )
        payload["observed_at"] = parse_datetime(payload.get("observed_at"))
        return payload

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serialize this observation into public primitive values."""
