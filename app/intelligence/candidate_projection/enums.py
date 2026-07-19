from enum import Enum


class CandidateProjectionStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"


class CandidateProjectionVersion(str, Enum):
    V1 = "V1"
