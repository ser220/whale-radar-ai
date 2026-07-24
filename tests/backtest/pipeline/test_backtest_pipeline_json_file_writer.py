import json
import os
import tempfile
from pathlib import Path
from typing import Any

import pytest

from app.backtest.pipeline.json_exporter import (
    BacktestPipelineJSONExporter,
)
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


class FailingWriteTemporaryFile:
    def __init__(
        self,
        temporary_file: Any,
        failure: OSError,
    ) -> None:
        self.name = temporary_file.name
        self._temporary_file = temporary_file
        self._failure = failure

    def write(self, value: str) -> None:
        self._temporary_file.write(
            value[:1]
        )
        raise self._failure

    def flush(self) -> None:
        self._temporary_file.flush()

    def close(self) -> None:
        self._temporary_file.close()


class FailingCloseTemporaryFile:
    def __init__(
        self,
        temporary_file: Any,
        failure: OSError,
    ) -> None:
        self.name = temporary_file.name
        self._temporary_file = temporary_file
        self._failure = failure

    def write(self, value: str) -> None:
        self._temporary_file.write(value)

    def flush(self) -> None:
        self._temporary_file.flush()

    def close(self) -> None:
        self._temporary_file.close()
        raise self._failure


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


def test_new_destination_contains_complete_utf8_json(
    tmp_path: Path,
) -> None:
    report = BacktestFinalReport(
        strategy_id="strategy-unicode",
        decision="PASS",
        rank=1,
        score=93.0,
        confidence=0.93,
        summary="Стратегия готова 🐋",
    )
    result = BacktestPipelineOrchestrator().run(
        report=report,
        risk_level="LOW",
    )
    output_file = tmp_path / "result.json"
    expected_json = (
        BacktestPipelineJSONExporter()
        .export(result)
    )

    written_file = (
        BacktestPipelineJSONFileWriter()
        .write(
            result=result,
            output_file=output_file,
        )
    )

    assert written_file == output_file
    assert output_file.read_text(
        encoding="utf-8",
    ) == expected_json
    assert "Стратегия готова 🐋" in (
        output_file.read_text(
            encoding="utf-8",
        )
    )


def test_existing_destination_is_replaced_with_complete_json(
    tmp_path: Path,
) -> None:
    result = _build_pipeline_result()
    output_file = tmp_path / "result.json"
    output_file.write_bytes(
        b"\x00previous contents\xff"
    )
    expected_json = (
        BacktestPipelineJSONExporter()
        .export(result)
    )

    written_file = (
        BacktestPipelineJSONFileWriter()
        .write(
            result=result,
            output_file=output_file,
        )
    )

    assert written_file == output_file
    assert output_file.read_text(
        encoding="utf-8",
    ) == expected_json


def test_temporary_file_is_created_in_destination_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _build_pipeline_result()
    output_file = (
        tmp_path
        / "exports"
        / "result.json"
    )
    original_named_temporary_file = (
        tempfile.NamedTemporaryFile
    )
    temporary_directories = []

    def tracking_named_temporary_file(
        **kwargs: Any,
    ) -> Any:
        temporary_directories.append(
            Path(kwargs["dir"])
        )
        return original_named_temporary_file(
            **kwargs
        )

    monkeypatch.setattr(
        "app.backtest.pipeline.json_file_writer."
        "tempfile.NamedTemporaryFile",
        tracking_named_temporary_file,
    )

    BacktestPipelineJSONFileWriter().write(
        result=result,
        output_file=output_file,
    )

    assert temporary_directories == [
        output_file.parent,
    ]


def test_replace_failure_preserves_destination_and_removes_temporary_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _build_pipeline_result()
    output_file = tmp_path / "result.json"
    original_contents = (
        b"\x00existing\r\ncontent\xff"
    )
    output_file.write_bytes(original_contents)
    failure = OSError(
        "replace failed"
    )

    def failing_replace(
        source: os.PathLike,
        destination: os.PathLike,
    ) -> None:
        raise failure

    monkeypatch.setattr(
        "app.backtest.pipeline.json_file_writer."
        "os.replace",
        failing_replace,
    )

    with pytest.raises(OSError) as raised:
        BacktestPipelineJSONFileWriter().write(
            result=result,
            output_file=output_file,
        )

    assert raised.value is failure
    assert output_file.read_bytes() == (
        original_contents
    )
    assert list(tmp_path.iterdir()) == [
        output_file,
    ]


def test_write_failure_removes_temporary_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _build_pipeline_result()
    output_file = tmp_path / "result.json"
    failure = OSError(
        "write failed"
    )
    original_named_temporary_file = (
        tempfile.NamedTemporaryFile
    )

    def failing_named_temporary_file(
        **kwargs: Any,
    ) -> FailingWriteTemporaryFile:
        return FailingWriteTemporaryFile(
            original_named_temporary_file(
                **kwargs
            ),
            failure,
        )

    monkeypatch.setattr(
        "app.backtest.pipeline.json_file_writer."
        "tempfile.NamedTemporaryFile",
        failing_named_temporary_file,
    )

    with pytest.raises(OSError) as raised:
        BacktestPipelineJSONFileWriter().write(
            result=result,
            output_file=output_file,
        )

    assert raised.value is failure
    assert not output_file.exists()
    assert list(tmp_path.iterdir()) == []


def test_close_failure_removes_temporary_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _build_pipeline_result()
    output_file = tmp_path / "result.json"
    failure = OSError(
        "close failed"
    )
    original_named_temporary_file = (
        tempfile.NamedTemporaryFile
    )

    def failing_named_temporary_file(
        **kwargs: Any,
    ) -> FailingCloseTemporaryFile:
        return FailingCloseTemporaryFile(
            original_named_temporary_file(
                **kwargs
            ),
            failure,
        )

    monkeypatch.setattr(
        "app.backtest.pipeline.json_file_writer."
        "tempfile.NamedTemporaryFile",
        failing_named_temporary_file,
    )

    with pytest.raises(OSError) as raised:
        BacktestPipelineJSONFileWriter().write(
            result=result,
            output_file=output_file,
        )

    assert raised.value is failure
    assert not output_file.exists()
    assert list(tmp_path.iterdir()) == []
