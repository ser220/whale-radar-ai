"""Contract-only interfaces for future external data collectors."""

from .exchange_market import (
    ExchangeMarketCollector,
    ExchangeMarketCollectorMetadata,
)


__all__ = [
    "ExchangeMarketCollector",
    "ExchangeMarketCollectorMetadata",
]
