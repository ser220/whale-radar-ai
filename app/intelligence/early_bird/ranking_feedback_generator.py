from .ranking_feedback_signal import RankingFeedbackSignal


class EarlyBirdRankingFeedbackGenerator:
    def generate(
        self,
        pattern: str,
        direction: str,
        historical_win_rate: float,
    ) -> RankingFeedbackSignal:

        if not 0.0 <= historical_win_rate <= 1.0:
            raise ValueError("historical_win_rate must be between 0 and 1")

        adjustment = historical_win_rate * 20.0

        return RankingFeedbackSignal(
            pattern=pattern,
            direction=direction,
            confidence_adjustment=adjustment,
            reason=(
                f"historical performance win rate "
                f"{historical_win_rate:.2f}"
            ),
        )
