from app.telegram.early_bird_sender import (
    send_early_bird_shadow,
)


def test_shadow_sender_sends_notification(
    monkeypatch,
):
    calls = []

    def fake_sender(message):
        calls.append(message)
        return True

    monkeypatch.setattr(
        "app.telegram.early_bird_sender.send_telegram_message",
        fake_sender,
    )

    result = send_early_bird_shadow(
        "🧠 Early Bird Shadow\nBTC",
    )

    assert result is True
    assert calls == [
        "🧠 Early Bird Shadow\nBTC"
    ]


def test_empty_message_is_rejected():
    import pytest

    with pytest.raises(
        ValueError,
        match="message must not be empty",
    ):
        send_early_bird_shadow("")
