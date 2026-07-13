"""Enumerations used by the intelligence contracts."""

from enum import Enum


class Direction(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class TrendState(str, Enum):
    TREND = "TREND"
    CORRECTION = "CORRECTION"
    REVERSAL = "REVERSAL"
    RANGE = "RANGE"
    UNKNOWN = "UNKNOWN"


class LifecycleState(str, Enum):
    WATCH = "WATCH"
    PREPARE = "PREPARE"
    READY = "READY"
    ACTION = "ACTION"
    MANAGE = "MANAGE"
    EXIT = "EXIT"
