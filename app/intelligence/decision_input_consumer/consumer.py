from datetime import datetime, timezone
from typing import Optional

from .enums import (
    DecisionInputConsumerStatus,
    DecisionInputConsumerVersion,
)
from .models import DecisionInputConsumerRecord
from .policy import DecisionInputConsumerPolicy


class DecisionInputConsumer:
    """Read-only consumer boundary for decision input."""

    def __init__(
        self,
        version: DecisionInputConsumerVersion = DecisionInputConsumerVersion.V1,
    ):
        self.version = version

    def consume(
        self,
        *,
        input_reference: str,
        status: DecisionInputConsumerStatus = DecisionInputConsumerStatus.AVAILABLE,
        consumed_at: Optional[datetime] = None,
    ) -> DecisionInputConsumerRecord:

        if consumed_at is None:
            consumed_at = datetime.now(timezone.utc)

        record = DecisionInputConsumerRecord(
            input_reference=input_reference,
            status=status,
            version=self.version,
            consumed_at=consumed_at,
        )

        return DecisionInputConsumerPolicy.validate(record)
