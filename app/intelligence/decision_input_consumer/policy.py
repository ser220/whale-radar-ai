from .enums import DecisionInputConsumerStatus
from .models import DecisionInputConsumerRecord


class DecisionInputConsumerPolicy:
    """Validation policy for read-only decision input consumption."""

    @staticmethod
    def validate(
        record: DecisionInputConsumerRecord,
    ) -> DecisionInputConsumerRecord:
        if not isinstance(
            record,
            DecisionInputConsumerRecord,
        ):
            raise TypeError(
                "record must be DecisionInputConsumerRecord"
            )

        if not isinstance(
            record.status,
            DecisionInputConsumerStatus,
        ):
            raise TypeError(
                "status must be DecisionInputConsumerStatus"
            )

        if not record.input_reference.strip():
            raise ValueError(
                "input_reference required"
            )

        return record
