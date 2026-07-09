import json
import sqlite3

from app.config import DB_PATH


def build_pattern_key(row) -> str:
    snapshot = json.loads(row["ai_snapshot"] or "{}")

    regime = snapshot.get("market_regime", {}).get("regime", "Unknown")
    heat = snapshot.get("market_heat", {}).get("label", "Unknown")
    wallet = snapshot.get("wallet_behaviour", {}).get("behaviour", "Unknown")
    direction = row["direction"] or "Unknown"
    asset = row["asset"] or "Unknown"

    return f"{asset}|{direction}|{regime}|{heat}|{wallet}"


def get_pattern_memory(limit: int = 200) -> dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM prediction_history
        WHERE outcome_checked = 1
          AND ai_snapshot IS NOT NULL
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    conn.close()

    patterns = {}

    for row in rows:
        key = build_pattern_key(row)

        if key not in patterns:
            patterns[key] = {
                "pattern": key,
                "seen": 0,
                "hits": 0,
                "accuracy": 0,
                "avg_move": 0,
            }

        patterns[key]["seen"] += 1
        patterns[key]["hits"] += 1 if row["target_hit"] == 1 else 0
        patterns[key]["avg_move"] += row["actual_move"] or 0

    for item in patterns.values():
        item["accuracy"] = round((item["hits"] / item["seen"]) * 100, 1) if item["seen"] else 0
        item["avg_move"] = round(item["avg_move"] / item["seen"], 2) if item["seen"] else 0

    return patterns


def format_pattern_memory(patterns: dict, max_items: int = 5) -> str:
    if not patterns:
        return "No pattern memory yet."

    rows = sorted(
        patterns.values(),
        key=lambda x: (x["seen"], x["accuracy"]),
        reverse=True,
    )[:max_items]

    lines = ["🧠 <b>Pattern Memory</b>", ""]

    for p in rows:
        lines.append(
            f"<b>{p['pattern']}</b>\n"
            f"Seen: {p['seen']}\n"
            f"Hits: {p['hits']}\n"
            f"Accuracy: {p['accuracy']}%\n"
            f"Avg Move: {p['avg_move']}%\n"
        )

    return "\n".join(lines)
def parse_pattern_key(key: str) -> dict:
    parts = key.split("|")

    return {
        "asset": parts[0] if len(parts) > 0 else "Unknown",
        "direction": parts[1] if len(parts) > 1 else "Unknown",
        "regime": parts[2] if len(parts) > 2 else "Unknown",
        "heat": parts[3] if len(parts) > 3 else "Unknown",
        "wallet_behaviour": parts[4] if len(parts) > 4 else "Unknown",
    }


def get_structured_patterns(limit: int = 200) -> list:
    patterns = get_pattern_memory(limit)

    rows = []

    for key, data in patterns.items():
        parsed = parse_pattern_key(key)

        rows.append({
            **parsed,
            "pattern": key,
            "seen": data.get("seen", 0),
            "hits": data.get("hits", 0),
            "accuracy": data.get("accuracy", 0),
            "avg_move": data.get("avg_move", 0),
        })

    rows.sort(
        key=lambda x: (x["seen"], x["accuracy"]),
        reverse=True,
    )

    return rows


def format_structured_patterns(rows: list, max_items: int = 5) -> str:
    if not rows:
        return "No structured pattern memory yet."

    lines = ["🧠 <b>Structured Pattern Memory</b>", ""]

    for i, p in enumerate(rows[:max_items], start=1):
        lines.append(
            f"<b>Pattern #{i}</b>\n"
            f"Asset: {p['asset']}\n"
            f"Bias: {p['direction']}\n"
            f"Regime: {p['regime']}\n"
            f"Heat: {p['heat']}\n"
            f"Wallet: {p['wallet_behaviour']}\n"
            f"Seen: {p['seen']}\n"
            f"Hits: {p['hits']}\n"
            f"Accuracy: {p['accuracy']}%\n"
            f"Avg Move: {p['avg_move']}%\n"
        )

    return "\n".join(lines)
