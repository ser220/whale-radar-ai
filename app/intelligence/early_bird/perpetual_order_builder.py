"""Perpetual order preparation builder."""

from app.intelligence.early_bird.perpetual_order_preparation import (
    PerpetualOrderPreparation,
)

from app.intelligence.early_bird.perpetual_risk_plan import (
    PerpetualRiskPlan,
)


class PerpetualOrderBuilder:
    """
    Builds exchange-independent order preparation
    from perpetual risk plan.
    """

    def build(
        self,
        risk_plan: PerpetualRiskPlan,
    ) -> PerpetualOrderPreparation:

        if not isinstance(
            risk_plan,
            PerpetualRiskPlan,
        ):
            raise TypeError(
                "risk_plan must be PerpetualRiskPlan"
            )

        return PerpetualOrderPreparation(
            asset=risk_plan.asset,
            direction=risk_plan.direction,
            order_type="LIMIT",
            entry_mode="RETEST",
            initial_size=risk_plan.initial_order_size,
            leverage=risk_plan.max_leverage,
            dca_enabled=(
                risk_plan.dca_budget > 0
            ),
            protection_mode=(
                "STRICT"
                if risk_plan.risk_mode == "RESTRICTED"
                else "NORMAL"
            ),
        )


__all__ = [
    "PerpetualOrderBuilder",
]
