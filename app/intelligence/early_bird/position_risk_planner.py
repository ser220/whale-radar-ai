"""Position risk planner engine."""

from app.intelligence.early_bird.perpetual_risk_plan import (
    PerpetualRiskPlan,
)


class PositionRiskPlanner:
    """
    Calculates risk profile for perpetual positions.
    """

    def plan(
        self,
        preparation,
        *,
        confidence: float,
        risk_score: float,
        news_risk: float,
        setup_type: str,
    ) -> PerpetualRiskPlan:

        risk_mode = self._risk_mode(
            confidence=confidence,
            risk_score=risk_score,
            news_risk=news_risk,
            setup_type=setup_type,
        )

        leverage = self._leverage_limit(
            preparation,
            risk_mode,
            setup_type,
        )

        risk = self._risk_allocation(
            preparation,
            risk_mode,
        )

        initial_size = self._initial_size(
            preparation,
            risk_mode,
        )

        dca_budget = self._dca_budget(
            preparation,
            risk_mode,
        )

        return PerpetualRiskPlan(
            asset=preparation.asset,
            direction=preparation.direction,
            risk_mode=risk_mode,
            max_position_risk=risk,
            initial_order_size=initial_size,
            dca_budget=dca_budget,
            max_leverage=leverage,
        )

    @staticmethod
    def _risk_mode(
        *,
        confidence,
        risk_score,
        news_risk,
        setup_type,
    ):

        if news_risk > 70 or risk_score > 70:
            return "RESTRICTED"

        if setup_type.upper() == "REVERSAL":
            return "REDUCED"

        if confidence >= 85 and risk_score <= 40:
            return "NORMAL"

        return "REDUCED"

    @staticmethod
    def _leverage_limit(
        preparation,
        risk_mode,
        setup_type,
    ):

        if (
            setup_type.upper() == "REVERSAL"
            or risk_mode == "RESTRICTED"
        ):
            return min(
                preparation.leverage_limit,
                3,
            )

        return preparation.leverage_limit

    @staticmethod
    def _risk_allocation(
        preparation,
        risk_mode,
    ):

        if risk_mode == "RESTRICTED":
            return min(
                preparation.risk_allocation,
                1.0,
            )

        if risk_mode == "REDUCED":
            return min(
                preparation.risk_allocation,
                2.0,
            )

        return preparation.risk_allocation

    @staticmethod
    def _initial_size(
        preparation,
        risk_mode,
    ):

        if risk_mode == "RESTRICTED":
            return preparation.risk_allocation * 5

        if risk_mode == "REDUCED":
            return preparation.risk_allocation * 10

        return preparation.risk_allocation * 20

    @staticmethod
    def _dca_budget(
        preparation,
        risk_mode,
    ):

        if risk_mode == "RESTRICTED":
            return 0.0

        if risk_mode == "REDUCED":
            return min(
                preparation.risk_allocation,
                10.0,
            )

        if preparation.dca_allowed:
            return 20.0

        return 0.0


__all__ = [
    "PositionRiskPlanner",
]
