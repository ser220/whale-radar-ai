"""Execution decision contract."""

from dataclasses import dataclass


VALID_ACTIONS = {
    "OPEN",
    "WAIT",
    "REJECT",
}

VALID_DIRECTIONS = {
    "LONG",
    "SHORT",
}


@dataclass(frozen=True)
class ExecutionDecision:
    """
    Final execution gate decision.

    Converts readiness state into:

    OPEN
    WAIT
    REJECT
    """

    def evaluate(
        self,
        readiness,
    ):
        action = self._resolve_action(
            readiness
        )

        return ExecutionDecisionResult(
            asset=readiness.asset,
            direction=readiness.direction,
            action=action,
            confidence=readiness.confidence,
            reason=readiness.reason,
        )

    @staticmethod
    def _resolve_action(
        readiness,
    ) -> str:

        if readiness.status == "READY":
            return "OPEN"

        if readiness.status == "PREPARE":
            return "WAIT"

        if readiness.status == "WAIT":
            return "WAIT"

        return "REJECT"


@dataclass(frozen=True)
class ExecutionDecisionResult:

    asset: str
    direction: str
    action: str
    confidence: float
    reason: str

    def __post_init__(self):

        if self.direction not in VALID_DIRECTIONS:
            raise ValueError(
                "invalid direction"
            )

        if self.action not in VALID_ACTIONS:
            raise ValueError(
                "invalid action"
            )


__all__ = [
    "ExecutionDecision",
    "ExecutionDecisionResult",
]
