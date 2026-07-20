from __future__ import annotations

from dataclasses import replace

from app.decision.contracts import (
    DecisionRecord,
    DecisionState,
)


class DecisionLifecycle:
    """
    Controls immutable DecisionRecord state transitions.

    No storage, execution, or decision logic allowed.
    """

    @staticmethod
    def approve(
        record: DecisionRecord,
    ) -> DecisionRecord:
        if not isinstance(
            record,
            DecisionRecord,
        ):
            raise TypeError(
                "record must be DecisionRecord"
            )

        if (
            record.decision_state
            != DecisionState.CREATED
        ):
            raise ValueError(
                "only CREATED decisions can be approved"
            )

        return replace(
            record,
            decision_state=DecisionState.APPROVED,
        )

    @staticmethod
    def reject(
        record: DecisionRecord,
    ) -> DecisionRecord:
        if not isinstance(
            record,
            DecisionRecord,
        ):
            raise TypeError(
                "record must be DecisionRecord"
            )

        if (
            record.decision_state
            != DecisionState.CREATED
        ):
            raise ValueError(
                "only CREATED decisions can be rejected"
            )

        return replace(
            record,
            decision_state=DecisionState.REJECTED,
        )
