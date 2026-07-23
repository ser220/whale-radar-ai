from app.backtest.summary.models import (
    BacktestAISummary,
)


class AISummaryGenerator:
    """
    Generates AI-style interpretation
    from backtest decision results.
    """

    def generate(
        self,
        strategy_id: str,
        decision: str,
        score: float,
        risk_level: str,
        confidence: float,
    ) -> BacktestAISummary:

        if decision == "PASS":

            headline = (
                "Strategy approved"
            )

            explanation = (
                "Backtest results indicate "
                "acceptable performance with "
                "a favorable risk profile."
            )

        elif decision == "REVIEW":

            headline = (
                "Strategy requires review"
            )

            explanation = (
                "Strategy shows potential but "
                "additional validation is required "
                "before deployment."
            )

        else:

            headline = (
                "Strategy rejected"
            )

            explanation = (
                "Backtest results do not satisfy "
                "current acceptance criteria."
            )

        return BacktestAISummary(
            strategy_id=strategy_id,
            decision=decision,
            headline=headline,
            explanation=explanation,
            risk_level=risk_level,
            confidence=confidence,
        )
