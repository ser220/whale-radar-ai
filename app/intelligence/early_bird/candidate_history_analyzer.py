"""Analyze candidate observation history."""

from dataclasses import dataclass
from typing import Optional

from app.intelligence.early_bird.candidate_observation_history import (
    CandidateObservationHistory,
)


@dataclass(frozen=True)
class CandidateHistoryAnalysis:
    """Derived behaviour metrics from candidate history."""

    asset: str
    quality_change: Optional[float]
    quality_direction: str
    open_interest_change: Optional[float] = None
    volume_expansion_change: Optional[float] = None
    funding_divergence_change: Optional[float] = None
    momentum_shift_change: Optional[float] = None
    data_completeness_change: Optional[float] = None
    positive_factor_count: int = 0
    negative_factor_count: int = 0
    behavior_direction: str = "insufficient"


class CandidateHistoryAnalyzer:
    """Calculate basic candidate behaviour trends."""

    def analyze(
        self,
        history: CandidateObservationHistory,
    ) -> CandidateHistoryAnalysis:

        observations = history.observations

        if len(observations) < 2:
            return CandidateHistoryAnalysis(
                asset=history.asset,
                quality_change=None,
                quality_direction="insufficient",
            )

        first = observations[0]
        last = observations[-1]

        change = (
            last.quality
            - first.quality
        )

        if change > 0:
            direction = "rising"
        elif change < 0:
            direction = "falling"
        else:
            direction = "stable"

        open_interest_change = (
            last.open_interest_change_score
            - first.open_interest_change_score
        )

        volume_expansion_change = (
            last.volume_expansion_score
            - first.volume_expansion_score
        )

        funding_divergence_change = (
            last.funding_divergence_score
            - first.funding_divergence_score
        )

        momentum_shift_change = (
            last.momentum_shift_score
            - first.momentum_shift_score
        )

        data_completeness_change = (
            last.data_completeness_score
            - first.data_completeness_score
        )

        factor_changes = (
            open_interest_change,
            volume_expansion_change,
            funding_divergence_change,
            momentum_shift_change,
            data_completeness_change,
        )

        positive_count = sum(
            1
            for value in factor_changes
            if value > 0
        )

        negative_count = sum(
            1
            for value in factor_changes
            if value < 0
        )

        if positive_count > negative_count:
            behavior = "strengthening"
        elif negative_count > positive_count:
            behavior = "weakening"
        else:
            behavior = "stable"

        return CandidateHistoryAnalysis(
            asset=history.asset,
            quality_change=change,
            quality_direction=direction,
            open_interest_change=open_interest_change,
            volume_expansion_change=volume_expansion_change,
            funding_divergence_change=funding_divergence_change,
            momentum_shift_change=momentum_shift_change,
            data_completeness_change=data_completeness_change,
            positive_factor_count=positive_count,
            negative_factor_count=negative_count,
            behavior_direction=behavior,
        )


__all__ = [
    "CandidateHistoryAnalyzer",
    "CandidateHistoryAnalysis",
]
