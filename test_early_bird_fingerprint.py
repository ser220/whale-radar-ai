from datetime import datetime, timezone

from app.intelligence.early_bird.fingerprint import (
    build_early_bird_fingerprint,
)


NOW = datetime(
    2026,
    8,
    2,
    7,
    0,
    tzinfo=timezone.utc,
)


def test_fingerprint_is_stable_for_same_payload():
    payload = {
        "asset": "BTC",
        "open_interest_change_score": 80,
        "data_completeness_score": 90,
        "observed_at": NOW.isoformat(),
    }

    first = build_early_bird_fingerprint(payload)
    second = build_early_bird_fingerprint(payload)

    assert first == second


def test_fingerprint_changes_when_payload_changes():
    first = build_early_bird_fingerprint(
        {
            "asset": "BTC",
            "score": 80,
        }
    )

    second = build_early_bird_fingerprint(
        {
            "asset": "BTC",
            "score": 81,
        }
    )

    assert first != second
