import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import db
from app.routers import deliveries, endpoints, events, sink
from app.services import dispatcher
from app.utils import info, success, warning

logging.basicConfig(level=logging.INFO, format="[LOG: %(levelname)s] %(message)s at %(asctime)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    info("Starting up database...")
    await db.connect()
    success("Database connection established.")

    task = asyncio.create_task(dispatcher.loop())
    success("Dispatcher loop started.")
    yield

    task.cancel()
    warning("Dispatcher loop stopped.")
    warning("Shutting down database...")
    await db.disconnect()


app = FastAPI(lifespan=lifespan)

app.include_router(events.router)
app.include_router(endpoints.router)
app.include_router(deliveries.router)
app.include_router(sink.router)


@app.get("/", status_code=200)
async def read_root():
    return {"status": "ok"}


@app.get("/health", status_code=200)
async def health_check():
    return {"status": "ok"}
