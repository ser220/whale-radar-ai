import hashlib
import json


def build_resolution_identity(
    *,
    asset: str,
    category: str,
    subject: str,
    time_window: str,
) -> str:
    if not asset:
        raise ValueError(
            "asset is required"
        )

    if not category:
        raise ValueError(
            "category is required"
        )

    if not subject:
        raise ValueError(
            "subject is required"
        )

    if not time_window:
        raise ValueError(
            "time_window is required"
        )

    payload = {
        "asset": asset.strip().upper(),
        "category": category.strip().lower(),
        "subject": subject.strip().lower(),
        "time_window": time_window.strip(),
    }

    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
    ).encode(
        "utf-8"
    )

    digest = hashlib.sha256(
        encoded
    ).hexdigest()

    return (
        f"resolution_{digest[:24]}"
    )
