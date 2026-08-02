"""Early Bird market sweep result contract."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Tuple


def _utc_datetime(
    value: datetime,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None:
        raise ValueError(
            f"{field_name} must be timezone aware"
        )

    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class EarlyBirdMarketSweepResult:
    """Immutable result of a market-wide Early Bird sweep."""

    items: Tuple[Any, ...]
    scanned_assets: Tuple[str, ...]
    generated_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "items",
            tuple(self.items),
        )

        object.__setattr__(
            self,
            "scanned_assets",
            tuple(
                asset.upper()
                for asset in self.scanned_assets
            ),
        )

        object.__setattr__(
            self,
            "generated_at",
            _utc_datetime(
                self.generated_at,
                "generated_at",
            ),
        )


__all__ = [
    "EarlyBirdMarketSweepResult",
]
