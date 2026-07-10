from typing import Any, Dict, Optional

from app.engine.historical_confidence_booster import (
    HistoricalConfidenceBooster,
    format_booster,
)
from app.engine.module_intelligence import (
    evaluate_module_intelligence,
)
from app.services.prediction_review_service import (
    PredictionReviewService,
)


class ConfidenceBoostPreviewService:
    """
    Builds current module scores and previews
    historical context influence.

    Shadow only:
    - does not modify stored scores;
    - does not modify production decisions;
    - does not update weights;
    - uses current lifecycle data from PredictionReviewService.
    """

    def __init__(
        self,
        review_service: Optional[
            PredictionReviewService
        ] = None,
        booster: Optional[
            HistoricalConfidenceBooster
        ] = None,
    ) -> None:
        self.review_service = (
            review_service
            or PredictionReviewService()
        )

        self.booster = (
            booster
            or HistoricalConfidenceBooster()
        )

    def build(
        self,
        prediction_id: int,
    ) -> Dict[str, Any]:
        prediction_id = int(prediction_id)

        review = self.review_service.get_review(
            prediction_id
        )

        if review is None:
            return {
                "status": "prediction_not_found",
                "prediction_id": prediction_id,
                "current_scores": {},
                "boost_result": None,
                "error": "Prediction was not found.",
                "mode": "Shadow only",
            }

        lifecycle = review.get("lifecycle")
        outcome_v2 = review.get("outcome_v2")

        if not lifecycle or not outcome_v2:
            source = (
                review.get("lifecycle_source")
                or {}
            )

            return {
                "status": "lifecycle_unavailable",
                "prediction_id": prediction_id,
                "current_scores": {},
                "boost_result": None,
                "error": (
                    source.get("error")
                    or "Lifecycle data is unavailable."
                ),
                "mode": "Shadow only",
            }

        prediction = review.get(
            "prediction"
        ) or {}

        snapshot = prediction.get(
            "ai_snapshot"
        ) or {}

        module_results = (
            evaluate_module_intelligence(
                outcome_v2=outcome_v2,
                lifecycle=lifecycle,
                ai_snapshot=snapshot,
            )
        )

        current_scores = {
            module: float(
                data.get("score") or 0.0
            )
            for module, data in (
                module_results.items()
            )
        }

        boost_result = self.booster.boost(
            prediction_id=prediction_id,
            current_modules=current_scores,
        )

        return {
            "status": "completed",
            "prediction_id": prediction_id,
            "asset": prediction.get("asset"),
            "direction": prediction.get(
                "direction"
            ),
            "current_scores": current_scores,
            "module_results": module_results,
            "boost_result": boost_result,
            "lifecycle_source": review.get(
                "lifecycle_source"
            ),
            "error": None,
            "mode": "Shadow only",
        }


def format_confidence_boost_preview(
    result: Dict[str, Any],
) -> str:
    if result.get("status") != "completed":
        return "\n".join([
            "🧠 <b>Confidence Boost Preview</b>",
            "<i>Shadow only</i>",
            "",
            (
                "Prediction ID: "
                f"{result.get('prediction_id')}"
            ),
            (
                "Status: "
                f"{result.get('status')}"
            ),
            (
                "Error: "
                f"{result.get('error')}"
            ),
            "",
            "Production decision unchanged.",
        ])

    boost_result = (
        result.get("boost_result")
        or {}
    )

    source = (
        result.get("lifecycle_source")
        or {}
    )

    header = "\n".join([
        "🧠 <b>Confidence Boost Preview</b>",
        "<i>Historical context shadow comparison</i>",
        "",
        (
            "Prediction ID: "
            f"{result.get('prediction_id')}"
        ),
        f"Asset: {result.get('asset')}",
        (
            "Direction: "
            f"{result.get('direction')}"
        ),
        (
            "Lifecycle Source: "
            f"{source.get('name')}"
        ),
        (
            "Candles: "
            f"{source.get('candles', 0)}"
        ),
        "",
    ])

    return (
        header
        + format_booster(
            boost_result
        )
        + "\n\n"
        + "Production decision unchanged."
    )
