"""State boundary for Early Bird shadow watcher."""

from datetime import datetime
from typing import Dict


class EarlyBirdShadowState:
    """In-memory state for shadow notifications."""

    def __init__(self) -> None:
        self.last_scan_at = None
        self.candidate_fingerprints: Dict[str, str] = {}
        self.sent_fingerprints: Dict[str, str] = {}

    def update_candidate(
        self,
        *,
        asset: str,
        fingerprint: str,
        observed_at: datetime,
    ) -> None:
        if not isinstance(asset, str) or not asset.strip():
            raise ValueError(
                "asset must not be empty"
            )

        if not isinstance(fingerprint, str) or not fingerprint.strip():
            raise ValueError(
                "fingerprint must not be empty"
            )

        if not isinstance(observed_at, datetime):
            raise TypeError(
                "observed_at must be datetime"
            )

        self.candidate_fingerprints[
            asset.upper()
        ] = fingerprint

        self.last_scan_at = observed_at

    def is_new_candidate(
        self,
        asset: str,
        fingerprint: str,
    ) -> bool:
        normalized = asset.upper()

        return (
            self.candidate_fingerprints.get(normalized)
            != fingerprint
        )


__all__ = [
    "EarlyBirdShadowState",
]
