"""Early Bird candidate observation contract."""

from dataclasses import dataclass
from datetime import datetime, timezone


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


def _utc_datetime(
    value: datetime,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(
            "{0} must be a datetime".format(
                field_name
            )
        )

    if value.tzinfo is None:
        raise ValueError(
            "{0} must be timezone aware".format(
                field_name
            )
        )

    return value.astimezone(timezone.utc)


def _percentage(
    value: float,
    field_name: str,
) -> float:
    if isinstance(value, bool) or not isinstance(
        value,
        (int, float),
    ):
        raise TypeError(
            "{0} must be numeric".format(
                field_name
            )
        )

    normalized = float(value)

    if not 0.0 <= normalized <= 100.0:
        raise ValueError(
            "{0} must be between 0 and 100".format(
                field_name
            )
        )

    return normalized


@dataclass(frozen=True)
class EarlyBirdCandidateObservation:
    """One immutable observation of candidate behaviour."""

    asset: str
    observed_at: datetime
    quality: float
    whale_activity_score: float
    open_interest_change_score: float
    funding_divergence_score: float
    volume_expansion_score: float
    relative_strength_score: float
    liquidity_event_score: float
    structure_event_score: float
    momentum_shift_score: float
    freshness_score: float
    data_completeness_score: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "asset",
            _required_asset(self.asset),
        )

        object.__setattr__(
            self,
            "observed_at",
            _utc_datetime(
                self.observed_at,
                "observed_at",
            ),
        )

        score_fields = (
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

        for field_name in score_fields:
            object.__setattr__(
                self,
                field_name,
                _percentage(
                    getattr(
                        self,
                        field_name,
                    ),
                    field_name,
                ),
            )


__all__ = [
    "EarlyBirdCandidateObservation",
]
