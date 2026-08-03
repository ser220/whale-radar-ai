from enum import Enum


class ArkhamChain(str, Enum):
    BITCOIN = "BITCOIN"
    ETHEREUM = "ETHEREUM"
    SOLANA = "SOLANA"
    OTHER = "OTHER"


class ArkhamFlowDirection(str, Enum):
    INFLOW = "INFLOW"
    OUTFLOW = "OUTFLOW"


class ArkhamEventType(str, Enum):
    CEX_DEPOSIT = "CEX_DEPOSIT"
    CEX_WITHDRAWAL = "CEX_WITHDRAWAL"
    STABLECOIN_MINT = "STABLECOIN_MINT"
    WHALE_TRANSFER = "WHALE_TRANSFER"
