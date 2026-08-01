from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timezone

import pytest

from app.domain.market import (
    InstrumentType,
    MarketIdentity,
    MarketType,
    TradingInstrument,
)


def crypto_identity(
    instrument_type=InstrumentType.SPOT,
) -> MarketIdentity:
    return MarketIdentity(
        market_type=MarketType.CRYPTO,
        instrument_type=instrument_type,
        symbol="BTCUSDT",
        venue="BINANCE",
        currency="USDT",
        timezone="UTC",
    )


def test_fields_are_exact() -> None:
    assert [field.name for field in fields(TradingInstrument)] == [
        "identity",
        "base_symbol",
        "quote_symbol",
        "settlement_currency",
        "expiry",
    ]


def test_crypto_spot_instrument() -> None:
    instrument = TradingInstrument(
        identity=crypto_identity(),
        base_symbol="btc",
        quote_symbol="usdt",
        settlement_currency="usdt",
        expiry=None,
    )

    assert instrument.identity.symbol == "BTCUSDT"
    assert instrument.base_symbol == "BTC"
    assert instrument.quote_symbol == "USDT"
    assert instrument.settlement_currency == "USDT"
    assert instrument.expiry is None


def test_crypto_perpetual_instrument() -> None:
    instrument = TradingInstrument(
        identity=crypto_identity(
            InstrumentType.PERPETUAL,
        ),
        base_symbol="BTC",
        quote_symbol="USDT",
        settlement_currency="USDT",
        expiry=None,
    )

    assert instrument.identity.instrument_type is InstrumentType.PERPETUAL
    assert instrument.expiry is None


def test_equity_instrument() -> None:
    identity = MarketIdentity(
        market_type=MarketType.EQUITY,
        instrument_type=InstrumentType.STOCK,
        symbol="AAPL",
        venue="NASDAQ",
        currency="USD",
        timezone="America/New_York",
    )

    instrument = TradingInstrument(
        identity=identity,
        base_symbol="AAPL",
        quote_symbol=None,
        settlement_currency="USD",
        expiry=None,
    )

    assert instrument.base_symbol == "AAPL"
    assert instrument.quote_symbol is None


def test_etf_instrument() -> None:
    identity = MarketIdentity(
        market_type=MarketType.ETF,
        instrument_type=InstrumentType.ETF,
        symbol="SPY",
        venue="NYSE-ARCA",
        currency="USD",
        timezone="America/New_York",
    )

    instrument = TradingInstrument(
        identity=identity,
        base_symbol="SPY",
        quote_symbol=None,
        settlement_currency="USD",
        expiry=None,
    )

    assert instrument.identity.market_type is MarketType.ETF


def test_future_instrument_accepts_utc_expiry() -> None:
    identity = MarketIdentity(
        market_type=MarketType.COMMODITY,
        instrument_type=InstrumentType.FUTURE,
        symbol="GCZ26",
        venue="CME",
        currency="USD",
        timezone="America/Chicago",
    )
    expiry = datetime(
        2026,
        12,
        28,
        18,
        0,
        tzinfo=timezone.utc,
    )

    instrument = TradingInstrument(
        identity=identity,
        base_symbol="GC",
        quote_symbol=None,
        settlement_currency="USD",
        expiry=expiry,
    )

    assert instrument.expiry == expiry


def test_identity_requires_market_identity() -> None:
    with pytest.raises(
        TypeError,
        match="identity must be a MarketIdentity",
    ):
        TradingInstrument(
            identity="BTCUSDT",
            base_symbol="BTC",
            quote_symbol="USDT",
            settlement_currency="USDT",
            expiry=None,
        )


@pytest.mark.parametrize(
    "field_name",
    (
        "base_symbol",
        "settlement_currency",
    ),
)
def test_required_text_fields_reject_empty_values(
    field_name,
) -> None:
    values = {
        "identity": crypto_identity(),
        "base_symbol": "BTC",
        "quote_symbol": "USDT",
        "settlement_currency": "USDT",
        "expiry": None,
    }
    values[field_name] = "   "

    with pytest.raises(
        ValueError,
        match="{0} must not be empty".format(field_name),
    ):
        TradingInstrument(**values)


def test_quote_symbol_may_be_none() -> None:
    instrument = TradingInstrument(
        identity=crypto_identity(),
        base_symbol="BTC",
        quote_symbol=None,
        settlement_currency="USDT",
        expiry=None,
    )

    assert instrument.quote_symbol is None


def test_quote_symbol_rejects_empty_string() -> None:
    with pytest.raises(
        ValueError,
        match="quote_symbol must not be empty",
    ):
        TradingInstrument(
            identity=crypto_identity(),
            base_symbol="BTC",
            quote_symbol="   ",
            settlement_currency="USDT",
            expiry=None,
        )


def test_expiry_requires_timezone_aware_datetime() -> None:
    with pytest.raises(
        ValueError,
        match="expiry must be timezone aware",
    ):
        TradingInstrument(
            identity=crypto_identity(
                InstrumentType.FUTURE,
            ),
            base_symbol="BTC",
            quote_symbol="USDT",
            settlement_currency="USDT",
            expiry=datetime(2026, 12, 31),
        )


def test_instrument_is_frozen_and_hashable() -> None:
    first = TradingInstrument(
        identity=crypto_identity(),
        base_symbol="BTC",
        quote_symbol="USDT",
        settlement_currency="USDT",
        expiry=None,
    )
    second = TradingInstrument(
        identity=crypto_identity(),
        base_symbol="BTC",
        quote_symbol="USDT",
        settlement_currency="USDT",
        expiry=None,
    )

    assert first == second
    assert hash(first) == hash(second)

    with pytest.raises(FrozenInstanceError):
        first.base_symbol = "ETH"


def test_to_dict_is_exact() -> None:
    instrument = TradingInstrument(
        identity=crypto_identity(),
        base_symbol="BTC",
        quote_symbol="USDT",
        settlement_currency="USDT",
        expiry=None,
    )

    assert instrument.to_dict() == {
        "identity": instrument.identity.to_dict(),
        "base_symbol": "BTC",
        "quote_symbol": "USDT",
        "settlement_currency": "USDT",
        "expiry": None,
    }


def test_from_dict_round_trip() -> None:
    instrument = TradingInstrument(
        identity=crypto_identity(),
        base_symbol="BTC",
        quote_symbol="USDT",
        settlement_currency="USDT",
        expiry=None,
    )

    assert TradingInstrument.from_dict(
        instrument.to_dict()
    ) == instrument


def test_public_type_hints_are_python_39_compatible() -> None:
    from typing import get_type_hints

    assert get_type_hints(TradingInstrument) == {
        "identity": MarketIdentity,
        "base_symbol": str,
        "quote_symbol": __import__("typing").Optional[str],
        "settlement_currency": str,
        "expiry": __import__("typing").Optional[datetime],
    }


def test_from_dict_rejects_unknown_fields() -> None:
    instrument = TradingInstrument(
        identity=crypto_identity(),
        base_symbol="BTC",
        quote_symbol="USDT",
        settlement_currency="USDT",
        expiry=None,
    )
    payload = instrument.to_dict()
    payload["unexpected"] = "value"

    with pytest.raises(
        ValueError,
        match="unknown fields",
    ):
        TradingInstrument.from_dict(payload)


def test_from_dict_rejects_missing_fields() -> None:
    instrument = TradingInstrument(
        identity=crypto_identity(),
        base_symbol="BTC",
        quote_symbol="USDT",
        settlement_currency="USDT",
        expiry=None,
    )
    payload = instrument.to_dict()
    del payload["settlement_currency"]

    with pytest.raises(
        ValueError,
        match="missing fields: settlement_currency",
    ):
        TradingInstrument.from_dict(payload)


def test_from_dict_requires_mapping() -> None:
    with pytest.raises(
        TypeError,
        match="trading instrument payload must be a mapping",
    ):
        TradingInstrument.from_dict(None)


def test_expiry_normalizes_to_utc() -> None:
    from datetime import timedelta

    identity = MarketIdentity(
        market_type=MarketType.COMMODITY,
        instrument_type=InstrumentType.FUTURE,
        symbol="GCZ26",
        venue="CME",
        currency="USD",
        timezone="America/Chicago",
    )
    expiry = datetime(
        2026,
        12,
        28,
        12,
        0,
        tzinfo=timezone(timedelta(hours=-6)),
    )

    instrument = TradingInstrument(
        identity=identity,
        base_symbol="GC",
        quote_symbol=None,
        settlement_currency="USD",
        expiry=expiry,
    )

    assert instrument.expiry == datetime(
        2026,
        12,
        28,
        18,
        0,
        tzinfo=timezone.utc,
    )
