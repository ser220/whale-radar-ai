"""Perpetual order preparation contract."""

from dataclasses import dataclass


VALID_DIRECTIONS = {
    "LONG",
    "SHORT",
}

VALID_ORDER_TYPES = {
    "LIMIT",
    "MARKET",
}

VALID_ENTRY_MODES = {
    "RETEST",
    "MARKET",
}

VALID_PROTECTION_MODES = {
    "NORMAL",
    "STRICT",
}


@dataclass(frozen=True)
class PerpetualOrderPreparation:
    """
    Prepared order parameters before exchange execution.

    This layer does not execute orders.
    It creates a controlled execution object.
    """

    asset: str
    direction: str
    order_type: str
    entry_mode: str
    initial_size: float
    leverage: int
    dca_enabled: bool
    protection_mode: str

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

        order_type = self.order_type.upper()

        if order_type not in VALID_ORDER_TYPES:
            raise ValueError(
                "invalid order_type"
            )

        object.__setattr__(
            self,
            "order_type",
            order_type,
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
                self.initial_size,
                (int, float),
            )
            or self.initial_size <= 0
        ):
            raise ValueError(
                "initial_size must be positive"
            )

        if (
            not isinstance(
                self.leverage,
                int,
            )
            or self.leverage <= 0
        ):
            raise ValueError(
                "leverage must be positive"
            )

        if not isinstance(
            self.dca_enabled,
            bool,
        ):
            raise TypeError(
                "dca_enabled must be bool"
            )

        protection_mode = self.protection_mode.upper()

        if protection_mode not in VALID_PROTECTION_MODES:
            raise ValueError(
                "invalid protection_mode"
            )

        object.__setattr__(
            self,
            "protection_mode",
            protection_mode,
        )


__all__ = [
    "PerpetualOrderPreparation",
]
