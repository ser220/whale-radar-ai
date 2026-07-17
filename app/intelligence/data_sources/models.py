"""Immutable normalized snapshots for future external data collectors."""

from collections.abc import Mapping
from dataclasses import dataclass, fields
from datetime import datetime
from typing import Any, Dict, Tuple, Type, TypeVar

from ._validation import (
    canonical_json,
    enum_value,
    exact_payload,
    finite_number,
    non_negative_number,
    parse_datetime,
    positive_number,
    required_text,
    utc_datetime,
)
from .enums import DataSourceCategory, DataSourceType, validate_source_pair


SnapshotT = TypeVar("SnapshotT")


def _source_identity(
    source_category: Any,
    source: Any,
    expected_category: DataSourceCategory,
) -> Tuple[DataSourceCategory, DataSourceType]:
    category = enum_value(
        DataSourceCategory, source_category, "source_category"
    )
    source_type = enum_value(DataSourceType, source, "source")
    if category is not expected_category:
        raise ValueError(
            "source_category must be {0}".format(expected_category.value)
        )
    validate_source_pair(category, source_type)
    return category, source_type


def _snapshot_payload(
    model_type: Type[SnapshotT],
    value: Mapping[str, Any],
) -> Dict[str, Any]:
    payload = exact_payload(
        value,
        tuple(item.name for item in fields(model_type)),
        model_type.__name__,
    )
    payload["source_category"] = enum_value(
        DataSourceCategory,
        payload["source_category"],
        "source_category",
    )
    payload["source"] = enum_value(
        DataSourceType,
        payload["source"],
        "source",
    )
    payload["captured_at"] = parse_datetime(payload["captured_at"])
    return payload


@dataclass(frozen=True)
class MarketSnapshot:
    """Normalized exchange market state without derived indicators."""

    source_category: DataSourceCategory
    source: DataSourceType
    symbol: str
    price: float
    volume_24h: float
    change_24h: float
    captured_at: datetime

    def __post_init__(self) -> None:
        category, source = _source_identity(
            self.source_category,
            self.source,
            DataSourceCategory.EXCHANGE,
        )
        object.__setattr__(self, "source_category", category)
        object.__setattr__(self, "source", source)
        object.__setattr__(
            self, "symbol", required_text(self.symbol, "symbol", uppercase=True)
        )
        object.__setattr__(self, "price", positive_number(self.price, "price"))
        object.__setattr__(
            self,
            "volume_24h",
            non_negative_number(self.volume_24h, "volume_24h"),
        )
        object.__setattr__(
            self, "change_24h", finite_number(self.change_24h, "change_24h")
        )
        object.__setattr__(
            self, "captured_at", utc_datetime(self.captured_at)
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_category": self.source_category.value,
            "source": self.source.value,
            "symbol": self.symbol,
            "price": self.price,
            "volume_24h": self.volume_24h,
            "change_24h": self.change_24h,
            "captured_at": self.captured_at.isoformat(),
        }

    def canonical_json(self) -> str:
        return canonical_json(self.to_dict())

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "MarketSnapshot":
        return cls(**_snapshot_payload(cls, value))


@dataclass(frozen=True)
class DerivativesSnapshot:
    """Normalized derivatives state without compatibility evaluation."""

    source_category: DataSourceCategory
    source: DataSourceType
    symbol: str
    open_interest: float
    funding_rate: float
    long_short_ratio: float
    liquidation_volume: float
    captured_at: datetime

    def __post_init__(self) -> None:
        category, source = _source_identity(
            self.source_category,
            self.source,
            DataSourceCategory.DERIVATIVES,
        )
        object.__setattr__(self, "source_category", category)
        object.__setattr__(self, "source", source)
        object.__setattr__(
            self, "symbol", required_text(self.symbol, "symbol", uppercase=True)
        )
        object.__setattr__(
            self,
            "open_interest",
            non_negative_number(self.open_interest, "open_interest"),
        )
        object.__setattr__(
            self,
            "funding_rate",
            finite_number(self.funding_rate, "funding_rate"),
        )
        object.__setattr__(
            self,
            "long_short_ratio",
            non_negative_number(self.long_short_ratio, "long_short_ratio"),
        )
        object.__setattr__(
            self,
            "liquidation_volume",
            non_negative_number(
                self.liquidation_volume, "liquidation_volume"
            ),
        )
        object.__setattr__(
            self, "captured_at", utc_datetime(self.captured_at)
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_category": self.source_category.value,
            "source": self.source.value,
            "symbol": self.symbol,
            "open_interest": self.open_interest,
            "funding_rate": self.funding_rate,
            "long_short_ratio": self.long_short_ratio,
            "liquidation_volume": self.liquidation_volume,
            "captured_at": self.captured_at.isoformat(),
        }

    def canonical_json(self) -> str:
        return canonical_json(self.to_dict())

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "DerivativesSnapshot":
        return cls(**_snapshot_payload(cls, value))


@dataclass(frozen=True)
class WhaleActivitySnapshot:
    """Normalized on-chain whale observation without wallet resolution."""

    source_category: DataSourceCategory
    source: DataSourceType
    asset: str
    wallet_reference: str
    direction: str
    amount: float
    entity_label: str
    captured_at: datetime

    def __post_init__(self) -> None:
        category, source = _source_identity(
            self.source_category,
            self.source,
            DataSourceCategory.ON_CHAIN,
        )
        object.__setattr__(self, "source_category", category)
        object.__setattr__(self, "source", source)
        object.__setattr__(
            self, "asset", required_text(self.asset, "asset", uppercase=True)
        )
        object.__setattr__(
            self,
            "wallet_reference",
            required_text(self.wallet_reference, "wallet_reference"),
        )
        object.__setattr__(
            self, "direction", required_text(self.direction, "direction")
        )
        object.__setattr__(
            self, "amount", positive_number(self.amount, "amount")
        )
        object.__setattr__(
            self,
            "entity_label",
            required_text(self.entity_label, "entity_label"),
        )
        object.__setattr__(
            self, "captured_at", utc_datetime(self.captured_at)
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_category": self.source_category.value,
            "source": self.source.value,
            "asset": self.asset,
            "wallet_reference": self.wallet_reference,
            "direction": self.direction,
            "amount": self.amount,
            "entity_label": self.entity_label,
            "captured_at": self.captured_at.isoformat(),
        }

    def canonical_json(self) -> str:
        return canonical_json(self.to_dict())

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "WhaleActivitySnapshot":
        return cls(**_snapshot_payload(cls, value))


@dataclass(frozen=True)
class SmartMoneySnapshot:
    """Normalized smart-money observation without identity resolution."""

    source_category: DataSourceCategory
    source: DataSourceType
    wallet_reference: str
    asset: str
    activity_type: str
    amount: float
    captured_at: datetime

    def __post_init__(self) -> None:
        category, source = _source_identity(
            self.source_category,
            self.source,
            DataSourceCategory.ON_CHAIN,
        )
        object.__setattr__(self, "source_category", category)
        object.__setattr__(self, "source", source)
        object.__setattr__(
            self,
            "wallet_reference",
            required_text(self.wallet_reference, "wallet_reference"),
        )
        object.__setattr__(
            self, "asset", required_text(self.asset, "asset", uppercase=True)
        )
        object.__setattr__(
            self,
            "activity_type",
            required_text(self.activity_type, "activity_type"),
        )
        object.__setattr__(
            self, "amount", positive_number(self.amount, "amount")
        )
        object.__setattr__(
            self, "captured_at", utc_datetime(self.captured_at)
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_category": self.source_category.value,
            "source": self.source.value,
            "wallet_reference": self.wallet_reference,
            "asset": self.asset,
            "activity_type": self.activity_type,
            "amount": self.amount,
            "captured_at": self.captured_at.isoformat(),
        }

    def canonical_json(self) -> str:
        return canonical_json(self.to_dict())

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "SmartMoneySnapshot":
        return cls(**_snapshot_payload(cls, value))


@dataclass(frozen=True)
class NewsEventSnapshot:
    """Normalized external news observation without impact calculation."""

    source_category: DataSourceCategory
    source: DataSourceType
    event_id: str
    asset: str
    category: str
    impact_level: str
    captured_at: datetime

    def __post_init__(self) -> None:
        category, source = _source_identity(
            self.source_category,
            self.source,
            DataSourceCategory.NEWS,
        )
        object.__setattr__(self, "source_category", category)
        object.__setattr__(self, "source", source)
        object.__setattr__(
            self, "event_id", required_text(self.event_id, "event_id")
        )
        object.__setattr__(
            self, "asset", required_text(self.asset, "asset", uppercase=True)
        )
        object.__setattr__(
            self, "category", required_text(self.category, "category")
        )
        object.__setattr__(
            self,
            "impact_level",
            required_text(self.impact_level, "impact_level"),
        )
        object.__setattr__(
            self, "captured_at", utc_datetime(self.captured_at)
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_category": self.source_category.value,
            "source": self.source.value,
            "event_id": self.event_id,
            "asset": self.asset,
            "category": self.category,
            "impact_level": self.impact_level,
            "captured_at": self.captured_at.isoformat(),
        }

    def canonical_json(self) -> str:
        return canonical_json(self.to_dict())

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "NewsEventSnapshot":
        return cls(**_snapshot_payload(cls, value))


@dataclass(frozen=True)
class TechnicalSignalSnapshot:
    """External TradingView analysis observation without signal generation."""

    source_category: DataSourceCategory
    source: DataSourceType
    symbol: str
    timeframe: str
    signal_type: str
    direction: str
    indicator_name: str
    value: float
    captured_at: datetime

    def __post_init__(self) -> None:
        category, source = _source_identity(
            self.source_category,
            self.source,
            DataSourceCategory.ANALYTICS,
        )
        object.__setattr__(self, "source_category", category)
        object.__setattr__(self, "source", source)
        object.__setattr__(
            self, "symbol", required_text(self.symbol, "symbol", uppercase=True)
        )
        object.__setattr__(
            self, "timeframe", required_text(self.timeframe, "timeframe")
        )
        object.__setattr__(
            self,
            "signal_type",
            required_text(self.signal_type, "signal_type"),
        )
        object.__setattr__(
            self, "direction", required_text(self.direction, "direction")
        )
        object.__setattr__(
            self,
            "indicator_name",
            required_text(self.indicator_name, "indicator_name"),
        )
        object.__setattr__(self, "value", finite_number(self.value, "value"))
        object.__setattr__(
            self, "captured_at", utc_datetime(self.captured_at)
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_category": self.source_category.value,
            "source": self.source.value,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "signal_type": self.signal_type,
            "direction": self.direction,
            "indicator_name": self.indicator_name,
            "value": self.value,
            "captured_at": self.captured_at.isoformat(),
        }

    def canonical_json(self) -> str:
        return canonical_json(self.to_dict())

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "TechnicalSignalSnapshot":
        return cls(**_snapshot_payload(cls, value))


__all__ = [
    "DerivativesSnapshot",
    "MarketSnapshot",
    "NewsEventSnapshot",
    "SmartMoneySnapshot",
    "TechnicalSignalSnapshot",
    "WhaleActivitySnapshot",
]
