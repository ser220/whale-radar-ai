from typing import Any, Dict, List, Optional

from app.engine.context_similarity import (
    ContextSimilarityEngine,
)


MATURITY_LEVELS = (
    {
        "name": "NEW",
        "min_samples": 0,
        "max_samples": 4,
        "max_history_weight": 0.00,
    },
    {
        "name": "COLLECTING",
        "min_samples": 5,
        "max_samples": 19,
        "max_history_weight": 0.05,
    },
    {
        "name": "RELIABLE",
        "min_samples": 20,
        "max_samples": 49,
        "max_history_weight": 0.15,
    },
    {
        "name": "STRONG",
        "min_samples": 50,
        "max_samples": 199,
        "max_history_weight": 0.25,
    },
    {
        "name": "INSTITUTIONAL",
        "min_samples": 200,
        "max_samples": None,
        "max_history_weight": 0.30,
    },
)


class ContextMaturityEngine:
    """
    Evaluates maturity and reliability of historical contexts.

    Shadow only:
    - does not alter production decisions;
    - does not change weights;
    - only calculates memory readiness.
    """

    def __init__(
        self,
        similarity_engine: Optional[
            ContextSimilarityEngine
        ] = None,
    ) -> None:
        self.similarity_engine = (
            similarity_engine
            or ContextSimilarityEngine()
        )

    def evaluate_prediction(
        self,
        prediction_id: int,
        limit: int = 5,
    ) -> Dict[str, Any]:
        prediction_id = int(prediction_id)

        similarity = (
            self.similarity_engine
            .find_for_prediction(
                prediction_id=prediction_id,
                limit=limit,
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
                "contexts": [],
                "overall": self._empty_overall(),
                "error": similarity.get("error"),
                "mode": "Shadow only",
            }

        matches = similarity.get(
            "matches"
        ) or []

        contexts = [
            self._evaluate_match(match)
            for match in matches
        ]

        overall = self._build_overall(
            contexts
        )

        return {
            "status": "completed",
            "prediction_id": prediction_id,
            "current_context": similarity.get(
                "current_context"
            ),
            "contexts": contexts,
            "overall": overall,
            "error": None,
            "mode": "Shadow only",
        }

    def _evaluate_match(
        self,
        match: Dict[str, Any],
    ) -> Dict[str, Any]:
        samples = int(
            match.get(
                "prediction_samples"
            )
            or 0
        )

        similarity = float(
            match.get("similarity")
            or 0.0
        )

        consistency = float(
            match.get(
                "average_consistency"
            )
            or 0.0
        )

        historical_confidence = float(
            match.get(
                "historical_confidence"
            )
            or 0.0
        )

        level = self._level_for_samples(
            samples
        )

        sample_score = min(
            samples / 200.0 * 100.0,
            100.0,
        )

        quality_score = (
            sample_score * 0.45
            + consistency * 0.25
            + similarity * 0.20
            + historical_confidence * 0.10
        )

        quality_score = round(
            max(
                0.0,
                min(
                    100.0,
                    quality_score,
                ),
            ),
            1,
        )

        readiness = self._readiness(
            level_name=level["name"],
            quality_score=quality_score,
            consistency=consistency,
        )

        recommended_weight = (
            self._recommended_history_weight(
                level=level,
                quality_score=quality_score,
                consistency=consistency,
                similarity=similarity,
            )
        )

        return {
            "context_key": match.get(
                "context_key"
            ),
            "samples": samples,
            "recommendation_samples": int(
                match.get(
                    "recommendation_samples"
                )
                or 0
            ),
            "similarity": round(
                similarity,
                1,
            ),
            "consistency": round(
                consistency,
                1,
            ),
            "historical_confidence": round(
                historical_confidence,
                1,
            ),
            "level": level["name"],
            "quality_score": quality_score,
            "readiness": readiness,
            "max_history_weight": round(
                float(
                    level[
                        "max_history_weight"
                    ]
                ),
                3,
            ),
            "recommended_history_weight": round(
                recommended_weight,
                3,
            ),
            "production_eligible": (
                readiness == "READY"
            ),
            "reason": self._reason(
                samples=samples,
                level=level["name"],
                quality_score=quality_score,
                consistency=consistency,
            ),
        }

    @staticmethod
    def _level_for_samples(
        samples: int,
    ) -> Dict[str, Any]:
        for level in MATURITY_LEVELS:
            minimum = int(
                level["min_samples"]
            )

            maximum = level[
                "max_samples"
            ]

            if samples < minimum:
                continue

            if (
                maximum is None
                or samples <= int(maximum)
            ):
                return dict(level)

        return dict(
            MATURITY_LEVELS[-1]
        )

    @staticmethod
    def _readiness(
        level_name: str,
        quality_score: float,
        consistency: float,
    ) -> str:
        if (
            level_name
            in {
                "STRONG",
                "INSTITUTIONAL",
            }
            and quality_score >= 70.0
            and consistency >= 70.0
        ):
            return "READY"

        if (
            level_name == "RELIABLE"
            and quality_score >= 55.0
            and consistency >= 60.0
        ):
            return "WATCH"

        if level_name == "COLLECTING":
            return "COLLECTING"

        return "NOT_READY"

    @staticmethod
    def _recommended_history_weight(
        level: Dict[str, Any],
        quality_score: float,
        consistency: float,
        similarity: float,
    ) -> float:
        max_weight = float(
            level["max_history_weight"]
        )

        if max_weight <= 0:
            return 0.0

        quality_factor = max(
            0.0,
            min(
                quality_score / 100.0,
                1.0,
            ),
        )

        consistency_factor = max(
            0.0,
            min(
                consistency / 100.0,
                1.0,
            ),
        )

        similarity_factor = max(
            0.0,
            min(
                similarity / 100.0,
                1.0,
            ),
        )

        return (
            max_weight
            * quality_factor
            * consistency_factor
            * similarity_factor
        )

    @staticmethod
    def _reason(
        samples: int,
        level: str,
        quality_score: float,
        consistency: float,
    ) -> str:
        if samples < 5:
            return (
                "Fewer than 5 independent "
                "historical predictions are available."
            )

        if samples < 20:
            return (
                "History is still collecting. "
                "At least 20 independent predictions "
                "are required for RELIABLE maturity."
            )

        if consistency < 60.0:
            return (
                "Sample count is sufficient, but "
                "module agreement remains weak."
            )

        if quality_score < 55.0:
            return (
                "Historical quality score is not "
                "high enough for decision influence."
            )

        return (
            f"Context maturity is {level} with "
            f"quality {quality_score}/100 and "
            f"consistency {consistency}%."
        )

    @staticmethod
    def _build_overall(
        contexts: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not contexts:
            return ContextMaturityEngine._empty_overall()

        best = max(
            contexts,
            key=lambda item: (
                item[
                    "recommended_history_weight"
                ],
                item["quality_score"],
                item["samples"],
            ),
        )

        ready_count = sum(
            item["readiness"] == "READY"
            for item in contexts
        )

        watch_count = sum(
            item["readiness"] == "WATCH"
            for item in contexts
        )

        return {
            "best_context_key": best[
                "context_key"
            ],
            "best_level": best["level"],
            "best_quality_score": best[
                "quality_score"
            ],
            "recommended_history_weight": best[
                "recommended_history_weight"
            ],
            "ready_contexts": ready_count,
            "watch_contexts": watch_count,
            "production_eligible": (
                ready_count > 0
            ),
            "status": (
                "READY"
                if ready_count > 0
                else (
                    "WATCH"
                    if watch_count > 0
                    else "NOT_READY"
                )
            ),
        }

    @staticmethod
    def _empty_overall() -> Dict[str, Any]:
        return {
            "best_context_key": None,
            "best_level": "NEW",
            "best_quality_score": 0.0,
            "recommended_history_weight": 0.0,
            "ready_contexts": 0,
            "watch_contexts": 0,
            "production_eligible": False,
            "status": "NOT_READY",
        }


def format_context_maturity(
    result: Dict[str, Any],
    max_contexts: int = 5,
) -> str:
    lines = [
        "🧠 <b>Historical Memory Maturity</b>",
        "<i>Shadow only — production unchanged</i>",
        "",
        (
            "Prediction ID: "
            f"{result.get('prediction_id')}"
        ),
        (
            "Status: "
            f"{result.get('status')}"
        ),
        "",
    ]

    contexts = result.get(
        "contexts"
    ) or []

    if not contexts:
        lines.extend([
            "No independent historical "
            "contexts are available.",
            "",
        ])
    else:
        for index, item in enumerate(
            contexts[:max_contexts],
            start=1,
        ):
            lines.extend([
                "────────────",
                f"<b>Context #{index}</b>",
                str(item["context_key"]),
                (
                    "Level: "
                    f"{item['level']}"
                ),
                (
                    "Readiness: "
                    f"{item['readiness']}"
                ),
                (
                    "Samples: "
                    f"{item['samples']}"
                ),
                (
                    "Similarity: "
                    f"{item['similarity']}%"
                ),
                (
                    "Consistency: "
                    f"{item['consistency']}%"
                ),
                (
                    "Quality: "
                    f"{item['quality_score']}/100"
                ),
                (
                    "Max History Weight: "
                    f"{item['max_history_weight'] * 100:.1f}%"
                ),
                (
                    "Recommended Weight: "
                    f"{item['recommended_history_weight'] * 100:.2f}%"
                ),
                (
                    "Production Eligible: "
                    f"{item['production_eligible']}"
                ),
                (
                    "Reason: "
                    f"{item['reason']}"
                ),
                "",
            ])

    overall = result.get(
        "overall"
    ) or {}

    lines.extend([
        "<b>Overall</b>",
        (
            "Status: "
            f"{overall.get('status')}"
        ),
        (
            "Best Level: "
            f"{overall.get('best_level')}"
        ),
        (
            "Recommended History Weight: "
            f"{float(overall.get('recommended_history_weight') or 0) * 100:.2f}%"
        ),
        (
            "Production Eligible: "
            f"{overall.get('production_eligible')}"
        ),
        "",
        "Mode: Shadow only",
    ])

    return "\n".join(lines)
