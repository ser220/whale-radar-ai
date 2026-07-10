import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from app.storage.history import get_recent_events, get_events_count
from app.engine.daily_radar import build_daily_radar
from app.engine.dashboard import build_dashboard
from app.engine.institutional_leaders import get_institutional_leaders
from app.engine.market_intelligence import build_market_snapshot
from app.engine.rotation import format_rotation
from app.storage.last_signal import get_last_signal
from app.telegram.formatter import format_signal
from app.engine.outcome_engine import evaluate_open_predictions
from app.engine.outcome_engine import evaluate_open_predictions
from app.engine.learning_engine import get_learning_stats, format_learning_stats
from app.engine.module_learning import get_module_learning_stats, format_module_learning_stats
from app.engine.adaptive_weights import get_adaptive_weights, format_adaptive_weights
from app.engine.adaptive_weights import get_adaptive_weights, format_adaptive_weights
from app.engine.learning_engine import get_learning_stats, format_learning_stats
from app.engine.context_learning import get_context_stats, format_context_stats
from app.engine.pattern_memory import get_pattern_memory, format_pattern_memory
from app.engine.pattern_memory import get_structured_patterns, format_structured_patterns
from app.engine.calibration_engine import calculate_calibration_weights, format_calibration_weights
from app.engine.calibration_audit import build_calibration_audit, format_calibration_audit
from app.engine.maintenance_engine import build_maintenance_report, format_maintenance_report
from app.engine.health_center import build_health_center, format_health_center
from app.services.prediction_review_service import (
    PredictionReviewService,
    format_prediction_review,
)



load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🐋 Whale Radar AI is online.\n\n"
        "Commands:\n"
        "/history - show recent events\n"
        "/status - show bot status"
    )


async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    events = get_recent_events(5)

    if not events:
        await update.message.reply_text("📭 History is empty")
        return

    lines = ["📜 Recent Whale Radar Events\n"]

    for e in events:
        amount = f"${e['amount_usd']:,.0f}"
        lines.append(
            f"#{e['id']} {e['asset']}\n"
            f"{amount}\n"
            f"{e['from_entity']} → {e['to_entity']}\n"
            f"{e['timestamp']}\n"
        )

    await update.message.reply_text("\n".join(lines))


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = get_events_count()

    await update.message.reply_text(
        "✅ Whale Radar AI is online.\n\n"
        f"Events in database: {count}\n"
        "Status: running"
    )

async def daily(update, context):
    text = build_daily_radar()
    await update.message.reply_text(text, parse_mode="HTML")

async def dashboard(update, context):
    text = build_dashboard()
    await update.message.reply_text(text, parse_mode="HTML")

async def leaders(update, context):
    leaders_list = get_institutional_leaders(10)

    if not leaders_list:
        await update.message.reply_text("🏛 No institutional leaders yet.")
        return

    medals = ["🥇", "🥈", "🥉"]
    lines = [
        "🏛 <b>Institutional Leaders</b>",
        "",
        "Top assets by latest Institutional Score:",
        "",
    ]

    for i, item in enumerate(leaders_list, start=1):
        medal = medals[i - 1] if i <= 3 else f"{i}."
        lines.append(
            f"{medal} <b>{item['asset']}</b>\n"
            f"Score: {item['score']}/100\n"
            f"Heat: {item['heat']}/100\n"
            f"Regime: {item['regime']}\n"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")

async def pulse(update, context):
    snapshot = build_market_snapshot()

    lines = [
        "🌡 <b>Market Pulse</b>",
        "",
        f"Score: {snapshot['market_score']}/100",
        f"State: {snapshot['market_state']}",
        "",
        "🏛 <b>Top Leaders</b>",
    ]

    for item in snapshot["leaders"][:5]:
        lines.append(
            f"{item['asset']} — {item['score']}/100, "
            f"Heat {item['heat']}/100, {item['regime']}"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")    

async def rotation(update, context):
    text = format_rotation(24)
    await update.message.reply_text(text, parse_mode="HTML")

async def details(update, context):
    last = get_last_signal()

    if not last:
        await update.message.reply_text("No last signal yet.")
        return

    intel = last["intel"]
    event = last["event"]

    text = f"""
<b>FULL SIGNAL DETAILS</b>

<b>Asset:</b> {event["asset"]}
<b>Amount:</b> ${event["amount_usd"]:,.0f}
<b>From:</b> {event["from_entity"]}
<b>To:</b> {event["to_entity"]}
<b>Network:</b> {event["chain"]}

<b>Overall AI Opinion:</b>
{intel["overall_opinion"]}

<b>Smart Money Narrative:</b>
{intel["smart_narrative"]}

<b>Institutional Score:</b>
{intel["institutional_score"]}

<b>Institutional Confidence:</b>
{intel["institutional_confidence"]}

<b>AI Probability:</b>
{intel["probability"]}

<b>AI Trade Decision:</b>
{intel["trade_decision"]}

<b>Signal Rating:</b>
{intel["signal_rating"]}

<b>Alert Priority:</b>
{intel["alert_priority"]}

<b>Similar Historical Events:</b>
{intel["similar_events"]}

<b>Market Heat:</b>
{intel["market_heat"]}

<b>Asset Intelligence:</b>
{intel["asset_ai"]}

<b>Wallet Ranking:</b>
{intel["wallet_rank"]}

<b>Wallet Intelligence:</b>
{intel["wallet_ai"]}

<b>Market Regime:</b>
{intel["market_regime"]}

<b>Whale Pressure:</b>
{intel["pressure"]}

<b>24h Context:</b>
{intel["context"]}

<b>Exchange Context:</b>
{intel["exchange_context"]}

<b>Wallet Context:</b>
{intel["wallet_context"]}
""".strip()

    await update.message.reply_text(text, parse_mode="HTML")


async def outcomes(update, context):
    result = evaluate_open_predictions()

    text = (
        "📊 <b>Outcome Evaluator</b>\n\n"
        f"Checked: {result['checked']}\n"
        f"Hits: {result['hits']}\n"
        f"Hit Rate: {result['hit_rate']}%"
    )

    await update.message.reply_text(text, parse_mode="HTML")

async def learning(update, context):
    stats = get_learning_stats()

    text = (
        "🧠 <b>Self Learning AI</b>\n\n"
        f"{format_learning_stats(stats)}"
    )

    await update.message.reply_text(text, parse_mode="HTML")

async def modules(update, context):
    rows = get_module_learning_stats()
    text = format_module_learning_stats(rows)
    await update.message.reply_text(text, parse_mode="HTML")

async def weights(update, context):
    w = get_adaptive_weights()

    text = (
        "⚖️ <b>Adaptive Weights</b>\n\n"
        f"{format_adaptive_weights(w)}"
    )

    await update.message.reply_text(text, parse_mode="HTML")

async def brain(update, context):
    weights = get_adaptive_weights()
    learning = get_learning_stats()

    text = (
        "🧠 <b>Whale Radar AI Brain</b>\n\n"
        "<b>Learning Stats:</b>\n"
        f"{format_learning_stats(learning)}\n\n"
        "<b>Adaptive Weights:</b>\n"
        f"{format_adaptive_weights(weights)}\n\n"
        "Mode: Shadow / Observation\n"
        "Status: Adaptive logic active, not yet controlling final decisions."
    )

    await update.message.reply_text(text, parse_mode="HTML")

async def context(update, context):
    rows = get_context_stats()
    text = format_context_stats(rows)
    await update.message.reply_text(text, parse_mode="HTML")

async def patterns(update, context):
    data = get_pattern_memory()
    text = format_pattern_memory(data)
    await update.message.reply_text(text, parse_mode="HTML")

async def structured_patterns(update, context):
    rows = get_structured_patterns()
    text = format_structured_patterns(rows)
    await update.message.reply_text(text, parse_mode="HTML")

async def calibration(update, context):
    weights = calculate_calibration_weights()
    text = format_calibration_weights(weights)
    await update.message.reply_text(text, parse_mode="HTML")

async def audit(update, context):
    data = build_calibration_audit()
    text = format_calibration_audit(data)
    await update.message.reply_text(text, parse_mode="HTML")

async def maintenance(update, context):
    report = build_maintenance_report()
    text = format_maintenance_report(report)
    await update.message.reply_text(text, parse_mode="HTML")

async def health(update, context):
    data = build_health_center()
    text = format_health_center(data)
    await update.message.reply_text(text, parse_mode="HTML")

async def outcome(update, context):
    if not context.args:
        await update.message.reply_text(
            "Usage: /outcome <prediction_id>"
        )
        return

    try:
        prediction_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "Prediction ID must be a number."
        )
        return

    service = PredictionReviewService()
    review = service.get_review(prediction_id)
    text = format_prediction_review(review)

    await update.message.reply_text(
        text,
        parse_mode="HTML",
    )

def run_bot():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is missing in .env")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("dashboard", dashboard))
    app.add_handler(CommandHandler("leaders", leaders)) 
    app.add_handler(CommandHandler("pulse", pulse))
    app.add_handler(CommandHandler("rotation", rotation))
    app.add_handler(CommandHandler("details", details))
    app.add_handler(CommandHandler("outcomes", outcomes))
    app.add_handler(CommandHandler("learning", learning))
    app.add_handler(CommandHandler("modules", modules))
    app.add_handler(CommandHandler("weights", weights))
    app.add_handler(CommandHandler("brain", brain))
    app.add_handler(CommandHandler("context", context))
    app.add_handler(CommandHandler("patterns", patterns))
    app.add_handler(CommandHandler("structured_patterns", structured_patterns))
    app.add_handler(CommandHandler("calibration", calibration))
    app.add_handler(CommandHandler("audit", audit))
    app.add_handler(CommandHandler("maintenance", maintenance))
    app.add_handler(CommandHandler("health", health))
    app.add_handler(CommandHandler("outcome", outcome))

    print("Telegram polling bot started...")
    app.run_polling()


if __name__ == "__main__":
    run_bot()
