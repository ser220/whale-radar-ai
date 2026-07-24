import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.backtest.pipeline.orchestrator import (
    BacktestPipelineOrchestrator,
)
from app.backtest.pipeline.timestamped_json_writer import (
    BacktestPipelineTimestampedJSONWriter,
)
from app.backtest.report import (
    BacktestFinalReport,
)


def test_timestamped_json_writer_writes_expected_file(
    tmp_path: Path,
) -> None:
    report = BacktestFinalReport(
        strategy_id="strategy-zeta",
        decision="PASS",
        rank=1,
        score=95.0,
        confidence=0.95,
        summary="Strategy approved",
    )

    result = BacktestPipelineOrchestrator().run(
        report=report,
        risk_level="LOW",
    )

    fixed_now = datetime(
        2026,
        7,
        23,
        18,
        30,
        45,
        tzinfo=timezone.utc,
    )

    writer = BacktestPipelineTimestampedJSONWriter(
        now_provider=lambda: fixed_now,
    )

    written_file = writer.write(
        result=result,
        output_directory=tmp_path / "exports",
    )

    expected_file = (
        tmp_path
        / "exports"
        / "strategy-zeta-20260723T183045Z.json"
    )

    assert written_file == expected_file
    assert expected_file.exists()

    data = json.loads(
        expected_file.read_text(
            encoding="utf-8",
        )
    )

    assert data["report"]["strategy_id"] == (
        "strategy-zeta"
    )
    assert data["report"]["decision"] == "PASS"
    assert data["summary"]["risk_level"] == "LOW"


def test_timestamped_json_writer_converts_time_to_utc(
    tmp_path: Path,
) -> None:
    source_timezone = timezone.utc

    report = BacktestFinalReport(
        strategy_id="strategy-eta",
        decision="REVIEW",
        rank=2,
        score=78.0,
        confidence=0.78,
        summary="Strategy requires review",
    )

    result = BacktestPipelineOrchestrator().run(
        report=report,
        risk_level="MEDIUM",
    )

    local_time = datetime(
        2026,
        7,
        23,
        20,
        15,
        0,
        tzinfo=source_timezone,
    )

    writer = BacktestPipelineTimestampedJSONWriter(
        now_provider=lambda: local_time,
    )

    written_file = writer.write(
        result=result,
        output_directory=tmp_path,
    )

    assert written_file.name == (
        "strategy-eta-20260723T201500Z.json"
    )


def test_timestamped_json_writer_treats_naive_time_as_utc(
    tmp_path: Path,
) -> None:
    report = BacktestFinalReport(
        strategy_id="strategy-theta",
        decision="REJECT",
        rank=3,
        score=42.0,
        confidence=0.42,
        summary="Strategy rejected",
    )

    result = BacktestPipelineOrchestrator().run(
        report=report,
        risk_level="HIGH",
    )

    naive_time = datetime(
        2026,
        7,
        24,
        6,
        5,
        4,
    )

    writer = BacktestPipelineTimestampedJSONWriter(
        now_provider=lambda: naive_time,
    )

    written_file = writer.write(
        result=result,
        output_directory=tmp_path,
    )

    assert written_file.name == (
        "strategy-theta-20260724T060504Z.json"
    )


def test_timestamped_json_writer_rejects_before_directory_creation(
    tmp_path: Path,
) -> None:
    report = BacktestFinalReport(
        strategy_id="../strategy",
        decision="PASS",
        rank=1,
        score=95.0,
        confidence=0.95,
        summary="Unsafe strategy identifier",
    )
    result = BacktestPipelineOrchestrator().run(
        report=report,
        risk_level="LOW",
    )
    output_directory = tmp_path / "missing" / "exports"
    writer = BacktestPipelineTimestampedJSONWriter()

    with pytest.raises(ValueError):
        writer.write(
            result=result,
            output_directory=output_directory,
        )

    assert not output_directory.exists()
    assert list(tmp_path.rglob("*")) == []


def test_timestamped_json_writer_output_is_direct_child(
    tmp_path: Path,
) -> None:
    report = BacktestFinalReport(
        strategy_id="strategy-direct-child",
        decision="PASS",
        rank=1,
        score=95.0,
        confidence=0.95,
        summary="Safe strategy identifier",
    )
    result = BacktestPipelineOrchestrator().run(
        report=report,
        risk_level="LOW",
    )
    fixed_now = datetime(
        2026,
        7,
        24,
        12,
        0,
        0,
        tzinfo=timezone.utc,
    )
    output_directory = tmp_path / "exports"
    writer = BacktestPipelineTimestampedJSONWriter(
        now_provider=lambda: fixed_now,
    )

    written_file = writer.write(
        result=result,
        output_directory=output_directory,
    )

    assert written_file.parent == output_directory
    assert written_file.name == (
        "strategy-direct-child-20260724T120000Z.json"
    )
