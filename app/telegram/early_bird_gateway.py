"""Shadow Telegram gateway for Early Bird test notifications."""

from typing import Callable


def send_early_bird_shadow_message(
    message: str,
    *,
    send_fn: Callable[[str], bool],
    enabled: bool = False,
) -> bool:
    """
    Send Early Bird Telegram output only when explicitly enabled.

    This gateway is shadow-only and has no decision influence.
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
    "send_early_bird_shadow_message",
]
