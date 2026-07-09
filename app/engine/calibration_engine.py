import sqlite3

from app.config import DB_PATH


MODULES = [
    "Probability Engine",
    "Risk Engine",
    "Campaign Detector",
    "Wallet Behaviour",
    "Scenario Engine",
    "Decision Engine",
]


def calculate_calibration_weights() -> dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS module_learning(
            module TEXT PRIMARY KEY,
            predictions INTEGER DEFAULT 0,
            hits INTEGER DEFAULT 0,
            accuracy REAL DEFAULT 0,
            updated_at TEXT
        )
    """)

    cur.execute("""
        SELECT module, predictions, hits, accuracy
        FROM module_learning
    """)

    rows = cur.fetchall()
    conn.close()

    weights = {}

    for module in MODULES:
        weights[module] = {
            "weight": 1.00,
            "reason": "Default weight. Not enough learning data yet.",
            "predictions": 0,
            "accuracy": 0,
        }

    for row in rows:
        module = row["module"]
        predictions = row["predictions"] or 0
        accuracy = row["accuracy"] or 0

        if predictions < 30:
            weight = 1.00
            reason = "Not enough samples for calibration."
        elif accuracy >= 90:
            weight = 1.20
            reason = "High historical accuracy."
        elif accuracy >= 80:
            weight = 1.10
            reason = "Good historical accuracy."
        elif accuracy >= 70:
            weight = 1.00
            reason = "Neutral historical accuracy."
        elif accuracy >= 60:
            weight = 0.90
            reason = "Weak historical accuracy."
        else:
            weight = 0.75
            reason = "Poor historical accuracy."

        weights[module] = {
            "weight": weight,
            "reason": reason,
            "predictions": predictions,
            "accuracy": accuracy,
        }

    return weights


def format_calibration_weights(weights: dict) -> str:
    lines = ["🧠 <b>Auto Calibration Engine</b>", ""]

    for module, data in weights.items():
        lines.append(
            f"<b>{module}</b>\n"
            f"Weight: x{data['weight']:.2f}\n"
            f"Predictions: {data['predictions']}\n"
            f"Accuracy: {data['accuracy']}%\n"
            f"Reason: {data['reason']}\n"
        )

    return "\n".join(lines)
