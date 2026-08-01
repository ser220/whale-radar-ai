"""Immutable external market data source contracts."""

from .enums import DataSourceCategory, DataSourceType
from .models import (
    DerivativesSnapshot,
    MarketSnapshot,
    OpenInterestSnapshot,
    NewsEventSnapshot,
    SmartMoneySnapshot,
    TechnicalSignalSnapshot,
    WhaleActivitySnapshot,
)


__all__ = [
    "DataSourceCategory",
    "DataSourceType",
    "DerivativesSnapshot",
    "MarketSnapshot",
    "OpenInterestSnapshot",
    "NewsEventSnapshot",
    "SmartMoneySnapshot",
    "TechnicalSignalSnapshot",
    "WhaleActivitySnapshot",
]
