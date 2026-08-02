"""Read-only Early Bird shadow demo orchestration."""

from typing import Any, Mapping, Optional

from app.intelligence.early_bird.shadow_message import (
    build_shadow_message,
)
from app.intelligence.early_bird.shadow_watcher import (
    EarlyBirdShadowWatcher,
)


_watcher = EarlyBirdShadowWatcher()


def run_shadow_demo(
    *,
    asset: str,
    payload: Mapping[str, Any],
) -> Optional[str]:
    """
    Evaluate one shadow payload.

    Returns formatted message only when
    notification is required.
    """

    result = _watcher.evaluate(
        asset=asset,
        payload=dict(payload),
    )

    if not result.notify:
        return None

    return build_shadow_message(
        asset=asset,
        payload=payload,
    )


__all__ = [
    "run_shadow_demo",
]
