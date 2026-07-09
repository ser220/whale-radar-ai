import sqlite3

from app.config import DB_PATH


def get_learning_stats(limit: int = 200) -> dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM prediction_history
        WHERE outcome_checked = 1
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    conn.close()

    total = len(rows)

    if total == 0:
        return {
            "total": 0,
            "hits": 0,
            "hit_rate": 0,
            "avg_accuracy": 0,
            "label": "No learning data yet",
        }

    hits = sum(1 for r in rows if r["target_hit"] == 1)
    accuracies = [r["accuracy"] or 0 for r in rows]
    avg_accuracy = sum(accuracies) / total

    hit_rate = (hits / total) * 100

    if avg_accuracy >= 85:
        label = "High historical reliability"
    elif avg_accuracy >= 70:
        label = "Moderate historical reliability"
    elif avg_accuracy >= 50:
        label = "Low historical reliability"
    else:
        label = "Insufficient / weak reliability"

    return {
        "total": total,
        "hits": hits,
        "hit_rate": round(hit_rate, 1),
        "avg_accuracy": round(avg_accuracy, 1),
        "label": label,
    }


def format_learning_stats(stats: dict) -> str:
    return (
        f"Signals Checked: {stats['total']}\n"
        f"Targets Hit: {stats['hits']}\n"
        f"Hit Rate: {stats['hit_rate']}%\n"
        f"Avg Accuracy: {stats['avg_accuracy']}%\n"
        f"Reliability: {stats['label']}"
    )
