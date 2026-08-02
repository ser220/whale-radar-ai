"""Execution performance memory contract."""

from dataclasses import dataclass
from datetime import datetime


VALID_EXECUTION_STATUSES = {
    "FILLED",
    "REJECTED",
    "FAILED",
}


@dataclass(frozen=True)
class ExecutionPerformanceRecord:
    """
    Immutable record of execution outcome.

    Links:
    candidate
        +
    execution result
        +
    trading outcome
    """

    candidate_id: str
    asset: str
    direction: str
    setup_type: str
    entry_score: float
    execution_status: str
    profit_loss: float
    success: bool
    timestamp: datetime

    def __post_init__(self) -> None:

        for field_name in (
            "candidate_id",
            "asset",
            "direction",
            "setup_type",
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
            "setup_type",
            self.setup_type.upper(),
        )

        if not isinstance(
            self.entry_score,
            (int, float),
        ):
            raise TypeError(
                "entry_score must be numeric"
            )

        if not 0.0 <= self.entry_score <= 100.0:
            raise ValueError(
                "entry_score must be between 0 and 100"
            )

        status = self.execution_status.upper()

        if status not in VALID_EXECUTION_STATUSES:
            raise ValueError(
                "invalid status"
            )

        object.__setattr__(
            self,
            "execution_status",
            status,
        )

        if not isinstance(
            self.profit_loss,
            (int, float),
        ):
            raise TypeError(
                "profit_loss must be numeric"
            )

        if not isinstance(
            self.success,
            bool,
        ):
            raise TypeError(
                "success must be bool"
            )

        if not isinstance(
            self.timestamp,
            datetime,
        ):
            raise TypeError(
                "timestamp must be datetime"
            )


__all__ = [
    "ExecutionPerformanceRecord",
]
