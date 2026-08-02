import pytest

from app.data.market.market_universe import (
    MarketUniverse,
)


def test_empty_universe_is_allowed():
    universe = MarketUniverse()

    assert universe.assets == ()


def test_universe_normalizes_assets():
    universe = MarketUniverse(
        assets=(
            "btc",
            "ETH",
            " sol ",
        )
    )

    assert universe.assets == (
        "BTC",
        "ETH",
        "SOL",
    )


def test_universe_rejects_empty_asset():
    with pytest.raises(
        ValueError,
        match="asset must not be empty",
    ):
        MarketUniverse(
            assets=("",)
        )
