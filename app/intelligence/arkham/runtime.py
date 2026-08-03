from __future__ import annotations

from .collector import ArkhamCollector
from .service import ArkhamIntelligenceService

from app.intelligence.early_bird.models import (
    EarlyBirdCandidate,
)


class ArkhamRuntime:
    """
    Runtime orchestration boundary.

    Collects Arkham events
    and produces intelligence candidates.

    No decision logic.
    No execution logic.
    """

    def __init__(
        self,
        collector: ArkhamCollector,
        intelligence: ArkhamIntelligenceService | None = None,
    ) -> None:

        self._collector = collector

        self._intelligence = (
            intelligence
            if intelligence is not None
            else ArkhamIntelligenceService()
        )


    def run_once(
        self,
    ) -> list[EarlyBirdCandidate]:

        events = (
            self._collector
            .collect()
        )

        return (
            self._intelligence
            .build_candidates(events)
        )


__all__ = [
    "ArkhamRuntime",
]
