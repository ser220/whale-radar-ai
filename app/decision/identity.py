from __future__ import annotations

import hashlib


def build_decision_id(
    candidate_reference: str,
    intelligence_reference: str,
    version: str = "v1",
) -> str:
    """
    Build a deterministic decision identifier.
    """

    payload = (
        f"{version}:"
        f"{candidate_reference}:"
        f"{intelligence_reference}"
    )

    digest = hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()

    return f"decision-{digest[:16]}"
