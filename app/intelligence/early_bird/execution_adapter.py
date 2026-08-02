"""Perpetual execution adapter contract."""

from dataclasses import dataclass


VALID_STATUSES = {
    "SUBMITTED",
    "FILLED",
    "REJECTED",
    "FAILED",
}


@dataclass(frozen=True)
class PerpetualExecutionResult:
    """
    Result returned by exchange execution layer.

    Represents execution state, not signal state.
    """

    status: str
    exchange: str
    order_id: str
    asset: str
    direction: str
    filled_size: float
    message: str

    def __post_init__(self) -> None:

        status = self.status.upper()

        if status not in VALID_STATUSES:
            raise ValueError(
                "invalid status"
            )

        object.__setattr__(
            self,
            "status",
            status,
        )

        exchange = self.exchange.strip().upper()

        if not exchange:
            raise ValueError(
                "exchange must not be empty"
            )

        object.__setattr__(
            self,
            "exchange",
            exchange,
        )

        if not isinstance(
            self.order_id,
            str,
        ):
            raise TypeError(
                "order_id must be string"
            )

        if not isinstance(
            self.asset,
            str,
        ):
            raise TypeError(
                "asset must be string"
            )

        if not isinstance(
            self.direction,
            str,
        ):
            raise TypeError(
                "direction must be string"
            )

        if (
            not isinstance(
                self.filled_size,
                (int, float),
            )
            or self.filled_size < 0
        ):
            raise ValueError(
                "filled_size must be non-negative"
            )

        if not isinstance(
            self.message,
            str,
        ):
            raise TypeError(
                "message must be string"
            )


class PerpetualExecutionAdapter:
    """
    Exchange execution interface.

    Concrete adapters:
    - OKX
    - Gate
    - Binance
    - 3Commas
    """

    def submit(
        self,
        request,
    ) -> PerpetualExecutionResult:
        raise NotImplementedError(
            "Execution adapter must implement submit()"
        )


__all__ = [
    "PerpetualExecutionAdapter",
    "PerpetualExecutionResult",
]
