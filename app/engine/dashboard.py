import sqlite3

from app.config import DB_PATH
from app.engine.market_heat import calculate_market_heat
from app.engine.pressure import get_whale_pressure
from app.engine.market_regime import detect_market_regime
from app.engine.wallet_intelligence import analyze_wallet


def build_dashboard(limit: int = 10):

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT asset,
               COUNT(*) as cnt,
               COALESCE(SUM(amount_usd),0) as volume
        FROM events
        GROUP BY asset
        ORDER BY volume DESC
        LIMIT ?
        """,
        (limit,),
    )

    rows = cur.fetchall()
    conn.close()

    text = [
        "🏛 <b>Institutional Dashboard</b>",
        "",
        "🔥 <b>Top Institutional Assets</b>",
    ]

    for asset, cnt, volume in rows:

        pressure = get_whale_pressure(asset, 6)

        if pressure["bearish_pct"] > pressure["bullish_pct"]:
            direction = "bearish"
        elif pressure["bullish_pct"] > pressure["bearish_pct"]:
            direction = "bullish"
        else:
            direction = "neutral"

        wallet_ai = analyze_wallet("Unknown Wallet", direction)

        regime = detect_market_regime(
            direction,
            cnt,
            pressure,
            wallet_ai,
        )

        heat = calculate_market_heat(
            asset,
            pressure,
            {"total_usd": volume},
            wallet_ai,
            regime,
        )

        text.append(
            f"{asset:<6} {heat['score']:>3}/100   {regime['emoji']} {regime['regime']}"
        )

    return "\n".join(text)
