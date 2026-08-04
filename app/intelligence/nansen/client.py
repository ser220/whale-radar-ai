from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping


class NansenClient(ABC):
    """
    Boundary for Nansen data access.

    Responsible only for retrieving
    external Nansen intelligence data.

    No mapping.
    No ranking.
    No decision logic.
    """

    @abstractmethod
    def get_smart_money_netflow(
        self,
        chain: str,
    ) -> list[Mapping[str, Any]]:
        """
        Retrieve Smart Money netflow payloads.
        """
        raise NotImplementedError
