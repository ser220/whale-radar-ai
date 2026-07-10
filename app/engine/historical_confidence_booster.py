from typing import Dict, Any, Optional

from app.engine.context_similarity import (
    ContextSimilarityEngine,
)


BASE_HISTORY_WEIGHT = 0.30
FULL_MATURITY = 20


class HistoricalConfidenceBooster:
    """
    Boost module confidence using historical
    context performance.

    Shadow only.
    Production decisions remain unchanged.
    """

    def __init__(
        self,
        similarity_engine: Optional[
            ContextSimilarityEngine
        ] = None,
    ):
        self.similarity_engine = (
            similarity_engine
            or ContextSimilarityEngine()
        )

    def boost(
        self,
        prediction_id: int,
        current_modules: Dict[str, float],
    ) -> Dict[str, Any]:

        similarity = (
            self.similarity_engine.find_for_prediction(
                prediction_id,
                limit=1,
            )
        )

        if similarity["match_count"] == 0:
            return {
                "status": "no_history",
                "modules": {},
                "mode": "Shadow only",
            }

        match = similarity["matches"][0]

        samples = match["prediction_samples"]

        maturity = min(
            samples / FULL_MATURITY,
            1.0,
        )

        history_weight = (
            BASE_HISTORY_WEIGHT
            * maturity
        )

        current_weight = (
            1.0 - history_weight
        )

        history = {}

        for module in match["modules"]:

            history[
                module["module"]
            ] = module["average_score"]

        boosted = {}

        for module, current in (
            current_modules.items()
        ):

            historical = history.get(
                module,
                current,
            )

            boosted_score = round(
                current * current_weight
                + historical * history_weight,
                2,
            )

            boosted[module] = {
                "current": current,
                "historical": historical,
                "boosted": boosted_score,
                "samples": samples,
                "history_weight": round(
                    history_weight,
                    3,
                ),
            }

        return {
            "status": "completed",
            "prediction_id": prediction_id,
            "history_weight": round(
                history_weight,
                3,
            ),
            "modules": boosted,
            "mode": "Shadow only",
        }


def format_booster(
    result: Dict[str, Any],
) -> str:

    if result["status"] != "completed":

        return (
            "🧠 <b>Historical Confidence Booster</b>\n\n"
            "No historical data.\n\n"
            "Mode: Shadow only"
        )

    lines = [
        "🧠 <b>Historical Confidence Booster</b>",
        "<i>Shadow only</i>",
        "",
        f"Prediction: {result['prediction_id']}",
        (
            "History Weight: "
            f"{result['history_weight']}"
        ),
        "",
    ]

    for name, row in (
        result["modules"].items()
    ):

        lines.extend(
            [
                f"<b>{name}</b>",
                (
                    "Current: "
                    f"{row['current']}"
                ),
                (
                    "Historical: "
                    f"{row['historical']}"
                ),
                (
                    "Boosted: "
                    f"{row['boosted']}"
                ),
                "",
            ]
        )

    lines.append(
        "Mode: Shadow only"
    )

    return "\n".join(lines)
