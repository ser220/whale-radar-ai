from typing import Any, Dict, Optional

from app.services.historical_memory_dashboard import (
    HistoricalMemoryDashboardService,
)


MATURITY_FACTORS = {
    "NEW": 0.0,
    "COLLECTING": 25.0,
    "RELIABLE": 60.0,
    "STRONG": 85.0,
    "INSTITUTIONAL": 100.0,
}


class AdaptiveTrustEngine:
    """
    Calculates explainable trust in historical memory.

    Trust combines:
    - context similarity;
    - module consistency;
    - memory maturity;
    - historical quality;
    - independent sample depth.

    Shadow only:
    - does not modify production decisions;
    - does not change module scores;
    - does not change weights;
    - does not write to the database.
    """

    def __init__(
        self,
        dashboard_service: Optional[
            HistoricalMemoryDashboardService
        ] = None,
    ) -> None:
        self.dashboard_service = (
            dashboard_service
            or HistoricalMemoryDashboardService()
        )

    def evaluate(
        self,
        prediction_id: int,
    ) -> Dict[str, Any]:
        prediction_id = int(prediction_id)

        dashboard = self.dashboard_service.build(
            prediction_id
        )

        if dashboard.get("status") != "completed":
            return self._empty_result(
                prediction_id=prediction_id,
                status=dashboard.get(
                    "status",
                    "dashboard_unavailable",
                ),
                reason=dashboard.get("error")
                or "Historical memory dashboard unavailable.",
                dashboard=dashboard,
            )

        matches = (
            dashboard.get("similarity", {})
            .get("matches")
            or []
        )

        maturity = dashboard.get(
            "maturity"
        ) or {}

        overall = maturity.get(
            "overall"
        ) or {}

        if not matches:
            return self._empty_result(
                prediction_id=prediction_id,
                status="no_history",
                reason=(
                    "No independent historical "
                    "contexts are available."
                ),
                dashboard=dashboard,
            )

        best_match = matches[0]

        samples = int(
            best_match.get(
                "prediction_samples"
            )
            or 0
        )

        similarity = self._clamp(
            best_match.get("similarity")
        )

        consistency = self._clamp(
            best_match.get(
                "average_consistency"
            )
        )

        historical_quality = self._clamp(
            best_match.get(
                "historical_confidence"
            )
        )

        maturity_level = str(
            overall.get("best_level")
            or dashboard.get(
                "memory_level"
            )
            or "NEW"
        ).upper()

        maturity_score = float(
            MATURITY_FACTORS.get(
                maturity_level,
                0.0,
            )
        )

        sample_score = self._sample_score(
            samples
        )

        components = {
            "similarity": {
                "value": round(
                    similarity,
                    1,
                ),
                "weight": 0.30,
            },
            "consistency": {
                "value": round(
                    consistency,
                    1,
                ),
                "weight": 0.30,
            },
            "maturity": {
                "value": round(
                    maturity_score,
                    1,
                ),
                "weight": 0.20,
            },
            "historical_quality": {
                "value": round(
                    historical_quality,
                    1,
                ),
                "weight": 0.10,
            },
            "independent_samples": {
                "value": round(
                    sample_score,
                    1,
                ),
                "weight": 0.10,
            },
        }

        raw_trust = sum(
            item["value"]
            * item["weight"]
            for item in components.values()
        )

        evidence_gate = self._evidence_gate(
            samples=samples,
            maturity_level=maturity_level,
        )

        trust_score = round(
            self._clamp(
                raw_trust
                * evidence_gate
            ),
            1,
        )

        trust_level = self._trust_level(
            trust_score
        )

        production_eligible = bool(
            overall.get(
                "production_eligible"
            )
        )

        return {
            "status": "completed",
            "prediction_id": prediction_id,
            "asset": dashboard.get("asset"),
            "direction": dashboard.get(
                "direction"
            ),
            "context_key": (
                dashboard.get(
                    "current_context"
                )
                or {}
            ).get("context_key"),
            "trust_score": trust_score,
            "trust_level": trust_level,
            "raw_trust_score": round(
                raw_trust,
                1,
            ),
            "evidence_gate": round(
                evidence_gate,
                3,
            ),
            "independent_samples": samples,
            "maturity_level": maturity_level,
            "components": components,
            "production_eligible": (
                production_eligible
            ),
            "recommended_history_weight": float(
                dashboard.get(
                    "recommended_history_weight"
                )
                or 0.0
            ),
            "reason": self._build_reason(
                trust_score=trust_score,
                trust_level=trust_level,
                samples=samples,
                maturity_level=maturity_level,
                similarity=similarity,
                consistency=consistency,
                production_eligible=(
                    production_eligible
                ),
            ),
            "dashboard": dashboard,
            "mode": "Shadow only",
        }

    @staticmethod
    def _sample_score(
        samples: int,
    ) -> float:
        """
        Saturates at 200 independent predictions.
        """
        if samples <= 0:
            return 0.0

        return min(
            samples / 200.0 * 100.0,
            100.0,
        )

    @staticmethod
    def _evidence_gate(
        samples: int,
        maturity_level: str,
    ) -> float:
        """
        Prevents high similarity from creating
        high trust on a tiny sample.
        """
        if samples < 5:
            return 0.0

        if maturity_level == "COLLECTING":
            return min(
                samples / 20.0,
                1.0,
            ) * 0.35

        if maturity_level == "RELIABLE":
            return 0.65

        if maturity_level == "STRONG":
            return 0.85

        if maturity_level == "INSTITUTIONAL":
            return 1.0

        return 0.0

    @staticmethod
    def _trust_level(
        score: float,
    ) -> str:
        if score >= 85.0:
            return "VERY HIGH"

        if score >= 70.0:
            return "HIGH"

        if score >= 45.0:
            return "MEDIUM"

        if score >= 15.0:
            return "LOW"

        return "NONE"

    @staticmethod
    def _build_reason(
        trust_score: float,
        trust_level: str,
        samples: int,
        maturity_level: str,
        similarity: float,
        consistency: float,
        production_eligible: bool,
    ) -> str:
        if samples < 5:
            return (
                "Trust is disabled because fewer than "
                "5 independent historical predictions "
                "are available."
            )

        eligibility_text = (
            "Memory is production-eligible."
            if production_eligible
            else "Memory is not production-eligible."
        )

        return (
            f"Trust is {trust_level} "
            f"({trust_score}/100) from "
            f"{samples} independent predictions, "
            f"{similarity:.1f}% similarity, "
            f"{consistency:.1f}% consistency, "
            f"and {maturity_level} maturity. "
            f"{eligibility_text}"
        )

    @classmethod
    def _empty_result(
        cls,
        prediction_id: int,
        status: str,
        reason: str,
        dashboard: Optional[
            Dict[str, Any]
        ] = None,
    ) -> Dict[str, Any]:
        return {
            "status": status,
            "prediction_id": prediction_id,
            "asset": (
                dashboard.get("asset")
                if dashboard
                else None
            ),
            "direction": (
                dashboard.get("direction")
                if dashboard
                else None
            ),
            "context_key": (
                (
                    dashboard.get(
                        "current_context"
                    )
                    or {}
                ).get("context_key")
                if dashboard
                else None
            ),
            "trust_score": 0.0,
            "trust_level": "NONE",
            "raw_trust_score": 0.0,
            "evidence_gate": 0.0,
            "independent_samples": 0,
            "maturity_level": "NEW",
            "components": {
                "similarity": {
                    "value": 0.0,
                    "weight": 0.30,
                },
                "consistency": {
                    "value": 0.0,
                    "weight": 0.30,
                },
                "maturity": {
                    "value": 0.0,
                    "weight": 0.20,
                },
                "historical_quality": {
                    "value": 0.0,
                    "weight": 0.10,
                },
                "independent_samples": {
                    "value": 0.0,
                    "weight": 0.10,
                },
            },
            "production_eligible": False,
            "recommended_history_weight": 0.0,
            "reason": reason,
            "dashboard": dashboard,
            "mode": "Shadow only",
        }

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


def format_adaptive_trust(
    result: Dict[str, Any],
) -> str:
    components = (
        result.get("components")
        or {}
    )

    lines = [
        "🧠 <b>Adaptive Trust Engine</b>",
        "<i>Explainable historical trust — Shadow only</i>",
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
            "Context: "
            f"{result.get('context_key') or 'Unavailable'}"
        ),
        "",
        "<b>Trust</b>",
        (
            "Score: "
            f"{result.get('trust_score', 0)}/100"
        ),
        (
            "Level: "
            f"{result.get('trust_level')}"
        ),
        (
            "Raw Score: "
            f"{result.get('raw_trust_score', 0)}/100"
        ),
        (
            "Evidence Gate: "
            f"{float(result.get('evidence_gate') or 0) * 100:.1f}%"
        ),
        (
            "Independent Samples: "
            f"{result.get('independent_samples', 0)}"
        ),
        (
            "Maturity: "
            f"{result.get('maturity_level')}"
        ),
        "",
        "<b>Trust Components</b>",
    ]

    labels = {
        "similarity": "Similarity",
        "consistency": "Consistency",
        "maturity": "Maturity",
        "historical_quality": (
            "Historical Quality"
        ),
        "independent_samples": (
            "Independent Samples"
        ),
    }

    for key, label in labels.items():
        item = components.get(key) or {}

        lines.append(
            f"{label}: "
            f"{item.get('value', 0)}/100 "
            f"(weight "
            f"{float(item.get('weight') or 0) * 100:.0f}%)"
        )

    lines.extend([
        "",
        "<b>Safety</b>",
        (
            "Production Eligible: "
            f"{result.get('production_eligible', False)}"
        ),
        (
            "Recommended History Weight: "
            f"{float(result.get('recommended_history_weight') or 0) * 100:.2f}%"
        ),
        (
            "Reason: "
            f"{result.get('reason')}"
        ),
        "",
        "Mode: Shadow only",
        "Production decision unchanged.",
    ])

    return "\n".join(lines)
