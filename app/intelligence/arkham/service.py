from __future__ import annotations

from .models import ArkhamWhaleEvent
from .early_bird_candidate_builder import (
    ArkhamEarlyBirdCandidateBuilder,
)

from app.intelligence.early_bird.models import (
    EarlyBirdCandidate,
)


class ArkhamIntelligenceService:
    """
    Arkham intelligence orchestration boundary.

    Source -> Event -> Candidate.

    No decision logic.
    No execution logic.
    """

    def __init__(
        self,
        candidate_builder: (
            ArkhamEarlyBirdCandidateBuilder
            | None
        ) = None,
    ) -> None:

        self._candidate_builder = (
            candidate_builder
            if candidate_builder is not None
            else ArkhamEarlyBirdCandidateBuilder()
        )


    def build_candidate(
        self,
        event: ArkhamWhaleEvent,
    ) -> EarlyBirdCandidate:

        return (
            self._candidate_builder
            .build(event)
        )


    def build_candidates(
        self,
        events: list[ArkhamWhaleEvent],
    ) -> list[EarlyBirdCandidate]:

        return [
            self.build_candidate(event)
            for event in events
        ]


__all__ = [
    "ArkhamIntelligenceService",
]
