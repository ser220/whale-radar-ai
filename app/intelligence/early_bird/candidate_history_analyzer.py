"""Analyze candidate observation history."""

from dataclasses import dataclass
from typing import Optional

from app.intelligence.early_bird.candidate_observation_history import (
    CandidateObservationHistory,
)

from app.intelligence.early_bird.candidate_behavior_score import (
    CandidateBehaviorScore,
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
    behavior_score: CandidateBehaviorScore | None = None


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

        positive_values = [
            value
            for value in factor_changes
            if value > 0
        ]

        negative_values = [
            abs(value)
            for value in factor_changes
            if value < 0
        ]

        strength_score = (
            min(
                sum(positive_values) / len(positive_values),
                100,
            )
            if positive_values
            else 0.0
        )

        decay_score = (
            min(
                sum(negative_values) / len(negative_values),
                100,
            )
            if negative_values
            else 0.0
        )

        confidence = min(
            (
                max(
                    positive_count,
                    negative_count,
                )
                / len(factor_changes)
            )
            * 100,
            100,
        )

        behavior_score = CandidateBehaviorScore(
            asset=history.asset,
            behavior_direction=behavior,
            strength_score=strength_score,
            decay_score=decay_score,
            confidence=confidence,
        )

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
            behavior_score=behavior_score,
        )


__all__ = [
    "CandidateHistoryAnalyzer",
    "CandidateHistoryAnalysis",
]
