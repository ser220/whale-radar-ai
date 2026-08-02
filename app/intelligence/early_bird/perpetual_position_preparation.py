"""Perpetual position preparation contract."""

from dataclasses import dataclass


VALID_DIRECTIONS = {
    "LONG",
    "SHORT",
}

VALID_ENTRY_MODES = {
    "LIMIT",
    "MARKET",
}


@dataclass(frozen=True)
class PerpetualPositionPreparation:
    """
    Prepared perpetual position parameters.

    This layer does not execute trades.
    It defines controlled preparation.
    """

    asset: str
    direction: str
    entry_mode: str
    risk_allocation: float
    leverage_limit: int
    dca_allowed: bool
    reason: str

    def __post_init__(self) -> None:

        asset = self.asset.strip().upper()

        if not asset:
            raise ValueError(
                "asset must not be empty"
            )

        object.__setattr__(
            self,
            "asset",
            asset,
        )

        direction = self.direction.upper()

        if direction not in VALID_DIRECTIONS:
            raise ValueError(
                "invalid direction"
            )

        object.__setattr__(
            self,
            "direction",
            direction,
        )

        entry_mode = self.entry_mode.upper()

        if entry_mode not in VALID_ENTRY_MODES:
            raise ValueError(
                "invalid entry_mode"
            )

        object.__setattr__(
            self,
            "entry_mode",
            entry_mode,
        )

        if (
            not isinstance(
                self.risk_allocation,
                (int, float),
            )
            or self.risk_allocation <= 0
            or self.risk_allocation > 100
        ):
            raise ValueError(
                "risk_allocation must be between 0 and 100"
            )

        if (
            not isinstance(
                self.leverage_limit,
                int,
            )
            or self.leverage_limit <= 0
        ):
            raise ValueError(
                "leverage must be positive"
            )

        if not isinstance(
            self.dca_allowed,
            bool,
        ):
            raise TypeError(
                "dca_allowed must be bool"
            )

        if not isinstance(
            self.reason,
            str,
        ):
            raise TypeError(
                "reason must be string"
            )


__all__ = [
    "PerpetualPositionPreparation",
]
