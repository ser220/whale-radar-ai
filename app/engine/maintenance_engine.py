from app.engine.diagnostics import build_ai_diagnostics


MAINTENANCE_MAP = {
    "Risk Engine": {
        "file": "app/engine/outcome_engine.py",
        "function": "evaluate_open_predictions",
        "issue": "Risk Engine appears to receive no successful outcome feedback.",
        "recommendation": "Check whether risk-specific validation is being mapped to module learning correctly.",
    },
    "Scenario Engine": {
        "file": "app/engine/outcome_engine.py",
        "function": "evaluate_open_predictions",
        "issue": "Scenario Engine accuracy is zero or unusually low.",
        "recommendation": "Check whether scenario success is judged only by target hit instead of scenario outcome.",
    },
    "Decision Engine": {
        "file": "app/engine/module_evaluator.py",
        "function": "evaluate_modules",
        "issue": "Decision Engine accuracy is unusually low.",
        "recommendation": "Check whether final decision is being penalized too strictly by target-only validation.",
    },
    "Probability Engine": {
        "file": "app/engine/probability_engine.py",
        "function": "calculate_probability",
        "issue": "Probability Engine may need calibration if accuracy deteriorates.",
        "recommendation": "Compare predicted probability buckets against actual hit rates.",
    },
    "Campaign Detector": {
        "file": "app/engine/campaign_detector.py",
        "function": "detect_campaign",
        "issue": "Campaign Detector may need review if campaign accuracy deteriorates.",
        "recommendation": "Check whether repeated transfers are classified correctly by direction and wallet.",
    },
    "Wallet Behaviour": {
        "file": "app/engine/wallet_behaviour.py",
        "function": "analyze_wallet_behaviour",
        "issue": "Wallet Behaviour may need review if accuracy deteriorates.",
        "recommendation": "Check whether exchange inflow/outflow behaviour matches actual price response.",
    },
}


def build_maintenance_report():
    diagnostics = build_ai_diagnostics()

    reports = []

    for module in diagnostics["modules"]:
        name = module["module"]
        health = module["health"]

        if health == "Healthy":
            continue

        info = MAINTENANCE_MAP.get(name, {})

        reports.append({
            "module": name,
            "health": health,
            "accuracy": module["accuracy"],
            "predictions": module["predictions"],
            "status": module["status"],
            "file": info.get("file", "Unknown"),
            "function": info.get("function", "Unknown"),
            "issue": info.get("issue", module["possible_causes"][0] if module["possible_causes"] else "Unknown issue."),
            "recommendation": info.get("recommendation", module["recommendations"][0] if module["recommendations"] else "Review module logic."),
        })

    return {
        "items": reports,
        "count": len(reports),
        "calibration_ready": diagnostics["calibration_ready"],
    }


def format_maintenance_report(data):
    lines = [
        "🛠 <b>AI Maintenance Engine</b>",
        "",
    ]

    if not data["items"]:
        lines.append("No maintenance issues detected.")
        lines.append("Calibration Ready: YES ✅")
        return "\n".join(lines)

    for item in data["items"]:
        lines.append(
            f"<b>{item['module']}</b>\n"
            f"Health: {item['health']}\n"
            f"Predictions: {item['predictions']}\n"
            f"Accuracy: {item['accuracy']}%\n"
            f"Likely file: <code>{item['file']}</code>\n"
            f"Likely function: <code>{item['function']}</code>\n"
            f"Issue: {item['issue']}\n"
            f"Recommendation: {item['recommendation']}\n"
        )
        lines.append("────────────")

    lines.append(f"Maintenance Items: {data['count']}")
    lines.append(f"Calibration Ready: {'YES ✅' if data['calibration_ready'] else 'NO ❌'}")

    return "\n".join(lines)
