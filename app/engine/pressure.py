import sqlite3
from datetime import datetime, timedelta

from app.config import DB_PATH
from app.storage.database import init_db


MAJOR_EXCHANGES = {
    "Binance",
    "Coinbase",
    "Coinbase Prime",
    "OKX",
    "Bybit",
    "Kraken",
    "Bitstamp",
    "Bitfinex",
    "Gate",
    "Gate.io",
    "KuCoin",
    "HTX",
    "Upbit",
}


def get_whale_pressure(asset: str, hours: int = 6) -> dict:
    init_db()

    since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    asset = asset.upper()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT from_entity, to_entity, amount_usd
        FROM events
        WHERE asset = ?
          AND timestamp >= ?
        """,
        (asset, since),
    )

    rows = cursor.fetchall()
    conn.close()

    inflow = 0.0
    outflow = 0.0

    for from_entity, to_entity, amount_usd in rows:
        from_entity = from_entity or ""
        to_entity = to_entity or ""
        amount = float(amount_usd or 0)

        if to_entity in MAJOR_EXCHANGES:
            inflow += amount

        if from_entity in MAJOR_EXCHANGES:
            outflow += amount

    total = inflow + outflow

    if total <= 0:
        return {
            "asset": asset,
            "hours": hours,
            "inflow_usd": 0.0,
            "outflow_usd": 0.0,
            "bullish_pct": 50,
            "bearish_pct": 50,
            "bias": "Neutral",
        }

    bullish_pct = round((outflow / total) * 100)
    bearish_pct = round((inflow / total) * 100)

    if bullish_pct >= 65:
        bias = "Bullish Dominance"
    elif bearish_pct >= 65:
        bias = "Bearish Dominance"
    else:
        bias = "Balanced"

    return {
        "asset": asset,
        "hours": hours,
        "inflow_usd": inflow,
        "outflow_usd": outflow,
        "bullish_pct": bullish_pct,
        "bearish_pct": bearish_pct,
        "bias": bias,
    }
