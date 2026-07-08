import json
from pathlib import Path

LAST_SIGNAL_PATH = Path("data/last_signal.json")


def save_last_signal(event, score_data, intel):
    LAST_SIGNAL_PATH.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "event": {
            "asset": event.asset,
            "amount_usd": event.amount_usd,
            "from_entity": event.from_entity,
            "to_entity": event.to_entity,
            "chain": getattr(event, "chain", None) or getattr(event, "network", None),
            "tx_hash": event.tx_hash,
        },
        "score_data": score_data,
        "intel": intel,
    }

    LAST_SIGNAL_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_last_signal():
    if not LAST_SIGNAL_PATH.exists():
        return None

    return json.loads(LAST_SIGNAL_PATH.read_text(encoding="utf-8"))
