"""Early Bird market sweep orchestration."""

from typing import Any

from app.data.market.market_universe import (
    MarketUniverse,
)


class EarlyBirdMarketSweep:
    """Run Early Bird scanning across a market universe."""

    def __init__(
        self,
        scanner: Any,
    ) -> None:
        if not callable(
            getattr(scanner, "scan", None)
        ):
            raise TypeError(
                "scanner must provide scan"
            )

        self._scanner = scanner

    def universe(
        self,
        universe: MarketUniverse,
        *,
        timeframe: str = "15m",
        limit: int = 5,
    ):
        if not isinstance(
            universe,
            MarketUniverse,
        ):
            raise TypeError(
                "universe must be a MarketUniverse"
            )

        return self._scanner.scan(
            universe.assets,
            timeframe=timeframe,
            limit=limit,
        )

    def rank(
        self,
        candidates,
    ):
        return tuple(
            sorted(
                candidates,
                key=lambda item: item.quality,
                reverse=True,
            )
        )

    def candidates(
        self,
        assets,
        *,
        timeframe: str = "15m",
        limit: int = 5,
    ):
        result = self._scanner.scan(
            tuple(assets),
            timeframe=timeframe,
            limit=limit,
        )

        candidates = tuple(
            item.build_result.candidate
            for item in result.items
        )

        return self.rank(candidates)

    def run(
        self,
        assets,
        *,
        timeframe: str = "15m",
        limit: int = 5,
    ):
        from app.intelligence.early_bird.market_sweep_result import (
            EarlyBirdMarketSweepResult,
        )

        normalized_assets = tuple(assets)

        result = self._scanner.scan(
            normalized_assets,
            timeframe=timeframe,
            limit=limit,
        )

        candidates = self.rank(
            tuple(
                item.build_result.candidate
                for item in result.items
            )
        )

        generated_at = getattr(
            result,
            "completed_at",
            None,
        )

        if generated_at is None:
            raise ValueError(
                "scan result must provide completed_at"
            )

        return EarlyBirdMarketSweepResult(
            items=candidates,
            scanned_assets=normalized_assets,
            generated_at=generated_at,
        )


__all__ = [
    "EarlyBirdMarketSweep",
]
