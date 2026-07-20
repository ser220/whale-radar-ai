from enum import Enum


class CandidateDecisionInputAvailabilityStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"


class CandidateDecisionInputAvailabilityVersion(str, Enum):
    V1 = "V1"
