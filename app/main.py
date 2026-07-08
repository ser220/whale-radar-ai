from fastapi import FastAPI, Request, Header, HTTPException
from app.sources.manager import source_manager
from app.engine.pipeline import process_event

app = FastAPI(title="Whale Radar AI")

WEBHOOK_SECRET = "whale_secret_123"


@app.get("/")
def health_check():
    return {"status": "ok", "service": "Whale Radar AI"}


@app.post("/webhook/arkham")
async def arkham_webhook(
    request: Request,
    x_webhook_secret: str = Header(default="")
):
    if x_webhook_secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    payload = await request.json()
    event = source_manager.parse("arkham", payload)

    if not event:
        return {
            "ok": False,
            "error": "invalid_arkham_payload",
        }

    result = process_event(event)

    return {"ok": True, "result": result}
