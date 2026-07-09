def calculate_source_consensus(event) -> dict:
    source = getattr(event, "source", "unknown") or "unknown"

    sources = [source]

    unique_sources = sorted(set(sources))
    count = len(unique_sources)

    if count >= 4:
        confidence_boost = 20
        label = "Very Strong Multi-Source Confirmation"
    elif count == 3:
        confidence_boost = 15
        label = "Strong Multi-Source Confirmation"
    elif count == 2:
        confidence_boost = 10
        label = "Confirmed by Multiple Sources"
    else:
        confidence_boost = 0
        label = "Single Source Signal"

    return {
        "sources": unique_sources,
        "count": count,
        "confidence_boost": confidence_boost,
        "label": label,
    }
