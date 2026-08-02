"""Perpetual execution request builder."""

from app.intelligence.early_bird.perpetual_execution_request import (
    PerpetualExecutionRequest,
)

from app.intelligence.early_bird.perpetual_order_preparation import (
    PerpetualOrderPreparation,
)


class PerpetualExecutionRequestBuilder:
    """
    Builds exchange-independent execution request
    from prepared perpetual order.
    """

    def build(
        self,
        order: PerpetualOrderPreparation,
        *,
        exchange: str,
    ) -> PerpetualExecutionRequest:

        if not isinstance(
            order,
            PerpetualOrderPreparation,
        ):
            raise TypeError(
                "order must be PerpetualOrderPreparation"
            )

        return PerpetualExecutionRequest(
            asset=order.asset,
            direction=order.direction,
            order_type=order.order_type,
            size=order.initial_size,
            leverage=order.leverage,
            exchange=exchange,
            client_reference=(
                f"early-bird:{order.asset}"
            ),
        )


__all__ = [
    "PerpetualExecutionRequestBuilder",
]
