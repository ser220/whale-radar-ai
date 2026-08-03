from __future__ import annotations

from telethon import TelegramClient

from .telegram_parser import ArkhamTelegramParser
from .store import ArkhamEventStore


class ArkhamTelegramListener:
    """
    Live Arkham Telegram ingestion.

    Telegram only.
    No trading logic.
    """

    def __init__(
        self,
        client: TelegramClient,
        parser: ArkhamTelegramParser | None = None,
        store: ArkhamEventStore | None = None,
    ) -> None:

        self._client = client

        self._parser = (
            parser
            if parser is not None
            else ArkhamTelegramParser()
        )

        self._store = (
            store
            if store is not None
            else ArkhamEventStore()
        )


    async def read_recent(
        self,
        limit: int = 10,
    ):

        events = []

        async for message in self._client.iter_messages(
            "ArkhamAlertBot",
            limit=limit,
        ):

            if not message.text:
                continue

            event = (
                self._parser
                .parse(message.text)
            )

            self._store.save(
                event
            )

            events.append(
                event
            )

        return events


__all__ = [
    "ArkhamTelegramListener",
]
