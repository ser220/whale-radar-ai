"""Execution performance memory store."""

from app.intelligence.early_bird.execution_performance_record import (
    ExecutionPerformanceRecord,
)


class ExecutionPerformanceMemory:
    """
    In-memory storage for execution performance records.

    First version:
    simple append-only memory.
    """

    def __init__(self) -> None:

        self._records = []


    def add(
        self,
        record: ExecutionPerformanceRecord,
    ) -> None:

        if not isinstance(
            record,
            ExecutionPerformanceRecord,
        ):
            raise TypeError(
                "record must be ExecutionPerformanceRecord"
            )

        self._records.append(
            record
        )


    def get_all(self) -> tuple:

        return tuple(
            self._records
        )


    def count(self) -> int:

        return len(
            self._records
        )


__all__ = [
    "ExecutionPerformanceMemory",
]
