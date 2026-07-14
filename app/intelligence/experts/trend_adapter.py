"""Shadow-facing adapter for the existing deterministic Trend Expert."""

from datetime import datetime
from typing import Optional

from app.intelligence.contracts import ExpertOpinion
from app.intelligence.experts.trend import TrendExpert
from app.intelligence.observations import StructureObservation, TrendObservation


class TrendExpertAdapter:
    """Expose WR-026B Trend Expert output under the shadow expert identity."""

    EXPERT_NAME = "trend_expert"
    INDICATORS_USED = (
        "trend_bias",
        "trend_strength",
        "moving_average_alignment",
        "slope",
        "price_change_pct",
        "swing_structure",
        "structure_break",
        "higher_timeframe_bias",
        "structure_quality",
    )

    def __init__(self, trend_expert: Optional[TrendExpert] = None) -> None:
        if trend_expert is not None and not isinstance(trend_expert, TrendExpert):
            raise TypeError("trend_expert must be a TrendExpert")
        self._trend_expert = trend_expert or TrendExpert()

    @property
    def trend_expert(self) -> TrendExpert:
        """Return the existing expert that owns trend interpretation."""
        return self._trend_expert

    def adapt(
        self,
        trend: TrendObservation,
        structure: StructureObservation,
        *,
        timestamp: Optional[datetime] = None,
    ) -> ExpertOpinion:
        """Evaluate normalized observations and add shadow provenance metadata."""
        source_opinion = self._trend_expert.evaluate(
            trend,
            structure,
            timestamp=timestamp,
        )
        metadata = dict(source_opinion.metadata)
        metadata.update(
            {
                "trend_source": trend.source,
                "structure_source": structure.source,
                "timeframe": trend.timeframe,
                "indicators_used": self.INDICATORS_USED,
                "generated_at": source_opinion.timestamp.isoformat(),
                "source_expert_name": source_opinion.expert_name,
            }
        )

        return ExpertOpinion(
            expert_name=self.EXPERT_NAME,
            direction=source_opinion.direction,
            state=source_opinion.state,
            score=source_opinion.score,
            confidence=source_opinion.confidence,
            quality=source_opinion.quality,
            reasons=source_opinion.reasons,
            warnings=source_opinion.warnings,
            metadata=metadata,
            timestamp=source_opinion.timestamp,
        )
