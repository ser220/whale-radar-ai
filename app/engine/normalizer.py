from typing import Optional


def normalize_entity(name: Optional[str]) -> Optional[str]:
    if not name:
        return None

    n = name.strip()
    low = n.lower()

    rules = {
        "binance": "Binance",
        "coinbase": "Coinbase",
        "okx": "OKX",
        "bybit": "Bybit",
        "kraken": "Kraken",
        "bitstamp": "Bitstamp",
        "bitfinex": "Bitfinex",
        "gate": "Gate.io",
        "kucoin": "KuCoin",
        "htx": "HTX",
        "huobi": "HTX",
        "upbit": "Upbit",
        "tether treasury": "Tether Treasury",
        "wintermute": "Wintermute",
        "blackrock": "BlackRock",
    }

    for key, value in rules.items():
        if key in low:
            return value

    return n


def normalize_asset(asset: Optional[str]) -> Optional[str]:
    if not asset:
        return None

    a = asset.strip().upper()

    mapping = {
        "WETH": "ETH",
        "WBTC": "BTC",
        "BSC-USD": "USDT",
        "TETHER": "USDT",
        "USD COIN": "USDC",
    }

    return mapping.get(a, a)
