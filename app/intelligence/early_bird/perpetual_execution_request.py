"""Perpetual execution request contract."""

from dataclasses import dataclass


VALID_DIRECTIONS = {
    "LONG",
    "SHORT",
}

VALID_ORDER_TYPES = {
    "LIMIT",
    "MARKET",
}


@dataclass(frozen=True)
class PerpetualExecutionRequest:
    """
    Exchange-independent execution request.

    This object is passed from intelligence
    layer to execution adapters.
    """

    asset: str
    direction: str
    order_type: str
    size: float
    leverage: int
    exchange: str
    client_reference: str

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

        if (
            not isinstance(
                self.size,
                (int, float),
            )
            or self.size <= 0
        ):
            raise ValueError(
                "size must be positive"
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
            self.client_reference,
            str,
        ):
            raise TypeError(
                "client_reference must be string"
            )

        if not self.client_reference.strip():
            raise ValueError(
                "client_reference must not be empty"
            )


__all__ = [
    "PerpetualExecutionRequest",
]
