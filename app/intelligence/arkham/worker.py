from __future__ import annotations

from .collector import ArkhamCollector


class ArkhamWorker:
    """
    Background worker boundary.

    Scheduling belongs outside.
    No trading logic.
    """

    def __init__(
        self,
        collector: ArkhamCollector,
    ) -> None:

        self._collector = collector


    def run_once(self):

        return (
            self._collector
            .collect()
        )


__all__ = [
    "ArkhamWorker",
]
