TARGET_PROJECTION_KEYS = {
    "expected_move_pct",
    "target",
    "eta",
    "confidence",
    "note",
}

INTEL_RAW_KEYS = {
    "current_price",
    "target_projection_raw",
}

PREDICTION_HISTORY_FIELDS = {
    "asset",
    "direction",
    "entry_price",
    "target_price",
    "expected_move",
    "eta",
}

def has_required_keys(data: dict, required_keys: set) -> bool:
    if not isinstance(data, dict):
        return False

    return required_keys.issubset(set(data.keys()))
