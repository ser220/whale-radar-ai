import pytest

from app.telegram.early_bird_gateway import (
    send_early_bird_shadow_message,
)


def test_shadow_gateway_disabled_by_default():

    sent = []

    result = send_early_bird_shadow_message(
        "TEST",
        send_fn=sent.append,
        enabled=False,
    )

    assert result is False
    assert sent == []


def test_shadow_gateway_sends_when_enabled():

    sent = []

    result = send_early_bird_shadow_message(
        "TEST MESSAGE",
        send_fn=sent.append,
        enabled=True,
    )

    assert result is True
    assert sent == ["TEST MESSAGE"]


def test_shadow_gateway_requires_callable_sender():

    with pytest.raises(
        TypeError,
        match="send_fn must be callable",
    ):
        send_early_bird_shadow_message(
            "TEST",
            send_fn=None,
            enabled=True,
        )
