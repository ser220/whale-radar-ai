from pathlib import Path

from app.backtest.pipeline import (
    BacktestPipelineExportManager,
    BacktestPipelineOrchestrator,
)
from app.backtest.report import (
    BacktestFinalReport,
)


def test_export_manager_exports_json(
    tmp_path: Path,
) -> None:
    report = BacktestFinalReport(
        strategy_id="strategy-manager",
        decision="PASS",
        rank=1,
        score=90.0,
        confidence=0.90,
        summary="Export manager test",
    )

    result = BacktestPipelineOrchestrator().run(
        report=report,
        risk_level="LOW",
    )

    manager = BacktestPipelineExportManager()

    output_file = tmp_path / "result.json"

    written = manager.export_json(
        result=result,
        path=output_file,
    )

    assert written == output_file
    assert output_file.exists()


def test_export_manager_exports_timestamped_json(
    tmp_path: Path,
) -> None:
    report = BacktestFinalReport(
        strategy_id="strategy-manager-time",
        decision="REVIEW",
        rank=2,
        score=75.0,
        confidence=0.75,
        summary="Timestamp export test",
    )

    result = BacktestPipelineOrchestrator().run(
        report=report,
        risk_level="MEDIUM",
    )

    manager = BacktestPipelineExportManager()

    written = manager.export_timestamped_json(
        result=result,
        output_directory=tmp_path,
    )

    assert written.exists()
    assert written.suffix == ".json"
