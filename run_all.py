import threading
import time
import uvicorn

from app.telegram.polling_bot import run_bot


def run_api():
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    print("Starting Whale Radar AI...")

    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()

    time.sleep(2)

    print("Whale Radar AI API started on http://127.0.0.1:8000")
    print("Starting Telegram bot...")

    run_bot()
