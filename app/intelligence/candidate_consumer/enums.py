from enum import Enum


class CandidateConsumerStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class CandidateConsumerVersion(str, Enum):
    V1 = "V1"
