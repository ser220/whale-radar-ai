"""Market universe contract for asset scanning."""

from dataclasses import dataclass
from typing import Iterable, Tuple


def _normalize_asset(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError(
            "asset must be a string"
        )

    normalized = value.strip().upper()

    if not normalized:
        raise ValueError(
            "asset must not be empty"
        )

    return normalized


@dataclass(frozen=True)
class MarketUniverse:
    """Immutable list of assets available for scanning."""

    assets: Tuple[str, ...] = ()

    def __init__(
        self,
        assets: Iterable[str] = (),
    ) -> None:
        normalized = tuple(
            _normalize_asset(asset)
            for asset in assets
        )

        object.__setattr__(
            self,
            "assets",
            tuple(dict.fromkeys(normalized)),
        )


__all__ = [
    "MarketUniverse",
]
