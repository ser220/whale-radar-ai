from app.decision.contracts.models import (
    DecisionRecord,
)


class DecisionPolicy:

    @staticmethod
    def validate(
        record: DecisionRecord,
    ) -> DecisionRecord:

        if not isinstance(
            record,
            DecisionRecord,
        ):
            raise TypeError(
                "record must be DecisionRecord"
            )

        return record
