"""Early Bird Telegram sender adapter."""

from typing import Callable

from app.telegram.sender import send_telegram_message


def send_early_bird_telegram(
    message: str,
    *,
    enabled: bool = False,
    send_fn: Callable[[str], bool] = send_telegram_message,
) -> bool:
    """
    Send Early Bird shadow message through Telegram.

    Disabled by default. This is a notification-only path.
    """

    if not callable(send_fn):
        raise TypeError(
            "send_fn must be callable"
        )

    if not enabled:
        return False

    result = send_fn(message)

    return True if result is None else bool(result)


def send_early_bird_shadow(
    message: str,
    *,
    send_fn: Callable[[str], bool] = None,
) -> bool:
    """Send enabled Early Bird shadow message."""

    if not isinstance(message, str) or not message.strip():
        raise ValueError(
            "message must not be empty"
        )

    if send_fn is None:
        send_fn = send_telegram_message

    return send_early_bird_telegram(
        message,
        enabled=True,
        send_fn=send_fn,
    )


__all__ = [
    "send_early_bird_telegram",
    "send_early_bird_shadow",
]
