"""Perpetual direction resolver."""

from app.intelligence.early_bird.perpetual_direction_decision import (
    PerpetualDirectionDecision,
)


class PerpetualDirectionResolver:
    """
    Resolves final perpetual trading direction.
    """

    def resolve(
        self,
        score,
        *,
        market_regime="neutral",
    ) -> PerpetualDirectionDecision:

        long_score = score.adjusted_long_score
        short_score = score.adjusted_short_score
        uncertainty = score.uncertainty_level

        risk_flags = []

        if uncertainty >= 70:
            risk_flags.append(
                "high_uncertainty"
            )

        # LONG continuation
        if (
            long_score >= 70
            and long_score > short_score + 15
            and uncertainty < 50
        ):
            return PerpetualDirectionDecision(
                asset=score.asset,
                direction="LONG",
                confidence=score.confidence,
                market_regime=market_regime,
                reason=(
                    "bullish continuation with "
                    "strong directional advantage"
                ),
                risk_flags=tuple(
                    risk_flags
                ),
            )

        # SHORT reversal / continuation
        if (
            short_score >= 70
            and (
                short_score > long_score + 10
                or market_regime
                == "bullish_exhaustion"
            )
            and uncertainty < 60
        ):
            return PerpetualDirectionDecision(
                asset=score.asset,
                direction="SHORT",
                confidence=score.confidence,
                market_regime=market_regime,
                reason=(
                    "bearish opportunity detected "
                    "through reversal pressure"
                ),
                risk_flags=tuple(
                    risk_flags
                ),
            )

        # No clear edge
        risk_flags.append(
            "insufficient_directional_edge"
        )

        return PerpetualDirectionDecision(
            asset=score.asset,
            direction="WAIT",
            confidence=score.confidence,
            market_regime=market_regime,
            reason=(
                "directional conflict or "
                "excessive uncertainty"
            ),
            risk_flags=tuple(
                risk_flags
            ),
        )


__all__ = [
    "PerpetualDirectionResolver",
]
