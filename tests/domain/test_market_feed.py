from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timezone

import pytest

from app.domain.candle import Candle
from app.data.market import MarketFeed
from app.domain.market import (
    InstrumentType,
    MarketIdentity,
    MarketType,
    TradingInstrument,
)
from app.intelligence.data_sources import (
    DataSourceCategory,
    DataSourceType,
    DerivativesSnapshot,
    MarketSnapshot,
    OpenInterestSnapshot,
)


CAPTURED_AT = datetime(
    2026,
    8,
    1,
    22,
    45,
    tzinfo=timezone.utc,
)


def build_instrument() -> TradingInstrument:
    identity = MarketIdentity(
        market_type=MarketType.CRYPTO,
        instrument_type=InstrumentType.SPOT,
        symbol="BTCUSDT",
        venue="BINANCE",
        currency="USDT",
        timezone="UTC",
    )
    return TradingInstrument(
        identity=identity,
        base_symbol="BTC",
        quote_symbol="USDT",
        settlement_currency="USDT",
        expiry=None,
    )


def build_candles():
    return (
        Candle(
            timestamp=datetime(
                2026,
                8,
                1,
                22,
                30,
                tzinfo=timezone.utc,
            ),
            open=62800,
            high=62900,
            low=62750,
            close=62850,
            volume=100,
        ),
        Candle(
            timestamp=CAPTURED_AT,
            open=62850,
            high=62950,
            low=62800,
            close=62900,
            volume=120,
        ),
    )


def build_market_snapshot() -> MarketSnapshot:
    return MarketSnapshot(
        source_category=DataSourceCategory.EXCHANGE,
        source=DataSourceType.BINANCE,
        symbol="BTCUSDT",
        price=62900,
        volume_24h=7552.1389,
        change_24h=-0.191,
        captured_at=CAPTURED_AT,
    )


def build_open_interest_snapshot() -> OpenInterestSnapshot:
    return OpenInterestSnapshot(
        source_category=DataSourceCategory.DERIVATIVES,
        source=DataSourceType.COINGLASS,
        asset="BTC",
        total_open_interest_usd=16577342768.52,
        execution_open_interest_usd=12871103626.94,
        exchange_count=4,
        largest_market="Binance",
        captured_at=CAPTURED_AT,
    )


def build_derivatives_snapshot() -> DerivativesSnapshot:
    return DerivativesSnapshot(
        source_category=DataSourceCategory.DERIVATIVES,
        source=DataSourceType.COINGLASS,
        symbol="BTCUSDT",
        open_interest=1000000,
        funding_rate=0.0001,
        long_short_ratio=1.05,
        liquidation_volume=250000,
        captured_at=CAPTURED_AT,
    )


def build_feed(**overrides) -> MarketFeed:
    values = {
        "instrument": build_instrument(),
        "candles": build_candles(),
        "market_snapshot": build_market_snapshot(),
        "derivatives_snapshot": build_derivatives_snapshot(),
        "open_interest_snapshot": build_open_interest_snapshot(),
        "captured_at": CAPTURED_AT,
    }
    values.update(overrides)
    return MarketFeed(**values)


def test_fields_are_exact() -> None:
    assert [field.name for field in fields(MarketFeed)] == [
        "instrument",
        "candles",
        "market_snapshot",
        "derivatives_snapshot",
        "open_interest_snapshot",
        "captured_at",
    ]


def test_feed_preserves_normalized_market_data() -> None:
    feed = build_feed()

    assert feed.instrument.identity.symbol == "BTCUSDT"
    assert len(feed.candles) == 2
    assert feed.market_snapshot.price == 62900.0
    assert feed.derivatives_snapshot.open_interest == 1000000.0
    assert (
        feed.open_interest_snapshot.total_open_interest_usd
        == 16577342768.52
    )
    assert feed.captured_at == CAPTURED_AT


def test_open_interest_snapshot_may_be_none() -> None:
    feed = build_feed(open_interest_snapshot=None)

    assert feed.open_interest_snapshot is None


def test_derivatives_snapshot_may_be_none() -> None:
    feed = build_feed(derivatives_snapshot=None)

    assert feed.derivatives_snapshot is None


def test_feed_is_frozen_hashable_and_deterministic() -> None:
    first = build_feed()
    second = build_feed()

    assert first == second
    assert hash(first) == hash(second)

    with pytest.raises(FrozenInstanceError):
        first.captured_at = datetime.now(timezone.utc)


def test_candles_normalize_to_tuple() -> None:
    feed = build_feed(candles=list(build_candles()))

    assert isinstance(feed.candles, tuple)


def test_candles_must_not_be_empty() -> None:
    with pytest.raises(
        ValueError,
        match="candles must not be empty",
    ):
        build_feed(candles=())


def test_candles_require_candle_instances() -> None:
    with pytest.raises(
        TypeError,
        match="candles must contain Candle instances",
    ):
        build_feed(candles=("invalid",))


def test_instrument_requires_trading_instrument() -> None:
    with pytest.raises(
        TypeError,
        match="instrument must be a TradingInstrument",
    ):
        build_feed(instrument="BTCUSDT")


def test_market_snapshot_requires_market_snapshot() -> None:
    with pytest.raises(
        TypeError,
        match="market_snapshot must be a MarketSnapshot",
    ):
        build_feed(market_snapshot={})


def test_open_interest_snapshot_requires_correct_type() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "open_interest_snapshot must be an "
            "OpenInterestSnapshot or None"
        ),
    ):
        build_feed(open_interest_snapshot={})


def test_derivatives_snapshot_requires_correct_type() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "derivatives_snapshot must be a "
            "DerivativesSnapshot or None"
        ),
    ):
        build_feed(derivatives_snapshot={})


def test_symbol_consistency_is_enforced() -> None:
    snapshot = MarketSnapshot(
        source_category=DataSourceCategory.EXCHANGE,
        source=DataSourceType.BINANCE,
        symbol="ETHUSDT",
        price=1848,
        volume_24h=1000,
        change_24h=-0.5,
        captured_at=CAPTURED_AT,
    )

    with pytest.raises(
        ValueError,
        match="market snapshot symbol must match instrument symbol",
    ):
        build_feed(market_snapshot=snapshot)


def test_derivatives_symbol_consistency_is_enforced() -> None:
    snapshot = DerivativesSnapshot(
        source_category=DataSourceCategory.DERIVATIVES,
        source=DataSourceType.COINGLASS,
        symbol="ETHUSDT",
        open_interest=100000,
        funding_rate=0.0002,
        long_short_ratio=1.10,
        liquidation_volume=50000,
        captured_at=CAPTURED_AT,
    )

    with pytest.raises(
        ValueError,
        match="derivatives snapshot symbol must match instrument symbol",
    ):
        build_feed(derivatives_snapshot=snapshot)


def test_captured_at_requires_datetime() -> None:
    with pytest.raises(
        TypeError,
        match="captured_at must be a datetime",
    ):
        build_feed(captured_at="2026-08-01T22:45:00Z")


def test_captured_at_requires_timezone() -> None:
    with pytest.raises(
        ValueError,
        match="captured_at must be timezone aware",
    ):
        build_feed(captured_at=datetime(2026, 8, 1, 22, 45))


def test_to_dict_is_exact() -> None:
    feed = build_feed()

    assert feed.to_dict() == {
        "instrument": feed.instrument.to_dict(),
        "candles": [
            candle.to_dict()
            for candle in feed.candles
        ],
        "market_snapshot": feed.market_snapshot.to_dict(),
        "derivatives_snapshot": (
            feed.derivatives_snapshot.to_dict()
        ),
        "open_interest_snapshot": (
            feed.open_interest_snapshot.to_dict()
        ),
        "captured_at": CAPTURED_AT.isoformat(),
    }


def test_from_dict_round_trip() -> None:
    feed = build_feed()

    assert MarketFeed.from_dict(feed.to_dict()) == feed


def test_from_dict_rejects_unknown_fields() -> None:
    payload = build_feed().to_dict()
    payload["unexpected"] = "value"

    with pytest.raises(
        ValueError,
        match="unknown fields",
    ):
        MarketFeed.from_dict(payload)


def test_from_dict_rejects_missing_fields() -> None:
    payload = build_feed().to_dict()
    del payload["candles"]

    with pytest.raises(
        ValueError,
        match="missing fields: candles",
    ):
        MarketFeed.from_dict(payload)


def test_public_export_in_data_market() -> None:
    import app.data.market

    assert "MarketFeed" in app.data.market.__all__


def test_public_type_hints_are_python_39_compatible() -> None:
    from typing import Optional, Tuple, get_type_hints

    assert get_type_hints(MarketFeed) == {
        "instrument": TradingInstrument,
        "candles": Tuple[Candle, ...],
        "market_snapshot": MarketSnapshot,
        "derivatives_snapshot": Optional[DerivativesSnapshot],
        "open_interest_snapshot": Optional[OpenInterestSnapshot],
        "captured_at": datetime,
    }


def test_from_dict_requires_mapping() -> None:
    with pytest.raises(
        TypeError,
        match="market feed payload must be a mapping",
    ):
        MarketFeed.from_dict(None)


def test_captured_at_normalizes_to_utc() -> None:
    from datetime import timedelta

    captured_at = datetime(
        2026,
        8,
        1,
        16,
        45,
        tzinfo=timezone(timedelta(hours=-6)),
    )

    feed = build_feed(captured_at=captured_at)

    assert feed.captured_at == CAPTURED_AT


def test_market_feed_has_no_runtime_layer_imports() -> None:
    import ast
    from pathlib import Path

    path = Path("app/data/market/feed.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))

    forbidden_prefixes = (
        "app.telegram",
        "app.execution",
        "app.backtest",
        "app.simulation",
        "app.services",
        "app.sources",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith(forbidden_prefixes)

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            assert not module.startswith(forbidden_prefixes)
