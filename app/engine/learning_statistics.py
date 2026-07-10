from statistics import mean
from typing import Any, Dict, List

from app.domain.learning_recommendation import (
    LearningRecommendation,
)


class LearningStatisticsEngine:
    """
    Aggregates historical Learning Recommendations.

    Shadow only.
    Produces statistics.
    Does NOT modify weights.
    """

    @staticmethod
    def build(
        recommendations: List[LearningRecommendation],
    ) -> Dict[str, Dict[str, Any]]:

        grouped: Dict[
            str,
            List[LearningRecommendation]
        ] = {}

        for item in recommendations:
            grouped.setdefault(
                item.module,
                [],
            ).append(item)

        result = {}

        for module, rows in grouped.items():

            scores = [
                r.average_module_score
                for r in rows
                if r.average_module_score is not None
            ]

            confidence = [
                r.confidence
                for r in rows
            ]

            changes = [
                r.suggested_change
                for r in rows
            ]

            pending = sum(
                r.status == "pending"
                for r in rows
            )

            approved = sum(
                r.status == "approved"
                for r in rows
            )

            applied = sum(
                r.status == "applied"
                for r in rows
            )

            increase = sum(
                r.suggested_change > 0
                for r in rows
            )

            decrease = sum(
                r.suggested_change < 0
                for r in rows
            )

            hold = sum(
                r.suggested_change == 0
                for r in rows
            )

            current_weight = rows[-1].current_weight

            avg_change = (
                mean(changes)
                if changes
                else 0.0
            )

            suggested_weight = (
                current_weight
                + avg_change
            )

            result[module] = {

                "module": module,

                "samples": len(rows),

                "pending": pending,
                "approved": approved,
                "applied": applied,

                "increase": increase,
                "decrease": decrease,
                "hold": hold,

                "average_score": (
                    round(mean(scores), 2)
                    if scores
                    else None
                ),

                "average_confidence": round(
                    mean(confidence),
                    2,
                ),

                "average_change": round(
                    avg_change,
                    4,
                ),

                "current_weight": round(
                    current_weight,
                    4,
                ),

                "suggested_weight": round(
                    suggested_weight,
                    4,
                ),

                "ready_for_review":
                    len(rows) >= 20,

                "mode":
                    "Shadow only",
            }

        return result


def format_learning_statistics(
    stats: Dict[str, Dict[str, Any]],
) -> str:

    lines = [
        "🧠 <b>Learning Statistics</b>",
        "<i>Shadow only</i>",
        "",
    ]

    for module in sorted(stats):

        row = stats[module]

        ready = (
            "READY"
            if row["ready_for_review"]
            else "Collecting"
        )

        lines.extend([

            f"<b>{module}</b>",

            f"Samples: {row['samples']}",

            f"Average Change: "
            f"{row['average_change']:+.4f}",

            f"Average Score: "
            f"{row['average_score']}",

            f"Average Confidence: "
            f"{row['average_confidence']}",

            f"Current Weight: "
            f"{row['current_weight']}",

            f"Suggested Weight: "
            f"{row['suggested_weight']}",

            f"Pending: {row['pending']}",

            f"Approved: {row['approved']}",

            f"Applied: {row['applied']}",

            f"Increase: {row['increase']}",

            f"Decrease: {row['decrease']}",

            f"Hold: {row['hold']}",

            f"Status: {ready}",

            "",
        ])

    lines.append(
        "Mode: Shadow only"
    )

    return "\n".join(lines)
