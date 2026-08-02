"""Perpetual risk plan contract."""

from dataclasses import dataclass


VALID_DIRECTIONS = {
    "LONG",
    "SHORT",
}

VALID_RISK_MODES = {
    "NORMAL",
    "REDUCED",
    "RESTRICTED",
}


@dataclass(frozen=True)
class PerpetualRiskPlan:
    """
    Risk configuration for perpetual position.

    Defines capital protection before execution.
    """

    asset: str
    direction: str
    risk_mode: str
    max_position_risk: float
    initial_order_size: float
    dca_budget: float
    max_leverage: int

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

        risk_mode = self.risk_mode.upper()

        if risk_mode not in VALID_RISK_MODES:
            raise ValueError(
                "invalid risk_mode"
            )

        object.__setattr__(
            self,
            "risk_mode",
            risk_mode,
        )

        for field_name in (
            "max_position_risk",
            "initial_order_size",
            "dca_budget",
        ):
            value = getattr(
                self,
                field_name,
            )

            if (
                not isinstance(
                    value,
                    (int, float),
                )
                or value < 0
            ):
                raise ValueError(
                    f"{field_name} must be non-negative"
                )

        if (
            not isinstance(
                self.max_leverage,
                int,
            )
            or self.max_leverage <= 0
        ):
            raise ValueError(
                "max_leverage must be positive"
            )


__all__ = [
    "PerpetualRiskPlan",
]
