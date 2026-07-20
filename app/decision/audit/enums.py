from enum import Enum


class DecisionAuditEventType(str, Enum):
    DECISION_CREATED = "decision_created"
    DECISION_APPROVED = "decision_approved"
    DECISION_REJECTED = "decision_rejected"
