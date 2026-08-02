"""Perpetual position preparation builder."""

from app.intelligence.early_bird.perpetual_position_preparation import (
    PerpetualPositionPreparation,
)

from app.intelligence.early_bird.perpetual_opportunity import (
    PerpetualOpportunity,
)


class PerpetualPositionBuilder:
    """
    Builds controlled position preparation
    from perpetual opportunity.
    """

    def build(
        self,
        opportunity: PerpetualOpportunity,
    ) -> PerpetualPositionPreparation:

        if not isinstance(
            opportunity,
            PerpetualOpportunity,
        ):
            raise TypeError(
                "opportunity must be PerpetualOpportunity"
            )

        reversal = (
            opportunity.setup_type.upper()
            == "REVERSAL"
        )

        return PerpetualPositionPreparation(
            asset=opportunity.asset,
            direction=opportunity.direction,
            entry_mode="LIMIT",
            risk_allocation=(
                2.0
                if reversal
                else 5.0
            ),
            leverage_limit=(
                3
                if reversal
                else 5
            ),
            dca_allowed=(
                False
                if reversal
                else True
            ),
            reason=(
                "reversal risk controlled"
                if reversal
                else "continuation opportunity controlled"
            ),
        )


__all__ = [
    "PerpetualPositionBuilder",
]
