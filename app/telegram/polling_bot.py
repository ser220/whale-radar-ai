import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from app.storage.history import get_recent_events, get_events_count
from app.engine.daily_radar import build_daily_radar
from app.engine.dashboard import build_dashboard


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


def run_bot():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is missing in .env")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("dashboard", dashboard))


    print("Telegram polling bot started...")
    app.run_polling()


if __name__ == "__main__":
    run_bot()
