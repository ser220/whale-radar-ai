from enum import Enum


class RiskFactor(str, Enum):
    FUNDING = "FUNDING"
    OPEN_INTEREST = "OPEN_INTEREST"
    LIQUIDITY = "LIQUIDITY"
    LIQUIDATIONS = "LIQUIDATIONS"
    CVD = "CVD"
    WHALE = "WHALE"
    FLOW = "FLOW"
    VOLATILITY = "VOLATILITY"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EXTREME = "EXTREME"
