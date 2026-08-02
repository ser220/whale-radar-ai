"""Candidate observation history for Early Bird lifecycle analysis."""

from typing import Tuple

from app.intelligence.early_bird.candidate_observation import (
    EarlyBirdCandidateObservation,
)


def _required_asset(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError(
            "asset must be a string"
        )

    normalized = value.strip().upper()

    if not normalized:
        raise ValueError(
            "asset must not be empty"
        )

    return normalized


class CandidateObservationHistory:
    """Ordered in-memory observation history for one asset."""

    def __init__(
        self,
        *,
        asset: str,
        max_observations: int = 96,
    ) -> None:
        self.asset = _required_asset(asset)

        if (
            isinstance(max_observations, bool)
            or not isinstance(max_observations, int)
        ):
            raise TypeError(
                "max_observations must be an integer"
            )

        if max_observations < 1:
            raise ValueError(
                "max_observations must be at least 1"
            )

        self.max_observations = max_observations
        self._observations = []

    @property
    def observations(
        self,
    ) -> Tuple[EarlyBirdCandidateObservation, ...]:
        return tuple(self._observations)

    def append(
        self,
        observation: EarlyBirdCandidateObservation,
    ) -> None:
        if not isinstance(
            observation,
            EarlyBirdCandidateObservation,
        ):
            raise TypeError(
                "observation must be "
                "EarlyBirdCandidateObservation"
            )

        if observation.asset != self.asset:
            raise ValueError(
                "observation asset must match history asset"
            )

        if any(
            item.observed_at == observation.observed_at
            for item in self._observations
        ):
            raise ValueError(
                "observation timestamp already exists"
            )

        if (
            self._observations
            and observation.observed_at
            < self._observations[-1].observed_at
        ):
            raise ValueError(
                "observation timestamp must not move backward"
            )

        self._observations.append(
            observation
        )

        overflow = (
            len(self._observations)
            - self.max_observations
        )

        if overflow > 0:
            del self._observations[:overflow]


__all__ = [
    "CandidateObservationHistory",
]
