import sqlite3

from app.config import DB_PATH


def build_calibration_audit():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT
            module,
            predictions,
            hits,
            accuracy,
            updated_at
        FROM module_learning
        ORDER BY module
    """)

    rows = cur.fetchall()
    conn.close()

    audit = []

    healthy = 0
    review = 0

    for row in rows:

        predictions = row["predictions"] or 0
        accuracy = row["accuracy"] or 0

        if predictions < 30:
            status = "🔵 Learning"
            reason = "Collecting more historical data."

        elif accuracy == 0:
            status = "🟡 Needs Review"
            reason = "Accuracy is zero. Check outcome feedback."

        elif accuracy < 10:
            status = "🟡 Needs Review"
            reason = "Accuracy unusually low."

        elif accuracy > 98:
            status = "🟡 Needs Review"
            reason = "Accuracy unusually high."

        else:
            status = "🟢 Healthy"
            reason = "Historical statistics look reliable."

        if status == "🟢 Healthy":
            healthy += 1
        else:
            review += 1

        audit.append({
            "module": row["module"],
            "status": status,
            "predictions": predictions,
            "accuracy": accuracy,
            "reason": reason,
        })

    calibration_ready = review == 0

    return {
        "modules": audit,
        "healthy": healthy,
        "review": review,
        "ready": calibration_ready,
    }


def format_calibration_audit(data):

    lines = [
        "🧠 <b>Calibration Audit</b>",
        "",
    ]

    for m in data["modules"]:

        lines.append(
            f"<b>{m['module']}</b>\n"
            f"{m['status']}\n"
            f"Predictions: {m['predictions']}\n"
            f"Accuracy: {m['accuracy']}%\n"
            f"Reason: {m['reason']}\n"
        )

    lines.append("────────────")

    lines.append(
        f"Healthy Modules: {data['healthy']}"
    )

    lines.append(
        f"Needs Review: {data['review']}"
    )

    lines.append(
        f"Calibration Ready: {'YES ✅' if data['ready'] else 'NO ❌'}"
    )

    return "\n".join(lines)
