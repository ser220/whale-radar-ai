from __future__ import annotations

from typing import Any


class ArkhamClient:
    """
    Arkham API client boundary.

    Converts external API data later.
    No intelligence logic.
    """

    def fetch_whale_events(
        self,
    ) -> list[dict[str, Any]]:
        """
        Fetch raw Arkham events.

        Real API implementation later.
        """

        raise NotImplementedError(
            "Arkham API client not implemented"
        )


__all__ = [
    "ArkhamClient",
]
