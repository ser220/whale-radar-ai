from datetime import datetime, timezone

from app.intelligence.early_bird.execution_performance_record import (
    ExecutionPerformanceRecord,
)

from app.intelligence.early_bird.execution_performance_memory import (
    ExecutionPerformanceMemory,
)

from app.intelligence.early_bird.performance_analyzer import (
    PerformanceAnalyzer,
)


def build_record(
    profit,
    success,
):

    return ExecutionPerformanceRecord(
        candidate_id="TEST-001",
        asset="HYPE",
        direction="SHORT",
        setup_type="REVERSAL",
        entry_score=90.0,
        execution_status="FILLED",
        profit_loss=profit,
        success=success,
        timestamp=datetime.now(
            timezone.utc
        ),
    )


def test_performance_analysis():

    memory = ExecutionPerformanceMemory()

    memory.add(
        build_record(
            10.0,
            True,
        )
    )

    memory.add(
        build_record(
            -5.0,
            False,
        )
    )

    result = PerformanceAnalyzer().analyze(
        memory
    )

    assert result.total_trades == 2
    assert result.successful_trades == 1
    assert result.win_rate == 50.0
    assert result.average_profit_loss == 2.5



def test_empty_memory():

    memory = ExecutionPerformanceMemory()

    result = PerformanceAnalyzer().analyze(
        memory
    )

    assert result.total_trades == 0
    assert result.win_rate == 0.0
