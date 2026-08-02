from app.data.market.market_universe import (
    MarketUniverse,
)
from app.data.market.static_market_universe_provider import (
    StaticMarketUniverseProvider,
)


def test_static_provider_returns_market_universe():
    provider = StaticMarketUniverseProvider(
        assets=(
            "BTC",
            "ETH",
            "SOL",
        )
    )

    result = provider.build()

    assert isinstance(
        result,
        MarketUniverse,
    )

    assert result.assets == (
        "BTC",
        "ETH",
        "SOL",
    )


def test_static_provider_normalizes_assets():
    provider = StaticMarketUniverseProvider(
        assets=(
            "btc",
            " eth ",
        )
    )

    assert provider.build().assets == (
        "BTC",
        "ETH",
    )
