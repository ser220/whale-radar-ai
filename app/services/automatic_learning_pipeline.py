from typing import Any, Dict, Iterable, List

from app.services.recommendation_pipeline import (
    RecommendationPipeline,
)


class AutomaticLearningPipeline:
    """
    Automatically runs the Shadow Learning pipeline
    for evaluated predictions.

    Safety:
    - production weights are not changed;
    - errors are isolated per prediction;
    - duplicate recommendations are prevented;
    - one failed prediction does not stop the others.
    """

    def __init__(
        self,
        recommendation_pipeline: RecommendationPipeline = None,
    ) -> None:
        self.recommendation_pipeline = (
            recommendation_pipeline
            or RecommendationPipeline()
        )

    def run_for_prediction(
        self,
        prediction_id: int,
    ) -> Dict[str, Any]:
        prediction_id = int(prediction_id)

        try:
            result = self.recommendation_pipeline.run(
                prediction_id=prediction_id,
                include_hold=True,
                prevent_duplicates=True,
            )

            return {
                "prediction_id": prediction_id,
                "status": result.get(
                    "status",
                    "unknown",
                ),
                "saved": int(
                    result.get("saved_count") or 0
                ),
                "skipped": int(
                    result.get("skipped_count") or 0
                ),
                "error": result.get("error"),
                "mode": "Shadow only",
            }

        except Exception as exc:
            return {
                "prediction_id": prediction_id,
                "status": "error",
                "saved": 0,
                "skipped": 0,
                "error": str(exc),
                "mode": "Shadow only",
            }

    def run_for_predictions(
        self,
        prediction_ids: Iterable[int],
    ) -> Dict[str, Any]:
        ids = [
            int(prediction_id)
            for prediction_id in prediction_ids
        ]

        processed: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []

        saved_total = 0
        skipped_total = 0

        for prediction_id in ids:
            result = self.run_for_prediction(
                prediction_id
            )

            processed.append(result)

            saved_total += result["saved"]
            skipped_total += result["skipped"]

            if result["status"] == "error":
                errors.append({
                    "prediction_id": prediction_id,
                    "error": result["error"],
                })

        return {
            "predictions_received": len(ids),
            "processed_count": len(processed),
            "error_count": len(errors),
            "saved_total": saved_total,
            "skipped_total": skipped_total,
            "processed": processed,
            "errors": errors,
            "mode": "Shadow only",
        }


def run_learning_pipeline(
    prediction_id: int,
) -> Dict[str, Any]:
    """
    Convenience entry point for one prediction.
    """

    pipeline = AutomaticLearningPipeline()

    return pipeline.run_for_prediction(
        prediction_id
    )


def format_automatic_learning(
    result: Dict[str, Any],
) -> str:
    lines = [
        "🧠 <b>Automatic Learning</b>",
        "<i>Shadow only — production weights unchanged</i>",
        "",
        (
            "Predictions Received: "
            f"{result.get('predictions_received', 0)}"
        ),
        (
            "Predictions Processed: "
            f"{result.get('processed_count', 0)}"
        ),
        (
            "Recommendations Saved: "
            f"{result.get('saved_total', 0)}"
        ),
        (
            "Recommendations Skipped: "
            f"{result.get('skipped_total', 0)}"
        ),
        f"Errors: {result.get('error_count', 0)}",
    ]

    errors = result.get("errors") or []

    if errors:
        lines.extend([
            "",
            "<b>Errors:</b>",
        ])

        for item in errors:
            lines.append(
                f"• Prediction "
                f"{item.get('prediction_id')}: "
                f"{item.get('error')}"
            )

    lines.extend([
        "",
        "Mode: Shadow only",
    ])

    return "\n".join(lines)
