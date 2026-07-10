from dataclasses import asdict, dataclass
from typing import Any, Dict, List


WAIT = "WAIT"
WATCH = "WATCH"
APPROVE = "APPROVE"
REJECT = "REJECT"


@dataclass
class LearningReview:
    module: str
    decision: str
    confidence: float
    samples: int
    agreement: float
    stability: float
    current_weight: float
    suggested_weight: float
    average_change: float
    dominant_direction: str
    reason: str
    mode: str = "Shadow only"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LearningReviewEngine:
    """
    Final review gate before any human-approved weight change.

    Shadow mode only:
    - does not change weights;
    - does not approve repository records;
    - does not apply recommendations.
    """

    MIN_WATCH_SAMPLES = 5
    MIN_APPROVE_SAMPLES = 20
    MIN_APPROVE_AGREEMENT = 80.0
    MIN_APPROVE_STABILITY = 80.0
    MIN_WATCH_AGREEMENT = 65.0
    MIN_WATCH_STABILITY = 60.0
    REJECT_AGREEMENT = 50.0

    @classmethod
    def build(
        cls,
        adaptive_recommendations: Dict[str, Dict[str, Any]],
    ) -> List[LearningReview]:
        reviews: List[LearningReview] = []

        for module, row in adaptive_recommendations.items():
            samples = int(row.get("samples") or 0)
            agreement = cls._clamp(
                row.get("dominant_share")
            )
            stability = cls._clamp(
                row.get("stability_score")
            )
            average_change = cls._number(
                row.get("average_change")
            )
            current_weight = cls._positive_number(
                row.get("current_weight"),
                default=1.0,
            )
            suggested_weight = cls._positive_number(
                row.get("suggested_weight"),
                default=current_weight,
            )
            dominant_direction = str(
                row.get("dominant_direction") or "hold"
            ).lower().strip()

            decision = cls._decision(
                samples=samples,
                agreement=agreement,
                stability=stability,
                average_change=average_change,
                dominant_direction=dominant_direction,
            )

            confidence = cls._confidence(
                samples=samples,
                agreement=agreement,
                stability=stability,
            )

            reason = cls._reason(
                decision=decision,
                samples=samples,
                agreement=agreement,
                stability=stability,
                average_change=average_change,
                dominant_direction=dominant_direction,
            )

            reviews.append(
                LearningReview(
                    module=module,
                    decision=decision,
                    confidence=confidence,
                    samples=samples,
                    agreement=agreement,
                    stability=stability,
                    current_weight=round(current_weight, 4),
                    suggested_weight=round(suggested_weight, 4),
                    average_change=round(average_change, 4),
                    dominant_direction=dominant_direction,
                    reason=reason,
                )
            )

        return sorted(
            reviews,
            key=lambda item: item.module,
        )

    @classmethod
    def _decision(
        cls,
        samples: int,
        agreement: float,
        stability: float,
        average_change: float,
        dominant_direction: str,
    ) -> str:
        meaningful_change = (
            abs(average_change) >= 0.01
        )

        if samples < cls.MIN_WATCH_SAMPLES:
            return WAIT

        if (
            dominant_direction != "hold"
            and agreement < cls.REJECT_AGREEMENT
        ):
            return REJECT

        if (
            samples >= cls.MIN_APPROVE_SAMPLES
            and agreement >= cls.MIN_APPROVE_AGREEMENT
            and stability >= cls.MIN_APPROVE_STABILITY
            and meaningful_change
            and dominant_direction in {"increase", "decrease"}
        ):
            return APPROVE

        if (
            samples >= cls.MIN_WATCH_SAMPLES
            and agreement >= cls.MIN_WATCH_AGREEMENT
            and stability >= cls.MIN_WATCH_STABILITY
        ):
            return WATCH

        return WAIT

    @classmethod
    def _confidence(
        cls,
        samples: int,
        agreement: float,
        stability: float,
    ) -> float:
        sample_maturity = min(
            samples / cls.MIN_APPROVE_SAMPLES,
            1.0,
        )

        evidence_quality = (
            agreement * 0.50
            + stability * 0.50
        )

        confidence = (
            evidence_quality
            * sample_maturity
        )

        return round(
            cls._clamp(confidence),
            1,
        )

    @classmethod
    def _reason(
        cls,
        decision: str,
        samples: int,
        agreement: float,
        stability: float,
        average_change: float,
        dominant_direction: str,
    ) -> str:
        if decision == APPROVE:
            return (
                f"{samples} samples show a stable "
                f"{dominant_direction} recommendation with "
                f"{agreement}% agreement, "
                f"{stability}/100 stability, and average change "
                f"{average_change:+.4f}."
            )

        if decision == WATCH:
            return (
                f"{samples} samples show a developing "
                f"{dominant_direction} tendency with "
                f"{agreement}% agreement and "
                f"{stability}/100 stability. "
                "Continue collecting evidence."
            )

        if decision == REJECT:
            return (
                f"Recommendation agreement is only "
                f"{agreement}%, below the minimum reliable level. "
                "The proposed weight change is not consistent."
            )

        return (
            f"Only {samples} samples are available, or the evidence "
            f"is not yet mature enough. Agreement: {agreement}%, "
            f"stability: {stability}/100."
        )

    @staticmethod
    def _number(
        value: Any,
    ) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @classmethod
    def _positive_number(
        cls,
        value: Any,
        default: float,
    ) -> float:
        number = cls._number(value)

        if number > 0:
            return number

        return default

    @classmethod
    def _clamp(
        cls,
        value: Any,
    ) -> float:
        return max(
            0.0,
            min(
                100.0,
                cls._number(value),
            ),
        )


def format_learning_review(
    reviews: List[LearningReview],
) -> str:
    if not reviews:
        return (
            "🧠 <b>Learning Review</b>\n\n"
            "No review data available.\n"
            "Mode: Shadow only"
        )

    icons = {
        APPROVE: "✅",
        WATCH: "🟡",
        WAIT: "⏳",
        REJECT: "❌",
    }

    lines = [
        "🧠 <b>Learning Review</b>",
        "<i>Shadow only — human approval required</i>",
        "",
    ]

    for review in reviews:
        icon = icons.get(
            review.decision,
            "",
        )

        lines.extend([
            f"<b>{review.module}</b>",
            f"Decision: {review.decision} {icon}",
            f"Confidence: {review.confidence}/100",
            f"Samples: {review.samples}",
            f"Agreement: {review.agreement}%",
            f"Stability: {review.stability}/100",
            (
                "Dominant Direction: "
                f"{review.dominant_direction}"
            ),
            (
                "Average Change: "
                f"{review.average_change:+.4f}"
            ),
            f"Current Weight: {review.current_weight}",
            f"Suggested Weight: {review.suggested_weight}",
            f"Reason: {review.reason}",
            "",
        ])

    lines.append(
        "Mode: Shadow only"
    )

    return "\n".join(lines)
