from enum import Enum


class CandidateDecisionInputStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class CandidateDecisionInputVersion(str, Enum):
    V1 = "V1"
