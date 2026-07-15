"""Pure append semantics for immutable Market Situation timelines."""

from datetime import datetime

from app.intelligence.timeline.models import (
    MarketSituationTimeline,
    MarketSituationTimelineEntry,
    _utc_datetime,
)


def append_timeline_entry(
    timeline: MarketSituationTimeline,
    entry: MarketSituationTimelineEntry,
    *,
    updated_at: datetime
) -> MarketSituationTimeline:
    """Return a new timeline version containing exactly one additional entry."""

    if not isinstance(timeline, MarketSituationTimeline):
        raise TypeError("timeline must be a MarketSituationTimeline")
    if not isinstance(entry, MarketSituationTimelineEntry):
        raise TypeError("entry must be a MarketSituationTimelineEntry")
    normalized_updated_at = _utc_datetime(updated_at, "updated_at")
    if entry.timeline_id != timeline.timeline_id:
        raise ValueError("entry timeline_id must match timeline timeline_id")
    if any(existing.entry_id == entry.entry_id for existing in timeline.entries):
        raise ValueError("entry_id already exists in timeline")
    if timeline.entries and entry.created_at < timeline.entries[-1].created_at:
        raise ValueError("entry created_at must not precede the last entry")
    if entry.created_at < timeline.created_at:
        raise ValueError("entry created_at must not precede timeline created_at")
    if normalized_updated_at < entry.created_at:
        raise ValueError("updated_at must not be before entry created_at")

    return MarketSituationTimeline(
        timeline_id=timeline.timeline_id,
        asset=timeline.asset,
        created_at=timeline.created_at,
        updated_at=normalized_updated_at,
        entries=timeline.entries + (entry,),
        current_stage=entry.stage,
        version=timeline.version + 1,
        metadata=timeline.metadata,
    )


__all__ = ["append_timeline_entry"]
