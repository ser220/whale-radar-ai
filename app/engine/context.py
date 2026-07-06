from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.models.event import MarketEvent


EVENT_MEMORY: List[MarketEvent] = []


def add_event(event: MarketEvent) -> None:
    EVENT_MEMORY.append(event)
    cleanup_old_events()


def cleanup_old_events(hours: int = 24) -> None:
    cutoff = datetime.utcnow() - timedelta(hours=hours)

    global EVENT_MEMORY
    EVENT_MEMORY = [
        event for event in EVENT_MEMORY
        if event.timestamp >= cutoff
    ]


def get_cluster(
    event: MarketEvent,
    window_minutes: int = 30,
) -> Dict[str, Any]:
    cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)

    similar_events = [
        e for e in EVENT_MEMORY
        if e.timestamp >= cutoff
        and e.asset == event.asset
        and e.from_entity == event.from_entity
        and e.to_entity == event.to_entity
    ]

    total_usd = sum(e.amount_usd for e in similar_events)

    return {
        "count": len(similar_events),
        "total_usd": total_usd,
        "window_minutes": window_minutes,
    }


def is_cluster_important(cluster: Dict[str, Any]) -> bool:
    return (
        cluster["count"] >= 3
        or cluster["total_usd"] >= 100_000_000
    )
