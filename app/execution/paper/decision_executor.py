from __future__ import annotations

from app.decision.contracts import (
    DecisionRecord,
    DecisionState,
    DecisionType,
)

from .models import PaperTrade
from .service import PaperExecutionService


class PaperDecisionExecutor:
    """
    Executes approved decisions
    through paper execution only.

    No exchange access.
    No decision creation.
    """

    def __init__(
        self,
        execution_service: PaperExecutionService | None = None,
    ) -> None:

        self._execution_service = (
            execution_service
            if execution_service is not None
            else PaperExecutionService()
        )

    def execute(
        self,
        decision: DecisionRecord,
        symbol: str,
        price: float,
        quantity: float,
    ) -> PaperTrade:

        if not isinstance(
            decision,
            DecisionRecord,
        ):
            raise TypeError(
                "decision must be DecisionRecord"
            )

        if (
            decision.decision_state
            != DecisionState.APPROVED
        ):
            raise ValueError(
                "only APPROVED decisions can be executed"
            )

        if decision.decision_type == DecisionType.LONG:
            side = "LONG"

        elif decision.decision_type == DecisionType.SHORT:
            side = "SHORT"

        else:
            raise ValueError(
                "decision type cannot be executed"
            )

        return self._execution_service.open_trade(
            symbol=symbol,
            side=side,
            price=price,
            quantity=quantity,
        )


__all__ = [
    "PaperDecisionExecutor",
]
