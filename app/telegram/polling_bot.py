import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from app.storage.history import get_recent_events, get_events_count

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


def run_bot():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is missing in .env")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("status", status))

    print("Telegram polling bot started...")
    app.run_polling()


if __name__ == "__main__":
    run_bot()
