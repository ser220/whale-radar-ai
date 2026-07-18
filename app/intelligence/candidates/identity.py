import hashlib
import json


def build_candidate_id(
    *,
    subject: str,
    category: str,
    hypothesis_reference: str,
    identity_policy_version: str,
) -> str:
    payload = {
        "category": category,
        "hypothesis_reference": hypothesis_reference,
        "identity_policy_version": identity_policy_version,
        "subject": subject,
    }

    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    digest = hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()

    return f"candidate-{digest[:16]}"
