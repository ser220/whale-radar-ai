from __future__ import annotations

from .models import ArkhamWhaleEvent
from .enums import (
    ArkhamFlowDirection,
)


class ArkhamAlertPolicy:
    """
    Evaluates Arkham whale events.

    Alerting only.
    No trading decision logic.
    """

    MIN_ALERT_USD = 10_000_000

    def evaluate(
        self,
        event: ArkhamWhaleEvent,
    ) -> bool:

        if not isinstance(
            event,
            ArkhamWhaleEvent,
        ):
            raise TypeError(
                "event must be ArkhamWhaleEvent"
            )

        if (
            event.amount_usd
            < self.MIN_ALERT_USD
        ):
            return False

        return True


__all__ = [
    "ArkhamAlertPolicy",
]
