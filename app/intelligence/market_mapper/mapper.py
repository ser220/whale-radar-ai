from __future__ import annotations

from app.intelligence.market import (
    MarketSnapshot,
)
from app.intelligence.candidate_decision_input import (
    CandidateDecisionInputProjection,
    CandidateDecisionInputStatus,
    CandidateDecisionInputVersion,
)


class MarketDecisionInputMapper:
    """
    Maps MarketSnapshot into Decision input boundary.

    Translation only.
    No decision logic allowed.
    """

    @staticmethod
    def from_snapshot(
        snapshot: MarketSnapshot,
    ) -> CandidateDecisionInputProjection:

        if not isinstance(
            snapshot,
            MarketSnapshot,
        ):
            raise TypeError(
                "snapshot must be MarketSnapshot"
            )

        return CandidateDecisionInputProjection(
            candidate_reference=(
                f"{snapshot.symbol}-candidate"
            ),
            intelligence_reference=(
                f"{snapshot.symbol}-market"
            ),
            status=(
                CandidateDecisionInputStatus.AVAILABLE
            ),
            version=(
                CandidateDecisionInputVersion.V1
            ),
            created_at=(
                snapshot.captured_at
            ),
        )
