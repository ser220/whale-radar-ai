from enum import Enum


class MarketType(str, Enum):
    CRYPTO = "CRYPTO"
    EQUITY = "EQUITY"
    ETF = "ETF"
    INDEX = "INDEX"
    COMMODITY = "COMMODITY"
    FOREX = "FOREX"
    FIXED_INCOME = "FIXED_INCOME"
    UNKNOWN = "UNKNOWN"


class InstrumentType(str, Enum):
    SPOT = "SPOT"
    PERPETUAL = "PERPETUAL"
    STOCK = "STOCK"
    ETF = "ETF"
    INDEX = "INDEX"
    FUTURE = "FUTURE"
    OPTION = "OPTION"
    FOREX_PAIR = "FOREX_PAIR"
    BOND = "BOND"
    UNKNOWN = "UNKNOWN"
