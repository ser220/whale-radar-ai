from app.engine.module_learning import get_module_learning_stats


DEFAULT_WEIGHTS = {
    "Probability Engine": 1.00,
    "Campaign Detector": 1.00,
    "Wallet Behaviour": 1.00,
    "Scenario Engine": 1.00,
    "Decision Engine": 1.00,
    "Risk Engine": 1.00,
}


def get_adaptive_weights():
    rows = get_module_learning_stats()

    weights = DEFAULT_WEIGHTS.copy()

    for row in rows:

        acc = row["accuracy"]

        if row["predictions"] < 20:
            weight = 1.00

        elif acc >= 95:
            weight = 1.20

        elif acc >= 90:
            weight = 1.10

        elif acc >= 80:
            weight = 1.00

        elif acc >= 70:
            weight = 0.90

        elif acc >= 60:
            weight = 0.80

        else:
            weight = 0.70

        weights[row["module"]] = weight

    return weights


def format_adaptive_weights(weights):

    lines = []

    for module, weight in weights.items():
        lines.append(
            f"{module}: x{weight:.2f}"
        )

    return "\n".join(lines)
