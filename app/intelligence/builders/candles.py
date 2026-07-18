"""Exchange-independent immutable normalized candle contract."""

from dataclasses import dataclass
from datetime import datetime, timezone
import math
from numbers import Real
from typing import Any, Dict, Mapping, Optional


def _utc_datetime(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _parse_datetime(value: Any, field_name: str) -> datetime:
    if isinstance(value, datetime):
        return _utc_datetime(value, field_name)
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a datetime or ISO-8601 string")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid ISO-8601 datetime") from exc
    return _utc_datetime(parsed, field_name)


def _number(value: Real, field_name: str, *, positive: bool) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{field_name} must be a real number")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"{field_name} must be finite")
    if positive and normalized <= 0.0:
        raise ValueError(f"{field_name} must be greater than 0")
    if not positive and normalized < 0.0:
        raise ValueError(f"{field_name} must be greater than or equal to 0")
    return normalized


@dataclass(frozen=True)
class Candle:
    """One normalized OHLCV candle with timezone-aware UTC timestamps."""

    open_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: Optional[datetime] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "open_time", _utc_datetime(self.open_time, "open_time"))
        if self.close_time is not None:
            object.__setattr__(
                self, "close_time", _utc_datetime(self.close_time, "close_time")
            )
        for field_name in ("open", "high", "low", "close"):
            object.__setattr__(
                self,
                field_name,
                _number(getattr(self, field_name), field_name, positive=True),
            )
        object.__setattr__(
            self, "volume", _number(self.volume, "volume", positive=False)
        )

        if self.low > min(self.open, self.close):
            raise ValueError("low must be less than or equal to open and close")
        if self.high < max(self.open, self.close):
            raise ValueError("high must be greater than or equal to open and close")
        if self.low > self.high:
            raise ValueError("low must be less than or equal to high")
        if self.close_time is not None and self.close_time < self.open_time:
            raise ValueError("close_time must not be earlier than open_time")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "open_time": self.open_time.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "close_time": (
                self.close_time.isoformat() if self.close_time is not None else None
            ),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Candle":
        if not isinstance(data, Mapping):
            raise TypeError("candle data must be a mapping")
        payload = dict(data)
        payload["open_time"] = _parse_datetime(payload.get("open_time"), "open_time")
        if payload.get("close_time") is not None:
            payload["close_time"] = _parse_datetime(
                payload.get("close_time"), "close_time"
            )
        return cls(**payload)
