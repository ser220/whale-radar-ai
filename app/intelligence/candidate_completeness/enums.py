from enum import Enum


class ProviderCompletenessStatus(str, Enum):
    """Availability state for one provider contribution."""

    AVAILABLE = "AVAILABLE"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"


class CandidateCompletenessStatus(str, Enum):
    """Overall completeness state across required providers."""

    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    INCOMPLETE = "INCOMPLETE"
