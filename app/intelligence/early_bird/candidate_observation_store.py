"""Store for Early Bird candidate observation histories."""

from typing import Dict, Tuple

from app.intelligence.early_bird.candidate_observation import (
    EarlyBirdCandidateObservation,
)

from app.intelligence.early_bird.candidate_observation_history import (
    CandidateObservationHistory,
)


class CandidateObservationStore:
    """
    Market-wide storage of candidate observation histories.
    """

    def __init__(
        self,
        *,
        max_observations: int = 96,
    ) -> None:
        self.max_observations = max_observations
        self._histories: Dict[
            str,
            CandidateObservationHistory,
        ] = {}

    @property
    def assets(
        self,
    ) -> Tuple[str, ...]:
        return tuple(
            self._histories.keys()
        )

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

        history = self._histories.get(
            observation.asset
        )

        if history is None:
            history = CandidateObservationHistory(
                asset=observation.asset,
                max_observations=self.max_observations,
            )

            self._histories[
                observation.asset
            ] = history

        history.append(
            observation
        )

    def history(
        self,
        asset: str,
    ):
        if not isinstance(asset, str):
            raise TypeError(
                "asset must be a string"
            )

        return self._histories.get(
            asset.strip().upper()
        )


__all__ = [
    "CandidateObservationStore",
]
