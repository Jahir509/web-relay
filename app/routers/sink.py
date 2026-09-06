import time

from fastapi import APIRouter, HTTPException, Request

from app.config import SINK_SECRET
from app.services import signing

router = APIRouter(prefix="/sink", tags=["sink"])


@router.post("")
async def sink(request: Request):
    timestamp = request.headers.get("x-timestamp")
    received_signature = request.headers.get("x-signature")

    if not timestamp or not received_signature:
        raise HTTPException(401, "missing headers")

    try:
        age = time.time() - int(timestamp)
    except (TypeError, ValueError):
        raise HTTPException(401, "invalid timestamp")

    raw = await request.body()

    if abs(age) > 300:
        raise HTTPException(401, "request too old")

    if not signing.verify(SINK_SECRET, timestamp, raw, received_signature):
        raise HTTPException(401, "invalid signature")

    return {"received": True}
