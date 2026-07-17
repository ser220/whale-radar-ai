"""Shared enums for normalized observation facts."""

from enum import Enum


class StructureBreak(str, Enum):
    NONE = "NONE"
    BULLISH_BOS = "BULLISH_BOS"
    BEARISH_BOS = "BEARISH_BOS"
    BULLISH_CHOCH = "BULLISH_CHOCH"
    BEARISH_CHOCH = "BEARISH_CHOCH"


class TrendBias(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class FundingBias(str, Enum):
    LONG_CROWDED = "LONG_CROWDED"
    SHORT_CROWDED = "SHORT_CROWDED"
    BALANCED = "BALANCED"
    UNKNOWN = "UNKNOWN"


class LiquiditySide(str, Enum):
    BUY_SIDE = "BUY_SIDE"
    SELL_SIDE = "SELL_SIDE"
    BOTH = "BOTH"
    NONE = "NONE"


class DataTrend(str, Enum):
    RISING = "RISING"
    FALLING = "FALLING"
    STABLE = "STABLE"
    UNKNOWN = "UNKNOWN"

class MarketObservationType(str, Enum):
    PRICE_MOVEMENT = "PRICE_MOVEMENT"
    VOLUME_CHANGE = "VOLUME_CHANGE"
    VOLATILITY_CHANGE = "VOLATILITY_CHANGE"
    MARKET_STATE = "MARKET_STATE"


class ObservationSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
