from uuid import UUID

from pydantic import BaseModel,Field
from enum import Enum



class EventType(str, Enum):
    ORDER_PAID = "order.paid"
    ORDER_CANCELLED = "order.cancelled"
    REFUND_ISSUED = "refund.issued"
    REFUND_CANCELLED = "refund.cancelled"


class EndpointIn(BaseModel):
    url: str
    event_types: list[EventType] = Field(default_factory=list)


class EndpointOut(BaseModel):
    id: UUID
    url: str
    secret: str
    event_types: list[EventType] = Field(default_factory=list)
