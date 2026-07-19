import hashlib
import json


def build_association_identity(
    *,
    candidate_id: str,
    situation_event_id: str,
    association_type: str,
    reference_version: str,
) -> str:
    if not candidate_id:
        raise ValueError(
            "candidate_id is required"
        )

    if not situation_event_id:
        raise ValueError(
            "situation_event_id is required"
        )

    if not association_type:
        raise ValueError(
            "association_type is required"
        )

    if not reference_version:
        raise ValueError(
            "reference_version is required"
        )

    payload = {
        "candidate_id": candidate_id.strip(),
        "situation_event_id": situation_event_id.strip(),
        "association_type": (
            association_type.strip().upper()
        ),
        "reference_version": (
            reference_version.strip().upper()
        ),
    }

    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
    ).encode("utf-8")

    digest = hashlib.sha256(
        encoded
    ).hexdigest()

    return (
        f"association_{digest[:24]}"
    )
