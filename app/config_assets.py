"""
Whale Radar AI
Institutional Asset Registry v1.0
"""

ASSETS = {

# ==========================================================
# CORE
# ==========================================================

"BTC": {
    "tier": "S",
    "type": "crypto",
    "sector": "Store of Value",
    "importance": 100,
    "min_whale": 10_000_000,
    "weight": 1.00,
},

"ETH": {
    "tier": "S",
    "type": "crypto",
    "sector": "Smart Contract",
    "importance": 99,
    "min_whale": 8_000_000,
    "weight": 1.00,
},

"BNB": {
    "tier": "S",
    "type": "exchange",
    "sector": "Exchange",
    "importance": 98,
    "min_whale": 5_000_000,
    "weight": 1.10,
},

"SOL": {
    "tier": "S",
    "type": "crypto",
    "sector": "Smart Contract",
    "importance": 97,
    "min_whale": 5_000_000,
    "weight": 1.05,
},

"XRP": {
    "tier": "S",
    "type": "payments",
    "sector": "Payments",
    "importance": 96,
    "min_whale": 5_000_000,
    "weight": 1.05,
},

# ==========================================================
# TIER A
# ==========================================================

"TON": {
    "tier": "A",
    "type": "crypto",
    "sector": "Payments",
    "importance": 95,
    "min_whale": 3_000_000,
    "weight": 1.05,
},

"HYPE": {
    "tier": "A",
    "type": "crypto",
    "sector": "Perpetual",
    "importance": 94,
    "min_whale": 2_000_000,
    "weight": 1.20,
},

"LINK": {
    "tier": "A",
    "type": "oracle",
    "sector": "Infrastructure",
    "importance": 93,
    "min_whale": 2_000_000,
    "weight": 1.15,
},

"DOGE": {
    "tier": "A",
    "type": "meme",
    "sector": "Meme",
    "importance": 92,
    "min_whale": 2_000_000,
    "weight": 1.10,
},

"AVAX": {
    "tier": "A",
    "type": "crypto",
    "sector": "Smart Contract",
    "importance": 91,
    "min_whale": 2_000_000,
    "weight": 1.10,
},

"ADA": {
    "tier": "A",
    "type": "crypto",
    "sector": "Smart Contract",
    "importance": 90,
    "min_whale": 2_000_000,
    "weight": 1.10,
},

"TRX": {
    "tier": "A",
    "type": "payments",
    "sector": "Payments",
    "importance": 89,
    "min_whale": 2_000_000,
    "weight": 1.10,
},

"LTC": {
    "tier": "A",
    "type": "crypto",
    "sector": "Store of Value",
    "importance": 88,
    "min_whale": 2_000_000,
    "weight": 1.10,
},

"BCH": {
    "tier": "A",
    "type": "crypto",
    "sector": "Store of Value",
    "importance": 87,
    "min_whale": 2_000_000,
    "weight": 1.10,
},

"SUI": {
    "tier": "A",
    "type": "crypto",
    "sector": "Smart Contract",
    "importance": 86,
    "min_whale": 1_500_000,
    "weight": 1.15,
},
}
def get_asset_profile(symbol: str) -> dict:
    return ASSETS.get(symbol.upper(), {})


def is_supported_asset(symbol: str) -> bool:
    return symbol.upper() in ASSETS


def get_min_whale(symbol: str) -> float:
    profile = get_asset_profile(symbol)
    return profile.get("min_whale", 10_000_000)


def get_asset_weight(symbol: str) -> float:
    profile = get_asset_profile(symbol)
    return profile.get("weight", 1.0)
def get_asset_profile(symbol: str) -> dict:
    return ASSETS.get(symbol.upper(), {})


def get_asset_importance(symbol: str) -> int:
    return get_asset_profile(symbol).get("importance", 50)


def get_asset_tier(symbol: str) -> str:
    return get_asset_profile(symbol).get("tier", "C")


def get_asset_sector(symbol: str) -> str:
    return get_asset_profile(symbol).get("sector", "Unknown")
