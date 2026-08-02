from app.intelligence.early_bird.exchange_adapter_registry import (
    ExchangeAdapterRegistry,
)


class DummyAdapter:
    pass



def test_register_and_get_adapter():

    registry = ExchangeAdapterRegistry()

    adapter = DummyAdapter()

    registry.register(
        "OKX",
        adapter,
    )

    result = registry.get(
        "OKX"
    )

    assert result is adapter



def test_unknown_exchange():

    registry = ExchangeAdapterRegistry()

    try:

        registry.get(
            "UNKNOWN"
        )

    except ValueError as exc:
        assert "exchange" in str(exc)

    else:
        raise AssertionError(
            "Expected ValueError"
        )
