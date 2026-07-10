from typing import Any, Dict, List, Optional

from app.domain.learning_recommendation import (
    LearningRecommendation,
)
from app.engine.module_intelligence import (
    evaluate_module_intelligence,
)
from app.engine.reflection_engine import (
    build_ai_reflection,
)
from app.repository.learning_recommendation_repository import (
    LearningRecommendationRepository,
)
from app.services.prediction_review_service import (
    PredictionReviewService,
)
from app.services.recommendation_builder import (
    RecommendationBuilder,
)


DEFAULT_WEIGHTS = {
    "Probability Engine": 0.70,
    "Campaign Detector": 0.90,
    "Wallet Behaviour": 0.80,
    "Scenario Engine": 0.85,
    "Risk Engine": 1.10,
    "Decision Engine": 1.00,
}


class RecommendationPipeline:
    """
    Runs the complete reflection-to-recommendation workflow.

    Shadow mode only:
    - builds real Prediction Review;
    - calculates Module Intelligence;
    - builds AI Reflection;
    - creates LearningRecommendation objects;
    - saves recommendations to SQLite;
    - does not change production weights.
    """

    def __init__(
        self,
        review_service: Optional[PredictionReviewService] = None,
        repository: Optional[
            LearningRecommendationRepository
        ] = None,
        current_weights: Optional[Dict[str, float]] = None,
    ) -> None:
        self.review_service = (
            review_service
            or PredictionReviewService()
        )
        self.repository = (
            repository
            or LearningRecommendationRepository()
        )
        self.current_weights = dict(
            current_weights
            or DEFAULT_WEIGHTS
        )

    def run(
        self,
        prediction_id: int,
        include_hold: bool = True,
        prevent_duplicates: bool = True,
    ) -> Dict[str, Any]:
        review = self.review_service.get_review(
            prediction_id
        )

        if review is None:
            return {
                "status": "not_found",
                "prediction_id": prediction_id,
                "saved": [],
                "skipped": [],
                "error": "Prediction not found.",
                "mode": "Shadow only",
            }

        outcome_v2 = review.get("outcome_v2")
        lifecycle = review.get("lifecycle")

        if not outcome_v2 or not lifecycle:
            source = review.get(
                "lifecycle_source",
                {},
            )

            return {
                "status": "lifecycle_unavailable",
                "prediction_id": prediction_id,
                "saved": [],
                "skipped": [],
                "error": (
                    source.get("error")
                    or "Lifecycle data unavailable."
                ),
                "mode": "Shadow only",
            }

        modules = evaluate_module_intelligence(
            outcome_v2=outcome_v2,
            lifecycle=lifecycle,
            ai_snapshot=review.get("ai") or {},
        )

        reflection = build_ai_reflection(
            module_intelligence=modules,
            outcome_v2=outcome_v2,
            lifecycle=lifecycle,
        )

        recommendations = RecommendationBuilder.build(
            reflection=reflection,
            current_weights=self.current_weights,
            prediction_id=prediction_id,
            include_hold=include_hold,
        )

        saved: List[LearningRecommendation] = []
        skipped: List[Dict[str, Any]] = []

        for recommendation in recommendations:
            if (
                prevent_duplicates
                and self._already_exists(
                    prediction_id=prediction_id,
                    module=recommendation.module,
                )
            ):
                skipped.append({
                    "module": recommendation.module,
                    "reason": (
                        "Recommendation already exists "
                        "for this prediction and module."
                    ),
                })
                continue

            saved.append(
                self.repository.save(
                    recommendation
                )
            )

        return {
            "status": "completed",
            "prediction_id": prediction_id,
            "review": review,
            "module_intelligence": modules,
            "reflection": reflection,
            "saved": saved,
            "skipped": skipped,
            "saved_count": len(saved),
            "skipped_count": len(skipped),
            "mode": "Shadow only",
        }

    def _already_exists(
        self,
        prediction_id: int,
        module: str,
    ) -> bool:
        existing = self.repository.list_by_module(
            module=module,
            limit=1000,
        )

        return any(
            item.prediction_id == prediction_id
            for item in existing
        )


def format_recommendation_pipeline(
    result: Dict[str, Any],
) -> str:
    status = result.get("status")

    if status != "completed":
        return (
            "🧠 <b>Recommendation Pipeline</b>\n\n"
            f"Status: {status}\n"
            f"Prediction ID: "
            f"{result.get('prediction_id')}\n"
            f"Error: {result.get('error')}\n"
            "Mode: Shadow only"
        )

    lines = [
        "🧠 <b>Recommendation Pipeline</b>",
        "<i>Shadow only — weights were not changed</i>",
        "",
        f"Prediction ID: {result['prediction_id']}",
        f"Saved: {result['saved_count']}",
        f"Skipped: {result['skipped_count']}",
        "",
    ]

    for item in result["saved"]:
        change = item.suggested_change

        change_text = (
            f"+{change:.2f}"
            if change > 0
            else f"{change:.2f}"
        )

        lines.extend([
            f"<b>{item.module}</b>",
            f"Recommendation ID: "
            f"{item.recommendation_id}",
            f"Current Weight: "
            f"{item.current_weight}",
            f"Suggested Change: "
            f"{change_text}",
            f"Suggested Weight: "
            f"{item.suggested_weight}",
            f"Status: {item.status}",
            "",
        ])

    if result["skipped"]:
        lines.append("<b>Skipped:</b>")

        for item in result["skipped"]:
            lines.append(
                f"• {item['module']}: "
                f"{item['reason']}"
            )

        lines.append("")

    lines.append("Mode: Shadow only")

    return "\n".join(lines)
