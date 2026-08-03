from __future__ import annotations

from app.intelligence.early_bird.models import (
    EarlyBirdCandidate,
)

from .runtime import ArkhamRuntime


class ArkhamCandidateProvider:
    """
    Early Bird provider boundary.

    Produces provider-neutral candidates.

    No ranking.
    No decision logic.
    """

    def __init__(
        self,
        runtime: ArkhamRuntime,
    ) -> None:

        self._runtime = runtime


    def collect_candidates(
        self,
    ) -> list[EarlyBirdCandidate]:

        return (
            self._runtime
            .run_once()
        )


__all__ = [
    "ArkhamCandidateProvider",
]
