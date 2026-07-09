from typing import Dict


def evaluate_modules(
    prediction_hit: bool,
    probability: Dict,
    campaign: Dict,
    wallet_behaviour: Dict,
    scenario: Dict,
) -> Dict[str, bool]:

    result = {}

    # Decision Engine
    result["Decision Engine"] = prediction_hit

    # Scenario Engine
    result["Scenario Engine"] = prediction_hit

    # Probability Engine
    if probability.get("bearish", 0) >= 80:
        result["Probability Engine"] = prediction_hit
    else:
        result["Probability Engine"] = True

    # Campaign Detector
    if campaign.get("confidence", 0) >= 90:
        result["Campaign Detector"] = prediction_hit
    else:
        result["Campaign Detector"] = True

    # Wallet Behaviour
    if wallet_behaviour.get("confidence") == "Very High":
        result["Wallet Behaviour"] = prediction_hit
    else:
        result["Wallet Behaviour"] = True

    # Risk Engine
    result["Risk Engine"] = prediction_hit

    return result
