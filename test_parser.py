from app.sources.arkham_parser import parse_arkham_payload

payload = {
    "symbol": "weth",
    "valueUsd": 75000000,
    "fromLabel": "Binance Hot Wallet 14",
    "toLabel": "Unknown Wallet",
    "chain": "Ethereum",
    "txHash": "abc123",
}

event = parse_arkham_payload(payload)
print(event)
