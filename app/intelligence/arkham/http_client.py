from __future__ import annotations

from typing import Any, Protocol

from .config import ArkhamConfig


class HttpTransport(Protocol):

    def get(
        self,
        url: str,
        headers: dict[str, str],
        timeout: int,
    ) -> Any:
        ...


class ArkhamHttpClient:
    """
    Real Arkham API boundary.

    No parsing.
    No intelligence logic.
    """

    def __init__(
        self,
        config: ArkhamConfig,
        transport: HttpTransport,
    ) -> None:

        self._config = config
        self._transport = transport

    def fetch_whale_events(
        self,
    ) -> list[dict]:

        if not self._config.api_key:
            raise ValueError(
                "ARKHAM_API_KEY is required"
            )

        response = self._transport.get(
            self._config.base_url,
            headers={
                "Authorization":
                    f"Bearer {self._config.api_key}"
            },
            timeout=10,
        )

        return response.json()


__all__ = [
    "ArkhamHttpClient",
]
