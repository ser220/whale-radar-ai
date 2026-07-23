from typing import Any, Dict

from app.backtest.pipeline.models import (
    BacktestPipelineResult,
)


class BacktestPipelineSerializer:
    """
    Serializes a completed backtest pipeline result
    into a JSON-compatible dictionary.
    """

    def serialize(
        self,
        result: BacktestPipelineResult,
    ) -> Dict[str, Any]:
        return {
            "report": {
                "strategy_id": result.report.strategy_id,
                "decision": result.report.decision,
                "rank": result.report.rank,
                "score": result.report.score,
                "confidence": result.report.confidence,
                "summary": result.report.summary,
            },
            "summary": {
                "strategy_id": result.summary.strategy_id,
                "decision": result.summary.decision,
                "headline": result.summary.headline,
                "explanation": result.summary.explanation,
                "risk_level": result.summary.risk_level,
                "confidence": result.summary.confidence,
            },
            "review": {
                "strategy_id": result.review.strategy_id,
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
                "confidence": result.review.confidence,
            },
        }
