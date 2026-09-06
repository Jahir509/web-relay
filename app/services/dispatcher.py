import asyncio
import json
import logging
import time
from datetime import timedelta

import httpx

from app import db
from app.config import POLL_INTERVAL
from app.models.delivery import Outcome
from app.repositories import delivery as delivery_repo
from app.services import signing
from app.services.retry import classify, next_interval

logger = logging.getLogger(__name__)


async def send(client, row):
    body = json.dumps(row["payload"]).encode()
    timestamp = str(int(time.time()))
    started = time.monotonic()

    try:
        response = await client.post(
            row["url"],
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Timestamp": timestamp,
                "X-Signature": signing.sign(row["secret"], timestamp, body),
            },
        )
    except Exception as e:
        return {
            "outcome": Outcome.PENDING,
            "response_status": None,
            "response_body": None,
            "duration_ms": int((time.monotonic() - started) * 1000),
            "error": str(e),
        }

    return {
        "outcome": classify(response.status_code),
        "response_status": response.status_code,
        "response_body": response.text[:500],
        "duration_ms": int(response.elapsed.total_seconds() * 1000),
        "error": None,
    }


async def loop():
    async with httpx.AsyncClient(timeout=10) as client:
        while True:
            try:
                async with db.acquire() as conn:
                    rows = await delivery_repo.get_due(conn)
    
                    if rows:
                        logger.info("picked up %d deliveries", len(rows))
    
                    for row in rows:
                        result = await send(client, row)
                        status = result["outcome"]
                        if result["error"]:
                            logger.warning("delivery %s failed: %s", row["id"], result["error"])
    
                        interval = next_interval(row["attempt_count"])
                        if interval is None:
                            status = Outcome.DEAD
                            interval = timedelta(seconds=0)
    
                        await delivery_repo.record_attempt(conn, row["id"], status, interval,row["attempt_count"]+1,result)
            except Exception as e:
                logger.exception("dispatcher iteration failed")

            await asyncio.sleep(POLL_INTERVAL)
