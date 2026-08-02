"""Environment flag for Early Bird Telegram shadow notifications."""

import os


_TRUE_VALUES = {
    "1",
    "true",
    "yes",
    "on",
    "enabled",
}


def early_bird_telegram_enabled() -> bool:
    """
    Return True only when explicit shadow Telegram flag is enabled.
    """

    value = os.getenv(
        "EARLY_BIRD_TELEGRAM_SHADOW",
        "",
    )

    return (
        value.strip().lower()
        in _TRUE_VALUES
    )


__all__ = [
    "early_bird_telegram_enabled",
]
