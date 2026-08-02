from datetime import datetime, timezone

from app.intelligence.early_bird.execution_performance_record import (
    ExecutionPerformanceRecord,
)


def test_performance_record_contract():

    record = ExecutionPerformanceRecord(
        candidate_id="HYPE-001",
        asset="HYPE",
        direction="SHORT",
        setup_type="REVERSAL",
        entry_score=92.0,
        execution_status="FILLED",
        profit_loss=18.5,
        success=True,
        timestamp=datetime.now(
            timezone.utc
        ),
    )

    assert record.asset == "HYPE"
    assert record.direction == "SHORT"
    assert record.setup_type == "REVERSAL"
    assert record.success is True



def test_invalid_execution_status():

    try:

        ExecutionPerformanceRecord(
            candidate_id="BTC-001",
            asset="BTC",
            direction="LONG",
            setup_type="CONTINUATION",
            entry_score=80.0,
            execution_status="UNKNOWN",
            profit_loss=0.0,
            success=False,
            timestamp=datetime.now(
                timezone.utc
            ),
        )

    except ValueError as exc:
        assert "status" in str(exc)

    else:
        raise AssertionError(
            "Expected ValueError"
        )
