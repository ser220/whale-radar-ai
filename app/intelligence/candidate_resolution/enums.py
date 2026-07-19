from enum import Enum


class CandidateResolutionType(str, Enum):
    EXACT_MATCH = "exact_match"
    MERGE_ALLOWED = "merge_allowed"
    KEEP_SEPARATE = "keep_separate"


class CandidateResolutionReason(str, Enum):
    SAME_IDENTITY = "same_identity"
    DIFFERENT_TIME_WINDOW = "different_time_window"
    DIFFERENT_SUBJECT = "different_subject"
    INSUFFICIENT_MATCH = "insufficient_match"
