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


__all__ = [
    "send_early_bird_telegram",
]
