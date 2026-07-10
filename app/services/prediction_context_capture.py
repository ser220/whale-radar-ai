from typing import Any, Dict, Optional

from app.repository.prediction_context_repository import (
    PredictionContextRepository,
)
from app.services.prediction_context_builder import (
    PredictionContextBuilder,
)


class PredictionContextCaptureService:
    """
    Builds and stores prediction context once per prediction.

    Safety:
    - idempotent: existing context is not replaced;
    - no external API calls;
    - failures are returned as data;
    - does not affect trading decisions or weights.
    """

    def __init__(
        self,
        context_repository: Optional[
            PredictionContextRepository
        ] = None,
        context_builder: Optional[
            PredictionContextBuilder
        ] = None,
    ) -> None:
        self.context_repository = (
            context_repository
            or PredictionContextRepository()
        )

        self.context_builder = (
            context_builder
            or PredictionContextBuilder()
        )

    def capture(
        self,
        prediction_id: int,
    ) -> Dict[str, Any]:
        prediction_id = int(prediction_id)

        existing = self.context_repository.get(
            prediction_id
        )

        if existing is not None:
            return {
                "prediction_id": prediction_id,
                "status": "existing",
                "saved": False,
                "context_id": existing.context_id,
                "context_key": existing.context_key,
                "error": None,
                "mode": "Shadow only",
            }

        try:
            context = self.context_builder.build(
                prediction_id
            )

            if context is None:
                return {
                    "prediction_id": prediction_id,
                    "status": "prediction_not_found",
                    "saved": False,
                    "context_id": None,
                    "context_key": None,
                    "error": (
                        "Prediction was not found."
                    ),
                    "mode": "Shadow only",
                }

            saved = self.context_repository.save(
                context
            )

            return {
                "prediction_id": prediction_id,
                "status": "saved",
                "saved": True,
                "context_id": saved.context_id,
                "context_key": saved.context_key,
                "error": None,
                "mode": "Shadow only",
            }

        except Exception as exc:
            return {
                "prediction_id": prediction_id,
                "status": "error",
                "saved": False,
                "context_id": None,
                "context_key": None,
                "error": str(exc),
                "mode": "Shadow only",
            }


def format_context_capture(
    result: Dict[str, Any],
) -> str:
    return "\n".join([
        "🌍 <b>Prediction Context Capture</b>",
        "",
        (
            "Prediction ID: "
            f"{result.get('prediction_id')}"
        ),
        f"Status: {result.get('status')}",
        f"Saved: {result.get('saved')}",
        (
            "Context ID: "
            f"{result.get('context_id')}"
        ),
        (
            "Context Key: "
            f"{result.get('context_key')}"
        ),
        (
            "Error: "
            f"{result.get('error')}"
        ),
        "",
        "Mode: Shadow only",
    ])
