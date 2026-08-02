from datetime import datetime, timezone

import pytest

from app.intelligence.early_bird.shadow_state import (
    EarlyBirdShadowState,
)


NOW = datetime(
    2026,
    8,
    2,
    7,
    0,
    tzinfo=timezone.utc,
)


def test_initial_state_is_empty():
    state = EarlyBirdShadowState()

    assert state.last_scan_at is None
    assert state.candidate_fingerprints == {}
    assert state.sent_fingerprints == {}


def test_state_stores_candidate_fingerprint():
    state = EarlyBirdShadowState()

    state.update_candidate(
        asset="BTC",
        fingerprint="abc123",
        observed_at=NOW,
    )

    assert state.candidate_fingerprints["BTC"] == "abc123"
    assert state.last_scan_at == NOW


def test_state_detects_new_candidate():
    state = EarlyBirdShadowState()

    assert (
        state.is_new_candidate(
            "BTC",
            "abc123",
        )
        is True
    )

    state.update_candidate(
        asset="BTC",
        fingerprint="abc123",
        observed_at=NOW,
    )

    assert (
        state.is_new_candidate(
            "BTC",
            "abc123",
        )
        is False
    )


def test_state_rejects_invalid_asset():
    state = EarlyBirdShadowState()

    with pytest.raises(
        ValueError,
        match="asset must not be empty",
    ):
        state.update_candidate(
            asset="",
            fingerprint="abc",
            observed_at=NOW,
        )
