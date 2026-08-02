"""Dual directional candidate lifecycle contract."""

from dataclasses import dataclass


VALID_STATES = {
    "LONG_DOMINANT",
    "SHORT_DOMINANT",
    "TRANSITION",
    "REVERSAL_CONFIRMED",
}


def _validate_asset(
    value: str,
) -> str:

    if not isinstance(value, str):
        raise TypeError(
            "asset must be string"
        )

    asset = value.strip().upper()

    if not asset:
        raise ValueError(
            "asset must not be empty"
        )

    return asset


@dataclass(frozen=True)
class CandidateDualRankLifecycle:
    """
    Complete lifecycle state of a dual-direction candidate.

    Keeps both sides alive:

    LONG:
    L1 -> L4

    SHORT:
    S1 -> S4

    and remembers reversals.
    """

    asset: str
    current_long_rank: str
    current_short_rank: str
    highest_long_rank: str
    highest_short_rank: str
    current_state: str
    transition_history: tuple[str, ...]

    def __post_init__(self) -> None:

        object.__setattr__(
            self,
            "asset",
            _validate_asset(
                self.asset
            ),
        )

        if self.current_state not in VALID_STATES:
            raise ValueError(
                "invalid state"
            )

        if not isinstance(
            self.transition_history,
            tuple,
        ):
            raise TypeError(
                "transition_history must be tuple"
            )

        for field_name in (
            "current_long_rank",
            "current_short_rank",
            "highest_long_rank",
            "highest_short_rank",
        ):
            if not isinstance(
                getattr(self, field_name),
                str,
            ):
                raise TypeError(
                    f"{field_name} must be string"
                )


__all__ = [
    "CandidateDualRankLifecycle",
]
