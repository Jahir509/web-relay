from uuid import UUID

from pydantic import BaseModel


class EventIn(BaseModel):
    event_type: str
    payload: dict


class EventOut(BaseModel):
    id: UUID
    event_type: str
    deliveries_created: int


class EventDetail(BaseModel):
    id: UUID
    event_type: str
    payload: dict
