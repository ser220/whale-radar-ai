from app.intelligence.early_bird.shadow_pipeline import (
    EarlyBirdShadowPipeline,
)


def test_new_signal_sends_notification():
    calls = []

    def fake_sender(message):
        calls.append(message)
        return True

    pipeline = EarlyBirdShadowPipeline(
        send_fn=fake_sender,
    )

    result = pipeline.process(
        asset="BTC",
        payload={
            "score": 80,
            "status": "AVAILABLE",
        },
    )

    assert result.sent is True
    assert len(calls) == 1
    assert "BTC" in calls[0]


def test_duplicate_signal_is_not_sent():
    calls = []

    pipeline = EarlyBirdShadowPipeline(
        send_fn=lambda message: (
            calls.append(message) or True
        ),
    )

    payload = {
        "score": 80,
    }

    first = pipeline.process(
        asset="BTC",
        payload=payload,
    )

    second = pipeline.process(
        asset="BTC",
        payload=payload,
    )

    assert first.sent is True
    assert second.sent is False
    assert len(calls) == 1


def test_changed_signal_sends_again():
    calls = []

    pipeline = EarlyBirdShadowPipeline(
        send_fn=lambda message: (
            calls.append(message) or True
        ),
    )

    pipeline.process(
        asset="BTC",
        payload={
            "score": 80,
        },
    )

    result = pipeline.process(
        asset="BTC",
        payload={
            "score": 90,
        },
    )

    assert result.sent is True
    assert len(calls) == 2
