import json
from pathlib import Path

import pytest

from app.backtest.pipeline.json_file_writer import (
    BacktestPipelineJSONFileWriter,
)
from app.backtest.pipeline.orchestrator import (
    BacktestPipelineOrchestrator,
)
from app.backtest.report import (
    BacktestFinalReport,
)


class FailingJSONExporter:
    def export(self, result: object) -> str:
        raise RuntimeError(
            "serialization failed"
        )


def _build_pipeline_result():
    report = BacktestFinalReport(
        strategy_id="strategy-preflight",
        decision="PASS",
        rank=1,
        score=93.0,
        confidence=0.93,
        summary="Serialization preflight test",
    )

    return BacktestPipelineOrchestrator().run(
        report=report,
        risk_level="LOW",
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


def test_serialization_failure_creates_no_directory_or_file(
    tmp_path: Path,
) -> None:
    result = _build_pipeline_result()
    output_file = (
        tmp_path
        / "missing"
        / "exports"
        / "result.json"
    )
    writer = BacktestPipelineJSONFileWriter(
        exporter=FailingJSONExporter(),
    )

    with pytest.raises(
        RuntimeError,
        match="serialization failed",
    ):
        writer.write(
            result=result,
            output_file=output_file,
        )

    assert not output_file.exists()
    assert not output_file.parent.exists()
    assert list(tmp_path.rglob("*")) == []


def test_serialization_failure_preserves_existing_file_bytes(
    tmp_path: Path,
) -> None:
    result = _build_pipeline_result()
    output_file = tmp_path / "result.json"
    original_contents = (
        b"\x00existing\r\ncontent\xff"
    )
    output_file.write_bytes(original_contents)
    writer = BacktestPipelineJSONFileWriter(
        exporter=FailingJSONExporter(),
    )

    with pytest.raises(
        RuntimeError,
        match="serialization failed",
    ):
        writer.write(
            result=result,
            output_file=output_file,
        )

    assert output_file.read_bytes() == original_contents
