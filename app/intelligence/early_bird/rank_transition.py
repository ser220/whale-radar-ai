"""Early Bird candidate rank transition contract."""

from enum import Enum


class RankTransition(str, Enum):
    """
    Lifecycle transition decision.

    It describes what should happen with
    a candidate rank.
    """

    PROMOTE = "promote"
    DOWNGRADE = "downgrade"
    HOLD = "hold"
    REMOVE = "remove"


__all__ = [
    "RankTransition",
]
