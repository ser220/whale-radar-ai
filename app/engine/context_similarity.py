from collections import defaultdict
from typing import Any, Dict, List, Optional

from app.engine.context_statistics import (
    ContextStatisticsEngine,
)
from app.repository.prediction_context_repository import (
    PredictionContextRepository,
)


FIELD_WEIGHTS = {
    "market_regime": 30.0,
    "volatility_regime": 20.0,
    "asset_trend": 20.0,
    "btc_trend": 15.0,
    "session": 15.0,
}

MIN_SIMILARITY = 40.0
MATURE_SAMPLE_COUNT = 20


class ContextSimilarityEngine:
    """
    Finds historically similar prediction contexts.

    Current stage:
    - uses stored prediction contexts;
    - uses Context Statistics as historical evidence;
    - does not alter confidence or production weights;
    - returns analytical Shadow Mode results only.
    """

    def __init__(
        self,
        context_repository: Optional[
            PredictionContextRepository
        ] = None,
        statistics_engine: Optional[
            ContextStatisticsEngine
        ] = None,
    ) -> None:
        self.context_repository = (
            context_repository
            or PredictionContextRepository()
        )

        self.statistics_engine = (
            statistics_engine
            or ContextStatisticsEngine()
        )

    def find_for_prediction(
        self,
        prediction_id: int,
        limit: int = 10,
        min_similarity: float = MIN_SIMILARITY,
    ) -> Dict[str, Any]:
        prediction_id = int(prediction_id)

        context = self.context_repository.get(
            prediction_id
        )

        if context is None:
            return {
                "status": "context_not_found",
                "prediction_id": prediction_id,
                "current_context": None,
                "matches": [],
                "match_count": 0,
                "error": (
                    "Prediction context was not found."
                ),
                "mode": "Shadow only",
            }

        statistics = self.statistics_engine.build(
            limit=5000,
            exclude_prediction_id=prediction_id,
        )

        grouped = self._group_statistics(
            statistics
        )

        matches: List[Dict[str, Any]] = []

        current_values = {
            "market_regime": context.market_regime,
            "volatility_regime": (
                context.volatility_regime
            ),
            "asset_trend": context.asset_trend,
            "btc_trend": context.btc_trend,
            "session": context.session,
        }

        for context_key, rows in grouped.items():
            if not rows:
                continue

            candidate_values = {
                "market_regime": rows[0].get(
                    "market_regime"
                ),
                "volatility_regime": rows[0].get(
                    "volatility_regime"
                ),
                "asset_trend": rows[0].get(
                    "asset_trend"
                ),
                "btc_trend": rows[0].get(
                    "btc_trend"
                ),
                "session": rows[0].get(
                    "session"
                ),
            }

            similarity = self._similarity_score(
                current=current_values,
                candidate=candidate_values,
                exact_key=(
                    context_key
                    == context.context_key
                ),
            )

            if similarity < float(
                min_similarity
            ):
                continue

            summary = self._summarize_match(
                context_key=context_key,
                similarity=similarity,
                rows=rows,
            )

            matches.append(summary)

        matches.sort(
            key=lambda item: (
                -item["similarity"],
                -item["prediction_samples"],
                -item["recommendation_samples"],
            )
        )

        matches = matches[
            :max(int(limit), 1)
        ]

        return {
            "status": "completed",
            "prediction_id": prediction_id,
            "current_context": {
                "context_id": context.context_id,
                "context_key": context.context_key,
                "asset": context.asset,
                "market_regime": (
                    context.market_regime
                ),
                "volatility_regime": (
                    context.volatility_regime
                ),
                "asset_trend": (
                    context.asset_trend
                ),
                "btc_trend": context.btc_trend,
                "session": context.session,
            },
            "matches": matches,
            "match_count": len(matches),
            "error": None,
            "mode": "Shadow only",
        }

    @staticmethod
    def _group_statistics(
        rows: List[Dict[str, Any]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        grouped: Dict[
            str,
            List[Dict[str, Any]]
        ] = defaultdict(list)

        for row in rows:
            context_key = str(
                row.get("context_key")
                or ""
            ).strip()

            if context_key:
                grouped[context_key].append(
                    row
                )

        return dict(grouped)

    @classmethod
    def _similarity_score(
        cls,
        current: Dict[str, Any],
        candidate: Dict[str, Any],
        exact_key: bool,
    ) -> float:
        if exact_key:
            return 100.0

        score = 0.0
        available_weight = 0.0

        for field, weight in (
            FIELD_WEIGHTS.items()
        ):
            current_value = cls._normalize(
                current.get(field)
            )
            candidate_value = cls._normalize(
                candidate.get(field)
            )

            if cls._is_unknown(
                current_value
            ):
                continue

            if cls._is_unknown(
                candidate_value
            ):
                continue

            available_weight += weight

            if current_value == candidate_value:
                score += weight

            elif field in {
                "asset_trend",
                "btc_trend",
            }:
                if (
                    current_value == "neutral"
                    or candidate_value == "neutral"
                ):
                    score += weight * 0.35

            elif field == "session":
                if cls._sessions_related(
                    current_value,
                    candidate_value,
                ):
                    score += weight * 0.40

        if available_weight <= 0:
            return 0.0

        normalized_score = (
            score
            / available_weight
            * 100.0
        )

        return round(
            max(
                0.0,
                min(
                    100.0,
                    normalized_score,
                ),
            ),
            1,
        )

    @classmethod
    def _summarize_match(
        cls,
        context_key: str,
        similarity: float,
        rows: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        prediction_ids = set()

        recommendation_samples = 0
        module_consistency = []
        module_scores = []
        module_summaries = []

        for row in rows:
            ids = row.get(
                "prediction_ids"
            ) or []

            prediction_ids.update(
                int(item)
                for item in ids
            )

            recommendation_samples += int(
                row.get("samples") or 0
            )

            module_consistency.append(
                float(
                    row.get(
                        "dominant_share"
                    )
                    or 0.0
                )
            )

            average_score = row.get(
                "average_score"
            )

            if average_score is not None:
                module_scores.append(
                    float(average_score)
                )

            module_summaries.append({
                "module": row.get("module"),
                "samples": int(
                    row.get("samples") or 0
                ),
                "average_score": (
                    round(
                        float(average_score),
                        2,
                    )
                    if average_score is not None
                    else None
                ),
                "average_change": round(
                    float(
                        row.get(
                            "average_change"
                        )
                        or 0.0
                    ),
                    4,
                ),
                "dominant_direction": (
                    row.get(
                        "dominant_direction"
                    )
                ),
                "dominant_share": round(
                    float(
                        row.get(
                            "dominant_share"
                        )
                        or 0.0
                    ),
                    2,
                ),
                "status": row.get("status"),
            })

        prediction_samples = len(
            prediction_ids
        )

        sample_maturity = min(
            prediction_samples
            / MATURE_SAMPLE_COUNT,
            1.0,
        )

        average_consistency = (
            sum(module_consistency)
            / len(module_consistency)
            if module_consistency
            else 0.0
        )

        historical_confidence = (
            similarity
            * 0.45
            + average_consistency
            * 0.35
            + sample_maturity
            * 100.0
            * 0.20
        ) * sample_maturity

        historical_confidence = round(
            max(
                0.0,
                min(
                    100.0,
                    historical_confidence,
                ),
            ),
            1,
        )

        return {
            "context_key": context_key,
            "similarity": similarity,
            "prediction_samples": (
                prediction_samples
            ),
            "recommendation_samples": (
                recommendation_samples
            ),
            "average_module_score": (
                round(
                    sum(module_scores)
                    / len(module_scores),
                    2,
                )
                if module_scores
                else None
            ),
            "average_consistency": round(
                average_consistency,
                2,
            ),
            "historical_confidence": (
                historical_confidence
            ),
            "maturity": cls._maturity(
                prediction_samples
            ),
            "prediction_ids": sorted(
                prediction_ids
            ),
            "modules": sorted(
                module_summaries,
                key=lambda item: (
                    item["module"] or ""
                ),
            ),
        }

    @staticmethod
    def _maturity(
        samples: int,
    ) -> str:
        if samples >= 20:
            return "MATURE"

        if samples >= 5:
            return "DEVELOPING"

        return "COLLECTING"

    @staticmethod
    def _normalize(
        value: Any,
    ) -> str:
        return str(
            value or "unknown"
        ).strip().lower()

    @staticmethod
    def _is_unknown(
        value: str,
    ) -> bool:
        return value in {
            "",
            "unknown",
            "none",
            "null",
        }

    @staticmethod
    def _sessions_related(
        first: str,
        second: str,
    ) -> bool:
        related = {
            "london": {
                "overlap",
            },
            "new-york": {
                "overlap",
            },
            "overlap": {
                "london",
                "new-york",
            },
        }

        return second in related.get(
            first,
            set(),
        )


def format_context_similarity(
    result: Dict[str, Any],
    max_matches: int = 5,
) -> str:
    if result.get("status") != "completed":
        return "\n".join([
            "🧠 <b>Similar Context Search</b>",
            "",
            f"Prediction ID: "
            f"{result.get('prediction_id')}",
            f"Status: {result.get('status')}",
            f"Error: {result.get('error')}",
            "",
            "Mode: Shadow only",
        ])

    current = result.get(
        "current_context"
    ) or {}

    matches = result.get(
        "matches"
    ) or []

    lines = [
        "🧠 <b>Similar Context Search</b>",
        "<i>Historical analysis only</i>",
        "",
        (
            "Prediction ID: "
            f"{result.get('prediction_id')}"
        ),
        f"Asset: {current.get('asset')}",
        (
            "Current Context: "
            f"{current.get('context_key')}"
        ),
        f"Matches: {len(matches)}",
        "",
    ]

    if not matches:
        lines.extend([
            "No sufficiently similar historical "
            "contexts were found.",
            "",
            "Mode: Shadow only",
        ])

        return "\n".join(lines)

    for index, match in enumerate(
        matches[:max_matches],
        start=1,
    ):
        lines.extend([
            "────────────",
            (
                f"<b>Match #{index}</b>"
            ),
            match["context_key"],
            (
                "Similarity: "
                f"{match['similarity']}%"
            ),
            (
                "Historical Predictions: "
                f"{match['prediction_samples']}"
            ),
            (
                "Recommendation Samples: "
                f"{match['recommendation_samples']}"
            ),
            (
                "Average Module Score: "
                f"{match['average_module_score']}"
            ),
            (
                "Consistency: "
                f"{match['average_consistency']}%"
            ),
            (
                "Historical Confidence: "
                f"{match['historical_confidence']}/100"
            ),
            (
                "Maturity: "
                f"{match['maturity']}"
            ),
            "",
        ])

        for module in match[
            "modules"
        ]:
            lines.append(
                f"• <b>{module['module']}</b>: "
                f"{module['dominant_direction']} "
                f"{module['dominant_share']}%, "
                f"score {module['average_score']}"
            )

        lines.append("")

    lines.append(
        "Mode: Shadow only"
    )

    return "\n".join(lines)
