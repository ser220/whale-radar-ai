import os
import requests
from dotenv import load_dotenv

load_dotenv()


BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


def send_telegram_message(text: str) -> bool:
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is missing in .env")

    if not CHAT_ID:
        raise ValueError("CHAT_ID is missing in .env")

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    response = requests.post(url, json=payload, timeout=10)

    if response.status_code != 200:
        print("Telegram error:", response.text)
        return False

    return True
