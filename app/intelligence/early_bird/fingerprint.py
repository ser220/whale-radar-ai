"""Stable fingerprint generation for Early Bird shadow state."""

import hashlib
import json
from typing import Any, Mapping


def build_early_bird_fingerprint(
    payload: Mapping[str, Any],
) -> str:
    """
    Build deterministic fingerprint from Early Bird payload.
    """

    if not isinstance(payload, Mapping):
        raise TypeError(
            "payload must be a mapping"
        )

    normalized = json.dumps(
        dict(payload),
        sort_keys=True,
        default=str,
        separators=(
            ",",
            ":",
        ),
    )

    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()


__all__ = [
    "build_early_bird_fingerprint",
]
