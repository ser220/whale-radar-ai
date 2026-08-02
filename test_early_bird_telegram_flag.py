import os

from app.telegram.early_bird_flag import (
    early_bird_telegram_enabled,
)


def test_flag_disabled_by_default(monkeypatch):
    monkeypatch.delenv(
        "EARLY_BIRD_TELEGRAM_SHADOW",
        raising=False,
    )

    assert early_bird_telegram_enabled() is False


def test_flag_enabled_from_environment(monkeypatch):
    monkeypatch.setenv(
        "EARLY_BIRD_TELEGRAM_SHADOW",
        "true",
    )

    assert early_bird_telegram_enabled() is True


def test_flag_accepts_common_true_values(monkeypatch):
    for value in ("1", "yes", "on", "enabled"):
        monkeypatch.setenv(
            "EARLY_BIRD_TELEGRAM_SHADOW",
            value,
        )

        assert early_bird_telegram_enabled() is True
