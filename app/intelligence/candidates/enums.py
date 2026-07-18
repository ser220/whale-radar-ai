from enum import Enum


class CandidateStatus(str, Enum):
    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    ARCHIVED = "ARCHIVED"


class CandidateCategory(str, Enum):
    MARKET = "MARKET"
    STRUCTURE = "STRUCTURE"
    LIQUIDITY = "LIQUIDITY"
    OTHER = "OTHER"
