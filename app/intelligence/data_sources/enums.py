"""Categories and typed identities for external market data sources."""

from enum import Enum
from types import MappingProxyType
from typing import FrozenSet, Mapping


class DataSourceCategory(str, Enum):
    EXCHANGE = "EXCHANGE"
    DERIVATIVES = "DERIVATIVES"
    ON_CHAIN = "ON_CHAIN"
    NEWS = "NEWS"
    SOCIAL = "SOCIAL"
    ANALYTICS = "ANALYTICS"
    UNKNOWN = "UNKNOWN"


class DataSourceType(str, Enum):
    BINANCE = "BINANCE"
    OKX = "OKX"
    BYBIT = "BYBIT"
    GATE = "GATE"
    MEXC = "MEXC"
    BITGET = "BITGET"
    KUCOIN = "KUCOIN"
    COINBASE = "COINBASE"
    COINGLASS = "COINGLASS"
    ARKHAM = "ARKHAM"
    NANSEN = "NANSEN"
    TRADINGVIEW = "TRADINGVIEW"
    UNKNOWN = "UNKNOWN"


EXCHANGE_SOURCES: FrozenSet[DataSourceType] = frozenset(
    {
        DataSourceType.BINANCE,
        DataSourceType.OKX,
        DataSourceType.BYBIT,
        DataSourceType.GATE,
        DataSourceType.MEXC,
        DataSourceType.BITGET,
        DataSourceType.KUCOIN,
        DataSourceType.COINBASE,
    }
)

DERIVATIVES_SOURCES: FrozenSet[DataSourceType] = frozenset(
    {DataSourceType.COINGLASS}
)

ON_CHAIN_SOURCES: FrozenSet[DataSourceType] = frozenset(
    {DataSourceType.ARKHAM, DataSourceType.NANSEN}
)

ANALYTICS_SOURCES: FrozenSet[DataSourceType] = frozenset(
    {DataSourceType.TRADINGVIEW}
)

_UNKNOWN_ONLY: FrozenSet[DataSourceType] = frozenset(
    {DataSourceType.UNKNOWN}
)

_CATEGORY_SOURCES: Mapping[
    DataSourceCategory, FrozenSet[DataSourceType]
] = MappingProxyType(
    {
        DataSourceCategory.EXCHANGE: EXCHANGE_SOURCES,
        DataSourceCategory.DERIVATIVES: DERIVATIVES_SOURCES,
        DataSourceCategory.ON_CHAIN: ON_CHAIN_SOURCES,
        DataSourceCategory.NEWS: _UNKNOWN_ONLY,
        DataSourceCategory.SOCIAL: _UNKNOWN_ONLY,
        DataSourceCategory.ANALYTICS: ANALYTICS_SOURCES,
        DataSourceCategory.UNKNOWN: _UNKNOWN_ONLY,
    }
)


def validate_source_pair(
    category: DataSourceCategory,
    source: DataSourceType,
) -> None:
    if source not in _CATEGORY_SOURCES[category]:
        raise ValueError(
            "source {0} is not valid for category {1}".format(
                source.value, category.value
            )
        )


__all__ = [
    "DataSourceCategory",
    "DataSourceType",
]
