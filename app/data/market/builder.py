from datetime import datetime, timedelta, timezone
from typing import Any

from app.domain.market import TradingInstrument

from .feed import MarketFeed


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(
            "{0} must be a string".format(field_name)
        )

    normalized = value.strip()

    if not normalized:
        raise ValueError(
            "{0} must not be empty".format(field_name)
        )

    return normalized


def _positive_integer(
    value: Any,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            "{0} must be a positive integer".format(
                field_name
            )
        )

    if value <= 0:
        raise ValueError(
            "{0} must be a positive integer".format(
                field_name
            )
        )

    return value


class UniversalMarketFeedBuilder:
    """Assemble one normalized MarketFeed from injected market sources."""

    def __init__(
        self,
        *,
        candle_source: Any,
        market_collector: Any,
    ) -> None:
        if not (
            callable(
                getattr(
                    candle_source,
                    "get_candles",
                    None,
                )
            )
            and callable(
                getattr(
                    candle_source,
                    "source_name",
                    None,
                )
            )
        ):
            raise TypeError(
                "candle_source must provide "
                "get_candles and source_name"
            )

        if not callable(
            getattr(
                market_collector,
                "collect",
                None,
            )
        ):
            raise TypeError(
                "market_collector must provide collect"
            )

        self._candle_source = candle_source
        self._market_collector = market_collector

    @property
    def candle_source(self) -> Any:
        return self._candle_source

    @property
    def market_collector(self) -> Any:
        return self._market_collector

    def build(
        self,
        *,
        instrument: TradingInstrument,
        timeframe: str,
        candle_count: int,
        captured_at: datetime,
    ):
        if not isinstance(
            instrument,
            TradingInstrument,
        ):
            raise TypeError(
                "instrument must be a TradingInstrument"
            )

        normalized_timeframe = _required_text(
            timeframe,
            "timeframe",
        )

        normalized_candle_count = _positive_integer(
            candle_count,
            "candle_count",
        )

        if not isinstance(
            captured_at,
            datetime,
        ):
            raise TypeError(
                "captured_at must be a datetime"
            )

        if captured_at.tzinfo is None:
            raise ValueError(
                "captured_at must be timezone aware"
            )

        normalized_captured_at = captured_at.astimezone(
            timezone.utc
        )

        interval_minutes = {
            "1m": 1,
            "3m": 3,
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "1h": 60,
            "2h": 120,
            "4h": 240,
            "6h": 360,
            "8h": 480,
            "12h": 720,
            "1d": 1440,
        }.get(normalized_timeframe)

        if interval_minutes is None:
            raise ValueError(
                "unsupported timeframe: {0}".format(
                    normalized_timeframe
                )
            )

        request_count = normalized_candle_count + 1

        start_time = normalized_captured_at - timedelta(
            minutes=(
                interval_minutes
                * request_count
            )
        )

        candles = self.candle_source.get_candles(
            asset=instrument.base_symbol,
            interval=normalized_timeframe,
            start_time=start_time,
            end_time=normalized_captured_at,
            limit=request_count,
        )

        interval_delta = timedelta(
            minutes=interval_minutes
        )

        completed_candles = tuple(
            candle
            for candle in candles
            if candle.timestamp + interval_delta
            <= normalized_captured_at
        )

        completed_candles = completed_candles[
            -normalized_candle_count:
        ]

        market_snapshot = self.market_collector.collect(
            instrument.identity.symbol
        )

        return MarketFeed(
            instrument=instrument,
            candles=completed_candles,
            market_snapshot=market_snapshot,
            derivatives_snapshot=None,
            captured_at=normalized_captured_at,
        )
