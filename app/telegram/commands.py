from app.storage.history import get_recent_events
from app.telegram.sender import send_telegram_message


def handle_history_command(limit: int = 5) -> bool:
    events = get_recent_events(limit)

    if not events:
        return send_telegram_message("📭 <b>History is empty</b>")

    lines = ["📜 <b>Recent Whale Radar Events</b>\n"]

    for e in events:
        amount = f"${e['amount_usd']:,.0f}"

        lines.append(
            f"<b>#{e['id']} {e['asset']}</b>\n"
            f"{amount}\n"
            f"{e['from_entity']} → {e['to_entity']}\n"
            f"{e['timestamp']}\n"
        )

    return send_telegram_message("\n".join(lines))
