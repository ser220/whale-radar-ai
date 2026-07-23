import json
from pathlib import Path

from app.backtest.pipeline.json_file_writer import (
    BacktestPipelineJSONFileWriter,
)
from app.backtest.pipeline.orchestrator import (
    BacktestPipelineOrchestrator,
)
from app.backtest.report import (
    BacktestFinalReport,
)


def test_backtest_pipeline_json_file_writer(
    tmp_path: Path,
) -> None:
    report = BacktestFinalReport(
        strategy_id="strategy-delta",
        decision="PASS",
        rank=1,
        score=93.0,
        confidence=0.93,
        summary="Strategy passed pipeline validation",
    )

    result = BacktestPipelineOrchestrator().run(
        report=report,
        risk_level="LOW",
    )

    output_file = (
        tmp_path
        / "exports"
        / "strategy-delta.json"
    )

    written_file = (
        BacktestPipelineJSONFileWriter().write(
            result=result,
            output_file=output_file,
        )
    )

    assert written_file == output_file
    assert output_file.exists()

    data = json.loads(
        output_file.read_text(
            encoding="utf-8",
        )
    )

    assert data["report"] == {
        "strategy_id": "strategy-delta",
        "decision": "PASS",
        "rank": 1,
        "score": 93.0,
        "confidence": 0.93,
        "summary": "Strategy passed pipeline validation",
    }

    assert data["summary"]["strategy_id"] == (
        "strategy-delta"
    )
    assert data["summary"]["risk_level"] == "LOW"
    assert data["review"]["strategy_id"] == (
        "strategy-delta"
    )


def test_json_file_writer_creates_parent_directories(
    tmp_path: Path,
) -> None:
    report = BacktestFinalReport(
        strategy_id="strategy-epsilon",
        decision="REVIEW",
        rank=2,
        score=74.0,
        confidence=0.74,
        summary="Strategy requires additional review",
    )

    result = BacktestPipelineOrchestrator().run(
        report=report,
        risk_level="MEDIUM",
    )

    output_file = (
        tmp_path
        / "nested"
        / "backtests"
        / "strategy-epsilon.json"
    )

    assert not output_file.parent.exists()

    BacktestPipelineJSONFileWriter().write(
        result=result,
        output_file=output_file,
    )

    assert output_file.parent.exists()
    assert output_file.exists()
