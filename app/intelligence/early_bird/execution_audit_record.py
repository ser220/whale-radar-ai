"""Execution audit trail contract."""

from dataclasses import dataclass
from datetime import datetime


VALID_STATUSES = {
    "REQUESTED",
    "SUBMITTED",
    "FILLED",
    "REJECTED",
    "FAILED",
}


@dataclass(frozen=True)
class ExecutionAuditRecord:
    """
    Immutable execution lifecycle record.

    Stores the history between decision
    and exchange execution result.
    """

    execution_id: str
    candidate_id: str
    asset: str
    direction: str
    decision: str
    exchange: str
    status: str
    timestamp: datetime
    message: str

    def __post_init__(self) -> None:

        for field_name in (
            "execution_id",
            "candidate_id",
            "asset",
            "direction",
            "decision",
            "exchange",
            "message",
        ):
            value = getattr(
                self,
                field_name,
            )

            if not isinstance(
                value,
                str,
            ):
                raise TypeError(
                    f"{field_name} must be string"
                )

            if not value.strip():
                raise ValueError(
                    f"{field_name} must not be empty"
                )

        object.__setattr__(
            self,
            "asset",
            self.asset.upper(),
        )

        object.__setattr__(
            self,
            "direction",
            self.direction.upper(),
        )

        object.__setattr__(
            self,
            "exchange",
            self.exchange.upper(),
        )

        status = self.status.upper()

        if status not in VALID_STATUSES:
            raise ValueError(
                "invalid status"
            )

        object.__setattr__(
            self,
            "status",
            status,
        )

        if not isinstance(
            self.timestamp,
            datetime,
        ):
            raise TypeError(
                "timestamp must be datetime"
            )


__all__ = [
    "ExecutionAuditRecord",
]
