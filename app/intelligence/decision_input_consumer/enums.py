from enum import Enum


class DecisionInputConsumerStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class DecisionInputConsumerVersion(str, Enum):
    V1 = "V1"
