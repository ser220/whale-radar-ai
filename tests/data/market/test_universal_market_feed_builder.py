from datetime import datetime, timezone

import pytest

from app.data.market import UniversalMarketFeedBuilder
from app.domain.market import (
    InstrumentType,
    MarketIdentity,
    MarketType,
    TradingInstrument,
)


NOW = datetime(2026, 8, 1, 23, 30, tzinfo=timezone.utc)


class FakeCandleSource:
    def source_name(self):
        return "fake-candles"

    def get_candles(
        self,
        asset,
        interval,
        start_time,
        end_time=None,
        limit=1000,
    ):
        raise NotImplementedError


class FakeMarketCollector:
    def collect(self, symbol):
        raise NotImplementedError


def build_instrument() -> TradingInstrument:
    return TradingInstrument(
        identity=MarketIdentity(
            market_type=MarketType.CRYPTO,
            instrument_type=InstrumentType.SPOT,
            symbol="BTCUSDT",
            venue="BINANCE",
            currency="USDT",
            timezone="UTC",
        ),
        base_symbol="BTC",
        quote_symbol="USDT",
        settlement_currency="USDT",
        expiry=None,
    )


def test_builder_preserves_injected_dependencies() -> None:
    candle_source = FakeCandleSource()
    market_collector = FakeMarketCollector()

    builder = UniversalMarketFeedBuilder(
        candle_source=candle_source,
        market_collector=market_collector,
    )

    assert builder.candle_source is candle_source
    assert builder.market_collector is market_collector


def test_builder_requires_candle_source_boundary() -> None:
    with pytest.raises(
        TypeError,
        match="candle_source must provide get_candles and source_name",
    ):
        UniversalMarketFeedBuilder(
            candle_source=object(),
            market_collector=FakeMarketCollector(),
        )


def test_builder_requires_market_collector_boundary() -> None:
    with pytest.raises(
        TypeError,
        match="market_collector must provide collect",
    ):
        UniversalMarketFeedBuilder(
            candle_source=FakeCandleSource(),
            market_collector=object(),
        )


def test_build_requires_trading_instrument() -> None:
    builder = UniversalMarketFeedBuilder(
        candle_source=FakeCandleSource(),
        market_collector=FakeMarketCollector(),
    )

    with pytest.raises(
        TypeError,
        match="instrument must be a TradingInstrument",
    ):
        builder.build(
            instrument="BTCUSDT",
            timeframe="15m",
            candle_count=100,
            captured_at=NOW,
        )


def test_timeframe_must_not_be_empty() -> None:
    builder = UniversalMarketFeedBuilder(
        candle_source=FakeCandleSource(),
        market_collector=FakeMarketCollector(),
    )

    with pytest.raises(
        ValueError,
        match="timeframe must not be empty",
    ):
        builder.build(
            instrument=build_instrument(),
            timeframe="   ",
            candle_count=100,
            captured_at=NOW,
        )


@pytest.mark.parametrize("candle_count", [True, False, 0, -1])
def test_candle_count_requires_positive_integer(candle_count) -> None:
    builder = UniversalMarketFeedBuilder(
        candle_source=FakeCandleSource(),
        market_collector=FakeMarketCollector(),
    )

    with pytest.raises(
        (TypeError, ValueError),
        match="candle_count must be a positive integer",
    ):
        builder.build(
            instrument=build_instrument(),
            timeframe="15m",
            candle_count=candle_count,
            captured_at=NOW,
        )


def test_captured_at_requires_timezone_aware_datetime() -> None:
    builder = UniversalMarketFeedBuilder(
        candle_source=FakeCandleSource(),
        market_collector=FakeMarketCollector(),
    )

    with pytest.raises(
        ValueError,
        match="captured_at must be timezone aware",
    ):
        builder.build(
            instrument=build_instrument(),
            timeframe="15m",
            candle_count=100,
            captured_at=datetime(2026, 8, 1, 23, 30),
        )


def test_build_assembles_market_feed_from_injected_sources() -> None:
    from datetime import timedelta

    from app.domain.candle import Candle
    from app.intelligence.data_sources import (
        DataSourceCategory,
        DataSourceType,
        MarketSnapshot,
    )

    class WorkingCandleSource:
        def source_name(self):
            return "fake-candles"

        def get_candles(
            self,
            asset,
            interval,
            start_time,
            end_time=None,
            limit=1000,
        ):
            assert asset == "BTC"
            assert interval == "15m"
            assert end_time == NOW
            assert limit == 3
            assert start_time == NOW - timedelta(minutes=45)

            return [
                Candle(
                    timestamp=NOW - timedelta(minutes=30),
                    open=100,
                    high=105,
                    low=95,
                    close=102,
                    volume=10,
                ),
                Candle(
                    timestamp=NOW - timedelta(minutes=15),
                    open=102,
                    high=106,
                    low=101,
                    close=104,
                    volume=12,
                ),
            ]

    class WorkingMarketCollector:
        def collect(self, symbol):
            assert symbol == "BTCUSDT"

            return MarketSnapshot(
                source_category=DataSourceCategory.EXCHANGE,
                source=DataSourceType.BINANCE,
                symbol="BTCUSDT",
                price=104,
                volume_24h=1000,
                change_24h=2.5,
                captured_at=NOW,
            )

    builder = UniversalMarketFeedBuilder(
        candle_source=WorkingCandleSource(),
        market_collector=WorkingMarketCollector(),
    )

    feed = builder.build(
        instrument=build_instrument(),
        timeframe="15m",
        candle_count=2,
        captured_at=NOW,
    )

    assert feed.instrument == build_instrument()
    assert len(feed.candles) == 2
    assert feed.market_snapshot.symbol == "BTCUSDT"
    assert feed.derivatives_snapshot is None
    assert feed.captured_at == NOW


def test_build_excludes_incomplete_current_candle() -> None:
    from datetime import timedelta

    from app.domain.candle import Candle
    from app.intelligence.data_sources import (
        DataSourceCategory,
        DataSourceType,
        MarketSnapshot,
    )

    class CandleSourceWithCurrentCandle:
        def source_name(self):
            return "fake-candles"

        def get_candles(
            self,
            asset,
            interval,
            start_time,
            end_time=None,
            limit=1000,
        ):
            assert asset == "BTC"
            assert interval == "15m"
            assert end_time == NOW
            assert limit == 3
            assert start_time == NOW - timedelta(minutes=45)

            return [
                Candle(
                    timestamp=NOW - timedelta(minutes=30),
                    open=100,
                    high=105,
                    low=95,
                    close=102,
                    volume=10,
                ),
                Candle(
                    timestamp=NOW - timedelta(minutes=15),
                    open=102,
                    high=106,
                    low=101,
                    close=104,
                    volume=12,
                ),
                Candle(
                    timestamp=NOW,
                    open=104,
                    high=107,
                    low=103,
                    close=106,
                    volume=3,
                ),
            ]

    class WorkingMarketCollector:
        def collect(self, symbol):
            return MarketSnapshot(
                source_category=DataSourceCategory.EXCHANGE,
                source=DataSourceType.BINANCE,
                symbol=symbol,
                price=106,
                volume_24h=1000,
                change_24h=2.5,
                captured_at=NOW,
            )

    builder = UniversalMarketFeedBuilder(
        candle_source=CandleSourceWithCurrentCandle(),
        market_collector=WorkingMarketCollector(),
    )

    feed = builder.build(
        instrument=build_instrument(),
        timeframe="15m",
        candle_count=2,
        captured_at=NOW,
    )

    assert len(feed.candles) == 2
    assert tuple(
        candle.timestamp
        for candle in feed.candles
    ) == (
        NOW - timedelta(minutes=30),
        NOW - timedelta(minutes=15),
    )
