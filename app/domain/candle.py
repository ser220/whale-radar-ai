from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Union


TimestampValue = Union[str, int, float, datetime]


@dataclass(frozen=True)
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    def __post_init__(self) -> None:
        timestamp = self._normalize_timestamp(self.timestamp)

        object.__setattr__(self, "timestamp", timestamp)
        object.__setattr__(self, "open", float(self.open))
        object.__setattr__(self, "high", float(self.high))
        object.__setattr__(self, "low", float(self.low))
        object.__setattr__(self, "close", float(self.close))
        object.__setattr__(self, "volume", float(self.volume or 0.0))

        if min(self.open, self.high, self.low, self.close) <= 0:
            raise ValueError("Candle prices must be greater than zero.")

        if self.high < self.low:
            raise ValueError("Candle high cannot be lower than candle low.")

        if self.high < max(self.open, self.close):
            raise ValueError(
                "Candle high cannot be lower than open or close."
            )

        if self.low > min(self.open, self.close):
            raise ValueError(
                "Candle low cannot be higher than open or close."
            )

        if self.volume < 0:
            raise ValueError("Candle volume cannot be negative.")

    @staticmethod
    def _normalize_timestamp(value: TimestampValue) -> datetime:
        if isinstance(value, datetime):
            result = value

        elif isinstance(value, (int, float)):
            numeric = float(value)

            if numeric > 10_000_000_000:
                numeric /= 1000

            result = datetime.fromtimestamp(
                numeric,
                tz=timezone.utc,
            )

        else:
            text = str(value).strip()

            if text.isdigit():
                return Candle._normalize_timestamp(int(text))

            result = datetime.fromisoformat(
                text.replace("Z", "+00:00")
            )

        if result.tzinfo is None:
            result = result.replace(tzinfo=timezone.utc)

        return result.astimezone(timezone.utc)

    @property
    def timestamp_iso(self) -> str:
        return self.timestamp.isoformat()

    @property
    def timestamp_ms(self) -> int:
        return int(self.timestamp.timestamp() * 1000)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["timestamp"] = self.timestamp_iso
        return data
