from app.models.event import MarketEvent
from app.engine.filter import is_noise_event
from app.engine.scorer import score_event
from app.engine.context import add_event, get_cluster, is_cluster_important
from app.telegram.formatter import format_signal
from app.telegram.sender import send_telegram_message
from app.storage.database import save_event

def process_event(event: MarketEvent) -> dict:
    if is_noise_event(event):
        return {
            "status": "ignored",
            "reason": "noise_event",
        }

    add_event(event)
    save_event(event)

    score_data = score_event(event)
    cluster = get_cluster(event)

    if is_cluster_important(cluster):
        score_data["score"] = min(score_data["score"] + 20, 100)
        score_data["reasons"].append(
            f"Cluster detected: {cluster['count']} similar events "
            f"in {cluster['window_minutes']} min, total ${cluster['total_usd']:,.0f}"
        )

    if score_data["score"] < 50:
        return {
            "status": "ignored",
            "reason": "low_score",
            "score": score_data["score"],
        }

    message = format_signal(event, score_data)
    sent = send_telegram_message(message)

    return {
        "status": "sent" if sent else "failed",
        "score": score_data["score"],
        "direction": score_data["direction"],
        "cluster": cluster,
    }
