from app.backtest.pipeline import (
    BacktestPipelineOrchestrator,
    BacktestPipelineSerializer,
)
from app.backtest.report import (
    BacktestFinalReport,
)


def test_pipeline_serializer() -> None:
    report = BacktestFinalReport(
        strategy_id="strategy-alpha",
        decision="PASS",
        rank=1,
        score=95.0,
        confidence=0.95,
        summary="Excellent strategy",
    )

    result = BacktestPipelineOrchestrator().run(
        report=report,
        risk_level="LOW",
    )

    data = BacktestPipelineSerializer().serialize(
        result
    )

    assert data["report"]["strategy_id"] == "strategy-alpha"
    assert data["report"]["decision"] == "PASS"

    assert data["summary"]["risk_level"] == "LOW"

    assert data["review"]["verdict"] == "APPROVE"
