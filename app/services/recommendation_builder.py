from typing import Any, Dict, List

from app.domain.learning_recommendation import (
    LearningRecommendation,
)


class RecommendationBuilder:
    @staticmethod
    def build(
        reflection: Dict[str, Any],
        current_weights: Dict[str, float],
        prediction_id: int,
        include_hold: bool = True,
    ) -> List[LearningRecommendation]:
        recommendations: List[LearningRecommendation] = []

        reflection_items = reflection.get(
            "reflections",
            [],
        )

        for item in reflection_items:
            module = str(
                item.get("module") or ""
            ).strip()

            if not module:
                continue

            suggested_change = RecommendationBuilder._number(
                item.get("suggested_weight_change")
            )

            if not include_hold and suggested_change == 0:
                continue

            current_weight = RecommendationBuilder._number(
                current_weights.get(module, 1.0)
            )

            if current_weight <= 0:
                current_weight = 1.0

            module_score = RecommendationBuilder._clamp(
                item.get("score")
            )

            recommendation_text = str(
                item.get("recommendation")
                or "Continue collecting validated outcomes."
            ).strip()

            recommendation = LearningRecommendation(
                module=module,
                prediction_id=prediction_id,
                current_weight=current_weight,
                suggested_change=suggested_change,
                confidence=module_score,
                average_module_score=module_score,
                sample_count=1,
                reason=recommendation_text,
                evidence={
                    "assessment": item.get("assessment"),
                    "lesson": item.get("lesson"),
                    "status": item.get("status"),
                    "reflection_score": module_score,
                    "overall_outcome_score": reflection.get(
                        "overall_outcome_score"
                    ),
                    "overall_quality": reflection.get(
                        "overall_quality"
                    ),
                    "lifecycle_state": reflection.get(
                        "lifecycle_state"
                    ),
                    "mode": "Shadow only",
                },
            )

            recommendations.append(recommendation)

        return recommendations

    @staticmethod
    def _number(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _clamp(value: Any) -> float:
        return max(
            0.0,
            min(
                100.0,
                RecommendationBuilder._number(value),
            ),
        )
