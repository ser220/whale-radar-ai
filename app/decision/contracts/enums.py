from enum import Enum


class DecisionType(str, Enum):
    LONG = "long"
    SHORT = "short"
    HOLD = "hold"
    NO_ACTION = "no_action"


class DecisionState(str, Enum):
    CREATED = "created"
    APPROVED = "approved"
    REJECTED = "rejected"


class DecisionContractVersion(str, Enum):
    V1 = "1.0"
