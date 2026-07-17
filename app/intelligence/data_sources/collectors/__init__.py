"""Contract-only interfaces for future external data collectors."""

from .binance import (
    BinanceMarketCollector,
    BinanceMarketCollectorResponseError,
    BinanceMarketCollectorTimeoutError,
    BinanceMarketCollectorTransportError,
)
from .exchange_market import (
    ExchangeMarketCollector,
    ExchangeMarketCollectorMetadata,
)


__all__ = [
    "BinanceMarketCollector",
    "BinanceMarketCollectorResponseError",
    "BinanceMarketCollectorTimeoutError",
    "BinanceMarketCollectorTransportError",
    "ExchangeMarketCollector",
    "ExchangeMarketCollectorMetadata",
]
