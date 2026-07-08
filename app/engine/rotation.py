import sqlite3
from datetime import datetime, timedelta

from app.config import DB_PATH


def build_rotation(hours: int = 24, limit: int = 5) -> dict:
    since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT DISTINCT asset FROM institutional_history")
    assets = [row["asset"] for row in cur.fetchall()]

    entering = []
    leaving = []

    for asset in assets:
        cur.execute(
            """
            SELECT institutional_score
            FROM institutional_history
            WHERE asset = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (asset,),
        )
        current_row = cur.fetchone()

        cur.execute(
            """
            SELECT institutional_score
            FROM institutional_history
            WHERE asset = ?
              AND timestamp <= ?
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (asset, since),
        )
        previous_row = cur.fetchone()

        if not current_row or not previous_row:
            continue

        current_score = current_row["institutional_score"]
        previous_score = previous_row["institutional_score"]
        delta = current_score - previous_score

        item = {
            "asset": asset,
            "current": current_score,
            "previous": previous_score,
            "delta": delta,
        }

        if delta > 0:
            entering.append(item)
        elif delta < 0:
            leaving.append(item)

    conn.close()

    entering = sorted(entering, key=lambda x: x["delta"], reverse=True)[:limit]
    leaving = sorted(leaving, key=lambda x: x["delta"])[:limit]

    return {
        "hours": hours,
        "entering": entering,
        "leaving": leaving,
    }


def format_rotation(hours: int = 24, limit: int = 5) -> str:
    data = build_rotation(hours, limit)

    lines = [
        "🔄 <b>Institutional Rotation</b>",
        "",
        f"Period: last {data['hours']}h",
        "",
        "⬆️ <b>Capital Entering</b>",
    ]

    if data["entering"]:
        for item in data["entering"]:
            lines.append(
                f"{item['asset']} ▲ +{item['delta']} "
                f"({item['previous']} → {item['current']})"
            )
    else:
        lines.append("No strong inflows yet.")

    lines.extend(["", "⬇️ <b>Capital Leaving</b>"])

    if data["leaving"]:
        for item in data["leaving"]:
            lines.append(
                f"{item['asset']} ▼ {item['delta']} "
                f"({item['previous']} → {item['current']})"
            )
    else:
        lines.append("No strong outflows yet.")

    return "\n".join(lines)
