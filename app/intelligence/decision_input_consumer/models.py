from dataclasses import dataclass
from datetime import datetime, timezone

from .enums import (
    DecisionInputConsumerStatus,
    DecisionInputConsumerVersion,
)


@dataclass(frozen=True)
class DecisionInputConsumerRecord:
    input_reference: str
    status: DecisionInputConsumerStatus
    version: DecisionInputConsumerVersion
    consumed_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.input_reference, str):
            raise TypeError("input_reference must be str")

        if not self.input_reference.strip():
            raise ValueError("input_reference required")

        if not isinstance(
            self.status,
            DecisionInputConsumerStatus,
        ):
            raise TypeError(
                "status must be DecisionInputConsumerStatus"
            )

        if not isinstance(
            self.version,
            DecisionInputConsumerVersion,
        ):
            raise TypeError(
                "version must be DecisionInputConsumerVersion"
            )

        if not isinstance(self.consumed_at, datetime):
            raise TypeError("consumed_at must be datetime")

        if self.consumed_at.tzinfo is None:
            raise ValueError(
                "consumed_at must be timezone-aware"
            )

        normalized_time = self.consumed_at.astimezone(
            timezone.utc
        )

        object.__setattr__(
            self,
            "consumed_at",
            normalized_time,
        )
