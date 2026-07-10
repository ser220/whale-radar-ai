from datetime import datetime, timezone
from typing import Iterable, List, Optional

from app.domain.candle import Candle
from app.sources.candle_source import CandleSource


class InMemoryCandleSource(CandleSource):
    def __init__(
        self,
        candles: Iterable[Candle],
        name: str = "in-memory",
    ) -> None:
        self._candles = sorted(
            list(candles),
            key=lambda candle: candle.timestamp,
        )
        self._name = name

    def source_name(self) -> str:
        return self._name

    def get_candles(
        self,
        asset: str,
        interval: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[Candle]:
        del asset
        del interval

        start = self._ensure_utc(start_time)
        end = self._ensure_utc(end_time) if end_time else None

        result = [
            candle
            for candle in self._candles
            if candle.timestamp >= start
            and (end is None or candle.timestamp <= end)
        ]

        return result[:max(int(limit), 0)]

    @staticmethod
    def _ensure_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)
