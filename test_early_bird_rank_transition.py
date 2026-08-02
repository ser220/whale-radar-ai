import pytest

from app.intelligence.early_bird.rank_transition import (
    RankTransition,
)


def test_transition_values_exist():
    assert RankTransition.PROMOTE.value == "promote"
    assert RankTransition.DOWNGRADE.value == "downgrade"
    assert RankTransition.HOLD.value == "hold"
    assert RankTransition.REMOVE.value == "remove"


def test_unknown_transition_is_invalid():
    with pytest.raises(ValueError):
        RankTransition("unknown")
