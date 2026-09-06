from typing import Annotated, Any

from fastapi import APIRouter, Depends

from app.db import get_conn
from app.models.delivery import DeliveryOut, Outcome
from app.repositories import delivery as delivery_repo

router = APIRouter(prefix="/deliveries", tags=["deliveries"])


@router.get("", status_code=200, response_model=DeliveryOut)
async def get_deliveries(
    conn: Annotated[Any, Depends(get_conn)],
    status: Outcome = Outcome.DEAD,
):
    rows = await delivery_repo.list_by_status(conn, status)

    return DeliveryOut(count=len(rows), deliveries=[dict(row) for row in rows])
