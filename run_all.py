import threading
import time
import uvicorn

from app.storage.database import init_db
from app.telegram.polling_bot import run_bot


def run_api():
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    print("Starting Whale Radar AI...")

    init_db()
    print("Database initialized")

    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()

    time.sleep(2)

    print("Whale Radar AI API started on http://127.0.0.1:8000")
    print("Starting Telegram bot...")

    run_bot()
