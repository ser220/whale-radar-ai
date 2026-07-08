import requests


BINANCE_URL = "https://api.binance.com/api/v3/ticker/price"


def get_price(symbol: str):
    """
    Returns current spot price from Binance.

    Example:
        BTC -> 112345.44
        ETH -> 3645.21
        BNB -> 689.54
    """

    try:
        pair = f"{symbol.upper()}USDT"

        r = requests.get(
            BINANCE_URL,
            params={"symbol": pair},
            timeout=5,
        )

        if r.status_code != 200:
            return None

        data = r.json()

        return float(data["price"])

    except Exception:
        return None
