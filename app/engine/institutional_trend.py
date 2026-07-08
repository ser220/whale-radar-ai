from collections import deque
from time import time

_history = {}

WINDOW_HOURS = 24


def record_score(asset: str, score: int):
    now = time()

    if asset not in _history:
        _history[asset] = deque()

    _history[asset].append((now, score))

    while _history[asset]:
        ts, _ = _history[asset][0]
        if now - ts > WINDOW_HOURS * 3600:
            _history[asset].popleft()
        else:
            break


def get_trend(asset: str):
    if asset not in _history or len(_history[asset]) < 2:
        return {
            "change": 0,
            "direction": "flat",
            "text": "Collecting institutional history..."
        }

    first = _history[asset][0][1]
    last = _history[asset][-1][1]

    delta = last - first

    if delta >= 15:
        direction = "up"
        text = f"🟢 Institutional demand rising (+{delta})"

    elif delta <= -15:
        direction = "down"
        text = f"🔴 Institutional demand falling ({delta})"

    else:
        direction = "flat"
        text = f"🟡 Stable ({delta:+})"

    return {
        "change": delta,
        "direction": direction,
        "text": text
    }
