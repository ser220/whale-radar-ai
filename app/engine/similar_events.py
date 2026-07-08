import sqlite3

from app.config import DB_PATH


EXCHANGES = ("binance", "coinbase", "okx", "kraken", "bybit", "gate")


def _is_exchange(name: str) -> bool:
    name = (name or "").lower()
    return any(ex in name for ex in EXCHANGES)


def find_similar_events(asset: str, direction: str, wallet: str, limit: int = 20) -> dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        """
        SELECT asset, amount_usd, from_entity, to_entity, timestamp
        FROM events
        WHERE asset = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (asset.upper(), limit * 5),
    )

    rows = cur.fetchall()
    conn.close()

    filtered = []

    for row in rows:
        from_entity = row["from_entity"] or ""
        to_entity = row["to_entity"] or ""

        if direction == "bearish" and _is_exchange(to_entity):
            filtered.append(row)

        elif direction == "bullish" and _is_exchange(from_entity):
            filtered.append(row)

        elif direction not in {"bearish", "bullish"}:
            filtered.append(row)

        if len(filtered) >= limit:
            break

    if not filtered:
        return {
            "count": 0,
            "text": "No similar historical events yet.",
        }

    same_wallet = 0
    total_amount = 0
    wallet_lower = (wallet or "").lower()

    for row in filtered:
        total_amount += row["amount_usd"] or 0

        if wallet_lower and (
            wallet_lower in (row["from_entity"] or "").lower()
            or wallet_lower in (row["to_entity"] or "").lower()
        ):
            same_wallet += 1

    avg_amount = total_amount / len(filtered)

    text = (
        f"Similar events found: {len(filtered)}\n"
        f"Same wallet matches: {same_wallet}\n"
        f"Average size: ${avg_amount:,.0f}"
    )

    return {
        "count": len(filtered),
        "same_wallet": same_wallet,
        "avg_amount": avg_amount,
        "text": text,
    }
