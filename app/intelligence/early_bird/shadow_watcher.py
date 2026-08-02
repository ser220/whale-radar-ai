"""Early Bird shadow watcher orchestration boundary."""

from dataclasses import dataclass
from datetime import datetime, timezone

from app.intelligence.early_bird.fingerprint import (
    build_early_bird_fingerprint,
)
from app.intelligence.early_bird.notification_policy import (
    EarlyBirdNotificationPolicy,
)
from app.intelligence.early_bird.shadow_state import (
    EarlyBirdShadowState,
)


@dataclass(frozen=True)
class EarlyBirdShadowNotification:
    """Result of shadow notification evaluation."""

    asset: str
    notify: bool
    fingerprint: str


class EarlyBirdShadowWatcher:
    """Coordinates state, fingerprinting and notification policy."""

    def __init__(
        self,
        *,
        state=None,
        policy=None,
    ) -> None:
        self.state = (
            state
            or EarlyBirdShadowState()
        )
        self.policy = (
            policy
            or EarlyBirdNotificationPolicy()
        )

    def evaluate(
        self,
        *,
        asset: str,
        payload: dict,
    ) -> EarlyBirdShadowNotification:
        fingerprint = (
            build_early_bird_fingerprint(payload)
        )

        normalized_asset = asset.upper()

        previous = (
            self.state.candidate_fingerprints.get(
                normalized_asset
            )
        )

        notify = self.policy.should_notify(
            previous=previous,
            current=fingerprint,
        )

        self.state.update_candidate(
            asset=normalized_asset,
            fingerprint=fingerprint,
            observed_at=(
                payload.get("observed_at")
                or datetime.now(timezone.utc)
            ),
        )

        return EarlyBirdShadowNotification(
            asset=normalized_asset,
            notify=notify,
            fingerprint=fingerprint,
        )


__all__ = [
    "EarlyBirdShadowWatcher",
    "EarlyBirdShadowNotification",
]
