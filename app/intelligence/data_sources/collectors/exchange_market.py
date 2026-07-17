"""Protocol boundary for future exchange market collector adapters."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol, Tuple, runtime_checkable

from .._validation import enum_value, required_text
from ..enums import DataSourceCategory, DataSourceType, validate_source_pair
from ..models import MarketSnapshot


_SUPPORTED_SOURCES = frozenset(
    {
        DataSourceType.BINANCE,
        DataSourceType.OKX,
        DataSourceType.GATE,
    }
)


@dataclass(frozen=True)
class ExchangeMarketCollectorMetadata:
    """Immutable identity and declared coverage for a collector adapter."""

    source: DataSourceType
    category: DataSourceCategory
    supported_symbols: Tuple[str, ...]

    def __post_init__(self) -> None:
        source = enum_value(DataSourceType, self.source, "source")
        category = enum_value(DataSourceCategory, self.category, "category")
        if category is not DataSourceCategory.EXCHANGE:
            raise ValueError("category must be EXCHANGE")
        validate_source_pair(category, source)
        if source not in _SUPPORTED_SOURCES:
            raise ValueError(
                "source {0} is not supported by this collector boundary".format(
                    source.value
                )
            )
        is_text = isinstance(
            self.supported_symbols, (str, bytes, bytearray)
        )
        if is_text or not isinstance(self.supported_symbols, Sequence):
            raise TypeError("supported_symbols must be a sequence of strings")
        symbols = tuple(
            required_text(value, "supported_symbols", uppercase=True)
            for value in self.supported_symbols
        )
        if not symbols:
            raise ValueError("supported_symbols must not be empty")
        if len(set(symbols)) != len(symbols):
            raise ValueError("supported_symbols must not contain duplicates")
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "category", category)
        object.__setattr__(self, "supported_symbols", symbols)


@runtime_checkable
class ExchangeMarketCollector(Protocol):
    """Adapter interface from an opaque exchange response to MarketSnapshot."""

    @property
    def metadata(self) -> ExchangeMarketCollectorMetadata:
        """Return immutable source identity and symbol coverage."""
        ...

    def transform(self, response: Mapping[str, Any]) -> MarketSnapshot:
        """Normalize an already-supplied external response."""
        ...


__all__ = [
    "ExchangeMarketCollector",
    "ExchangeMarketCollectorMetadata",
]
