from typing import Any, Dict, Optional

from app.services.confidence_boost_preview import (
    ConfidenceBoostPreviewService,
)


DEFAULT_MODULE_WEIGHTS = {
    "Probability Engine": 0.70,
    "Campaign Detector": 0.90,
    "Wallet Behaviour": 0.80,
    "Scenario Engine": 0.85,
    "Risk Engine": 1.10,
    "Decision Engine": 1.00,
}


class DecisionABComparisonService:
    """
    Compares baseline module scoring against
    history-adjusted module scoring.

    A = current module scores.
    B = historically boosted module scores.

    Shadow only:
    - does not alter production decisions;
    - does not write to the database;
    - does not update weights;
    - does not issue trading orders.
    """

    def __init__(
        self,
        preview_service: Optional[
            ConfidenceBoostPreviewService
        ] = None,
        module_weights: Optional[
            Dict[str, float]
        ] = None,
    ) -> None:
        self.preview_service = (
            preview_service
            or ConfidenceBoostPreviewService()
        )

        self.module_weights = dict(
            module_weights
            or DEFAULT_MODULE_WEIGHTS
        )

    def compare(
        self,
        prediction_id: int,
    ) -> Dict[str, Any]:
        prediction_id = int(prediction_id)

        preview = self.preview_service.build(
            prediction_id
        )

        if preview.get("status") != "completed":
            return {
                "status": preview.get(
                    "status",
                    "preview_unavailable",
                ),
                "prediction_id": prediction_id,
                "baseline": None,
                "historical_shadow": None,
                "comparison": None,
                "error": preview.get("error"),
                "mode": "Shadow only",
            }

        current_scores = {
            str(module): float(score)
            for module, score in (
                preview.get("current_scores")
                or {}
            ).items()
        }

        boost_result = (
            preview.get("boost_result")
            or {}
        )

        boost_status = boost_result.get(
            "status"
        )

        boosted_scores = self._extract_boosted_scores(
            current_scores=current_scores,
            boost_result=boost_result,
        )

        baseline = self._build_decision(
            scores=current_scores,
            label="Baseline",
        )

        historical_shadow = self._build_decision(
            scores=boosted_scores,
            label="Historical Shadow",
        )

        score_change = round(
            historical_shadow["score"]
            - baseline["score"],
            2,
        )

        band_changed = (
            baseline["band"]
            != historical_shadow["band"]
        )

        changed_modules = []

        for module in current_scores:
            before = current_scores[module]
            after = boosted_scores.get(
                module,
                before,
            )

            change = round(
                after - before,
                2,
            )

            if abs(change) >= 0.01:
                changed_modules.append({
                    "module": module,
                    "baseline": round(
                        before,
                        2,
                    ),
                    "historical_shadow": round(
                        after,
                        2,
                    ),
                    "change": change,
                })

        changed_modules.sort(
            key=lambda item: abs(
                item["change"]
            ),
            reverse=True,
        )

        comparison_status = self._comparison_status(
            boost_status=boost_status,
            score_change=score_change,
            band_changed=band_changed,
        )

        return {
            "status": "completed",
            "prediction_id": prediction_id,
            "asset": preview.get("asset"),
            "direction": preview.get(
                "direction"
            ),
            "baseline": baseline,
            "historical_shadow": (
                historical_shadow
            ),
            "comparison": {
                "score_change": score_change,
                "band_changed": band_changed,
                "changed_modules": (
                    changed_modules
                ),
                "changed_module_count": len(
                    changed_modules
                ),
                "boost_status": boost_status,
                "assessment": comparison_status,
            },
            "boost_result": boost_result,
            "lifecycle_source": preview.get(
                "lifecycle_source"
            ),
            "error": None,
            "mode": "Shadow only",
        }

    def _build_decision(
        self,
        scores: Dict[str, float],
        label: str,
    ) -> Dict[str, Any]:
        weighted_sum = 0.0
        total_weight = 0.0
        contributions = {}

        for module, weight in (
            self.module_weights.items()
        ):
            if module not in scores:
                continue

            score = self._clamp(
                scores[module]
            )

            normalized_weight = max(
                float(weight),
                0.0,
            )

            contribution = (
                score
                * normalized_weight
            )

            weighted_sum += contribution
            total_weight += normalized_weight

            contributions[module] = {
                "score": round(
                    score,
                    2,
                ),
                "weight": round(
                    normalized_weight,
                    4,
                ),
                "weighted_points": round(
                    contribution,
                    2,
                ),
            }

        final_score = (
            weighted_sum / total_weight
            if total_weight > 0
            else 0.0
        )

        final_score = round(
            self._clamp(final_score),
            2,
        )

        return {
            "label": label,
            "score": final_score,
            "band": self._decision_band(
                final_score
            ),
            "action": self._decision_action(
                final_score
            ),
            "module_count": len(
                contributions
            ),
            "total_weight": round(
                total_weight,
                4,
            ),
            "contributions": contributions,
        }

    @staticmethod
    def _extract_boosted_scores(
        current_scores: Dict[str, float],
        boost_result: Dict[str, Any],
    ) -> Dict[str, float]:
        if (
            boost_result.get("status")
            != "completed"
        ):
            return dict(current_scores)

        modules = (
            boost_result.get("modules")
            or {}
        )

        result = dict(current_scores)

        for module, data in modules.items():
            boosted = data.get("boosted")

            if boosted is None:
                boosted = data.get(
                    "boosted_score"
                )

            if boosted is None:
                continue

            try:
                result[module] = float(
                    boosted
                )
            except (
                TypeError,
                ValueError,
            ):
                continue

        return result

    @staticmethod
    def _decision_band(
        score: float,
    ) -> str:
        if score >= 80:
            return "VERY HIGH"

        if score >= 65:
            return "HIGH"

        if score >= 50:
            return "MODERATE"

        if score >= 35:
            return "LOW"

        return "VERY LOW"

    @staticmethod
    def _decision_action(
        score: float,
    ) -> str:
        if score >= 80:
            return "Strong setup"

        if score >= 65:
            return "Qualified setup"

        if score >= 50:
            return "Wait for confirmation"

        if score >= 35:
            return "Weak setup"

        return "Avoid"

    @staticmethod
    def _comparison_status(
        boost_status: Any,
        score_change: float,
        band_changed: bool,
    ) -> str:
        if boost_status != "completed":
            return (
                "No independent historical "
                "evidence was available."
            )

        if band_changed:
            return (
                "Historical context changed "
                "the decision band."
            )

        if abs(score_change) >= 5.0:
            return (
                "Historical context produced "
                "a material score change."
            )

        if abs(score_change) >= 1.0:
            return (
                "Historical context produced "
                "a moderate score change."
            )

        return (
            "Historical context produced "
            "only a minor score change."
        )

    @staticmethod
    def _clamp(
        value: Any,
    ) -> float:
        try:
            number = float(value)
        except (
            TypeError,
            ValueError,
        ):
            number = 0.0

        return max(
            0.0,
            min(
                100.0,
                number,
            ),
        )


def format_decision_ab_comparison(
    result: Dict[str, Any],
) -> str:
    if result.get("status") != "completed":
        return "\n".join([
            "⚖️ <b>A/B Decision Comparison</b>",
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

    baseline = result["baseline"]
    shadow = result[
        "historical_shadow"
    ]
    comparison = result["comparison"]

    lines = [
        "⚖️ <b>A/B Decision Comparison</b>",
        "<i>Baseline vs Historical Shadow</i>",
        "",
        (
            "Prediction ID: "
            f"{result['prediction_id']}"
        ),
        f"Asset: {result.get('asset')}",
        (
            "Direction: "
            f"{result.get('direction')}"
        ),
        "",
        "<b>A — Baseline</b>",
        (
            "Score: "
            f"{baseline['score']}/100"
        ),
        f"Band: {baseline['band']}",
        f"Action: {baseline['action']}",
        "",
        "<b>B — Historical Shadow</b>",
        (
            "Score: "
            f"{shadow['score']}/100"
        ),
        f"Band: {shadow['band']}",
        f"Action: {shadow['action']}",
        "",
        "<b>Comparison</b>",
        (
            "Score Change: "
            f"{comparison['score_change']:+.2f}"
        ),
        (
            "Band Changed: "
            f"{comparison['band_changed']}"
        ),
        (
            "Changed Modules: "
            f"{comparison['changed_module_count']}"
        ),
        (
            "History Status: "
            f"{comparison['boost_status']}"
        ),
        (
            "Assessment: "
            f"{comparison['assessment']}"
        ),
    ]

    changed_modules = (
        comparison.get(
            "changed_modules"
        )
        or []
    )

    if changed_modules:
        lines.extend([
            "",
            "<b>Largest Module Changes</b>",
        ])

        for item in changed_modules[:6]:
            lines.append(
                f"• {item['module']}: "
                f"{item['baseline']:.2f} "
                f"→ "
                f"{item['historical_shadow']:.2f} "
                f"({item['change']:+.2f})"
            )

    lines.extend([
        "",
        "Mode: Shadow only",
        "Production decision unchanged.",
    ])

    return "\n".join(lines)
