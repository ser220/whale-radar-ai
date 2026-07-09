from app.engine.calibration_audit import build_calibration_audit


def build_ai_diagnostics():
    audit = build_calibration_audit()

    diagnostics = []

    for module in audit["modules"]:
        status = module["status"]
        accuracy = module["accuracy"]
        predictions = module["predictions"]

        possible_causes = []
        recommendations = []

        if predictions < 30:
            health = "Learning"
            possible_causes.append("Not enough historical samples yet.")
            recommendations.append("Collect more validated outcomes.")

        elif accuracy == 0:
            health = "Critical"
            possible_causes.append("No successful validations recorded.")
            possible_causes.append("Outcome feedback may be missing or too strict.")
            recommendations.append("Review outcome validation logic.")

        elif accuracy < 10:
            health = "Warning"
            possible_causes.append("Accuracy is unusually low.")
            possible_causes.append("Module may be penalized by incorrect outcome mapping.")
            recommendations.append("Check module-specific learning rules.")

        elif accuracy > 98:
            health = "Warning"
            possible_causes.append("Accuracy is unusually high.")
            possible_causes.append("Possible overfitting or insufficient diversity.")
            recommendations.append("Verify sample quality.")

        else:
            health = "Healthy"
            possible_causes.append("Statistics look usable.")
            recommendations.append("Continue monitoring.")

        diagnostics.append({
            "module": module["module"],
            "status": status,
            "health": health,
            "predictions": predictions,
            "accuracy": accuracy,
            "possible_causes": possible_causes,
            "recommendations": recommendations,
        })

    return {
        "modules": diagnostics,
        "healthy": audit["healthy"],
        "review": audit["review"],
        "calibration_ready": audit["ready"],
    }


def format_ai_diagnostics(data):
    lines = ["🧠 <b>AI Observatory</b>", ""]

    for module in data["modules"]:
        lines.append(
            f"<b>{module['module']}</b>\n"
            f"{module['status']}\n"
            f"Health: {module['health']}\n"
            f"Predictions: {module['predictions']}\n"
            f"Accuracy: {module['accuracy']}%\n"
        )

        lines.append("Possible causes:")
        for cause in module["possible_causes"]:
            lines.append(f"• {cause}")

        lines.append("Recommendation:")
        for rec in module["recommendations"]:
            lines.append(f"• {rec}")

        lines.append("────────────")

    lines.append(
        f"Healthy Modules: {data['healthy']}"
    )
    lines.append(
        f"Needs Review: {data['review']}"
    )
    lines.append(
        f"Calibration Ready: {'YES ✅' if data['calibration_ready'] else 'NO ❌'}"
    )

    return "\n".join(lines)
