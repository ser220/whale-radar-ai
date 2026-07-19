from enum import Enum


class CandidateEnvelopeStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"


class CandidateEnvelopeVersion(str, Enum):
    V1 = "V1"
