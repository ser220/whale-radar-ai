from datetime import datetime, timezone

from app.intelligence.early_bird.execution_performance_record import (
    ExecutionPerformanceRecord,
)

from app.intelligence.early_bird.execution_performance_memory import (
    ExecutionPerformanceMemory,
)


def build_record(asset):

    return ExecutionPerformanceRecord(
        candidate_id=f"{asset}-001",
        asset=asset,
        direction="SHORT",
        setup_type="REVERSAL",
        entry_score=90.0,
        execution_status="FILLED",
        profit_loss=10.0,
        success=True,
        timestamp=datetime.now(
            timezone.utc
        ),
    )


def test_memory_add_and_get():

    memory = ExecutionPerformanceMemory()

    record = build_record(
        "HYPE"
    )

    memory.add(
        record
    )

    result = memory.get_all()

    assert len(result) == 1
    assert result[0].asset == "HYPE"



def test_memory_count():

    memory = ExecutionPerformanceMemory()

    memory.add(
        build_record("BTC")
    )

    memory.add(
        build_record("SOL")
    )

    assert memory.count() == 2
