from app.engine.calibration_audit import build_calibration_audit
from app.engine.learning_engine import get_learning_stats
from app.engine.maintenance_engine import build_maintenance_report
from app.engine.module_learning import get_module_learning_stats
from app.engine.pattern_memory import get_structured_patterns


def build_health_center():
    learning = get_learning_stats()
    modules = get_module_learning_stats()
    audit = build_calibration_audit()
    maintenance = build_maintenance_report()
    patterns = get_structured_patterns()

    total_modules = len(modules)
    healthy_modules = audit["healthy"]
    review_modules = audit["review"]

    top_pattern = patterns[0] if patterns else None

    if audit["ready"] and maintenance["count"] == 0:
        overall = "🟢 Healthy"
    elif review_modules <= 2:
        overall = "🟡 Needs Monitoring"
    else:
        overall = "🟠 Needs Review"

    return {
        "learning": learning,
        "total_modules": total_modules,
        "healthy_modules": healthy_modules,
        "review_modules": review_modules,
        "calibration_ready": audit["ready"],
        "maintenance_items": maintenance["count"],
        "top_pattern": top_pattern,
        "overall": overall,
    }


def format_health_center(data):
    learning = data["learning"]
    top_pattern = data["top_pattern"]

    lines = [
        "🧠 <b>Whale Radar AI Health</b>",
        "",
        f"Overall Status: {data['overall']}",
        "",
        "<b>Learning</b>",
        f"Signals Checked: {learning['total']}",
        f"Hit Rate: {learning['hit_rate']}%",
        f"Avg Accuracy: {learning['avg_accuracy']}%",
        f"Reliability: {learning['label']}",
        "",
        "<b>Modules</b>",
        f"Healthy: {data['healthy_modules']}/{data['total_modules']}",
        f"Needs Review: {data['review_modules']}",
        "",
        "<b>Calibration</b>",
        f"Ready: {'YES ✅' if data['calibration_ready'] else 'NO ❌'}",
        "",
        "<b>Maintenance</b>",
        f"Open Items: {data['maintenance_items']}",
        "",
        "<b>Top Pattern</b>",
    ]

    if top_pattern:
        lines.extend([
            f"Asset: {top_pattern['asset']}",
            f"Bias: {top_pattern['direction']}",
            f"Regime: {top_pattern['regime']}",
            f"Heat: {top_pattern['heat']}",
            f"Wallet: {top_pattern['wallet_behaviour']}",
            f"Seen: {top_pattern['seen']}",
            f"Accuracy: {top_pattern['accuracy']}%",
        ])
    else:
        lines.append("No pattern data yet.")

    return "\n".join(lines)
