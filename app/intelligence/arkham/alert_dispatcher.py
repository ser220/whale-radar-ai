from __future__ import annotations

from .models import ArkhamWhaleEvent


class ArkhamAlertDispatcher:
    """
    Dispatches Arkham alerts.

    Delivery boundary only.
    No intelligence logic.
    """

    def __init__(self) -> None:
        self._sent = []

    def dispatch(
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

        self._sent.append(event)


    def sent_events(self):

        return tuple(
            self._sent
        )


__all__ = [
    "ArkhamAlertDispatcher",
]
