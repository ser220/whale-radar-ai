from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from app.intelligence.data_sources import OpenInterestSnapshot


def _normalize_asset(value: str) -> str:
    asset = str(value or "").strip().upper()

    if not asset:
        raise ValueError("asset must not be empty")

    return asset


class OpenInterestHistory:
    """In-memory chronological history of Open Interest snapshots."""

    def __init__(self) -> None:
        self._snapshots: Dict[
            str,
            List[OpenInterestSnapshot],
        ] = {}

    def append(
        self,
        snapshot: OpenInterestSnapshot,
    ) -> OpenInterestSnapshot:
        if not isinstance(
            snapshot,
            OpenInterestSnapshot,
        ):
            raise TypeError(
                "snapshot must be an OpenInterestSnapshot"
            )

        asset = snapshot.asset
        values = list(
            self._snapshots.get(asset, ())
        )

        values = [
            value
            for value in values
            if value.captured_at != snapshot.captured_at
        ]

        values.append(snapshot)
        values.sort(
            key=lambda value: value.captured_at
        )

        self._snapshots[asset] = values

        return snapshot

    def assets(self) -> Tuple[str, ...]:
        return tuple(
            sorted(self._snapshots)
        )

    def snapshots(
        self,
        asset: str,
    ) -> Tuple[OpenInterestSnapshot, ...]:
        normalized_asset = _normalize_asset(asset)

        return tuple(
            self._snapshots.get(
                normalized_asset,
                (),
            )
        )

    def latest(
        self,
        asset: str,
    ) -> Optional[OpenInterestSnapshot]:
        values = self.snapshots(asset)

        if not values:
            return None

        return values[-1]

    def previous(
        self,
        asset: str,
        *,
        before: datetime,
    ) -> Optional[OpenInterestSnapshot]:
        if not isinstance(before, datetime):
            raise TypeError(
                "before must be a datetime"
            )

        if (
            before.tzinfo is None
            or before.utcoffset() is None
        ):
            raise ValueError(
                "before must be timezone aware"
            )

        before_utc = before.astimezone(
            timezone.utc
        )

        earlier = tuple(
            value
            for value in self.snapshots(asset)
            if value.captured_at < before_utc
        )

        if not earlier:
            return None

        return earlier[-1]
