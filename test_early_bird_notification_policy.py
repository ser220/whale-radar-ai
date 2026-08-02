from app.intelligence.early_bird.notification_policy import (
    EarlyBirdNotificationPolicy,
)


def test_new_fingerprint_requires_notification():
    policy = EarlyBirdNotificationPolicy()

    result = policy.should_notify(
        previous=None,
        current="abc123",
    )

    assert result is True


def test_same_fingerprint_does_not_notify():
    policy = EarlyBirdNotificationPolicy()

    result = policy.should_notify(
        previous="abc123",
        current="abc123",
    )

    assert result is False


def test_changed_fingerprint_requires_notification():
    policy = EarlyBirdNotificationPolicy()

    result = policy.should_notify(
        previous="abc123",
        current="xyz789",
    )

    assert result is True
