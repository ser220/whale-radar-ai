from typing import Any, Dict, Optional

from app.domain.prediction import Prediction
from app.engine.outcome_intelligence import calculate_outcome_score
from app.repository.prediction_repository import PredictionRepository


class PredictionReviewService:
    def __init__(
        self,
        repository: Optional[PredictionRepository] = None,
    ) -> None:
        self.repository = repository or PredictionRepository()

    def get_review(self, prediction_id: int) -> Optional[Dict[str, Any]]:
        prediction = self.repository.get(prediction_id)

        if prediction is None:
            return None

        outcome = self._build_outcome(prediction)

        return {
            "prediction": prediction.to_dict(),
            "market": {
                "regime": prediction.ai_snapshot.get(
                    "market_regime",
                    {},
                ),
                "heat": prediction.ai_snapshot.get(
                    "market_heat",
                    {},
                ),
            },
            "ai": {
                "probability": prediction.ai_snapshot.get(
                    "probability",
                    {},
                ),
                "campaign": prediction.ai_snapshot.get(
                    "campaign",
                    {},
                ),
                "wallet_behaviour": prediction.ai_snapshot.get(
                    "wallet_behaviour",
                    {},
                ),
                "decision": prediction.ai_snapshot.get(
                    "decision",
                    {},
                ),
            },
            "outcome": outcome,
            "learning": {
                "checked": prediction.outcome_checked,
                "target_hit": prediction.target_hit,
                "accuracy": prediction.accuracy,
                "checked_at": prediction.checked_at,
            },
            "summary": {
                "asset": prediction.asset,
                "direction": prediction.direction,
                "quality": outcome["label"],
                "score": outcome["score"],
            },
        }

    @staticmethod
    def _build_outcome(prediction: Prediction) -> Dict[str, Any]:
        evaluation_price = (
            prediction.current_price
            if prediction.current_price is not None
            else prediction.entry_price
        )

        return calculate_outcome_score(
            direction=prediction.direction,
            entry_price=prediction.entry_price,
            target_price=prediction.target_price,
            current_price=evaluation_price,
            expected_move=prediction.expected_move,
            eta=prediction.eta,
        )


def format_prediction_review(review: Optional[Dict[str, Any]]) -> str:
    if review is None:
        return "Prediction not found."

    prediction = review["prediction"]
    outcome = review["outcome"]
    learning = review["learning"]

    return (
        "🧠 <b>Prediction Review</b>\n\n"
        f"ID: {prediction['id']}\n"
        f"Asset: {prediction['asset']}\n"
        f"Direction: {prediction['direction']}\n"
        f"Entry: {prediction['entry_price']}\n"
        f"Target: {prediction['target_price']}\n"
        f"Current: {prediction.get('current_price')}\n"
        f"Checked: {learning['checked']}\n\n"
        "<b>Outcome Intelligence:</b>\n"
        f"Outcome Score: {outcome['score']}/100\n"
        f"Quality: {outcome['label']}\n"
        f"Direction Score: {outcome['direction_score']}/40\n"
        f"Target Score: {outcome['target_score']}/40\n"
        f"Move Score: {outcome['move_score']}/20\n"
        f"Actual Move: {outcome.get('actual_move', 0)}%\n"
        f"Target Hit: {outcome.get('target_hit')}\n"
        f"Direction Correct: {outcome.get('direction_correct')}\n"
        "Mode: Shadow only"
    )
