from app.intelligence.early_bird.shadow_demo import (
    run_shadow_demo,
)


def test_shadow_demo_returns_notification_message():
    result = run_shadow_demo(
        asset="BTC",
        payload={
            "score": 80,
            "status": "AVAILABLE",
        },
    )

    assert result is not None
    assert "BTC" in result
    assert "80" in result


def test_shadow_demo_ignores_duplicate_payload():
    first = run_shadow_demo(
        asset="BTC",
        payload={
            "score": 80,
        },
    )

    second = run_shadow_demo(
        asset="BTC",
        payload={
            "score": 80,
        },
    )

    assert first is not None
    assert second is None
