import pytest

from app.data.market.market_universe_provider import (
    MarketUniverseProvider,
)


def test_provider_requires_build_method():
    provider = MarketUniverseProvider()

    with pytest.raises(
        NotImplementedError,
    ):
        provider.build()


def test_provider_contract_is_callable():
    provider = MarketUniverseProvider()

    assert callable(provider.build)
