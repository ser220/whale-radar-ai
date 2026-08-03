from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import os


@dataclass(frozen=True)
class ArkhamConfig:
    """
    Arkham API connection configuration.

    No API logic.
    """

    api_key: Optional[str] = None

    base_url: str = (
        "https://api.arkhamintelligence.com"
    )

    @classmethod
    def from_env(cls) -> "ArkhamConfig":

        return cls(
            api_key=os.getenv(
                "ARKHAM_API_KEY"
            ),
            base_url=os.getenv(
                "ARKHAM_BASE_URL",
                "https://api.arkhamintelligence.com",
            ),
        )


__all__ = [
    "ArkhamConfig",
]
