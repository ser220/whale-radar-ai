from __future__ import annotations

from .telegram_listener import (
    ArkhamTelegramListener,
)

from .models import ArkhamWhaleEvent


class ArkhamTelegramCollectorAdapter:
    """
    Adapter between Telegram listener
    and Arkham worker boundary.

    No intelligence logic.
    """

    def __init__(
        self,
        listener: ArkhamTelegramListener,
    ) -> None:

        self._listener = listener


    def collect(
        self,
    ) -> list[ArkhamWhaleEvent]:

        import asyncio

        return asyncio.run(
            self._listener.read_recent()
        )


__all__ = [
    "ArkhamTelegramCollectorAdapter",
]
