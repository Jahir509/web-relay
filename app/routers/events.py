from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.db import get_conn
from app.models.event import EventDetail, EventIn, EventOut
from app.repositories import delivery as delivery_repo
from app.repositories import endpoint as endpoint_repo
from app.repositories import message as message_repo

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", status_code=202, response_model=EventOut)
async def publish_event(event: EventIn, conn: Annotated[Any, Depends(get_conn)]):
    async with conn.transaction():
        row = await message_repo.create(conn, event.event_type, event.payload)
        # endpoint_id = await endpoint_repo.get_first_id(conn)
        # await delivery_repo.create(conn, row["id"], endpoint_id)
        deliveries = await delivery_repo.fan_out(conn, row["id"],row["event_type"])

    return EventOut(id=row["id"], event_type=row["event_type"],deliveries_created=len(deliveries),
)


@router.get("/{event_id}", status_code=200, response_model=EventDetail)
async def get_event(event_id: UUID, conn: Annotated[Any, Depends(get_conn)]):
    row = await message_repo.get(conn, event_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Event with ID {event_id} not found.")

    return EventDetail(id=row["id"], event_type=row["event_type"], payload=row["payload"])
