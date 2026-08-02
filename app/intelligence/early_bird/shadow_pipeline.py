"""Early Bird shadow notification pipeline."""

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from app.intelligence.early_bird.shadow_message import (
    build_shadow_message,
)
from app.intelligence.early_bird.shadow_watcher import (
    EarlyBirdShadowWatcher,
)


@dataclass(frozen=True)
class EarlyBirdShadowPipelineResult:
    """Result of one shadow pipeline execution."""

    notified: bool
    sent: bool
    message: str | None


class EarlyBirdShadowPipeline:
    """Connects shadow evaluation with notification transport."""

    def __init__(
        self,
        *,
        send_fn: Callable[[str], bool] | None = None,
        watcher: EarlyBirdShadowWatcher | None = None,
    ) -> None:
        self.send_fn = send_fn or (lambda _: False)
        self.watcher = (
            watcher
            or EarlyBirdShadowWatcher()
        )

    def process(
        self,
        *,
        asset: str,
        payload: Mapping[str, Any],
    ) -> EarlyBirdShadowPipelineResult:
        decision = self.watcher.evaluate(
            asset=asset,
            payload=dict(payload),
        )

        if not decision.notify:
            return EarlyBirdShadowPipelineResult(
                notified=False,
                sent=False,
                message=None,
            )

        message = build_shadow_message(
            asset=asset,
            payload=payload,
        )

        sent = bool(
            self.send_fn(message)
        )

        return EarlyBirdShadowPipelineResult(
            notified=True,
            sent=sent,
            message=message,
        )


__all__ = [
    "EarlyBirdShadowPipeline",
    "EarlyBirdShadowPipelineResult",
]
