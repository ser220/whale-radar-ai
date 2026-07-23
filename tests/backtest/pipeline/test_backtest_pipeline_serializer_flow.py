from app.backtest.pipeline import (
    BacktestPipelineOrchestrator,
    BacktestPipelineSerializer,
)
from app.backtest.report import (
    BacktestFinalReport,
)


def test_pipeline_serializer_flow() -> None:
    report = BacktestFinalReport(
        strategy_id="strategy-beta",
        decision="REVIEW",
        rank=2,
        score=78.5,
        confidence=0.78,
        summary="Strategy requires additional validation",
    )

    result = BacktestPipelineOrchestrator().run(
        report=report,
        risk_level="MEDIUM",
    )

    data = BacktestPipelineSerializer().serialize(
        result
    )

    assert data == {
        "report": {
            "strategy_id": "strategy-beta",
            "decision": "REVIEW",
            "rank": 2,
            "score": 78.5,
            "confidence": 0.78,
            "summary": (
                "Strategy requires additional validation"
            ),
        },
        "summary": {
            "strategy_id": "strategy-beta",
            "decision": "REVIEW",
            "headline": result.summary.headline,
            "explanation": result.summary.explanation,
            "risk_level": "MEDIUM",
            "confidence": 0.78,
        },
        "review": {
            "strategy_id": "strategy-beta",
            "verdict": result.review.verdict,
            "production_readiness": (
                result.review.production_readiness
            ),
            "strengths": list(
                result.review.strengths
            ),
            "risks": list(
                result.review.risks
            ),
            "recommended_actions": list(
                result.review.recommended_actions
            ),
            "confidence": 0.78,
        },
    }
