"""Text builder for Early Bird shadow notifications."""

from typing import Any, Mapping


def build_shadow_message(
    *,
    asset: str,
    payload: Mapping[str, Any],
) -> str:
    """Build human-readable shadow notification text."""

    if not isinstance(asset, str) or not asset.strip():
        raise ValueError(
            "asset must not be empty"
        )

    lines = [
        "🧠 Early Bird Shadow",
        "Asset: {0}".format(asset.upper()),
    ]

    if "score" in payload:
        lines.append(
            "Score: {0}".format(
                payload["score"]
            )
        )

    if "status" in payload:
        lines.append(
            "Status: {0}".format(
                payload["status"]
            )
        )

    return "\n".join(lines)


__all__ = [
    "build_shadow_message",
]
