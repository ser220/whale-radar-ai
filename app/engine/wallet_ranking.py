KNOWN_WALLETS = {
    "blackrock": {
        "rank": 100,
        "label": "★★★★★ Elite Institutional Wallet",
        "type": "Asset Manager",
        "weight": 1.30,
    },
    "coinbase prime": {
        "rank": 95,
        "label": "★★★★★ Prime Custody / Institutional",
        "type": "Custody",
        "weight": 1.25,
    },
    "jump trading": {
        "rank": 95,
        "label": "★★★★★ Elite Market Maker",
        "type": "Market Maker",
        "weight": 1.25,
    },
    "wintermute": {
        "rank": 90,
        "label": "★★★★ Major Market Maker",
        "type": "Market Maker",
        "weight": 1.20,
    },
    "binance": {
        "rank": 85,
        "label": "★★★★ Major Exchange Wallet",
        "type": "Exchange",
        "weight": 1.15,
    },
    "coinbase": {
        "rank": 85,
        "label": "★★★★ Major Exchange Wallet",
        "type": "Exchange",
        "weight": 1.15,
    },
    "okx": {
        "rank": 80,
        "label": "★★★★ Major Exchange Wallet",
        "type": "Exchange",
        "weight": 1.10,
    },
}


def rank_wallet(wallet_name: str) -> dict:
    name = (wallet_name or "Unknown Wallet").lower()

    for key, profile in KNOWN_WALLETS.items():
        if key in name:
            return {
                "wallet": wallet_name,
                "rank": profile["rank"],
                "label": profile["label"],
                "type": profile["type"],
                "weight": profile["weight"],
            }

    if "unknown" in name:
        return {
            "wallet": wallet_name or "Unknown Wallet",
            "rank": 45,
            "label": "★★ Unknown Wallet",
            "type": "Unknown",
            "weight": 1.00,
        }

    return {
        "wallet": wallet_name or "Unknown Wallet",
        "rank": 55,
        "label": "★★★ Tracked Wallet",
        "type": "Tracked",
        "weight": 1.05,
    }
