from __future__ import annotations

from .models import ArkhamWhaleEvent


class ArkhamEventStore:
    """
    Stores Arkham whale events.

    Storage boundary only.
    No intelligence logic.
    """

    def __init__(self) -> None:
        self._events: dict[str, ArkhamWhaleEvent] = {}

    def save(
        self,
        event: ArkhamWhaleEvent,
    ) -> None:

        if not isinstance(
            event,
            ArkhamWhaleEvent,
        ):
            raise TypeError(
                "event must be ArkhamWhaleEvent"
            )

        self._events[
            event.event_id
        ] = event


    def get(
        self,
        event_id: str,
    ) -> ArkhamWhaleEvent | None:

        return self._events.get(
            event_id
        )


    def all(
        self,
    ) -> tuple[ArkhamWhaleEvent, ...]:

        return tuple(
            self._events.values()
        )


__all__ = [
    "ArkhamEventStore",
]
