def build_price_plan(direction: str, current_price: float) -> dict:
    if not current_price or current_price <= 0:
        return {
            "entry_zone": "Price data unavailable",
            "stop": "N/A",
            "tp1": "N/A",
            "tp2": "N/A",
            "rr": "N/A",
            "note": "Live price source is not connected yet.",
        }

    if direction == "bearish":
        entry_low = current_price * 1.003
        entry_high = current_price * 1.010
        stop = current_price * 1.018
        tp1 = current_price * 0.985
        tp2 = current_price * 0.965
        rr = 2.2
        note = "Short bias: wait for pullback into entry zone."

    elif direction == "bullish":
        entry_low = current_price * 0.990
        entry_high = current_price * 0.997
        stop = current_price * 0.982
        tp1 = current_price * 1.015
        tp2 = current_price * 1.035
        rr = 2.2
        note = "Long bias: wait for pullback into entry zone."

    else:
        return {
            "entry_zone": "No directional setup",
            "stop": "N/A",
            "tp1": "N/A",
            "tp2": "N/A",
            "rr": "N/A",
            "note": "No trade until direction confirms.",
        }

    return {
        "entry_zone": f"{entry_low:.2f} - {entry_high:.2f}",
        "stop": f"{stop:.2f}",
        "tp1": f"{tp1:.2f}",
        "tp2": f"{tp2:.2f}",
        "rr": rr,
        "note": note,
    }
