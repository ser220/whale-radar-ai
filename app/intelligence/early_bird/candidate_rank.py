"""Early Bird candidate lifecycle rank contract."""

from enum import Enum


class CandidateRank(str, Enum):
    """
    Lifecycle rank of an Early Bird candidate.

    Higher ranks mean stronger historical validation,
    not simply a higher current score.
    """

    DISCOVERY = "discovery"
    WATCHLIST = "watchlist"
    PRIME = "prime"
    ACTIONABLE = "actionable"


__all__ = [
    "CandidateRank",
]
