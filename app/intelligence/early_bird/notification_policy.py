"""Notification decision boundary for Early Bird shadow watcher."""

from typing import Optional


class EarlyBirdNotificationPolicy:
    """Decides whether a shadow notification is required."""

    def should_notify(
        self,
        *,
        previous: Optional[str],
        current: str,
    ) -> bool:
        if not isinstance(current, str) or not current.strip():
            raise ValueError(
                "current fingerprint must not be empty"
            )

        if previous is None:
            return True

        return previous != current


__all__ = [
    "EarlyBirdNotificationPolicy",
]
