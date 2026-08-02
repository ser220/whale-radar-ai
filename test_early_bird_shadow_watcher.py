from app.intelligence.early_bird.shadow_watcher import (
    EarlyBirdShadowWatcher,
)


def test_first_payload_requires_notification():
    watcher = EarlyBirdShadowWatcher()

    result = watcher.evaluate(
        asset="BTC",
        payload={
            "score": 80,
        },
    )

    assert result.notify is True


def test_same_payload_is_ignored():
    watcher = EarlyBirdShadowWatcher()

    payload = {
        "score": 80,
    }

    watcher.evaluate(
        asset="BTC",
        payload=payload,
    )

    result = watcher.evaluate(
        asset="BTC",
        payload=payload,
    )

    assert result.notify is False


def test_changed_payload_requires_notification():
    watcher = EarlyBirdShadowWatcher()

    watcher.evaluate(
        asset="BTC",
        payload={
            "score": 80,
        },
    )

    result = watcher.evaluate(
        asset="BTC",
        payload={
            "score": 90,
        },
    )

    assert result.notify is True
