from datetime import datetime, timezone

from app.intelligence.early_bird.execution_audit_record import (
    ExecutionAuditRecord,
)


def test_execution_audit_record_contract():

    record = ExecutionAuditRecord(
        execution_id="exec-001",
        candidate_id="HYPE-001",
        asset="HYPE",
        direction="SHORT",
        decision="OPEN",
        exchange="OKX",
        status="SUBMITTED",
        timestamp=datetime.now(
            timezone.utc
        ),
        message="order accepted",
    )

    assert record.asset == "HYPE"
    assert record.direction == "SHORT"
    assert record.status == "SUBMITTED"
    assert record.exchange == "OKX"



def test_invalid_status():

    try:

        ExecutionAuditRecord(
            execution_id="exec-002",
            candidate_id="BTC-001",
            asset="BTC",
            direction="LONG",
            decision="OPEN",
            exchange="OKX",
            status="UNKNOWN",
            timestamp=datetime.now(
                timezone.utc
            ),
            message="test",
        )

    except ValueError as exc:
        assert "status" in str(exc)

    else:
        raise AssertionError(
            "Expected ValueError"
        )
