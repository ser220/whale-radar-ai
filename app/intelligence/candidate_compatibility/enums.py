from enum import Enum


class CandidateCompatibilityStatus(str, Enum):
    COMPATIBLE = "COMPATIBLE"
    INCOMPATIBLE = "INCOMPATIBLE"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"


class CandidateCompatibilityVersion(str, Enum):
    V1 = "V1"
