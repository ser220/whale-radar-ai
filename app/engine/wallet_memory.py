import sqlite3

from app.config import DB_PATH


def analyze_wallet_memory(wallet: str, hours: int = 168) -> dict:
    wallet_lower = (wallet or "").lower()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        """
        SELECT asset, amount_usd, from_entity, to_entity, timestamp
        FROM events
        WHERE lower(from_entity) LIKE ?
           OR lower(to_entity) LIKE ?
        ORDER BY timestamp DESC
        LIMIT 500
        """,
        (f"%{wallet_lower}%", f"%{wallet_lower}%"),
    )

    rows = cur.fetchall()
    conn.close()

    if not rows:
        return {
            "wallet": wallet or "Unknown Wallet",
            "seen": 0,
            "total_usd": 0,
            "avg_transfer": 0,
            "top_assets": [],
            "profile": "No wallet history yet.",
        }

    total_usd = sum((row["amount_usd"] or 0) for row in rows)
    avg_transfer = total_usd / len(rows)

    assets = {}
    exchanges = {}

    for row in rows:
        asset = row["asset"] or "UNKNOWN"
        assets[asset] = assets.get(asset, 0) + 1

        for entity in [row["from_entity"], row["to_entity"]]:
            name = entity or ""
            if any(x in name.lower() for x in ["binance", "coinbase", "okx", "bybit", "kraken", "gate"]):
                exchanges[name] = exchanges.get(name, 0) + 1

    top_assets = sorted(assets.items(), key=lambda x: x[1], reverse=True)[:3]
    top_exchanges = sorted(exchanges.items(), key=lambda x: x[1], reverse=True)[:3]

    if len(rows) >= 100:
        profile = "Highly active institutional wallet."
    elif len(rows) >= 30:
        profile = "Active institutional wallet."
    elif len(rows) >= 10:
        profile = "Tracked wallet with limited history."
    else:
        profile = "New or rarely seen wallet."

    return {
        "wallet": wallet or "Unknown Wallet",
        "seen": len(rows),
        "total_usd": total_usd,
        "avg_transfer": avg_transfer,
        "top_assets": top_assets,
        "top_exchanges": top_exchanges,
        "profile": profile,
    }


def format_wallet_memory(memory: dict) -> str:
    assets = ", ".join([f"{a}({c})" for a, c in memory.get("top_assets", [])]) or "N/A"
    exchanges = ", ".join([f"{e}({c})" for e, c in memory.get("top_exchanges", [])]) or "N/A"

    return (
        f"{memory['wallet']}\n"
        f"Profile: {memory['profile']}\n"
        f"Seen: {memory['seen']} events\n"
        f"Total Flow: ${memory['total_usd']:,.0f}\n"
        f"Average Transfer: ${memory['avg_transfer']:,.0f}\n"
        f"Top Assets: {assets}\n"
        f"Top Exchanges: {exchanges}"
    )
