from __future__ import annotations

from datetime import datetime, timezone

from .enums import (
    ArkhamChain,
    ArkhamEventType,
    ArkhamFlowDirection,
)

from .models import (
    ArkhamWhaleEvent,
)


class ArkhamEventParser:
    """
    Converts Arkham API payload
    into internal whale event contract.

    No intelligence logic.
    """

    def parse(
        self,
        payload: dict,
    ) -> ArkhamWhaleEvent:

        if not isinstance(
            payload,
            dict,
        ):
            raise TypeError(
                "payload must be dict"
            )

        return ArkhamWhaleEvent(
            event_id=payload["id"],
            chain=ArkhamChain(
                payload["chain"]
            ),
            event_type=ArkhamEventType(
                payload["event_type"]
            ),
            direction=ArkhamFlowDirection(
                payload["direction"]
            ),
            asset=payload["asset"],
            amount_usd=payload["amount_usd"],
            source_entity=payload["from"],
            destination_entity=payload["to"],
            observed_at=datetime.fromisoformat(
                payload["timestamp"]
            ).astimezone(
                timezone.utc
            ),
        )


__all__ = [
    "ArkhamEventParser",
]
