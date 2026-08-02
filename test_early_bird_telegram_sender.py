from app.telegram.early_bird_sender import (
    send_early_bird_telegram,
)


def test_sender_disabled_without_flag():
    calls = []

    result = send_early_bird_telegram(
        "TEST",
        enabled=False,
        send_fn=calls.append,
    )

    assert result is False
    assert calls == []


def test_sender_calls_real_sender_when_enabled():
    calls = []

    result = send_early_bird_telegram(
        "TEST MESSAGE",
        enabled=True,
        send_fn=calls.append,
    )

    assert result is True
    assert calls == ["TEST MESSAGE"]
