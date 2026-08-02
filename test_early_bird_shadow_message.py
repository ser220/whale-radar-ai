from app.intelligence.early_bird.shadow_message import (
    build_shadow_message,
)


def test_build_shadow_message_contains_asset():
    message = build_shadow_message(
        asset="BTC",
        payload={
            "score": 80,
            "status": "AVAILABLE",
        },
    )

    assert "BTC" in message
    assert "80" in message


def test_build_shadow_message_is_text():
    message = build_shadow_message(
        asset="ETH",
        payload={},
    )

    assert isinstance(message, str)
