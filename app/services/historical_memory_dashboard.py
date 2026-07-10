from typing import Any, Dict, Optional

from app.engine.context_maturity import (
    ContextMaturityEngine,
)
from app.engine.context_similarity import (
    ContextSimilarityEngine,
)
from app.services.decision_ab_comparison import (
    DecisionABComparisonService,
)


class HistoricalMemoryDashboardService:
    def __init__(
        self,
        similarity_engine: Optional[
            ContextSimilarityEngine
        ] = None,
        maturity_engine: Optional[
            ContextMaturityEngine
        ] = None,
        ab_service: Optional[
            DecisionABComparisonService
        ] = None,
    ) -> None:
        self.similarity_engine = (
            similarity_engine
            or ContextSimilarityEngine()
        )
        self.maturity_engine = (
            maturity_engine
            or ContextMaturityEngine()
        )
        self.ab_service = (
            ab_service
            or DecisionABComparisonService()
        )

    def build(
        self,
        prediction_id: int,
    ) -> Dict[str, Any]:
        prediction_id = int(prediction_id)

        similarity = (
            self.similarity_engine
            .find_for_prediction(
                prediction_id=prediction_id,
                limit=5,
            )
        )

        if similarity.get("status") != "completed":
            return {
                "status": similarity.get(
                    "status",
                    "context_unavailable",
                ),
                "prediction_id": prediction_id,
                "current_context": similarity.get(
                    "current_context"
                ),
                "similarity": similarity,
                "maturity": None,
                "decision_ab": None,
                "production_gate": self._closed_gate(
                    similarity.get("error")
                    or "Prediction context unavailable."
                ),
                "error": similarity.get("error"),
                "mode": "Shadow only",
            }

        maturity = (
            self.maturity_engine
            .evaluate_prediction(
                prediction_id=prediction_id,
                limit=5,
            )
        )

        decision_ab = (
            self.ab_service.compare(
                prediction_id
            )
        )

        production_gate = (
            self._build_production_gate(
                maturity=maturity,
                decision_ab=decision_ab,
            )
        )

        matches = similarity.get("matches") or []
        best_match = matches[0] if matches else None

        overall_maturity = (
            maturity.get("overall") or {}
        )

        return {
            "status": "completed",
            "prediction_id": prediction_id,
            "asset": (
                decision_ab.get("asset")
                or (
                    similarity.get(
                        "current_context"
                    )
                    or {}
                ).get("asset")
            ),
            "direction": decision_ab.get(
                "direction"
            ),
            "current_context": similarity.get(
                "current_context"
            ),
            "historical_matches": len(matches),
            "best_match": best_match,
            "memory_level": (
                overall_maturity.get(
                    "best_level"
                )
                or "NEW"
            ),
            "memory_status": (
                overall_maturity.get(
                    "status"
                )
                or "NOT_READY"
            ),
            "recommended_history_weight": float(
                overall_maturity.get(
                    "recommended_history_weight"
                )
                or 0.0
            ),
            "similarity": similarity,
            "maturity": maturity,
            "decision_ab": decision_ab,
            "production_gate": production_gate,
            "error": None,
            "mode": "Shadow only",
        }

    @staticmethod
    def _build_production_gate(
        maturity: Dict[str, Any],
        decision_ab: Dict[str, Any],
    ) -> Dict[str, Any]:
        maturity_overall = (
            maturity.get("overall") or {}
        )

        maturity_eligible = bool(
            maturity_overall.get(
                "production_eligible"
            )
        )

        ab_completed = (
            decision_ab.get("status")
            == "completed"
        )

        comparison = (
            decision_ab.get("comparison")
            or {}
        )

        history_available = (
            comparison.get("boost_status")
            == "completed"
        )

        enabled = (
            maturity_eligible
            and ab_completed
            and history_available
        )

        if not maturity_eligible:
            reason = (
                "Historical memory has not reached "
                "production maturity."
            )
        elif not ab_completed:
            reason = (
                "A/B decision comparison is unavailable."
            )
        elif not history_available:
            reason = (
                "No independent historical evidence "
                "is available for this prediction."
            )
        else:
            reason = (
                "Historical memory passed the maturity "
                "and comparison gates."
            )

        return {
            "enabled": enabled,
            "state": (
                "ELIGIBLE"
                if enabled
                else "OFF"
            ),
            "maturity_eligible": maturity_eligible,
            "ab_completed": ab_completed,
            "history_available": history_available,
            "reason": reason,
            "mode": "Shadow only",
        }

    @staticmethod
    def _closed_gate(
        reason: str,
    ) -> Dict[str, Any]:
        return {
            "enabled": False,
            "state": "OFF",
            "maturity_eligible": False,
            "ab_completed": False,
            "history_available": False,
            "reason": reason,
            "mode": "Shadow only",
        }


def format_historical_memory_dashboard(
    result: Dict[str, Any],
) -> str:
    if result.get("status") != "completed":
        gate = (
            result.get("production_gate")
            or {}
        )

        return "\n".join([
            "🧠 <b>Historical Memory Dashboard</b>",
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
            (
                "Production Gate: "
                f"{gate.get('state', 'OFF')}"
            ),
            (
                "Reason: "
                f"{gate.get('reason')}"
            ),
            "",
            "Production decision unchanged.",
        ])

    current_context = (
        result.get("current_context") or {}
    )
    best_match = (
        result.get("best_match") or {}
    )
    decision_ab = (
        result.get("decision_ab") or {}
    )
    baseline = (
        decision_ab.get("baseline") or {}
    )
    historical_shadow = (
        decision_ab.get(
            "historical_shadow"
        ) or {}
    )
    comparison = (
        decision_ab.get("comparison") or {}
    )
    gate = (
        result.get("production_gate") or {}
    )

    lines = [
        "🧠 <b>Historical Memory Dashboard</b>",
        "<i>Unified shadow diagnostic</i>",
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
        "",
        "<b>Current Context</b>",
        str(
            current_context.get("context_key")
            or "Unavailable"
        ),
        "",
        "<b>Historical Memory</b>",
        (
            "Independent Matches: "
            f"{result.get('historical_matches', 0)}"
        ),
        (
            "Memory Level: "
            f"{result.get('memory_level')}"
        ),
        (
            "Memory Status: "
            f"{result.get('memory_status')}"
        ),
        (
            "Recommended History Weight: "
            f"{result.get('recommended_history_weight', 0) * 100:.2f}%"
        ),
    ]

    if best_match:
        lines.extend([
            (
                "Best Similarity: "
                f"{best_match.get('similarity', 0)}%"
            ),
            (
                "Historical Predictions: "
                f"{best_match.get('prediction_samples', 0)}"
            ),
            (
                "Historical Confidence: "
                f"{best_match.get('historical_confidence', 0)}/100"
            ),
        ])
    else:
        lines.append(
            "Best Match: unavailable"
        )

    lines.extend([
        "",
        "<b>A/B Decision</b>",
        (
            "Baseline: "
            f"{baseline.get('score', 0)}/100 "
            f"({baseline.get('band', 'N/A')})"
        ),
        (
            "Historical Shadow: "
            f"{historical_shadow.get('score', 0)}/100 "
            f"({historical_shadow.get('band', 'N/A')})"
        ),
        (
            "Score Change: "
            f"{float(comparison.get('score_change') or 0):+.2f}"
        ),
        (
            "Band Changed: "
            f"{comparison.get('band_changed', False)}"
        ),
        (
            "History Status: "
            f"{comparison.get('boost_status', 'unavailable')}"
        ),
        "",
        "<b>Production Gate</b>",
        (
            "State: "
            f"{gate.get('state', 'OFF')}"
        ),
        (
            "Memory Eligible: "
            f"{gate.get('maturity_eligible', False)}"
        ),
        (
            "Independent History: "
            f"{gate.get('history_available', False)}"
        ),
        (
            "Reason: "
            f"{gate.get('reason')}"
        ),
        "",
        "Mode: Shadow only",
        "Production decision unchanged.",
    ])

    return "\n".join(lines)
