import secrets
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends

from app.db import get_conn
from app.models.endpoint import EndpointIn, EndpointOut
from app.repositories import delivery as delivery_repo
from app.repositories import endpoint as endpoint_repo

router = APIRouter(prefix="/endpoints", tags=["endpoints"])


@router.post("", status_code=201, response_model=EndpointOut)
async def create_endpoint(endpoint: EndpointIn, conn: Annotated[Any, Depends(get_conn)]):
    secret = "whsec_" + secrets.token_urlsafe(32)
    row = await endpoint_repo.create(conn, endpoint.url, secret,endpoint.event_types)

    return EndpointOut(id=row["id"], url=row["url"], secret=row["secret"], event_types=row["event_types"])


@router.post("/{endpoint_id}/replay", status_code=200)
async def replay_deliveries(endpoint_id: UUID, conn: Annotated[Any, Depends(get_conn)]):
    rows = await delivery_repo.replay_dead(conn, endpoint_id)

    return {"replayed": len(rows)}
