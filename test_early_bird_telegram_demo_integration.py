from app.telegram.early_bird_flag import (
    early_bird_telegram_enabled,
)


def test_shadow_flag_module_is_available():
    assert callable(
        early_bird_telegram_enabled
    )
