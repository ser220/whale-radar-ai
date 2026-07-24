from pathlib import Path

from app.backtest.pipeline import (
    BacktestPipelineExportManager,
    BacktestPipelineJSONFileWriter,
    BacktestPipelineOrchestrator,
    BacktestPipelineResult,
    BacktestPipelineTimestampedJSONWriter,
)
from app.backtest.report import (
    BacktestFinalReport,
)


class FalsyJSONFileWriter(
    BacktestPipelineJSONFileWriter
):
    def __init__(
        self,
        return_path: Path,
    ) -> None:
        self.return_path = return_path
        self.calls = []

    def __bool__(self) -> bool:
        return False

    def write(
        self,
        result: BacktestPipelineResult,
        output_file: Path,
    ) -> Path:
        self.calls.append(
            (
                result,
                output_file,
            )
        )
        return self.return_path


class FalsyTimestampedJSONWriter(
    BacktestPipelineTimestampedJSONWriter
):
    def __init__(
        self,
        return_path: Path,
    ) -> None:
        self.return_path = return_path
        self.calls = []

    def __bool__(self) -> bool:
        return False

    def write(
        self,
        result: BacktestPipelineResult,
        output_directory: Path,
    ) -> Path:
        self.calls.append(
            (
                result,
                output_directory,
            )
        )
        return self.return_path


def _build_pipeline_result(
    strategy_id: str,
) -> BacktestPipelineResult:
    report = BacktestFinalReport(
        strategy_id=strategy_id,
        decision="PASS",
        rank=1,
        score=90.0,
        confidence=0.90,
        summary="Export manager dependency test",
    )

    return BacktestPipelineOrchestrator().run(
        report=report,
        risk_level="LOW",
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

    manager = BacktestPipelineExportManager(
        file_writer=None,
    )

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

    manager = BacktestPipelineExportManager(
        timestamped_writer=None,
    )

    written = manager.export_timestamped_json(
        result=result,
        output_directory=tmp_path,
    )

    assert written.exists()
    assert written.suffix == ".json"


def test_export_json_invokes_injected_falsy_writer(
    tmp_path: Path,
) -> None:
    result = _build_pipeline_result(
        "strategy-falsy-json-writer"
    )
    requested_path = (
        tmp_path
        / "requested.json"
    )
    injected_return_path = (
        tmp_path
        / "injected-return.json"
    )
    writer = FalsyJSONFileWriter(
        return_path=injected_return_path,
    )
    manager = BacktestPipelineExportManager(
        file_writer=writer,
    )

    returned_path = manager.export_json(
        result=result,
        path=requested_path,
    )

    assert len(writer.calls) == 1
    received_result, received_path = (
        writer.calls[0]
    )
    assert received_result is result
    assert received_path is requested_path
    assert returned_path is injected_return_path


def test_export_timestamped_json_invokes_injected_falsy_writer(
    tmp_path: Path,
) -> None:
    result = _build_pipeline_result(
        "strategy-falsy-timestamped-writer"
    )
    requested_directory = (
        tmp_path
        / "requested-directory"
    )
    injected_return_path = (
        tmp_path
        / "injected-timestamped-return.json"
    )
    writer = FalsyTimestampedJSONWriter(
        return_path=injected_return_path,
    )
    manager = BacktestPipelineExportManager(
        timestamped_writer=writer,
    )

    returned_path = (
        manager.export_timestamped_json(
            result=result,
            output_directory=(
                requested_directory
            ),
        )
    )

    assert len(writer.calls) == 1
    received_result, received_path = (
        writer.calls[0]
    )
    assert received_result is result
    assert received_path is requested_directory
    assert returned_path is injected_return_path
