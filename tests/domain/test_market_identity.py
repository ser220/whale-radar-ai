from dataclasses import FrozenInstanceError, fields

import pytest

from app.domain.market import (
    InstrumentType,
    MarketIdentity,
    MarketType,
)


def build_identity(**overrides) -> MarketIdentity:
    values = {
        "market_type": MarketType.CRYPTO,
        "instrument_type": InstrumentType.SPOT,
        "symbol": "BTCUSDT",
        "venue": "BINANCE",
        "currency": "USDT",
        "timezone": "UTC",
    }
    values.update(overrides)
    return MarketIdentity(**values)


def test_market_type_members_are_stable() -> None:
    assert {
        item.name: item.value
        for item in MarketType
    } == {
        "CRYPTO": "CRYPTO",
        "EQUITY": "EQUITY",
        "ETF": "ETF",
        "INDEX": "INDEX",
        "COMMODITY": "COMMODITY",
        "FOREX": "FOREX",
        "FIXED_INCOME": "FIXED_INCOME",
        "UNKNOWN": "UNKNOWN",
    }


def test_instrument_type_members_are_stable() -> None:
    assert {
        item.name: item.value
        for item in InstrumentType
    } == {
        "SPOT": "SPOT",
        "PERPETUAL": "PERPETUAL",
        "STOCK": "STOCK",
        "ETF": "ETF",
        "INDEX": "INDEX",
        "FUTURE": "FUTURE",
        "OPTION": "OPTION",
        "FOREX_PAIR": "FOREX_PAIR",
        "BOND": "BOND",
        "UNKNOWN": "UNKNOWN",
    }


def test_fields_are_exact() -> None:
    assert [field.name for field in fields(MarketIdentity)] == [
        "market_type",
        "instrument_type",
        "symbol",
        "venue",
        "currency",
        "timezone",
    ]


def test_crypto_spot_identity() -> None:
    identity = build_identity()

    assert identity.market_type is MarketType.CRYPTO
    assert identity.instrument_type is InstrumentType.SPOT
    assert identity.symbol == "BTCUSDT"
    assert identity.venue == "BINANCE"
    assert identity.currency == "USDT"
    assert identity.timezone == "UTC"


def test_equity_identity() -> None:
    identity = build_identity(
        market_type=MarketType.EQUITY,
        instrument_type=InstrumentType.STOCK,
        symbol="aapl",
        venue="nasdaq",
        currency="usd",
        timezone="America/New_York",
    )

    assert identity.symbol == "AAPL"
    assert identity.venue == "NASDAQ"
    assert identity.currency == "USD"
    assert identity.timezone == "America/New_York"


def test_etf_identity() -> None:
    identity = build_identity(
        market_type=MarketType.ETF,
        instrument_type=InstrumentType.ETF,
        symbol="spy",
        venue="nyse-arca",
        currency="usd",
        timezone="America/New_York",
    )

    assert identity.symbol == "SPY"
    assert identity.venue == "NYSE-ARCA"


def test_identity_is_frozen_hashable_and_deterministic() -> None:
    first = build_identity()
    second = build_identity()

    assert first == second
    assert hash(first) == hash(second)
    assert {first, second} == {first}

    with pytest.raises(FrozenInstanceError):
        first.symbol = "ETHUSDT"


@pytest.mark.parametrize(
    "field_name",
    (
        "symbol",
        "venue",
        "currency",
        "timezone",
    ),
)
def test_required_text_fields_reject_empty_values(field_name) -> None:
    with pytest.raises(
        ValueError,
        match="{0} must not be empty".format(field_name),
    ):
        build_identity(**{field_name: "   "})


def test_market_type_requires_enum() -> None:
    with pytest.raises(
        TypeError,
        match="market_type must be a MarketType",
    ):
        build_identity(market_type="CRYPTO")


def test_instrument_type_requires_enum() -> None:
    with pytest.raises(
        TypeError,
        match="instrument_type must be an InstrumentType",
    ):
        build_identity(instrument_type="SPOT")


def test_to_dict_is_exact_and_serializable() -> None:
    identity = build_identity()

    assert identity.to_dict() == {
        "market_type": "CRYPTO",
        "instrument_type": "SPOT",
        "symbol": "BTCUSDT",
        "venue": "BINANCE",
        "currency": "USDT",
        "timezone": "UTC",
    }


def test_from_dict_round_trip() -> None:
    identity = build_identity()

    assert MarketIdentity.from_dict(identity.to_dict()) == identity


def test_from_dict_rejects_unknown_fields() -> None:
    payload = build_identity().to_dict()
    payload["unexpected"] = "value"

    with pytest.raises(
        ValueError,
        match="unknown fields",
    ):
        MarketIdentity.from_dict(payload)


def test_public_exports_are_exact() -> None:
    import app.domain.market

    assert app.domain.market.__all__ == [
        "InstrumentType",
        "MarketIdentity",
        "MarketType",
        "TradingInstrument",
    ]


def test_public_type_hints_are_python_39_compatible() -> None:
    from typing import get_type_hints

    assert get_type_hints(MarketIdentity) == {
        "market_type": MarketType,
        "instrument_type": InstrumentType,
        "symbol": str,
        "venue": str,
        "currency": str,
        "timezone": str,
    }


def test_from_dict_rejects_missing_fields() -> None:
    payload = build_identity().to_dict()
    del payload["venue"]

    with pytest.raises(
        ValueError,
        match="missing fields: venue",
    ):
        MarketIdentity.from_dict(payload)


def test_from_dict_requires_mapping() -> None:
    with pytest.raises(
        TypeError,
        match="market identity payload must be a mapping",
    ):
        MarketIdentity.from_dict(None)


def test_market_domain_has_no_runtime_layer_imports() -> None:
    import ast
    from pathlib import Path

    package_directory = Path("app/domain/market")
    forbidden_prefixes = (
        "app.intelligence",
        "app.decision",
        "app.execution",
        "app.backtest",
        "app.simulation",
        "app.sources",
        "app.telegram",
    )

    for path in package_directory.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))

        for node in ast.walk(tree):
            module = None

            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith(forbidden_prefixes)

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                assert not module.startswith(forbidden_prefixes)
