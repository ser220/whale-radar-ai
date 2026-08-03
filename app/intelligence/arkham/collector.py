from __future__ import annotations

from .client import ArkhamClient
from .parser import ArkhamEventParser
from .alert_policy import ArkhamAlertPolicy
from .store import ArkhamEventStore
from .models import ArkhamWhaleEvent


class ArkhamCollector:
    """
    Collects and stores Arkham whale events.
    """

    def __init__(
        self,
        client: ArkhamClient | None = None,
        parser: ArkhamEventParser | None = None,
        policy: ArkhamAlertPolicy | None = None,
        store: ArkhamEventStore | None = None,
    ) -> None:

        self._client = (
            client
            if client is not None
            else ArkhamClient()
        )

        self._parser = (
            parser
            if parser is not None
            else ArkhamEventParser()
        )

        self._policy = (
            policy
            if policy is not None
            else ArkhamAlertPolicy()
        )

        self._store = (
            store
            if store is not None
            else ArkhamEventStore()
        )

    def collect(
        self,
    ) -> list[ArkhamWhaleEvent]:

        accepted = []

        payloads = (
            self._client
            .fetch_whale_events()
        )

        for payload in payloads:

            event = (
                self._parser
                .parse(payload)
            )

            if self._policy.evaluate(event):

                self._store.save(event)

                accepted.append(event)

        return accepted


__all__ = [
    "ArkhamCollector",
]
