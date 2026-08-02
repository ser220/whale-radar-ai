"""Adapter from Early Bird candidate into observation contract."""

from app.intelligence.early_bird.candidate_observation import (
    EarlyBirdCandidateObservation,
)


_OBSERVATION_FIELDS = (
    "asset",
    "observed_at",
    "quality",
    "whale_activity_score",
    "open_interest_change_score",
    "funding_divergence_score",
    "volume_expansion_score",
    "relative_strength_score",
    "liquidity_event_score",
    "structure_event_score",
    "momentum_shift_score",
    "freshness_score",
    "data_completeness_score",
)


def build_candidate_observation(
    candidate,
) -> EarlyBirdCandidateObservation:
    """
    Convert one Early Bird candidate into an immutable observation.
    """

    missing_fields = tuple(
        field_name
        for field_name in _OBSERVATION_FIELDS
        if not hasattr(candidate, field_name)
    )

    if missing_fields:
        raise TypeError(
            "candidate must provide fields: {0}".format(
                ", ".join(missing_fields)
            )
        )

    return EarlyBirdCandidateObservation(
        asset=candidate.asset,
        observed_at=candidate.observed_at,
        quality=candidate.quality,
        whale_activity_score=(
            candidate.whale_activity_score
        ),
        open_interest_change_score=(
            candidate.open_interest_change_score
        ),
        funding_divergence_score=(
            candidate.funding_divergence_score
        ),
        volume_expansion_score=(
            candidate.volume_expansion_score
        ),
        relative_strength_score=(
            candidate.relative_strength_score
        ),
        liquidity_event_score=(
            candidate.liquidity_event_score
        ),
        structure_event_score=(
            candidate.structure_event_score
        ),
        momentum_shift_score=(
            candidate.momentum_shift_score
        ),
        freshness_score=(
            candidate.freshness_score
        ),
        data_completeness_score=(
            candidate.data_completeness_score
        ),
    )


__all__ = [
    "build_candidate_observation",
]
