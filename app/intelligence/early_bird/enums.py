"""Public factor vocabulary for Early Bird opportunity assessment."""

from enum import Enum


class EarlyBirdFactor(str, Enum):
    """Provider-neutral factors contributing to opportunity attention."""

    WHALE_ACTIVITY = "whale_activity"
    OPEN_INTEREST_CHANGE = "open_interest_change"
    FUNDING_DIVERGENCE = "funding_divergence"
    VOLUME_EXPANSION = "volume_expansion"
    RELATIVE_STRENGTH = "relative_strength"
    LIQUIDITY_EVENT = "liquidity_event"
    STRUCTURE_EVENT = "structure_event"
    MOMENTUM_SHIFT = "momentum_shift"
