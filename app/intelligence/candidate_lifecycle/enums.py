from enum import Enum


class CandidateLifecycleState(str, Enum):
    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    UPDATED = "UPDATED"
    SUPERSEDED = "SUPERSEDED"
    EXPIRED = "EXPIRED"
