from typing import Any, Dict


MIN_WATCH_SAMPLES = 5
MIN_READY_SAMPLES = 20
MIN_DIRECTION_SHARE = 70.0
MIN_AVERAGE_CHANGE = 0.01


class AdaptiveRecommendationEngine:
    """
    Converts aggregated learning statistics into review readiness.

    Shadow mode only:
    - does not change adaptive weights;
    - does not approve recommendations;
    - only evaluates whether evidence is mature enough for review.
    """

    @staticmethod
    def build(
        learning_stats: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        result: Dict[str, Dict[str, Any]] = {}

        for module, row in learning_stats.items():
            samples = int(row.get("samples") or 0)

            increase = int(row.get("increase") or 0)
            decrease = int(row.get("decrease") or 0)
            hold = int(row.get("hold") or 0)

            average_change = float(
                row.get("average_change") or 0.0
            )
            current_weight = float(
                row.get("current_weight") or 1.0
            )

            directional_total = increase + decrease

            if directional_total > 0:
                increase_share = round(
                    increase / directional_total * 100,
                    2,
                )
                decrease_share = round(
                    decrease / directional_total * 100,
                    2,
                )
            else:
                increase_share = 0.0
                decrease_share = 0.0

            dominant_direction = "hold"
            dominant_share = 0.0

            if increase_share > decrease_share:
                dominant_direction = "increase"
                dominant_share = increase_share

            elif decrease_share > increase_share:
                dominant_direction = "decrease"
                dominant_share = decrease_share

            stability = AdaptiveRecommendationEngine._stability_score(
                samples=samples,
                dominant_share=dominant_share,
                average_change=average_change,
            )

            status = AdaptiveRecommendationEngine._status(
                samples=samples,
                dominant_direction=dominant_direction,
                dominant_share=dominant_share,
                average_change=average_change,
            )

            suggested_weight = round(
                max(
                    0.10,
                    min(
                        2.00,
                        current_weight + average_change,
                    ),
                ),
                4,
            )

            result[module] = {
                "module": module,
                "samples": samples,
                "status": status,
                "dominant_direction": dominant_direction,
                "dominant_share": dominant_share,
                "increase_share": increase_share,
                "decrease_share": decrease_share,
                "hold_count": hold,
                "average_change": round(
                    average_change,
                    4,
                ),
                "current_weight": round(
                    current_weight,
                    4,
                ),
                "suggested_weight": suggested_weight,
                "stability_score": stability,
                "ready_for_review": (
                    status == "READY FOR REVIEW"
                ),
                "reason": AdaptiveRecommendationEngine._reason(
                    status=status,
                    samples=samples,
                    dominant_direction=dominant_direction,
                    dominant_share=dominant_share,
                    average_change=average_change,
                ),
                "mode": "Shadow only",
            }

        return result

    @staticmethod
    def _status(
        samples: int,
        dominant_direction: str,
        dominant_share: float,
        average_change: float,
    ) -> str:
        meaningful_change = (
            abs(average_change)
            >= MIN_AVERAGE_CHANGE
        )

        stable_direction = (
            dominant_direction in {
                "increase",
                "decrease",
            }
            and dominant_share
            >= MIN_DIRECTION_SHARE
        )

        if (
            samples >= MIN_READY_SAMPLES
            and meaningful_change
            and stable_direction
        ):
            return "READY FOR REVIEW"

        if samples >= MIN_WATCH_SAMPLES:
            return "WATCH"

        return "COLLECTING"

    @staticmethod
    def _stability_score(
        samples: int,
        dominant_share: float,
        average_change: float,
    ) -> float:
        sample_score = min(
            samples / MIN_READY_SAMPLES * 40,
            40,
        )

        direction_score = (
            dominant_share / 100 * 40
        )

        change_score = min(
            abs(average_change)
            / 0.03
            * 20,
            20,
        )

        return round(
            sample_score
            + direction_score
            + change_score,
            1,
        )

    @staticmethod
    def _reason(
        status: str,
        samples: int,
        dominant_direction: str,
        dominant_share: float,
        average_change: float,
    ) -> str:
        if status == "READY FOR REVIEW":
            return (
                f"{samples} samples show a stable "
                f"{dominant_direction} tendency "
                f"({dominant_share}%) with average change "
                f"{average_change:+.4f}."
            )

        if status == "WATCH":
            return (
                f"{samples} samples collected. "
                f"Dominant direction: {dominant_direction} "
                f"({dominant_share}%). More evidence is required."
            )

        return (
            f"Only {samples} samples collected. "
            f"At least {MIN_WATCH_SAMPLES} are needed for WATCH "
            f"and {MIN_READY_SAMPLES} for READY FOR REVIEW."
        )


def format_adaptive_recommendations(
    data: Dict[str, Dict[str, Any]],
) -> str:
    lines = [
        "🧠 <b>Adaptive Recommendations</b>",
        "<i>Shadow only — no weights changed</i>",
        "",
    ]

    for module in sorted(data):
        row = data[module]

        lines.extend([
            f"<b>{module}</b>",
            f"Status: {row['status']}",
            f"Samples: {row['samples']}",
            (
                "Dominant Direction: "
                f"{row['dominant_direction']} "
                f"({row['dominant_share']}%)"
            ),
            (
                "Average Change: "
                f"{row['average_change']:+.4f}"
            ),
            f"Current Weight: {row['current_weight']}",
            f"Suggested Weight: {row['suggested_weight']}",
            f"Stability: {row['stability_score']}/100",
            f"Reason: {row['reason']}",
            "",
        ])

    lines.append("Mode: Shadow only")

    return "\n".join(lines)
