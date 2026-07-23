import json

from app.backtest.pipeline.json_exporter import (
    BacktestPipelineJSONExporter,
)
from app.backtest.pipeline.orchestrator import (
    BacktestPipelineOrchestrator,
)
from app.backtest.report import (
    BacktestFinalReport,
)


def test_backtest_pipeline_json_exporter() -> None:
    report = BacktestFinalReport(
        strategy_id="strategy-gamma",
        decision="PASS",
        rank=1,
        score=91.5,
        confidence=0.91,
        summary="Strategy is suitable for production review",
    )

    result = BacktestPipelineOrchestrator().run(
        report=report,
        risk_level="LOW",
    )

    exported = BacktestPipelineJSONExporter().export(result)
    data = json.loads(exported)

    assert data["report"] == {
        "strategy_id": "strategy-gamma",
        "decision": "PASS",
        "rank": 1,
        "score": 91.5,
        "confidence": 0.91,
        "summary": "Strategy is suitable for production review",
    }

    assert data["summary"]["strategy_id"] == "strategy-gamma"
    assert data["summary"]["risk_level"] == "LOW"
    assert data["summary"]["confidence"] == 0.91

    assert data["review"]["strategy_id"] == "strategy-gamma"
    assert data["review"]["confidence"] == 0.91

    assert isinstance(data["review"]["strengths"], list)
    assert isinstance(data["review"]["risks"], list)
    assert isinstance(data["review"]["recommended_actions"], list)


def test_json_exporter_uses_stable_formatting() -> None:
    data = {
        "zeta": 2,
        "alpha": 1,
    }

    exported = BacktestPipelineJSONExporter().export_data(data)

    assert exported == (
        '{\n'
        '  "alpha": 1,\n'
        '  "zeta": 2\n'
        '}'
    )
